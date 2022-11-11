import json
import libyang
import logging

from io import StringIO
from typing import List

from yangvoodoo.SchemaData import Expander


class PlantUMLExpander(Expander):
    QUOTE_ESCAPE_STYLE = "escape"

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

    def write_header(self):
        self.result.write("@startjson\n")

    def write_body(self):
        self.result.write(json.dumps(self.obj, indent=4))

    def write_footer(self):
        self.result.write("\n@endjson\n")

    def open_containing_node(self, node):
        # self.result.write(self.get_indent())
        # self.result.write(f'"{node.name()}":')
        # self.result.write(" {\n")
        # self.open_indent()
        self.obj_pointer[-1][node.name()] = {}
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])
        # self.obj = self.obj[node.name()]
        print(self.obj)

    def close_containing_node(self, node):
        # self.close_indent()
        # self.result.write(self.get_indent())
        # self.result.write("}\n")
        self.obj_pointer.pop()
        pass

    def write_leaf(self, node, value, default=None, key=False):
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

    def open_list(self, node, count):
        self.obj_pointer[-1][node.name()] = []
        self.obj_pointer.append(self.obj_pointer[-1][node.name()])

    def close_list(self, node):
        self.obj_pointer.pop()

    def open_list_element(self, key_values):
        x = {}
        self.obj_pointer[-1].append(x)
        self.obj_pointer.append(x)

        for key, val in key_values:
            self.obj_pointer[-1][f"{key} <key>"] = val

        # self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        # self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        # self.result.write(
        #     f"\n{self.get_indent()}<p align='right'>Need some buttons here to trigger removing this list element</p>\n"
        # )
        pass

    def close_list_element(self):
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
