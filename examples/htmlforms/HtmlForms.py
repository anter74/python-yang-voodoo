import logging
from yangvoodoo.SchemaData import Expander
from yangvoodoo import Types


class HtmlFormExpander(Expander):

    INCLUDE_BLANK_LIST_ELEMENTS = False
    LEAF_MAPPING = {
        Types.DATA_ABSTRACTION_MAPPING["BOOLEAN"]: "_write_checkbox",
        Types.DATA_ABSTRACTION_MAPPING["EMPTY"]: "_write_checkbox_empty",
        Types.DATA_ABSTRACTION_MAPPING["ENUM"]: "_write_dropdown",
    }
    AJAX_BASE_SERVER_URL = "http://127.0.0.1:8099/ajax"
    BASE64_ENCODE_PATHS = True

    """
    This provides an example implementation of forming a HTML from a given YANG based data tree
    (and it's associated schema).

    Assuming a server maintains an instance of this class per user - we can provide the user with
    an HTML form based on the data available.

        instance = HtmlFormExpander('my-yang-model', log)
        instance.process('initial-instance-data')

    The server could then provide an AJAX interface to match the hooks in yangui.js

        - `leaf_blur`, `check_blur`, `select_blur` could call `instance.data_tree_set_leaf(data_xpath, value)`
        - `add_leaflist_item`, `add_list_element` could call
           `instance.data_tree_add_list_element(list_data_xpath, [[key1,val1,key2,val2]])
           Note: a leaf-list is simply a list with a key of `.`
        - `remove_leaflist_item` `remove_list_element` could call
           `instance.data_tree_remove_list_element(list_element_xpath)`
        - `presence_container_expand` could call `data_tree_set_leaf(xpath, '')`
           Note: libyang represents a presence container as existing as a blank string.


    """

    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.default_collapse_state = "collapse show"
        self._disable_input_fields = False

    def callback_write_header(self, module):
        self.result.write(
            f"""{self.open_indent()}<head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js" integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/js-base64@3.7.3/base64.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/fork-awesome@1.2.0/css/fork-awesome.min.css" integrity="sha256-XoaMnoYC5TH6/+ihMEnospgm0J1PM/nioxbOUdnM8HY=" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/mousetrap@1.6.5/mousetrap.min.js" integrity="sha256-2saPjkUr3g4fEnQtPpdCpBLSnYd9L+qC5SXQUGQQv8E=" crossorigin="anonymous"></script>
<link rel="stylesheet" href="static/css/yangui.css"></head>
<script src="static/js/yangui.js"></script>
<script language="Javascript">
    AJAX_BASE_SERVER_URL="{self.AJAX_BASE_SERVER_URL}";
    LIBYANG_USER_PAYLOAD = {{}};  // this will be populated in the footer
    LIBYANG_CHANGES = [];
</script>
</head>\n"""
        )
        self.close_indent()

    def callback_write_open_body(self, module):
        self.result.write(f"{self.open_indent()}<body>\n")

        self.result.write(f'{self.get_indent()}<div id="alerts" class="yangui-alerts"></div>')

        self.result.write(
            f"""
        <div id="yangui-spinner" class='yangui-spinner'>
            <div class="spinner-border text-info" style="width: 10rem; height: 10rem;" role="status">
                <span class="sr-only">Please Wait...</span>
            </div>
            <p>
                <span id='yangui-spinnertext'>loading...</span>
            </p>
        </div>

        <div id="mymodal" class="modal" tabindex="-1" role="dialog">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Are you sure?</h5>
              </div>
              <div class="modal-body">
                <p>If you continue to delete this list element all the data will be removed</p>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-primary">Save changes</button>
                <button type="button" onClick="modal_visibility('mymodal', 'hide')" class="btn btn-secondary" data-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        </div>

        <div class='yangui-floating-left-buttons'>
          <div id='yangui-validate-button' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:validate_payload()" role="button">
              <i class="fa fa-stethoscope" aria-hidden="false"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-save-button' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:download_payload()" role="button">
                <i class="fa fa-download" aria-hidden="false"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-undo-button' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:yangui_undo()" role="button">
                <i class="fa fa-undo" aria-hidden="false"></i>
            </a>
          </div>
        </div>

        <div id='capture-new-item' class='yangui-popup yangui-hidden'>
            <h2>Add a new item <span id='capture-new-item-list-name'>...listname....</span><h2>

            <div id='capture-new-item-list-contents'></div>

            <hr/>
            <div align='right'>
            """
        )
        self._write_generic_button("href='javascript:close_new_item()' ", "cross", "danger")
        self._write_generic_button("href='javascript:save_new_item()' ", "check")
        self.result.write(
            """
            </div>
        </div>


        """
        )

        self.result.write(f"{self.open_indent()}<div class='container mt-5'>\n")
        self.result.write(
            """
        <div id="adams-debug-div"></div>



"""
        )

    def callback_write_close_body(self, module):
        self.result.write(f"{self.close_indent()}</div> <!-- close container -->\n")
        self.result.write(f"{self.close_indent()}</body>\n")

    def callback_open_containing_node(self, node, presence, node_id):
        """
        Open a container - which can be either:

        - A presence container which does not exist (presence=False)
          (it has not children so has not been created implicitly AND has not been created explicitly)
          This container should be dim and collapsed by default.
        - A presence container which exists and has not containers (presence=True)
          This container should match the user's
        - A non-presence container (presence=None)

        In the first case we need to support a hook to create the container even if there is no
        need to set child nodes.
        """
        this_container_collapse_or_show = self.default_collapse_state
        this_container_disable = ""
        this_container_expand_javascript = ""
        if presence is False:
            this_container_collapse_or_show = "collapse"
            this_container_disable = "yangui-disable"
            this_container_expand_javascript = self._get_html_attr("onClick", "presence_container_expand", data=True)

        self._write_anchor("Container")
        self._write_open_first_div("structure_container", extra_class=this_container_disable)
        self._write_button("th-large", on_click=this_container_expand_javascript)
        self._write_label(node, "structure_containerlabel", linebreak=True)
        self._write_open_second_div("structure_indent", extra_class=this_container_collapse_or_show)

    def callback_close_containing_node(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_write_leaf(self, node, value, quote, explicit, default, key, node_id):
        """
        Write an input box to capture input from a leaf.

        - Enumerations are represented as drop-down boxes.
        - Booleans and Empty leaves are represented as c
        """
        if key:
            return
        disabled = ""
        if self._disable_input_fields:
            disabled = "disabled"

        basetype = node.type().base()
        if basetype in self.LEAF_MAPPING:
            getattr(self, self.LEAF_MAPPING[basetype])(node, value, disabled)
        else:
            self._write_textbox(node, value, quote, disabled)

    def _write_checkbox(self, node, value, disabled, extra_button=""):
        """
        Write a checkbox to handle a boolean - within libyang booleans are stored as `true` and `false`
        """
        if value is True:
            checked = "checked"
        else:
            checked = ""

        self.result.write(f'{self.get_indent()}<div class="form-switch">\n')
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")

        self.result.write(
            f"{self.get_indent()}<input class='no-margin-left form-check-input' role='switch' type='checkbox'"
        )
        self.result.write(f"name={self.get_id(quote=True)} id={self.get_id(quote=True)} ")
        self.result.write(f"{self._get_html_attr('onChange', 'check_change', this=True, data=True)} ")
        self.result.write(f"{self._get_html_attr('onBlur', 'check_blur', this=True, data=True)} ")
        self.result.write(f"{checked} {disabled}><br/>\n")
        self.result.write(f"{self.get_indent()} {extra_button}\n")

    def _write_checkbox_empty(self, node, value, disabled, extra_button=""):
        """
        Write a checkbox to handle an empty leaf - within libyang an empty leaf is represented as
        a blank string - ''
        """
        if value is not None:
            checked = "checked"
        else:
            checked = ""

        self.result.write(
            f"{self.open_indent()}<input class='no-margin-left form-check-input' role='switch' type='checkbox'"
        )
        self.result.write(f"name={self.get_id(quote=True)} id={self.get_id(quote=True)} ")
        self.result.write(f"{self._get_html_attr('onChange', 'empty_change', this=True, data=True)} ")
        self.result.write(f"{self._get_html_attr('onBlur', 'empty_blur', this=True, data=True)} ")
        self.result.write(f"{checked} {disabled}><br/>\n")
        self.result.write(f"{self.get_indent()} {extra_button}\n")
        self.close_indent()

    def _write_dropdown(self, node, value, disabled, extra_button=""):
        """
        Write a drop down-box for enumerations, an enumeration *should* be implemented as a label
        and a numeric value (either explicitly assigned in the yang model, or auto-assigned).
        YANGVOODOO did not implement values for enumerations.
        """
        self.result.write(f'{self.get_indent()}<div class="form-check form-switch">\n')
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")

        self.result.write(
            f"{self.get_indent()}<select class='form-input' name={self.get_id(quote=True)} id={self.get_id(quote=True)} "
        )
        self.result.write(f"{self._get_html_attr('onChange', 'select_change', this=True, data=True)} ")
        self.result.write(f"{self._get_html_attr('onBlur', 'select_blur', this=True, data=True)} {disabled}>\n")
        for enum, _ in node.type().enums():
            selected = ""
            if value == enum:
                selected = "selected"
            self.result.write(f"{self.get_indent()}  <option {selected}>{enum}</option>\n")
        self.result.write(f"{self.get_indent()}</select>\n")

        self.result.write(f"{self.get_indent()} {extra_button}</div>\n")

    def _write_textbox(self, node, value, quote, disabled, extra_button=""):
        """
        Write a text box - this is used for strings and integers.
        """
        self.result.write(f"{self.get_indent()}<div>\n")
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")

        self.result.write(
            f"{self.get_indent()}<input type='text' name={self.get_id(quote=True)} id={self.get_id(quote=True)} "
        )
        self.result.write(f"value={quote}{value}{quote} ")
        self.result.write(f"{self._get_html_attr('onChange', 'leaf_change', this=True, data=True)} ")
        self.result.write(f"{self._get_html_attr('onBlur', 'leaf_blur', this=True, data=True)} {disabled} ")

        self.result.write(
            f'data-toggle="tooltip" data-placement="top" data-html="true" title="{"".join(self._get_tooltip_types(node))}"'
        )

        self.result.write(">\n")
        self.result.write(f"{self.get_indent()} {extra_button}</div>\n")

    def callback_open_list(self, node, count, node_id):
        """
        A list need to support adding items, but a list may have keys of differing types, may many keys
        (composite keys). When the user presses the plus button it is necessary to capture the values of
        all keys before data can be captured in the data tree. The list keys and values (predicates) are
        fundamental to a data xpath. e.g. /testform:simplelist[simplekey='num1']

        One approach is an AJAX call from create the data in the data tree (i.e. data_tree_add_list_element)
        and then calling subprocess to get the new sections of the web page to stitch into the DOM.
        """
        self._write_anchor("List")
        self._write_open_first_div("structure_list")
        self._write_button("list")
        self._write_extra_button(
            self._get_html_attr("href", "javascript:add_list_element", data=True, schema=True), "plus"
        )
        self._write_label(node, "structure_listlabel", linebreak=False)

        self.result.write(f"&nbsp;&nbsp;<span class='not-important-info' id='count-{self.get_hybrid_id()}'>{count} ")
        self.result.write(f"item{self.pluralise(count)}:")
        self.result.write("</span>")
        keys = [n.name() for n in node.keys()]
        self.result.write(f"&nbsp;&nbsp;<span class='not-important-info'>key{self.pluralise(keys)}: ")
        for comma, key in self.commaify(keys):
            self.result.write(f"{comma}{key}")
        self.result.write("</span>")

        self._write_open_second_div("structure_null")

    def callback_open_list_element(self, node, key_values, empty_list_element, node_id):
        self.result.write(f"{self.open_indent()}<div id='list-item-{self.get_hybrid_id()}'>\n")
        self.result.write(f"{self.get_indent()}<hr/>")
        self._write_anchor("ListElements")
        self._write_open_first_div("structure_listelement")
        self._write_button("angle-right")

        for comma, val in self.commaify([v for _, v in key_values]):
            self.result.write(f"{comma}<b>{val}</b>")

        self._write_extra_button(
            self._get_html_attr("href", "javascript:remove_list_element", data=True),
            "times",
            "danger",
            "Delete this list element all the descendant data",
        )

        self._write_open_second_div("structure_null", self.default_collapse_state)

    def callback_close_list_element(self, node):
        self._write_close_second_div()
        self._write_close_first_div()
        self.result.write(f"{self.close_indent()}</div>\n")

    def callback_close_list(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_open_choice(self, node, node_id):
        """
        A choice holds mutually exclusive data nodes, however the data xpath does not represent
        the structure of the choice of case nodes - these only exist in the schema.
        YANGVOODOO's auto-completion shows the choice/case nodes in the auto-completion

        If we have try to load  data tree belonging to multiple cases libyang will throw a
        MarshallingError.

        If we call `data_tree_set_leaf` and set data under a case any data which may already exist
        in other cases will be removed - when we dump out the data we will see data belonging to
        the last case which had it's data set.

        It is therefore possible to have a simple UI behaviour.
        - pressing the 'disable case' button only needs to cosmetically set opactity/disable for
          all cases
        - Show 'enable' case buttons for all cases.
        - pressing an 'enable' case button simply sets the opactity/enable for the specific case.
        - if the user changes data that will result in data changes
        - if the user doesn't change data within the new case the old behaviour would be retained.
          (this is potentially confusing because the user may believe the 'disable case' was a
           delete). But to do it fully means find and deleting all data under the case which is
           somewhat expensive because there is no data xpath to delete /.../mychoice/mycase1/*

        """
        self._parent_id = self.get_hybrid_id()
        self._write_anchor("Choice")
        self._write_open_first_div("structure_choice")
        self._write_button("object-group")
        self._write_label(node, "structure_choicelabel", linebreak=False)
        self._write_open_second_div("structure_null")

    def callback_open_case(self, node, active_case, no_active_case, node_id):
        self._disable_input_fields = True
        this_case_collapse_or_show = self.default_collapse_state
        div_disable = ""
        if not active_case:
            this_case_collapse_or_show = "collapse"
            div_disable = "yangui-disable"

        self._write_anchor("Case")
        self._write_open_first_div("structure_case")
        self._write_button("bullseye")

        self._write_extra_button(
            self._get_html_attr("href", "javascript:disable_case", parent=True),
            "compress",
            "warning",
            (
                "Cases within a choice are mutually exclusive - disable this case.\n\n"
                "This data will only be remove if data is entered in a differnt case."
            ),
            name="remove-case",
            visible=active_case,
        )

        if no_active_case:
            this_case_collapse_or_show = ""
        self._write_extra_button(
            self._get_html_attr("href", "javascript:enable_case", data=True, parent=True),
            "expand",
            "success",
            "Cases within a choice are mutually exclusive - enable this case",
            name="enable-case",
            visible=no_active_case,
        )

        self._write_label(node, "structure_caselabel", linebreak=False)
        self._write_open_second_div("structure_null")
        self.result.write(
            f"\n{self.open_indent()}<div class='{div_disable} {this_case_collapse_or_show}' id='case-{self.get_hybrid_id()}'>\n"
        )

    def callback_close_case(self, node):
        self._disable_input_fields = False
        self.result.write(f"\n{self.open_indent()}</div>\n")
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_close_choice(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_open_leaflist(self, node, count, node_id):
        """
        A leaf list behave the same as a single key list with a key name of `.`
        """
        self._write_anchor("LeafList")
        self._write_open_first_div("structure_leaflist")
        self._write_button("list-ul")
        self._write_extra_button(
            self._get_html_attr("href", "javascript:add_leaflist_item", data=True, schema=True), "plus"
        )
        self._write_label(node, "structure_leaflistlabel", linebreak=False)

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id='count-{self.get_hybrid_id()}'>{count} item{self.pluralise(count)}:"
        )
        self.result.write("</span>")

        self._write_open_second_div("structure_null")

    def callback_close_leaflist(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_write_leaflist_item(self, node, value, quote, explicit, node_id):
        self.result.write(f"{self.open_indent()}<div id='leaflist-item-{self.get_hybrid_id()}'>\n")
        extra_button = f"{self.get_indent()}&nbsp;&nbsp;<a class='btn btn-danger' {self._get_html_attr('href', 'javascript:remove_leaflist_item', data=True)}><i class='fa fa-times warning'></i></a>&nbsp;\n"

        basetype = node.type().base()
        if basetype in self.LEAF_MAPPING:
            getattr(self, self.LEAF_MAPPING[basetype])(node, value, False, extra_button)
        else:
            self._write_textbox(node, value, quote, False, extra_button)
        self.result.write(f"{self.close_indent()}</div>\n")

    @staticmethod
    def _get_tooltip(description):
        return description.replace('"', "&quote;")

    def _get_tooltip_types(self, node):
        for type, constraint in self.get_human_types(node):
            if constraint:
                yield f"{type} {{{', '.join(constraint)}}}" + "\n"
            else:
                yield f"{type}" + "\n"

    def _write_anchor(self, section_type):
        """
        Write an anchor and provide the path
        """
        self.result.write(f"\n{self.get_indent()}<!-- {section_type}: {self.get_hybrid_id()} -->")
        self.result.write(f"\n{self.get_indent()}<!-- {' '*len(section_type)}: {''.join(self.id_path_trail)} -->")
        self.result.write(f"\n{self.get_indent()}<a name='{self.get_hybrid_id()}'></a>")

    def _write_button(self, icon, on_click=""):
        """
        Write a button which will serve as something to expand/collapse a div with a given icon

        - icon: is a fork awesome icon
        """
        self.result.write(f"\n{self.open_indent()}&nbsp;&nbsp;")
        self.result.write(
            f"<a class='btn' data-bs-toggle='collapse' role='button' href='#collapse-{self.get_hybrid_id(as_uuid=True)}'"
        )
        self.result.write(
            f" aria-expanded='false' aria-controls='collapse-{self.get_hybrid_id(as_uuid=True)}' {on_click}>"
        )
        self.result.write(f"<i class='fa fa-{icon}' aria-hidden='true'></i></a>")

    def _write_extra_button(self, action, icon, theme="success", tooltip=None, name="", visible=True):
        """
        Write an extra button - e.g. used for adding/removing list element.

        - icon: is a fork awesome icon
        """
        if visible:
            visible = ""
        else:
            visible = "yangui-hidden"
        self.result.write(f"<span id='{name}-{self.get_hybrid_id()}' class='{visible}'>")
        self.result.write(f"&nbsp;<a class='btn btn-{theme}' {action} ")
        if tooltip:
            self.result.write(f'data-toggle="tooltip" data-placement="top" data-html="true" title="{tooltip}"')
        self.result.write(f"><i class='fa fa-{icon}'></i></a>&nbsp;</span>")

    def _write_generic_button(self, action, icon, theme="success", tooltip=None, name="", visible=True):
        """
        Write an extra button for actions on the page which are not based on yang nodes (i.e. do not require an id)
        """
        self.result.write(f"&nbsp;<a class='btn btn-{theme}' {action} ")
        if tooltip:
            self.result.write(f'data-toggle="tooltip" data-placement="top" data-html="true" title="{tooltip}"')
        self.result.write(f"><i class='fa fa-{icon}'></i></a>&nbsp;")

    def _write_open_first_div(self, structure_class, extra_class=""):
        self.result.write(
            f"\n{self.open_indent()}<div class='{structure_class} {extra_class}' id={self.get_hybrid_id()}>\n"
        )

    def _write_open_second_div(self, structure_class, extra_class=""):
        self.result.write(
            f"{self.open_indent()}<div class='{structure_class} {extra_class}' id='collapse-{self.get_hybrid_id(as_uuid=True)}'>\n"
        )
        self.open_indent()

    def _write_label(self, node, css_class, linebreak=True, label_icon=None):
        if label_icon:
            self.result.write(
                f"{self.get_indent()}<i class='fa {label_icon} yang_icon' aria-hidden='true'></i>&nbsp;\n"
            )
        self.result.write(f"{self.get_indent()}<label class='{css_class}' ")
        if node.description():
            self.result.write(
                f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
            )
        self.result.write(f">{node.name()}</label>")
        if linebreak:
            self.result.write(" <br/>")
        self.result.write("\n")

    def _write_close_second_div(self):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.close_indent()

    def _write_close_first_div(self):
        self.result.write(f"{self.close_indent()}</div>\n")

    def _get_html_attr(self, attribute, method, data=False, schema=False, parent=False, this=False):
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
            args.append(f"{inner_quote}{self.get_hybrid_id()}{inner_quote}")
        if schema:
            args.append(f"'{self.get_schema_id()}'")
        if parent:
            args.append(f"{inner_quote}{self._parent_id}{inner_quote}")
        if this:
            args.append("this")
        return f"{attribute}={attr_quote}{method}({', '.join(args)}){attr_quote}"

    def callback_write_footer(self, module):
        self.result.write("<script language=Javascript>\n")
        self.result.write(f"LIBYANG_USER_PAYLOAD = {self.data_ctx.dumps(2)};\n")
        self.result.write("stop_yangui_spinner();\n")
        self.result.write("</script>")


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(55)

    generator = HtmlFormExpander("testforms", log)
    generator.process(open("templates/forms/choicecase.xml").read())
    generator.dumps()
    generator.dump("examples/htmlforms/test.html")
