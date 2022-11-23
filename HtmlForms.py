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
<link rel="stylesheet" href="static/css/mystyle.css"></head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/fork-awesome@1.2.0/css/fork-awesome.min.css" integrity="sha256-XoaMnoYC5TH6/+ihMEnospgm0J1PM/nioxbOUdnM8HY=" crossorigin="anonymous">
<script src="static/js/yangui.js"></script>
</head>
                   """
        )

    def write_footer(self):
        pass

    def open_containing_node(self, node):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- container type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_container' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-th-large' aria-hidden='true'></i></a>"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_containerlabel'>{node.name()}</label><br/>\n")
        self.result.write(f"{self.open_indent()}<div class='collapse show' id='collapse-{self.get_uuid()}'>\n")

    def close_containing_node(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} container-->\n\n")

    @staticmethod
    def _get_tooltip(description):
        return description.replace('"', "&quote;")

    def write_leaf(self, node, value, default=None, key=False):
        """
        Here we should return different data based on the leaf type
        i.e. boolean/empty leaves should be checkbox
        enumerations should be drop-down boxes
        we should extract description of the yang model as a tool tip

        we should deal with default values too when the data isn't set - perhaps with a lighter colour in the input
        than if it haves explicit values. (WOULD HAVE TO BE HANDLED IN Javascript so not worth the effort)
        """
        if key:
            return
        disabled = ""
        self.result.write(
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i class='fa fa-leaf yang_icon' aria-hidden='true'></i>&nbsp;"
        )

        self.result.write(f"{self.get_indent()}<label class='structure_leaflabel' for={self.get_id()}")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>\n")

        basetype = node.type().base()
        if basetype in (3, 5):
            if value == '"True"':
                checked = "checked"
            else:
                checked = ""

            self.result.write(
                f"{self.get_indent()}&nbsp;<input class='form-check-input' type='checkbox' name={self.get_id()} id={self.get_id()} onChange='leaf_change(this)' onBlur='leaf_blur(this)' {checked}><br/>\n"
            )
        elif basetype == 6:
            self.result.write(
                f"{self.get_indent()}<select class='form' name={self.get_id()} id={self.get_id()} onChange='leaf_change(this)' onBlur='leaf_blur(this)'>\n"
            )
            for enum, _ in node.type().enums():
                selected = ""
                if value == selected:
                    selected = "selected"
                self.result.write(f"{self.get_indent()}  <option {selected}>{enum}</option>\n")
            self.result.write(f"{self.get_indent()}</select><br/>\n")
        else:
            self.result.write(
                f"{self.get_indent()}<input type='text' name={self.get_id()} id={self.get_id()} value={value} onChange='leaf_change(this)' onBlur='leaf_blur(this)' {disabled}><br/>\n"
            )

    @staticmethod
    def pluralise(listobj):
        if isinstance(listobj, int):
            if listobj > 1:
                return "s"
            return ""
        if len(listobj) > 1:
            return "s"
        return ""

    @staticmethod
    def commaify(listobj):
        comma = ""
        for item in listobj:
            yield comma, item
            comma = ", "

    def open_list(self, node, count):
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
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-list' aria-hidden='true'></i></a>"
        )
        self.result.write(
            f"&nbsp;<a class='btn btn-success' href=javascript:add_list_element({self.get_id()})><i class='fa fa-plus'></i></a>&nbsp;"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_listlabel'>{node.name()}</label>  \n")

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id=count-{self.get_id()}>{count} item{self.pluralise(count)}:"
        )
        self.result.write("</span>")
        keys = [n.name() for n in node.keys()]
        self.result.write(f"&nbsp;&nbsp;<span class='not-important-info'>key{self.pluralise(keys)}: ")
        for comma, key in self.commaify(keys):
            self.result.write(f"{comma}{key}")
        self.result.write("</span>")
        self.result.write(f"{self.open_indent()}<div class='collapse show' id='collapse-{self.get_uuid()}'>\n")

    def close_list(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} list -->\n\n")

    def open_list_element(self, key_values):
        self.result.write(f"{self.get_indent()}<hr/>")
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-angle-right' aria-hidden='true'></i></a>"
        )
        for comma, val in self.commaify([v for _, v in key_values]):
            self.result.write(f"{comma}<b>{val}</b>")
        self.result.write(
            f"&nbsp;&nbsp;<a class='btn btn-warning' href=javascript:remove_list_element({self.get_id()})><i class='fa fa-times warning'></i></a>&nbsp;"
        )

        self.result.write(f"{self.open_indent()}<div class='collapse show' id='collapse-{self.get_uuid()}'>\n")

    def close_list_element(self):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} listelement -->\n\n")


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = HtmlFormExpander("testforms", log)
    generator.process(open("resources/simplelist3.xml").read())
    generator.dumps()
    generator.dump("test.html")
