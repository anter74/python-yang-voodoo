import json
import libyang
import logging

from io import StringIO
from typing import List

from yangvoodoo.SchemaData import Expander

collapse_or_show = "collapse show"


class HtmlFormExpander(Expander):
    INCLUDE_BLANK_LIST_ELEMENTS = False

    def callback_write_header(self, module):
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

    def callback_open_containing_node(self, node, presence, node_id):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- container type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_container' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-th-large' aria-hidden='true'></i></a>"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_containerlabel' ")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label><br/>\n")
        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_close_containing_node(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} container-->\n\n")

    @staticmethod
    def _get_tooltip(description):
        return description.replace('"', "&quote;")

    def callback_write_leaf(self, node, value, default, key, node_id):
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
                f"{self.get_indent()}&nbsp;<input class='form-check-input' type='checkbox' name={self.get_id()} id={self.get_id()} {self.get_html_attr('onChange', 'check_change', this=True, data=True)} {self.get_html_attr('onBlur', 'check_blur', this=True, data=True)} {checked}><br/>\n"
            )
        elif basetype == 6:
            self.result.write(
                f"{self.get_indent()}<select class='form' name={self.get_id()} id={self.get_id()} {self.get_html_attr('onChange', 'select_change', this=True, data=True)} {self.get_html_attr('onBlur', 'select_blur', this=True, data=True)}>\n"
            )
            for enum, _ in node.type().enums():
                selected = ""
                if value == selected:
                    selected = "selected"
                self.result.write(f"{self.get_indent()}  <option {selected}>{enum}</option>\n")
            self.result.write(f"{self.get_indent()}</select><br/>\n")
        else:
            self.result.write(
                f"{self.get_indent()}<input type='text' name={self.get_id()} id={self.get_id()} value={value} {self.get_html_attr('onChange', 'leaf_change', this=True, data=True)} {self.get_html_attr('onBlur', 'leaf_blur', this=True, data=True)} {disabled}"
            )

            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{", ".join(self.get_tooltip_types(node))}"'
            )

            self.result.write("><br/>\n")

    def get_tooltip_types(self, node):
        for type, constraint in self.get_human_types(node):
            yield f"{type} {{{', '.join(constraint)}}}"

    def callback_open_list(self, node, count, node_id):
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
            f"&nbsp;<a class='btn btn-success' {self.get_html_attr('href', 'javascript:add_list_element', data=True, schema=True)}><i class='fa fa-plus'></i></a>&nbsp;"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_listlabel'")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>  \n")

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id=count-{self.get_id()}>{count} item{self.pluralise(count)}:"
        )
        self.result.write("</span>")
        keys = [n.name() for n in node.keys()]
        self.result.write(f"&nbsp;&nbsp;<span class='not-important-info'>key{self.pluralise(keys)}: ")
        for comma, key in self.commaify(keys):
            self.result.write(f"{comma}{key}")
        self.result.write("</span>")
        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_close_list(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} list -->\n\n")

    def callback_open_choice(self, node, node_id):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- choice type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_choice' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-object-group' aria-hidden='true'></i></a>"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_choicelabel'")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>  \n")
        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_open_case(self, node, active_case, no_active_case, node_id):
        self.log.warning("Need to set case on the UI to disabled based on no active cases")
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- case type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_choice' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-map-pin' aria-hidden='true'></i></a>"
        )
        self.result.write(
            f"&nbsp;<a class='btn btn-warning' {self.get_html_attr('href', 'javascript:remove_case', schema=True)}><i class='fa fa-times'></i></a>&nbsp;"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_choicelabel'")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>  \n")
        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_close_case(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} -case -->\n\n")

    def callback_close_choice(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} choice -->\n\n")

    def callback_open_list_element(self, node, key_values, empty_list_element, node_id):
        self.result.write(f"{self.get_indent()}<hr/>")
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- listelement type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-angle-right' aria-hidden='true'></i></a>"
        )
        for comma, val in self.commaify([v for _, v in key_values]):
            self.result.write(f"{comma}<b>{val}</b>")
        self.result.write(
            f"&nbsp;&nbsp;<a class='btn btn-warning' {self.get_html_attr('href', 'javascript:remove_list_element', data=True, schema=True)}><i class='fa fa-times warning'></i></a>&nbsp;"
        )

        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_close_list_element(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} listelement -->\n\n")

    def callback_open_leaflist(self, node, count, node_id):
        self.result.write(f"\n{self.get_indent()}<a name={self.get_id()}></a> <!-- leaf list type -->")
        self.result.write(f"\n{self.open_indent()}<div class='structure_leaflist' id={self.get_id()}>\n")
        self.result.write(
            f"\n{self.open_indent()}&nbsp;&nbsp;<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_uuid()}' aria-expanded='false' aria-controls='collapse-{self.get_uuid()}'><i class='fa fa-list-ul' aria-hidden='true'></i></a>"
        )
        self.result.write(
            f"&nbsp;<a class='btn btn-success' {self.get_html_attr('href', 'javascript:add_leaflist_element', data=True, schema=True)}><i class='fa fa-plus'></i></a>&nbsp;"
        )
        self.result.write(f"{self.get_indent()}<label class='structure_leaflistlabel' ")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>  \n")

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id=count-{self.get_id()}>{count} item{self.pluralise(count)}:"
        )
        self.result.write("</span>")
        self.result.write(f"{self.open_indent()}<div class='{collapse_or_show}' id='collapse-{self.get_uuid()}'>\n")

    def callback_close_leaflist(self, node):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.result.write(f"{self.close_indent()}</div> <!-- closes {self.get_id()} ;eaf list -->\n\n")

    def callback_write_leaflist_item(self, value, node_id):
        self.result.write(f"\n{self.open_indent()}<div class='structure_listelement' id={self.get_id()}>\n")
        self.result.write(
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i class='fa fa-leaf yang_icon' aria-hidden='true'></i>&nbsp;"
        )
        self.result.write(
            f"{self.get_indent()}<input type='text' name={self.get_id()} id={self.get_id()} value={value} {self.get_html_attr('onBlur', 'leaf_blur', this=True, data=True)} disable>\n"
        )
        self.result.write(
            f"{self.get_indent()}&nbsp;&nbsp;<a class='btn btn-warning' {self.get_html_attr('href', 'javascript:remove_leaflist_element', data=True)}><i class='fa fa-times warning'></i></a>&nbsp;\n"
        )
        #
        self.result.write(f"{self.close_indent()}</div>\n")

    def get_html_attr(self, attribute, method, data=False, schema=False, this=False):
        """
        For a HTML attribute for href's onBlur, onChange etc and ensure we use the correct quoting/encoding
        of quotes.
        """
        d = self.get_id()
        if d[0] == '"':
            outer_quote = "'"
            replace_quote = "&apos;"
            inner_quote = '"'
        else:
            outer_quote = '"'
            replace_quote = "&quot;"
            inner_quote = "'"

        args = []
        if data:
            args.append(f"{inner_quote}{d[1:-1].replace(outer_quote, replace_quote)}{inner_quote}")
        if schema:
            args.append(f"{inner_quote}{self.get_schema_id()[1:-1].replace(outer_quote, replace_quote)}{inner_quote}")
        if this:
            args.append("this")
        return f"{attribute}={outer_quote}{method}({', '.join(args)}){outer_quote}"

    def get_html_id(self):
        result = self.get_id()
        if result[0] == "'":
            return result.replace('"', "&quot;")
        return result.replace("'", "&apos;")

    def get_html_schema_id(self):
        result = self.get_schema_id()
        if result[0] == "'":
            return result.replace('"', "&quot;")
        return result.replace("'", "&apos;")


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(5)

    generator = HtmlFormExpander("testforms", log)
    generator.process(open("templates/forms/simplelist4.xml").read())
    generator.dumps()
    generator.dump("examples/html-forms/test.html")
