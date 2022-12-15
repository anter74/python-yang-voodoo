import base64
import logging
import uuid

from io import StringIO
from typing import List, Tuple

import libyang
from yangvoodoo import Types
from yangvoodoo.Common import Utils


class EscapeOptions:

    SELECT_SINGLE_VS_DOUBE = "select-single-vs-double"
    ESCAPE_INVERSE_OF_QUOTE = "escape-inverse-of-quoting"
    ESCAPE_ONLY = "escape"


class UnableToRenderFormError:
    pass


class UnableToDetermineQuotesError(UnableToRenderFormError):
    def __init__(self, value):
        super().__init__(f"Unable to find a quote style to use for the following value:\n{value}")


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
    QUOTE_ESCAPE_STYLE = EscapeOptions.SELECT_SINGLE_VS_DOUBE
    ESCAPE_FOR_DOUBLE_QUOTES = '\\"'
    ESCAPE_FOR_SINGLE_QUOTES = "\\'"
    INDENT_CHAR = " "
    INDENT_MINIMUM = 0
    INDENT_SPACING = 2
    SCHEMA_NODE_TYPE_MAP = {
        1: "_handle_schema_containing_node",
        2: "_handle_schema_choice",
        4: "_handle_schema_leaf",
        8: "_handle_schema_leaflist",
        16: "_handle_schema_list",
    }
    INCLUDE_BLANK_LIST_ELEMENTS = False
    BASE64_ENCODE_PATHS = False
    YANGUI_HIDDEN_KEY = "yangui-hidden"
    ALWAYS_FETCH_CONTAINER_CONTENTS = True
    ALWAYS_FETCH_LISTELEMENT_CONTENTS = True
    ALWAYS_FETCH_LIST_CONTENTS = True
    AUTO_EXPAND_NON_PRESENCE_CONTAINERS = True

    def __init__(self, yang_module, log: logging.Logger):
        self.log = log
        self.yang_module = yang_module
        self.ctx = libyang.Context(self.YANG_LOCATION)
        self.ctx.load_module(yang_module)
        self.data_ctx = libyang.DataTree(self.ctx)
        self.schema_filter_list = []
        self.schema_path_not_matched = False
        self.schema_path_matched = True
        self._is_schema_node_filtered = lambda x: False
        self.result = StringIO()
        self.indent = 0
        self.data_loaded = False
        self.expanded_elements = {}

    def set_schema_filter_list(self, filter_list: List[str]):
        """
        Take a list of nodes and filter it and it's decendants

        Args:
            filter_list: A list of yang schema xpaths
        """
        self._is_schema_node_filtered = self._is_schema_node_filtered_check_with_filter_list
        self.schema_filter_list = filter_list

    def dumps(self) -> str:
        self.result.seek(0)
        return self.result.read()

    def dump(self, filename):
        self.result.seek(0)
        with open(filename, "w") as fh:
            fh.write(self.result.read())

    def _is_schema_node_filtered_check_with_filter_list(self, node: libyang.schema.Node) -> bool:
        """
        Check if a node's schema path is on a filter list - case should be taken constructing the
        list to ensure the most likely parts are earlier in the list to avoid recursing the filter
        list more than necessary.

        Args:
            node: A libyang schema node.

        Returns:
            if this node should be filtered.
        """
        for path in self.schema_filter_list:
            schema_path = node.schema_path()
            if schema_path.startswith(path):
                return self.schema_path_matched
        return self.schema_path_not_matched

    def load(self, initial_data: str = None, format: int = 1, trusted=False):
        """
        Load an initial data tree but do not trigger processing based on the root of the data/scheam tree.

        Args:
            initial_data: An IETF JSON or XML data payload conforming to a yang model.
            format: payload format (1=XML, 2=IETF JSON)
        """
        self.log.info("Loading: %s", self.yang_module)
        if initial_data:
            self.data_ctx.loads(initial_data, format, trusted=trusted)
        self.data_path_trail = [""]
        self.id_path_trail = [""]
        self.schema_path_trail = [""]

    def process(self, initial_data: str = None, format: int = 1) -> StringIO:
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

        Args:
            initial_data: An IETF JSON or XML data payload conforming to a yang model.
            format: payload format (1=XML, 2=IETF JSON)
        """
        self.log.info("Schema Data Expander: %s", self.__class__.__name__)
        if initial_data:
            self.log.info("Loading: %s: %s bytes", self.yang_module, len(initial_data))
            self.load(initial_data, format)
            self.data_loaded = True
        self.result = StringIO()

        self.callback_write_header(self.ctx.get_module(self.yang_module))
        self.callback_write_title(self.ctx.get_module(self.yang_module))

        self.callback_write_open_body(self.ctx.get_module(self.yang_module))

        self.data_path_trail = [""]
        self.id_path_trail = [""]
        self.schema_path_trail = [""]

        self.log.info("Schema Data Expander: starting recursion")
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            self._process_nodes(node)
        self.log.info("Schema Data Expander: completed recursion")

        self.callback_write_close_body(self.ctx.get_module(self.yang_module))

        self.callback_write_footer(self.ctx.get_module(self.yang_module))

        self.result.seek(0)
        return self.result

    def data_tree_delete_list_element(self, list_element_xpath: str):
        self.data_ctx.delete_xpath(list_element_xpath)

    def data_tree_add_list_element(self, list_xpath: str, key_values: List[Tuple[str, str]]) -> str:
        """
        Args:
            list_xpath: XPATH to a leaf-list of list
            key_value: A list of key_value tuples - not the libyang convention of `.` as a key-name for leaf-lists.

        Return:
            The predicates of the listelement.
        """
        predicates = ""
        for k, v in key_values:
            predicates += Utils.encode_xpath_predicate(k, v)
        self.data_ctx.set_xpath(list_xpath + predicates, "")
        return predicates

    def data_tree_create_container(self, xpath: str):
        self.data_ctx.set_xpath(xpath, "")

    def data_tree_delete_container(self, xpath: str):
        self.data_ctx.delete_xpath(xpath)

    def data_tree_set_leaf(self, xpath: str, value: str):
        if not value:
            self.data_ctx.delete_xpath(xpath)
        else:
            self.data_ctx.set_xpath(xpath, value)

    def _clear(self):
        self.result.seek(0)
        self.result.truncate()
        self.data_path_trail = [""]
        self.id_path_trail = [""]
        self.schema_path_trail = [""]

    def subprocess_create_list(self, data_xpath: str, schema_xpath: str):
        """
        Form a basic page with *just* enough eleemnts to
        """
        self._clear()

        self.id_path_trail.append(data_xpath)
        self.data_path_trail.append(data_xpath)
        self.schema_path_trail.append(schema_xpath)

        self.grow_trail(list_element_predicates="", schema=False)
        for subnode in self.ctx.find_path(f"{schema_xpath}/*"):
            if subnode.get_extension(self.YANGUI_HIDDEN_KEY):
                continue
            if subnode.nodetype() == Types.LIBYANG_NODETYPE["LEAF"] and subnode.is_key():
                self.grow_trail(subnode)
                self.callback_write_leaf(
                    subnode,
                    "",
                    '"',
                    False,
                    default="",
                    key=True,
                    template=True,
                    node_id="".join(self.id_path_trail),
                )
                self.shrink_trail()

        self.shrink_trail(schema=False)

    def subprocess_create_leaf_list(self, data_xpath: str, schema_xpath: str):
        self._clear()

        self.id_path_trail.append(data_xpath)
        self.data_path_trail.append(data_xpath)
        self.schema_path_trail.append(schema_xpath)

        node = next(self.ctx.find_path("".join(self.schema_path_trail)))
        self.grow_trail(list_element_predicates="", schema=False)

        xpath = "".join(self.schema_path_trail)
        self.callback_write_leaflist_item(
            node,
            "",
            '"',
            True,
            template=True,
            node_id="".join(self.id_path_trail),
        )

        self.shrink_trail(schema=False)

    def subprocess_existing_list(self, list_xpath: str):
        self._clear()

        for result in self.data_ctx.get_xpath(list_xpath):
            if result.get_schema().nodetype() != Types.LIBYANG_NODETYPE["LIST"]:
                raise NotImplementedError(f"subprocess only supports processing of a list: {list_xpath}")
            break
        else:
            self.log.error("Cannot subprocess non-existing data path: %s", list_xpath)
            return

        node = result.get_schema()
        self.id_path_trail.append(list_xpath)
        self.data_path_trail.append(list_xpath)
        self.schema_path_trail.append(result.get_schema_path())

        self.log.info("Schema Data Expander: starting recursion for a list_element: %s", list_xpath)
        self._handle_list_contents(node)
        self.log.info("Schema Data Expander: completed recursion of a list element: %s", list_xpath)

    def subprocess_listelement(self, list_xpath: str):
        """
        This is used to expand a list element which is not expanded on the UI
        """
        self._clear()
        for result in self.data_ctx.get_xpath(list_xpath):
            if result.get_schema().nodetype() != Types.LIBYANG_NODETYPE["LIST"]:
                raise NotImplementedError(f"subprocess only supports processing of a list: {list_xpath}")
            break
        else:
            self.log.error("Cannot subprocess non-existing data path: %s", list_xpath)
            return

        node = result.get_schema()
        self.id_path_trail.append(list_xpath)
        self.data_path_trail.append(list_xpath)
        self.schema_path_trail.append(result.get_schema_path())

        self.log.info("Schema Data Expander: starting recursion for a list_element: %s", list_xpath)
        self._handle_container_contents(node)
        self.log.info("Schema Data Expander: completed recursion of a list element: %s", list_xpath)

    def subprocess_container(self, container_xpath: str):
        self._clear()

        for result in self.data_ctx.get_xpath(container_xpath):
            if result.get_schema().nodetype() != Types.LIBYANG_NODETYPE["CONTAINER"]:
                raise NotImplementedError(f"subprocess only supports processing of a container: {container_xpath}")
            break
        else:
            self.log.error("Cannot subprocess non-existing data path: %s", container_xpath)
            return

        node = result.get_schema()
        self.id_path_trail.append(container_xpath)
        self.data_path_trail.append(container_xpath)
        self.schema_path_trail.append(result.get_schema_path())

        self.log.info("Schema Data Expander: starting recursion for a container: %s", container_xpath)
        self._handle_container_contents(node)
        self.log.info("Schema Data Expander: completed recursion of a container: %s", container_xpath)

    def subprocess_list(self, list_data_xpath: str, predicates: str):
        """
        Mimic the call from `handle_schema_list` -> `_handle_list_element`, which may mimic a user
        action of adding a list element.

        The trails are not perfectly formed therefore we may not shrink the trails up the data tree
        - however assuming this is about creating additions of list elements to ane existing data
        tree this should be ok.
        """
        self._clear()

        for result in self.data_ctx.get_xpath(list_data_xpath):
            if result.get_schema().nodetype() != Types.LIBYANG_NODETYPE["LIST"]:
                raise NotImplementedError(
                    f"subprocess only supports processing of a list element: {list_element_data_xpath}"
                )
            break
        else:
            self.log.error("Cannot subprocess non-existing data path: %s", list_element_data_xpath)
            return

        node = result.get_schema()
        self.id_path_trail.append(list_data_xpath)
        self.data_path_trail.append(list_data_xpath)
        self.schema_path_trail.append(result.get_schema_path())

        self.log.info("Schema Data Expander: starting recursion for a list element: %s", list_data_xpath)
        for list_node in [f"{list_data_xpath}{predicates}"]:
            self.grow_trail(list_element_predicates=predicates, schema=False)
            self._handle_list_element(node, force_open=True)
            self.shrink_trail(result.get_schema_path())
        self.log.info("Schema Data Expander: completed recursion of a list element: %s", list_data_xpath)

    def subprocess_leaflist(self, leaflist_xpath: str, value: str):
        self._clear()

        for result in self.data_ctx.get_xpath(leaflist_xpath):
            if result.get_schema().nodetype() != Types.LIBYANG_NODETYPE["LEAFLIST"]:
                raise NotImplementedError(f"subprocess only supports processing of a list element: {leaflist_xpath}")
            break
        else:
            self.log.error("Cannot subprocess non-existing data path: %s", leaflist_xpath)
            return

        node = result.get_schema()
        self.id_path_trail.append(leaflist_xpath)
        self.data_path_trail.append(leaflist_xpath)
        self.schema_path_trail.append(result.get_schema_path())
        predicates = Utils.encode_xpath_predicate(".", value)

        self.grow_trail(list_element_predicates=predicates, schema=False)
        self.callback_write_leaflist_item(
            node,
            *self.get_data(node),
            template=False,
            node_id="".join(self.id_path_trail),
        )
        self.shrink_trail(schema=False)

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

    def callback_write_open_body(self, module: libyang.schema.Module):
        """
        Called in order to provide information in a body before starting to process the yang model.

        Args:
            module: The libyang schema module
        """

    def callback_write_close_body(self, module: libyang.schema.Module):
        """
        Called in order to provide information at the end of processing the yang model.

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
        force_open: bool,
        node_id: str,
    ):
        """
        Called when the a list element has been encountered.

        Args:
            node: The libyang node of the list element statement
            key_values: A list of key and value tuples.
            empty_list_element: Indiciates this is not an item in the list rather based on the schema.
            force_open: indicates if this node should be forced open (i.e. a user has created it)
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
        self,
        node: libyang.Node,
        value: str,
        quote: str,
        explicit: bool,
        default: str,
        key: bool,
        template: bool,
        node_id: str,
    ):
        """
        Called when the a leaf has been encountered.

        Args:
            node: The libyang node of the leaf statement
            value: The value of the leaf - which will be quoted/escaped
            quote: Preferred quotation marks for quoting
            explicit: Data exists in the data tree
            default: The default value for the leaf
            key: Indicates this leaf is a key of a list
            template: Indicates this is a templated representation of the leaf
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_write_leaf")

    def callback_open_containing_node(self, node: libyang.Node, presence: bool, node_id: str):
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

    def callback_write_leaflist_item(self, node: libyang.Node, value: str, quote: str, _, template, node_id: str):
        """
        Called when the a leaf-list has been encountered.

        Args:
            node: The libyang node of the leaf-list statement
            value: The value of the leaf-list node
            quote: The preferred quote style.
            explicit: If the value is explicitly set in the data tree (N/A for a leaf-list)
            template: If the item is a template rather (i.e. used when offering creation of this type of leaf-list)
            node_id: The node id using a hybrid schema/data path.
        """
        raise NotImplementedError("callback_write_leaflist_item")

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

    def callback_open_case(self, node: libyang.Node, active_case: bool, no_active_case: bool, node_id: str):
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
        if node.get_extension(self.YANGUI_HIDDEN_KEY):
            return
        if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
            raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
        if not self._is_schema_node_filtered(node):
            getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    def _handle_schema_containing_node(self, node):
        self.grow_trail(node)
        presence = None
        if node.presence() is not None:
            presence = False
            if self.get_raw_data() is not None:
                presence = True

        self.callback_open_containing_node(node, presence=presence, node_id="".join(self.id_path_trail))
        if self._should_container_be_visible(node, presence):
            self._handle_container_contents(node)

        self.callback_close_containing_node(node)

        self.shrink_trail()

    def _handle_container_contents(self, node):
        """
        This can be used for the inner of a container (and also list elements)
        """
        try:
            for subnode in self.ctx.find_path(f"{node.schema_path()}/*"):
                self._process_nodes(subnode)
        except libyang.util.LibyangError:
            pass

    def _should_container_be_visible(self, node: libyang.schema.Node, presence: bool) -> bool:
        """
        Determine if a container should be visible:

        Args:
            node: The libyang schema node
            presence: if a presence container False/True represents it's state in the data tree (None for non-presence)
        """
        result = False
        uuid = self.get_uuid()
        if uuid in self.expanded_elements and self.expanded_elements[uuid]:
            return True

        if presence is None or presence is True or (presence is False and self.AUTO_EXPAND_NON_PRESENCE_CONTAINERS):
            # base on the data we should be expanded
            result = True

        if node.get_extension("yangui-force-minimised"):
            return False

        if node.get_extension("yangui-force-expand"):
            return True

        if self.ALWAYS_FETCH_CONTAINER_CONTENTS:
            return result

        return False

    def _should_listelement_be_visible(self, node: libyang.schema.Node, force_open: bool) -> bool:
        """
        Determine if a list element should be visible:

        Args:
            node: The libyang schema node
            force_open: If a user has added this item just now we want to force it open.
        """
        if force_open:
            return True
        result = True

        uuid = self.get_uuid()
        if uuid in self.expanded_elements and self.expanded_elements[uuid]:
            return True

        if node.get_extension("yangui-force-minimised"):
            return False

        if node.get_extension("yangui-force-expand"):
            return True

        if self.ALWAYS_FETCH_LISTELEMENT_CONTENTS:
            return result

        return False

    def _should_list_be_visible(self, node: libyang.schema.Node) -> bool:
        """
        Determine if a list should be visible:

        Args:
            node: The libyang schema node
        """
        result = True
        uuid = self.get_uuid()
        if uuid in self.expanded_elements and self.expanded_elements[uuid]:
            return True

        if node.get_extension("yangui-force-minimised"):
            return False

        if node.get_extension("yangui-force-expand"):
            return True

        if self.ALWAYS_FETCH_LIST_CONTENTS:
            return result

        return False

    def _gets(self, data_path):
        for result in self.data_ctx.get_xpath(data_path):
            yield result.value

    def _exists(self, data_path, predicates=None, child_contents=False):
        if predicates:
            for k, v in predicates:
                data_path += Utils.encode_xpath_predicate(k, v)
        if child_contents:
            data_path += "/*"
        try:
            next(self.data_ctx.get_xpath(data_path))
            return True
        except StopIteration:
            pass
        except libyang.util.LibyangError:
            pass
        return False

    def _handle_schema_leaf(self, node: libyang.schema.Node):
        """
        Here we should return different data based on the leaf type
        i.e. boolean/empty leaves should be checkbox
        enumerations should be drop-down boxes
        we should extract description of the yang model as a tool tip

        we should deal with default values too when the data isn't set - perhaps with a lighter colour in the input
        than if it haves explicit values. (WOULD HAVE TO BE HANDLED IN Javascript so not worth the effort)

        Args:
            node: A libyang schema node
            key: if None (default) lookup if the node is a key (otherwise use this argument as an override)
        """
        self.grow_trail(node)
        self.callback_write_leaf(
            node,
            *self.get_data(node),
            default=Utils.convert_to_libyang_value_to_pythonic(node, node.default()),
            key=node.is_key(),
            template=False,
            node_id="".join(self.id_path_trail),
        )
        self.shrink_trail()

    def _handle_schema_list(self, node):
        """
        Expanding the schema list to either
        a) include a templated list element (if there are not items in the list)
        b) include list elements that do exist in the data tree)

        Example:
          trail: /testforms:toplevel/simplelist   (built from the data path to the list)
          list_items: ["/testforms:toplevel/simplelist[simplekey='A']",
                       "/testforms:toplevel/simplelist[simplekey='B']"]
                                                  (built from a query of trail to the list
          node: <libyang.schema.List: simplelist [simplekey]>    the schema node of the list
          list_xpath: "[simplekey='A']"   the predicates of the list
          schema_path_trail: ['', '/testforms:toplevel', '/testforms:simplelist']
          data_path_trail: ['', '/testforms:toplevel', '/simplelist']
          id_path_trail: ['', '/testforms:toplevel', '/simplelist']
        """

        self.grow_trail(node)

        trail = "".join(self.data_path_trail)
        self.callback_open_list(
            node,
            count=len(list(self.data_ctx.gets_xpath(trail))),
            node_id="".join(self.id_path_trail),
        )

        if self._should_list_be_visible(node):
            self._handle_list_contents(node)

        self.callback_close_list(node)

        self.shrink_trail()

    def _handle_list_contents(self, node):
        trail = "".join(self.data_path_trail)
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

    def _handle_list_element(self, node: libyang.Node, populate_key_value_tuple: bool = True, force_open=False):
        """
        Args:
            node: The node of the list containing this list element.
            populate_key_value_tuple: flag indicating if we should populate a full_key_value tuple.
        """
        if populate_key_value_tuple:
            xpath = "".join(self.data_path_trail)
            key_values = list(list(self.data_ctx.get_xpath(xpath))[0].get_list_key_values())
        else:
            key_values = [(k.name(), None) for k in node.keys()]

        self.callback_open_list_element(
            node,
            key_values=key_values,
            empty_list_element=populate_key_value_tuple is not True,
            force_open=force_open,
            node_id="".join(self.id_path_trail),
        )

        if self._should_listelement_be_visible(node, force_open):
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
                node,
                *self.get_data(node),
                template=False,
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
                active_case is None,
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

    def get_raw_data(self) -> str:
        """
        Return raw data

        Returns:
            The raw libyang data (str)
        """
        xpath = "".join(self.data_path_trail)
        value = list(self.data_ctx.get_xpath(xpath))
        if value:
            return value[0].value
        return None

    def get_data(self, node: libyang.schema.Node) -> Tuple[str, str, bool]:
        """
        Return data for the current data item at the head of the trail.

        Args:
            node: the libyang schema node used to derive defaults.

        Returns:
            Tuple of escaped (if required) data, a preferred quoting style, and if the data is explicit in the data tree
        """
        xpath = "".join(self.data_path_trail)
        value = list(self.data_ctx.get_xpath(xpath))
        if node.type() == Types.DATA_ABSTRACTION_MAPPING["EMPTY"]:
            if value is not None:
                return True
            return False
        if value:
            self.log.debug("GET XPATH: %s = %s", xpath, value[0].value)
            quote = self.get_quote_style(value[0].value)
            return self.escape_value(value[0].value, quote), quote, True
        if node.default():
            default = Utils.convert_to_libyang_value_to_pythonic(node, node.default())
            quote = self.get_quote_style(default)
            return self.escape_value(default, quote), quote, False
        return "", self.get_quote_style(""), False

    def get_quote_style(self, value: str) -> str:
        """
        Return a set of preferred quote to use if quoting the data, this depends on the configuration
        of the class variables.

        Args:
            value: to asses

        Returns:
            A preference of single vs double quotes.
        """
        if self.QUOTE_ESCAPE_STYLE == EscapeOptions.ESCAPE_ONLY:
            return ""
        if not isinstance(value, str):
            return '"'
        if '"' in value and "'" in value:
            raise UnableToDetermineQuotesError(value)
        if "'" in value:
            return '"'
        return "'"

    def escape_value(self, value: str, quote: str) -> str:
        """
        Return and escaped (if necessary) string, this depends on the configuration of the class variables.

        Args:
            value: the string to assess
            quote: the preferred quote character.

        Returns:
            A string which may have been escpaed.
        """
        if isinstance(value, str):
            if self.QUOTE_ESCAPE_STYLE == EscapeOptions.ESCAPE_ONLY:
                value.replace('"', self.ESCAPE_FOR_DOUBLE_QUOTES)
            elif self.QUOTE_ESCAPE_STYLE == EscapeOptions.ESCAPE_INVERSE_OF_QUOTE and quote == '"':
                value.replace('"', self.ESCAPE_FOR_DOUBLE_QUOTES)
            elif self.QUOTE_ESCAPE_STYLE == EscapeOptions.ESCAPE_INVERSE_OF_QUOTE and quote == "'":
                value.replace("'", self.ESCAPE_FOR_SINGLE_QUOTES)
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

    def grow_trail(self, node=None, list_element_predicates=None, schema=True, data=True):
        if data:
            if list_element_predicates is not None:
                data_component = list_element_predicates
            elif node.module().name() != self.yang_module or len(self.data_path_trail) == 1:
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

    def get_id(self, escape=False, prefix=""):
        """
        Get an identifier based on the data tree.

        Args:
            quote: if set to `True` a suitable quote will be used to surround an un-escaped value.
            escape: escape the id
            prefix: add a prefix to the id
        """
        if len(self.data_path_trail) == 1:
            return "'__root__'"
        trail = "".join(self.data_path_trail)
        if self.BASE64_ENCODE_PATHS:
            return base64.urlsafe_b64encode(trail.encode("utf-8")).decode("utf-8")
        if escape:
            quote = self.get_quote_style(trail)
            trail = self.escape_value(trail, quote)
        return f"{trail}"

    def get_schema_id(self):
        if len(self.schema_path_trail) == 1:
            return "'__root__'"
        trail = "".join(self.schema_path_trail)
        if self.BASE64_ENCODE_PATHS:
            return base64.urlsafe_b64encode(trail.encode("utf-8")).decode("utf-8")
        quote = self.get_quote_style(trail)
        return f"{quote}{trail}{quote}"

    def get_hybrid_id(self, as_uuid=False):
        """
        Return a hybrid trail id, which is the data path with additional nodes to denote and
        choice/case statement.
        """
        if len(self.id_path_trail) == 1:
            return "'__root__'"
        trail = "".join(self.id_path_trail)
        if as_uuid:
            return str(uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_URL, "pyvwu"), trail))
        if self.BASE64_ENCODE_PATHS:
            return base64.urlsafe_b64encode(trail.encode("utf-8")).decode("utf-8")
        quote = self.get_quote_style(trail)
        return f"{quote}{trail}{quote}"

    def get_uuid(self):
        trail = "".join(self.id_path_trail)
        return str(uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_URL, "pyvwu"), trail))

    def get_indent(self):
        return self.INDENT_CHAR * (self.indent + self.INDENT_MINIMUM) * self.INDENT_SPACING

    def get_blank_indent(self, extra_indent=0):
        return (
            " " * (len(self.INDENT_CHAR) + (self.indent - 1) + self.INDENT_MINIMUM + extra_indent) * self.INDENT_SPACING
        )

    def _get_html_attr(
        self, attribute, method, data=False, hybrid=False, schema=False, parent=False, this=False, uuid=False
    ):
        """
        For a HTML attribute for href's onBlur, onChange etc and ensure we use the correct quoting/encoding
        of quotes - this needs to ensure we use.

        Based on an XPATH we are likely to receive
            "/xpath/to/thing[with-list-key='1234']"

        However if the list key values container a " then we would receive
            '/xpath/to/thing[with-list-key="1234"]'

        A HTML attribute will be formed in the form of the following - instead of this we create Base64
        encoded XPATH's isntead of trying to escape/find the best quotes.
            onClick='myfunction("/an/xpath[listkey='listval']")'
                    ^           ^                  ^       ^ ^ ^
                    |           |                  |       | | |- outer quote
                    |           |                  |       | |--- inner quote
                    |           |                  |       |
                    |           |                  |-------|-- these need replacing with html codes
                    |           |- inner quote
                    |- outer quote

        Args:
            attribute: e.g., href, onClick, onBlur, onChange
            method: e.g. javascript:function, function
            data: include the data xpath
            xpath: incldue the schema xpath
            parent: add in parent id
            this: include the literal 'this'
        """
        args = []
        attr_quote = '"'
        inner_quote = "'"
        if data:
            args.append(f"{inner_quote}{self.get_id()}{inner_quote}")
        if schema:
            args.append(f"'{self.get_schema_id()}'")
        if hybrid:
            args.append(f"{inner_quote}{self.get_hybrid_id()}{inner_quote}")
        if parent:
            args.append(f"{inner_quote}{self._parent_id}{inner_quote}")
        if this:
            args.append("this")
        if uuid:
            args.append(f"{inner_quote}{self.get_hybrid_id(as_uuid=True)}{inner_quote}")
        return f"{attribute}={attr_quote}{method}({', '.join(args)}){attr_quote}"

    def block_quotify(self, text, width, indent, newline_split="\n", newline="\n"):
        next_line_indent = None
        lines = text.split(newline_split)
        for line in lines:
            if next_line_indent:
                yield next_line_indent
            if len(line) < width:
                yield f"{line}"
            else:
                line_width = 0
                for word in line.split(" "):
                    line_width += len(word)
                    if len(word) > width:
                        yield f"{newline}{indent}{word}"
                    elif line_width < width:
                        yield f"{word} "
                    else:
                        yield f"{newline}{indent}{word} "
                        line_width = 0
            next_line_indent = f"{newline}{indent}"

    def open_indent(self):
        self.indent += 1
        return self.INDENT_CHAR * ((self.indent - 1) + self.INDENT_MINIMUM) * self.INDENT_SPACING

    def close_indent(self):
        self.indent -= 1
        return self.INDENT_CHAR * (self.indent + self.INDENT_MINIMUM) * self.INDENT_SPACING

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
            return f"leafref -> {libyang.c2str(type._type.info.lref.path)}", []

        if type.base() == 6:
            enums = [enum[0] for enum in type.enums()]
            return f"enumeration [ {'; '.join(enums)} ]", list(self.get_human_constraints(type))

        derrived_type = type.derived_type().name()
        this_type = type.name()
        if this_type != derrived_type:
            return f"{this_type} ({derrived_type})", list(self.get_human_constraints(type))
        return type.name(), list(self.get_human_constraints(type))

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

    def get_human_constraints(self, type):
        for pattern in type.all_patterns():
            if pattern[1]:
                yield f"Pattern (Inverse): {pattern[0]}"
            else:
                yield f"Pattern: {pattern[0]}"
        for length in type.all_lengths():
            yield f"Length: {length}"
        for range in type.all_ranges():
            yield f"Range: {range}"
