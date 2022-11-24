import json
import libyang

import logging
import uuid

from io import StringIO
from typing import List, Tuple


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
      Yang2Text: provide human readable summarised yang models (implemented in this project)

      In order to build a HTML form the hooks for `open_list` could map to a `+` button to add list elements,
      the `open_list_element` could map to a `-` button to remove a list element. The `open_xxx` and `close_xxx`
      methods could be used to open and close `<div>`'s.

      Output can be rendered for PlantUML (https://plantuml.com/json) in order to build diagrams.
    """

    YANG_LOCATION = "yang"
    QUOTE_ESCAPE_STYLE = "select-single-vs-double"
    INDENT_SPACING = 2
    SCHEMA_NODE_TYPE_MAP = {
        1: "_handle_schema_containing_node",
        2: "_handle_schema_choice",
        4: "_handle_schema_leaf",
        8: "_handle_schema_leaflist",
        16: "_handle_schema_list",
    }
    INCLUDE_BLANK_LIST_ELEMENTS = False

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

    def process(self, initial_data: str, format: int = 1) -> StringIO:
        """
        Process a starting data tree in a given format (XML=1, JSON=2) as recursing the schema expand
        to include any data that exists against each part of the schema. During expansion of the schema/data tree
        call a number of callbacks.

        The callbacks are provided as a `open` set which are called when starting to process a node which holds
        contents (i.e. a List, Leaf-List ListElement, Container, Choice, Case) and a `close` when processing of that
        node has finished.

        Terminating nodes (Leaves and items in a Leaf-List) are called with a `write` method.

        There are structural methods to write headers, titles, bodies and footers.

        In the process of navigating the schema we keep track of the hirearchy of the model in three 'trails', this
        allows us to keep a consistent view of the schema path, data path and a hybrid path.
        """
        self.log.info("Processing: %s", self.yang_module)
        if initial_data:
            self.data_ctx.loads(initial_data, format)
        self.result = StringIO()

        self.callback_write_header(self.ctx.get_module(self.yang_module))

        self.callback_write_title(self.ctx.get_module(self.yang_module))

        self.data_path_trail = [""]
        self.id_path_trail = [""]
        self.schema_path_trail = [""]
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            self._process_nodes(node)

        self.callback_write_body(self.ctx.get_module(self.yang_module))

        self.callback_write_footer(self.ctx.get_module(self.yang_module))

        return self.result

    def callback_write_header(self, module: libyang.schema.Module):
        """
        Called in order to provide information in a body before starting to process the yang model.

        Args:
            module: The libyang schema module
        """

    def callback_write_footer(self, module: libyang.schema.Module):
        """
        Called in order to provide information in a body before starting to process the yang model.

        Args:
            module: The libyang schema module
        """

    def callback_write_title(self, module: libyang.schema.Module):
        """
        Called in order to provide information in a body before starting to process the yang model.

        Args:
            module: The libyang schema module
        """

    def callback_write_body(self, module: libyang.schema.Module):
        """
        Called in order to provide information in a body before starting to process the yang model.

        Args:
            module: The libyang schema module
        """

    def callback_open_list(self, node: libyang.Node, count: int, node_id: str):
        """
        Called when the a list has been encountered, a list contains list elements.

        Args:
            node: The libyang node of the list statement
            count: The number of items in the list.
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_list")

    def callback_open_list_element(
        self,
        node: libyang.Node,
        key_values: List[Tuple[str, str]],
        empty_list_element: bool,
        node_id: str,
    ):
        """
        Called when the a list element has been encountered.

        Args:
            node: The libyang node of the list element statement
            key_values: A list of key and value tuples.
            empty_list_element: Indiciates this is not an item in the list rather based on the schema.
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_list_element")

    def callback_close_list_element(self, node: libyang.Node):
        """
        Called when the a list element has been processed.

        Args:
            node: The libyang node of the list element statement
        """
        raise NotImplementedError("callback_close_list_element")

    def callback_close_list(self, node: libyang.Node):
        """
        Called when the a list has finished processing.

        Args:
            node: The libyang node of the list statement
        """
        raise NotImplementedError("callback_close_list")

    def callback_write_leaf(
        self, node: libyang.Node, value: str, default: str, key: bool, node_id: str
    ):
        """
        Called when the a leaf has been encountered.

        Args:
            node: The libyang node of the leaf statement
            value: The value of the leaf - which will be quoted/escaped
            default: The default value for the leaf
            key: Indicates this leaf is a key of a list
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_write_leaf")

    def callback_open_containing_node(
        self, node: libyang.Node, presence: bool, node_id: str
    ):
        """
        Called when the a container has been encountered.

        Args:
            node: The libyang node of the container statement
            presence: True/False indicates the state of a presence code (non-presence container = None)
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_containing_node")

    def callback_close_containing_node(self, node: libyang.Node):
        """
        Called when the a container has finished processing

        Args:
            node: The libyang node of the container statement
        """
        raise NotImplementedError("callback_close_containing_node")

    def callback_open_leaflist(self, node: libyang.Node, count: int, node_id: str):
        """
        Called when the a leaf-list has been encountered.

        Args:
            node: The libyang node of the leaf-list statement
            count: The number of items in the leaf-list
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_leaflist_node")

    def callback_close_leaflist(self, node):
        """
        Called when the a leaf-list has finished processing.

        Args:
            node: The libyang node of the leaf-list statement
        """
        raise NotImplementedError("callback_close_leaflist_node")

    def callback_open_choice(self, node: libyang.Node, node_id: str):
        """
        Called when the a choice statement has been encountered. The YANG standard supports a choice
        without case statements - however yangvoodoo does not support statements other than case within
        a choice.

        Args:
            node: The libyang node of the choice statement
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_choice")

    def callback_close_choice(self, node: libyang.Node):
        """
        Called when the a choice statement has finished processing.

        Args:
            node: The libyang node of the choice statement
        """
        raise NotImplementedError("callback_close_choice")

    def callback_open_case(
        self, node: libyang.Node, active_case: bool, no_active_case: bool, node_id: str
    ):
        """
        Called when the a case statement (mutually exclusive) has been encountered.

        Args:
            node: The libyang node of the case statement
            active_case: Indicates this is the active case
            no_active_case: Indiciates data does not exist for any cases within the choice
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_open_case")

    def callback_close_case(self, node: libyang.Node):
        """
        Called when the contents of a specific case has finished processing.

        Args:
            node: The libyang node of the case statement
        """
        raise NotImplementedError("callback_close_case")

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

        self.callback_open_containing_node(
            node, presence=presence, node_id="".join(self.id_path_trail)
        )

        try:
            for subnode in self.ctx.find_path(f"{node.schema_path()}/*"):
                self._process_nodes(subnode)
        except libyang.util.LibyangError:
            pass

        self.callback_close_containing_node(node)
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
        self.callback_write_leaf(
            node,
            value,
            default=node.default(),
            key=node.is_key(),
            node_id="".join(self.id_path_trail),
        )
        self.shrink_trail()

    def _handle_schema_list(self, node):
        self.grow_trail(node)

        trail = "".join(self.data_path_trail)
        self.callback_open_list(
            node,
            count=len(list(self.data_ctx.gets_xpath(trail))),
            node_id="".join(self.id_path_trail),
        )

        list_items = list(self.data_ctx.gets_xpath(trail))

        if not list_items and self.INCLUDE_BLANK_LIST_ELEMENTS:
            self.grow_trail(list_element_predicates="", schema=False)
            self._handle_list_element(node, populate_key_value_tuple=False)
            self.shrink_trail(schema=False)

        for list_node in list_items:
            list_xpath = list_node[len(trail) :]
            self.grow_trail(list_element_predicates=list_xpath, schema=False)
            self._handle_list_element(node)
            self.shrink_trail(schema=False)

        self.callback_close_list(node)

        self.shrink_trail()

    def _handle_list_element(
        self, node: libyang.Node, populate_key_value_tuple: bool = True
    ):
        """
        Args:
            node: The node of the list containing this list element.
            populate_key_value_tuple: flag indicating if we should populate a full_key_value tuple.
        """
        if populate_key_value_tuple:
            keys = []
            xpath = "".join(self.data_path_trail)
            key_values = list(
                list(self.data_ctx.get_xpath(xpath))[0].get_list_key_values()
            )
        else:
            key_values = [(k.name(), None) for k in node.keys()]

        self.callback_open_list_element(
            node,
            key_values=key_values,
            empty_list_element=populate_key_value_tuple != True,
            node_id="".join(self.id_path_trail),
        )

        xpath = "".join(self.schema_path_trail)
        for subnode in self.ctx.find_path(f"{xpath}/*"):
            self._process_nodes(subnode)

        self.callback_close_list_element(node)

    def _handle_schema_leaflist(self, node):
        self.grow_trail(node)

        trail = "".join(self.data_path_trail)
        self.callback_open_leaflist(
            node,
            count=len(list(self.data_ctx.gets_xpath(trail))),
            node_id="".join(self.id_path_trail),
        )

        for list_node in self.data_ctx.gets_xpath(trail):
            list_xpath = list_node[len(trail) :]
            self.grow_trail(list_element_predicates=list_xpath, schema=False)
            self.callback_write_leaflist_item(
                self.get_data(),
                node_id="".join(self.id_path_trail),
            )
            self.shrink_trail(schema=False)

        self.callback_close_leaflist(node)

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

        self.callback_open_choice(node, node_id="".join(self.id_path_trail))

        for case in cases:
            self.grow_trail(case, data=False)
            self.callback_open_case(
                case,
                active_case == case,
                active_case == None,
                node_id="".join(self.id_path_trail),
            )

            try:
                for subnode in self.ctx.find_path(f"{case.schema_path()}/*"):
                    self._process_nodes(subnode)
            except libyang.util.LibyangError:
                pass

            self.callback_close_case(case)
            self.shrink_trail(data=False)

        self.callback_close_choice(node)

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
            if list_element_predicates is not None:
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
            self.id_path_trail.append(f"/{node.name()}")
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
        return " " * self.indent * self.INDENT_SPACING

    def open_indent(self):
        self.indent += 1
        return " " * (self.indent - 1) * self.INDENT_SPACING

    def close_indent(self):
        self.indent -= 1
        return " " * self.indent * self.INDENT_SPACING

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

    def _humanise_type(self, type):
        if type.base() == 9:
            return f"leafref -> {libyang.c2str(type._type.info.lref.path)}"

        if type.base() == 6:
            enums = [enum[0] for enum in type.enums()]
            return f"enumeration [ {'; '.join(enums)} ]"

        derrived_type = type.derived_type().name()
        this_type = type.name()
        if this_type != derrived_type:
            return f"{this_type} ({derrived_type})"
        return type.name()

    def _expand_types(self, type):
        union_types = list(type.union_types())

        for type in union_types:
            if type.base() == 11:
                yield from self._expand_types(type)
            else:
                yield self._humanise_type(type)

        if not union_types:
            yield self._humanise_type(type)

    def get_human_types(self, node):
        yield from self._expand_types(node.type())

    def get_human_constraints(self, node):
        type = node.type()
        for pattern in type.all_patterns():
            if pattern[1]:
                yield f"Pattern (Inverse): {pattern[0]}"
            else:
                yield f"Pattern: {pattern[0]}"
        for length in type.all_lengths():
            yield f"Length: {length}"
        for range in type.all_ranges():
            yield f"Range: {range}"
