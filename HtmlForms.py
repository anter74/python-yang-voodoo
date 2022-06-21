import json
import libyang
import logging

from io import StringIO
from typing import List


class UnableToRenderFormError:
    pass


class UnableToFormNodeIdError(UnableToRenderFormError):
    def __init__(self, schema, data):
        super().__init__(f"Unable to form an identifier for the following path\nData: {data}\nSchema: {schema}")


class Generator:

    YANG_LOCATION = "yang"
    SCHEMA_NODE_TYPE_MAP = {1: "_handle_schema_containing_node", 4: "_handle_schema_leaf", 16: "_handle_schema_list"}

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

    def process(self, initial_data: str, additional_xpaths: List[str]):
        self.log.info("Processing: %s", self.yang_module)
        self.result = StringIO()
        self.data_path_trail = [""]
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            self._process_nodes(node)

        return self.result

    def _process_nodes(self, node):
        if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
            raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
        getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    def _handle_schema_containing_node(self, node):
        self.data_path_trail.append(self.get_data_path_component(node))
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id(node)}></a> <!-- container type -->")
        self.result.write(f"\n{self.open_indent()}<div id={self.get_id(node)}>\n")

        for subnode in self.ctx.find_path(f"{node.schema_path()}/*"):
            self._process_nodes(subnode)

        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id(node)} container-->\n\n")
        self.data_path_trail.pop()

    def _handle_schema_leaf(self, node):
        """
        Here we should return different data based on the leaf type
        i.e. boolean/empty leaves should be checkbox
        enumerations should be drop-down boxes
        we should extract description of the yang model as a tool tip
        """
        self.data_path_trail.append(self.get_data_path_component(node))
        self.result.write(
            f"{self.get_indent()}<input type='text' name={self.get_id(node)} id={self.get_id(node)} value=''>\n"
        )
        self.data_path_trail.pop()

    def _handle_schema_list(self, node):
        """
        Some client side javascript to try capture list key values?
        before submitting the form back to the server?

        Can the javascript goes as far as checking existing list key/values (if not do that server side)

        Assumption is rather than being *too* ajaxy going backwards and forwards to the client isn't the
        end of the world.
        """
        self.data_path_trail.append(self.get_data_path_component(node))
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id(node)}></a> <!-- list type -->")
        self.result.write(f"\n{self.open_indent()}<div id={self.get_id(node)}>\n")

        self.result.write(f"\n{self.get_indent()}Need some buttons here to trigger adding extra list element\n")
        # for node in self.ctx.find_path(f"{node.schema_path()}/*"):
        #     self._process_nodes(node)

        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id(node)} list -->\n\n")
        self.data_path_trail.pop()

    def get_data_path_component(self, node):
        if node.module().name() != self.yang_module or len(self.data_path_trail) == 1:
            return f"{node.module().name()}:{node.name()}"
        return node.name()

    def get_id(self, node):
        if len(self.data_path_trail) == 1:
            return "'__root__'"
        trail = "/".join(self.data_path_trail)
        if '"' in trail and "'" in trail:
            raise UnableToFormNodeIdError(node.schema_path(), trail)
        if "'" in trail:
            return f'"{trail}"'
        return f'"{trail}"'

    def get_indent(self):
        return " " * self.indent * 2

    def open_indent(self):
        self.indent += 1
        return " " * (self.indent - 1) * 2

    def close_indent(self):
        self.indent -= 1
        return " " * self.indent * 2


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = Generator("testforms", log)
    generator.process(None, None)
    generator.dumps()
