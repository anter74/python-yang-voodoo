import json
import libyang
import logging

from io import StringIO
from typing import List


class UnableToRenderFormError:
    pass


class UnableToDetermineQuotesError(UnableToRenderFormError):
    def __init__(self, value):
        super().__init__(f"Unable to find a quote style to use for the following value:\n{value}")


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

    def write_header(self):
        self.result.write(
            """
        <head>
<link rel="stylesheet" href="mystyle.css"></head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/fork-awesome@1.2.0/css/fork-awesome.min.css" integrity="sha256-XoaMnoYC5TH6/+ihMEnospgm0J1PM/nioxbOUdnM8HY=" crossorigin="anonymous">
</head>
                   """
        )

    def dumps(self):
        self.result.seek(0)
        print(self.result.read())

    def process(self, initial_data: str):
        self.log.info("Processing: %s", self.yang_module)
        if initial_data:
            self.data_ctx.loads(initial_data)
        self.result = StringIO()
        self.write_header()
        self.data_path_trail = [""]
        self.schema_path_trail = [""]
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            self._process_nodes(node)

        return self.result

    def _process_nodes(self, node):
        if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
            raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
        getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    def _handle_schema_containing_node(self, node):
        self.grow_trail(node)

        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- container type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_container' id={self.get_id()}>\n")
        self.result.write(f"{self.get_indent()}<label class='structure_containerlabel'>{node.name()}</label><br/>\n")
        for subnode in self.ctx.find_path(f"{node.schema_path()}/*"):
            self._process_nodes(subnode)

        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} container-->\n\n")
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
        self.result.write(
            f"{self.get_indent()}<label class='structure_leaflabel' for={self.get_id()}>{node.name()}</label>\n"
        )
        self.result.write(
            f"{self.get_indent()}<input type='text' name={self.get_id()} id={self.get_id()} value={value}><br/>\n"
        )
        self.shrink_trail()

    def _handle_schema_list(self, node):
        """
        Some client side javascript to try capture list key values?
        before submitting the form back to the server?

        Can the javascript goes as far as checking existing list key/values (if not do that server side)

        Assumption is rather than being *too* ajaxy going backwards and forwards to the client isn't the
        end of the world.

        When we are in a list we won't look at the schema but instead look to the data tree to find list elements
        which exist - and then pass those to prcoess_nodes?
        """
        self.grow_trail(node)
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- list type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_list' id={self.get_id()}>\n")
        self.result.write(f"{self.get_indent()}<label class='structure_listlabel'>{node.name()}</label><br/>\n")
        self.result.write(
            f"\n{self.get_indent()}<p align='right'>Need some {self.get_id()} buttons here to trigger adding extra list element</p>\n"
        )

        trail = "".join(self.data_path_trail)

        for list_node in self.data_ctx.gets_xpath(trail):
            list_xpath = list_node[len(trail) :]
            self.grow_trail(list_element_predicates=list_xpath, schema=False)
            self._handle_list_element()
            self.shrink_trail(schema=False)

        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} list -->\n\n")
        self.shrink_trail()

    def _handle_list_element(self):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.get_indent()}<p align='right'>Need some buttons here to trigger removing this list element</p>\n"
        )

        xpath = "".join(self.schema_path_trail)
        for subnode in self.ctx.find_path(f"{xpath}/*"):
            self._process_nodes(subnode)

        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} listelement -->\n\n")

    def get_data(self, default=None, quoted=True):
        xpath = "".join(self.data_path_trail)
        value = list(self.data_ctx.get_xpath(xpath))
        if value:
            self.log.debug("GET XPATH: %s = %s", xpath, value[0].value)
            quote = self.get_quote_style(value[0].value)
            return f"{quote}{value[0].value}{quote}"
        if default:
            quote = self.get_quote_style(default)
            return f"{quote}{default}{quote}"
        return ""

    def get_quote_style(self, value):
        if '"' in value and "'" in value:
            raise UnableToDetermineQuotesError(value)
        if "'" in value:
            return '"'
        return "'"

    def shrink_trail(self, schema=True, data=True):
        if data:
            self.data_path_trail.pop()
        if schema:
            self.schema_path_trail.pop()
        self.log.debug("SHRINK: %s", self.data_path_trail)
        self.log.debug("SHRINK: %s", self.schema_path_trail)

    def grow_trail(self, node=None, list_element_predicates=None, schema=True, data=True):
        if data:
            if list_element_predicates:
                data_component = list_element_predicates
            elif node.module().name() != self.yang_module or len(self.data_path_trail) == 1:
                data_component = f"/{node.module().name()}:{node.name()}"
            else:
                data_component = f"/{node.name()}"
            self.data_path_trail.append(f"{data_component}")
        if schema:
            self.schema_path_trail.append(f"/{node.module().name()}:{node.name()}")
        self.log.debug("GROW: %s", self.data_path_trail)
        self.log.debug("GROW: %s", self.schema_path_trail)

    def get_id(self):
        if len(self.data_path_trail) == 1:
            return "'__root__'"
        trail = "".join(self.data_path_trail)
        quote = self.get_quote_style(trail)
        return f"{quote}{trail}{quote}"

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
    #    generator.process(None)
    generator.process(open("resources/simplelist2.xml").read())
    generator.dumps()
