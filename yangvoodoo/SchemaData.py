import json
import libyang

import logging
import uuid

from io import StringIO
from typing import List


class UnableToRenderFormError:
    pass


class UnableToDetermineQuotesError(UnableToRenderFormError):
    def __init__(self, value):
        super().__init__(
            f"Unable to find a quote style to use for the following value:\n{value}"
        )


class Expander:

    """
    Process the YANG model by reading through the schema of the yang model and expanding as necessary
    using the input data tree.

    It is not possible to transparently navigate through an empty list - as this would involve injecting
    artifical data for the list keys.

    This class is intended to be extended by 'presentation' classes in order to make use of the
    expanded data. The presentation is given a file-like object to write to.

    Examples:
      Yang2Text: provide human readable summarised yang models.
      HtmlForms: provide the given schema/data as an HTML form
      PlantUML Diagrams: provide an example schema with example data.
    """

    YANG_LOCATION = "yang"
    QUOTE_ESCAPE_STYLE = "select-single-vs-double"
    SCHEMA_NODE_TYPE_MAP = {
        1: "_handle_schema_containing_node",
        2: "_handle_schema_choice",
        4: "_handle_schema_leaf",
        8: "_handle_schema_leaflist",
        16: "_handle_schema_list",
    }

    def __init__(self, yang_module, log: logging.Logger):
        self.log = log
        self.yang_module = yang_module
        self.ctx = libyang.Context(self.YANG_LOCATION)
        self.ctx.load_module(yang_module)
        self.data_ctx = libyang.DataTree(self.ctx)

        self.result = StringIO()
        self.indent = 0

    def dumps(self):
        self.result.seek(0)
        print(self.result.read())

    def dump(self, filename):
        self.result.seek(0)
        with open(filename, "w") as fh:
            fh.write(self.result.read())

    def process(self, initial_data: str, format: int = 1):
        """

        In the process of navigating the schema we keep track of:
         - The schema path
         - The data path
         - And an artificial 'id' path
        """
        self.log.info("Processing: %s", self.yang_module)
        if initial_data:
            self.data_ctx.loads(initial_data, format)
        self.result = StringIO()

        self.write_header()

        self.write_title(self.ctx.get_module(self.yang_module))

        self.data_path_trail = [""]
        self.id_path_trail = [""]
        self.schema_path_trail = [""]
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            self._process_nodes(node)

        self.write_body()

        self.write_footer()

        return self.result

    def write_header(self):
        pass

    def write_footer(self):
        pass

    def write_title(self):
        pass

    def write_body(self):
        pass

    def _process_nodes(self, node):
        if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
            raise NotImplementedError(
                f"{node.schema_path()} has unknown type {node.nodetype()}"
            )
        getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    def _handle_schema_containing_node(self, node):
        self.grow_trail(node)
        presence = None
        if node.presence():
            presence = False
            value = self.get_data(raw=True)
            if value is not None:
                presence = True
        self.open_containing_node(node, presence=presence)

        try:
            for subnode in self.ctx.find_path(f"{node.schema_path()}/*"):
                self._process_nodes(subnode)
        except libyang.util.LibyangError:
            pass

        self.close_containing_node(node)
        self.shrink_trail()

    def _handle_schema_leaf(self, node):
        """
        Here we should return different data based on the leaf type
        i.e. boolean/empty leaves should be checkbox
        enumerations should be drop-down boxes
        we should extract description of the yang model as a tool tip

        we should deal with default values too when the data isn't set - perhaps with a lighter colour in the input
        than if it haves explicit values. (WOULD HAVE TO BE HANDLED IN Javascript so not worth the effort)
        """
        self.grow_trail(node)
        value = self.get_data(default=node.default())
        self.write_leaf(node, value, default=node.default(), key=node.is_key())
        self.shrink_trail()

    def _handle_schema_list(self, node):
        self.grow_trail(node)

        trail = "".join(self.data_path_trail)
        self.open_list(node, count=len(list(self.data_ctx.gets_xpath(trail))))

        for list_node in self.data_ctx.gets_xpath(trail):
            list_xpath = list_node[len(trail) :]
            self.grow_trail(list_element_predicates=list_xpath, schema=False)
            self._handle_list_element()
            self.shrink_trail(schema=False)

        self.close_list(node)

        self.shrink_trail()

    def _handle_list_element(self):
        keys = []
        xpath = "".join(self.data_path_trail)
        value = list(self.data_ctx.get_xpath(xpath))[0]

        self.open_list_element(key_values=list(value.get_list_key_values()))

        xpath = "".join(self.schema_path_trail)
        for subnode in self.ctx.find_path(f"{xpath}/*"):
            self._process_nodes(subnode)

        self.close_list_element()

    def _handle_schema_leaflist(self, node):
        self.grow_trail(node)

        trail = "".join(self.data_path_trail)
        self.open_leaflist(node, count=len(list(self.data_ctx.gets_xpath(trail))))

        for list_node in self.data_ctx.gets_xpath(trail):
            list_xpath = list_node[len(trail) :]
            self.grow_trail(list_element_predicates=list_xpath, schema=False)
            self.write_leaflist_item(self.get_data())
            self.shrink_trail(schema=False)

        self.close_leaflist(node)

        self.shrink_trail()

    def _handle_schema_choice(self, node):
        self.grow_trail(node, data=False)

        active_case = None
        cases = []
        for case in self.ctx.find_path(f"{node.schema_path()}/*"):
            if case.nodetype() == 64:
                cases.append(case)

        choice_path = node.schema_path()

        trail = "".join(self.data_path_trail)
        for data_xpath in self.data_ctx.gets_xpath(f"{trail}/*"):
            value = list(self.data_ctx.get_xpath(data_xpath))
            if value:
                for case in cases:
                    if value[0].get_schema_path().startswith(case.schema_path()):
                        active_case = case
                        break

        self.open_choice(node)

        for case in cases:
            self.grow_trail(case, data=False)
            self.open_case(case, active_case == case)

            try:
                for subnode in self.ctx.find_path(f"{case.schema_path()}/*"):
                    self._process_nodes(subnode)
            except libyang.util.LibyangError:
                pass

            self.close_case(case)
            self.shrink_trail(data=False)

        self.close_choice(node)

        self.shrink_trail(data=False)

    def get_data(self, default=None, quoted=True, raw=False):
        xpath = "".join(self.data_path_trail)
        value = list(self.data_ctx.get_xpath(xpath))
        if raw:
            if value:
                return value[0].value
            return None
        if value:
            self.log.debug("GET XPATH: %s = %s", xpath, value[0].value)
            quote = self.get_quote_style(value[0].value, quoted)
            return f"{quote}{self.escape_value(value[0].value)}{quote}"
        if default:
            quote = self.get_quote_style(default, quoted)
            return f"{quote}{self.escape_value(default)}{quote}"
        quote = self.get_quote_style(default, quoted)
        return f"{quote}{quote}"

    def get_quote_style(self, value, quoted=True):
        if self.QUOTE_ESCAPE_STYLE == "escape":
            return ""
        if not isinstance(value, str):
            return '"'
        if '"' in value and "'" in value:
            raise UnableToDetermineQuotesError(value)
        if "'" in value:
            return '"'
        return "'"

    def escape_value(self, value):
        if self.QUOTE_ESCAPE_STYLE == "escape":
            if isinstance(value, str):
                value.replace('"', '\\"')
        return value

    def shrink_trail(self, schema=True, data=True):
        if data:
            self.data_path_trail.pop()
        if schema:
            self.schema_path_trail.pop()
        self.id_path_trail.pop()
        self.log.debug("SHRINK: %s", self.data_path_trail)
        self.log.debug("SHRINK: %s", self.schema_path_trail)
        self.log.debug("SHRINK: %s", self.id_path_trail)

    def grow_trail(
        self, node=None, list_element_predicates=None, schema=True, data=True
    ):
        if data:
            if list_element_predicates:
                data_component = list_element_predicates
            elif (
                node.module().name() != self.yang_module
                or len(self.data_path_trail) == 1
            ):
                data_component = f"/{node.module().name()}:{node.name()}"
            else:
                data_component = f"/{node.name()}"
            self.data_path_trail.append(f"{data_component}")
            self.id_path_trail.append(f"{data_component}")
        else:
            self.id_path_trail.append(f"{node.name()}")
        if schema:
            self.schema_path_trail.append(f"/{node.module().name()}:{node.name()}")
        self.log.debug("GROW: %s", self.data_path_trail)
        self.log.debug("GROW: %s", self.schema_path_trail)
        self.log.debug("GROW: %s", self.id_path_trail)

    def get_id(self):
        if len(self.data_path_trail) == 1:
            return "'__root__'"
        trail = "".join(self.data_path_trail)
        quote = self.get_quote_style(trail)
        return f"{quote}{trail}{quote}"

    def get_uuid(self):
        trail = "".join(self.id_path_trail)
        return str(uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_URL, "pyvwu"), trail))

    def get_indent(self):
        return " " * self.indent * 2

    def open_indent(self):
        self.indent += 1
        return " " * (self.indent - 1) * 2

    def close_indent(self):
        self.indent -= 1
        return " " * self.indent * 2

    @staticmethod
    def pluralise(listobj):
        if isinstance(listobj, int):
            if listobj != 1:
                return "s"
            return ""
        if len(listobj) != 1:
            return "s"
        return ""

    @staticmethod
    def commaify(listobj):
        comma = ""
        for item in listobj:
            yield comma, item
            comma = ", "

    def get_human_types(self, node):
        if node.type().name() == "leafref":
            leafref_path = libyang.c2str(node._leaf.type.info.lref.path)
            yield f"leafref -> {leafref_path}"
        else:
            enums = [enum[0] for enum in node.type().all_enums()]
            if enums:
                yield f"enumeration [ {'; '.join(enums)} ]"
            for base_name in node.type().basenames():
                if str(base_name) not in ("enumeration",):
                    yield str(base_name)
