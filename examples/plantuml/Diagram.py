import json
import libyang
import logging

from io import StringIO
from typing import List

from yangvoodoo.SchemaData import Expander


class PlantUMLExpander(Expander):
    QUOTE_ESCAPE_STYLE = "escape"
    INCLUDE_BLANK_LIST_ELEMENTS = True

    """
    Render a schema with data expanded into a PlantUML diagram

    @startjson
    {
    "null": null,
    "true": true,
    "false": false,
    "JSON_Number": [-1, -1.1, "<color:green>TBC"],
    "JSON_String": "ab\rc\td <color:green>TBC...",
    "JSON_Object": {
      "{}": {},
      "k_int": 123,
      "k_str": "abc",
      "k_obj": {"k": "v"}
    },
    "JSON_Array" : [
      [ [], [], [],[[],[[ [[[]]] ] ]] ],
      [true, false],
      [-1, 1],
      ["a", "b", "c"],
      ["mix", null, true, 1, {"k": "v"}]
    ]
    }
    @endjson
    """

    def __init__(self, yang_module, log: logging.Logger):
        super().__init__(yang_module, log)
        self.comma_required = False
        self.obj = {}
        self.obj_pointer = [self.obj]

    def callback_write_header(self, module):
        self.result.write("@startjson\n")

    def callback_write_body(self, module):
        self.result.write(json.dumps(self.obj, indent=4))

    def callback_write_footer(self, module):
        self.result.write("\n@endjson\n")

    def callback_open_containing_node(self, node, presence, node_id):
        self.obj_pointer[-1][node.name()] = {}
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])

    def callback_close_containing_node(self, node):
        self.obj_pointer.pop()

    def callback_write_leaf(self, node, value, quote, explicit, default, key, template, node_id):
        if key:
            return
        if not default:
            self.obj_pointer[-1][node.name()] = "<color:gray>unset"
        if default and not value:
            self.obj_pointer[-1][node.name()] = f"<color:orange> default={default}"
        if default and value == default:
            self.obj_pointer[-1][node.name()] = f"<color:green> default={default}"
        if default and value != default:
            self.obj_pointer[-1][node.name()] = f"{value} <color:red> default={default}"

    def callback_open_leaflist(self, node, count, node_id):
        self.obj_pointer[-1][node.name()] = []
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])

    def callback_close_leaflist(self, node):
        self.obj_pointer.pop()

    def callback_open_choice(self, node, node_id):
        label = f"choice... {node.name()}"
        self.obj_pointer[-1][label] = {}
        self.obj_pointer.append(self.obj_pointer[-1][label])

    def callback_close_choice(self, node):
        self.obj_pointer.pop()

    def callback_open_case(self, node, active_case, no_active_case, node_id):
        label = f"case... {node.name()}"
        self.obj_pointer[-1][label] = {}
        self.obj_pointer.append(self.obj_pointer[-1][label])

    def callback_close_case(self, node):
        self.obj_pointer.pop()

    def callback_open_list(self, node, count, node_id):
        label = f"list... {node.name()}"
        self.obj_pointer[-1][label] = {}
        self.obj_pointer.append(self.obj_pointer[-1][label])

    def callback_close_list(self, node):
        self.obj_pointer.pop()

    def callback_open_list_element(self, node, key_values, empty_list_element, node_id):
        for key, val in key_values:
            if empty_list_element:
                val = "<color:gray>unset"
            self.obj_pointer[-1][f"{key} <key>"] = val

        label = "list-element.."
        self.obj_pointer[-1][label] = {}
        self.obj_pointer.append(self.obj_pointer[-1][label])

    def callback_close_list_element(self, node):
        self.obj_pointer.pop()


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = PlantUMLExpander("testforms", log)
    generator.process(open("templates/forms/simplelist2.xml").read())
    generator.dumps()
    generator.dump("examples/plantuml/uml.txt")
