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
        # self.result.write(self.get_indent())
        # self.result.write(f'"{node.name()}":')
        # self.result.write(" {\n")
        # self.open_indent()
        self.obj_pointer[-1][node.name()] = {}
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])
        # self.obj = self.obj[node.name()]
        print(self.obj)

    def callback_close_containing_node(self, node):
        # self.close_indent()
        # self.result.write(self.get_indent())
        # self.result.write("}\n")
        self.obj_pointer.pop()
        pass

    def callback_write_leaf(self, node, value, default, key, node_id):
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

    def callback_open_list(self, node, count, node_id):
        self.obj_pointer[-1][node.name()] = []
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])

    def callback_close_list(self, node):
        self.obj_pointer.pop()

    def callback_open_list_element(self, node, key_values, empty_list_element, node_id):
        x = {}
        self.obj_pointer[-1].append(x)
        self.obj_pointer.append(x)

        for key, val in key_values:
            if empty_list_element:
                val = "<color:gray>unset"
            self.obj_pointer[-1][f"{key} <key>"] = val

        # self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        # self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        # self.result.write(
        #     f"\n{self.get_indent()}<p align='right'>Need some buttons here to trigger removing this list element</p>\n"
        # )
        pass

    def callback_close_list_element(self, node):
        # self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} listelement -->\n\n")
        self.obj_pointer.pop()


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = PlantUMLExpander("testforms", log)
    generator.process(open("resources/simplelist2.xml").read())
    generator.dumps()
    generator.dump("uml.txt")
