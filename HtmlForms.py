import json
import libyang
import logging

from io import StringIO
from typing import List

from yangvoodoo.SchemaData import Expander


class HtmlFormExpander(Expander):
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

    def write_footer(self):
        pass

    def open_containing_node(self, node):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- container type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_container' id={self.get_id()}>\n")
        self.result.write(f"{self.get_indent()}<label class='structure_containerlabel'>{node.name()}</label><br/>\n")

    def close_containing_node(self, node):
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} container-->\n\n")

    def write_leaf(self, node, value, default=None):
        """
        Here we should return different data based on the leaf type
        i.e. boolean/empty leaves should be checkbox
        enumerations should be drop-down boxes
        we should extract description of the yang model as a tool tip

        we should deal with default values too when the data isn't set - perhaps with a lighter colour in the input
        than if it haves explicit values. (WOULD HAVE TO BE HANDLED IN Javascript so not worth the effort)
        """
        self.result.write(
            f"{self.get_indent()}<label class='structure_leaflabel' for={self.get_id()}>{node.name()}</label>\n"
        )
        self.result.write(
            f"{self.get_indent()}<input type='text' name={self.get_id()} id={self.get_id()} value={value}><br/>\n"
        )

    def open_list(self, node):
        """
        Some client side javascript to try capture list key values?
        before submitting the form back to the server?

        Can the javascript goes as far as checking existing list key/values (if not do that server side)

        Assumption is rather than being *too* ajaxy going backwards and forwards to the client isn't the
        end of the world.

        When we are in a list we won't look at the schema but instead look to the data tree to find list elements
        which exist - and then pass those to prcoess_nodes?
        """
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- list type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_list' id={self.get_id()}>\n")
        self.result.write(f"{self.get_indent()}<label class='structure_listlabel'>{node.name()}</label><br/>\n")
        self.result.write(
            f"\n{self.get_indent()}<p align='right'>Need some {self.get_id()} buttons here to trigger adding extra list element</p>\n"
        )

    def close_list(self, node):
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} list -->\n\n")

    def open_list_element(self):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.get_indent()}<p align='right'>Need some buttons here to trigger removing this list element</p>\n"
        )

    def close_list_element(self):
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} listelement -->\n\n")


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = HtmlFormExpander("testforms", log)
    generator.process(open("resources/simplelist2.xml").read())
    generator.dumps()
