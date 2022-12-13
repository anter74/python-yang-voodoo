import libyang
from examples.htmlforms.HtmlForms import HtmlFormExpander


class HtmlExpander(HtmlFormExpander):

    TITLE = "YANG On A Page"
    INCLUDE_BLANK_LIST_ELEMENTS = True
    BASE64_ENCODE_PATHS = True
    ALWAYS_FETCH_CONTAINER_CONTENTS = True  # overrides all yang annotations
    AUTO_EXPAND_LIST_ELEMENTS = True
    ALWAYS_FETCH_CONTAINER_CONTENTS = True
    ALWAYS_FETCH_LISTELEMENT_CONTENTS = True
    ALWAYS_FETCH_LIST_CONTENTS = True
    SHOW_DESCRIPTIONS = "inline"
    READONLY = True

    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.default_collapse_state = "collapse show"
        self.USER_UI_STATE_CHANGES = {}
        self.include_as_subpage = False

    def _should_container_be_visisble(self, node: libyang.schema.Node, presence: bool) -> bool:
        return True

    def _should_listelement_be_visisble(self, node: libyang.schema.Node, force_visible: bool) -> bool:
        return True

    def _should_list_be_visisble(self, node: libyang.schema.Node) -> bool:
        return True

    def callback_write_header(self, module):
        if self.include_as_subpage:
            return
        self.result.write(
            f"""<html lang="en">
{self.open_indent()}<head>
<title>{self.yang_module} - {self.TITLE}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js" integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css" integrity="sha512-MV7K8+y+gLIBoVD59lQIYicR65iaqukzvf/nwasF0nqhPay5w/9lJmVM2hMDcnK1OnMGCdVK+iQrJ7lzPJQd1w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
"""
        )
        self.result.write(
            """
<style>
.yangui-main-wrapper {
}
.structure_indent {
  margin-left: 35px;
}
.structure_null {
}
.structure_choice {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;
}
.structure_case {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;
}
.structure_list {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;
}
.structure_listelement {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;

}
.structure_leaflist {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;
}
.structure_container {
  border-style: dotted;
  border-radius: 15px;
  border-color: silver;
  padding-left: 10px;
  padding-top: 10px;
}
.structure_leaflabel{
  min-width: 150px;
}
.yang_icon {
  color: gray;
}
.not-important-info {
  color: gray;
}
.yangui-disable {
  opacity: 0.5;
}
.yangui-deleted {
  opacity: 0.1;
}
.fix-margin-left-switch-2 {
    margin-left: 2em !important;
}
.fix-margin-left-switch-1 {
    margin-left: -2.5em !important;
}
.yangui-hidden {
  display: none;
}
blockquote:not([class]) {
    margin: 1em 40px;
    border-left: 4px solid #eaecf0;
    padding: 8px 32px;
    color: dimgray;
}
</style>

<script>
function presence_container_expand(){
// null function
}
</script>
"""
        )

    def callback_write_leaf(self, node, value, quote, explicit, default, key, template, node_id):
        if key and not template:
            return
        disabled = ""

        basetype = node.type().base()

        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")
        if not value:
            self.result.write(f"{self.get_indent()} <i class='not-important-info'>not set</i>")
        else:
            self.result.write(f"{self.get_indent()} <u>{value}</u>")
        self.result.write("<br/>\n")
        self.result.write("<ul>")
        for type, constraints in self.get_human_types(node):
            self.result.write(f" <li> {type}")
            if constraints:
                self.result.write("<ui>")
                for constraint in constraints:
                    self.result.write(f" <li> {constraint}")
                self.result.write("</ui>")
            if node.mandatory():
                self.result.write(f"<li> Mandatory ")
            if node.when_condition():
                for line in node.when_condition().split("\n"):
                    self.result.write(f"<li> <b>When</b> {line}")
            if node.must_conditions():
                for cond in node.must_conditions():
                    for line in cond.split("\n"):
                        self.result.write(f"<li> <b>Must</b> {line}")
        self.result.write("</ul>")
        self.result.write("<BR>")
        if self.SHOW_DESCRIPTIONS == "inline":
            if node.description():
                self.result.write("<blockquote>")
                for word in self.block_quotify(node.description(), 200, "", newline="<br>"):
                    self.result.write(word)
                self.result.write("</blockquote>")

    def _write_close_first_div(self):
        self.result.write(f"{self.close_indent()}</div>\n")

    def callback_write_open_body(self, module):
        if self.include_as_subpage:
            return
        self.result.write("<body>\n")
        self.result.write("<div class='container'>\n")

        self.result.write(f"<h1>{self.yang_module}</h1>")

        for word in self.block_quotify(module.description(), 400, "", newline="<br>"):
            self.result.write(word)

        self.result.write("<p></p>")

        self.result.write("<h3>Revisions</h3>")
        self.result.write("<table border=0 cellspacing=3><tr><th>Revision</th><th>&nbsp;</th></tr>")
        revisions = list(module.revisions())
        for rev in revisions[0:5]:
            self.result.write(f"<tr valign=top><td width=200>{rev.date()}</td><td>")
            for word in self.block_quotify(rev.description(), 350, "", newline_split="\n", newline="<br/>"):
                self.result.write(f"{word}")
            self.result.write("</td></tr>")
        self.result.write("</table><p></p>")

    def callback_write_close_body(self, module):
        self.result.write("</div>\n")
        self.result.write("</body>\n")

    def callback_write_footer(self, module):
        if self.include_as_subpage:
            return
