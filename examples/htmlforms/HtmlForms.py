import logging
import os
from yangvoodoo.SchemaData import Expander
from yangvoodoo import Types


class HtmlFormExpander(Expander):

    TITLE = "YANG Unicorn Interface ✨ 🦄 ✨ - 💣 Prototype 💣 "
    INCLUDE_BLANK_LIST_ELEMENTS = False
    LEAF_MAPPING = {
        Types.DATA_ABSTRACTION_MAPPING["BOOLEAN"]: "_write_checkbox",
        Types.DATA_ABSTRACTION_MAPPING["EMPTY"]: "_write_checkbox_empty",
        Types.DATA_ABSTRACTION_MAPPING["ENUM"]: "_write_dropdown",
    }
    AJAX_BASE_SERVER_URL = os.getenv("YANGUI_BASE_API", "http://127.0.0.1:8099/api")
    BASE64_ENCODE_PATHS = True
    ALWAYS_FETCH_CONTAINER_CONTENTS = False
    ALWAYS_FETCH_LISTELEMENT_CONTENTS = False
    ALWAYS_FETCH_LIST_CONTENTS = False
    SHOW_DESCRIPTIONS = "tooltip"
    READONLY = False

    """
    This provides an example implementation of forming a HTML from a given YANG based data tree
    (and it's associated schema).

    Assuming a server maintains an instance of this class per user - we can provide the user with
    an HTML form based on the data available.

        instance = HtmlFormExpander('my-yang-model', log)
        instance.process('initial-instance-data')

    Approach 1: (NOT IMPLEMENTED)

    The server could then provide an AJAX interface to match the hooks in yangui.js

        - `yangui_leaf_blur`, `check_blur`, `select_blur` could call `instance.data_tree_set_leaf(data_xpath, value)`
        - `add_leaflist_item`, `yangui_add_list_element_dialog` could call
           `instance.data_tree_add_list_element(list_data_xpath, [[key1,val1,key2,val2]])
           Note: a leaf-list is simply a list with a key of `.`
        - `yangui_soft_delete_leaflist_item` `yangui_soft_delete_list_element` could call
           `instance.data_tree_yangui_soft_delete_list_element(list_element_xpath)`
        - `presence_container_expand` could call `data_tree_set_leaf(xpath, '')`
           Note: libyang represents a presence container as existing as a blank string.

    Approach 2 (PROOF OF CONCEPT IMPLEMENTATION):

    Or an an alternative is to keep as much as possible client side, by (in Javascript) starting with a JSON
    encoded payload. The UI decisions the user makes can the build a list of changes that may then be processed.
    (This pattern may work well for a CLI interface with 'candidate' transactions).

    The first approach has a downside of managing server side sessions and memory- the second has more processing
    doen client side with more dependency on the browser not crashing. This may be the least performant option
    of the browser.

    This could be refactored to provide templates to build the page.


    Overview of the Dom:

    - Each containing node (i.e. containers, choices, case, list) have a <div id="collapse-UUID"></div>
      The UUID is calculated based on the hybrid path

    - When adding items to a list element or leaf-list they are appended into this div

    - When 'soft' deleting items from a list element or leaf-list they are disabled rather than delete.

    - When changing cases in a choice the UI is disabled but the data is not removed.
    """

    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.default_collapse_state = "collapse show"

    def callback_write_header(self, module):
        self.result.write(
            f"""<html lang="en">
{self.open_indent()}<head>
<title>{self.TITLE} - {self.yang_module}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js" integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/js-base64@3.7.3/base64.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css" integrity="sha512-MV7K8+y+gLIBoVD59lQIYicR65iaqukzvf/nwasF0nqhPay5w/9lJmVM2hMDcnK1OnMGCdVK+iQrJ7lzPJQd1w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<script src="https://cdn.jsdelivr.net/npm/mousetrap@1.6.5/mousetrap.min.js" integrity="sha256-2saPjkUr3g4fEnQtPpdCpBLSnYd9L+qC5SXQUGQQv8E=" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-select@1.14.0-beta3/dist/css/bootstrap-select.min.css">
<script src="https://cdn.jsdelivr.net/npm/bootstrap-select@1.14.0-beta3/dist/js/bootstrap-select.min.js"></script>
<link rel="stylesheet" href="/static/css/yangui.css"></head>
<script src="/static/js/yangui.js"></script>
<script src="/static/js/your-actions.js"></script>
<script language="Javascript">
    AJAX_BASE_SERVER_URL="{self.AJAX_BASE_SERVER_URL}/{self.yang_module}";
    LIBYANG_USER_PAYLOAD = {{}};  // this will be populated in the footer
    LIBYANG_CHANGES = []; // a list of changes we need to make (supports the ability to do a simple UNDO mechnism)
    ELEMENTS_EXPANDED_BY_USER = {{}}; // this contains the UUID's of elements which have been expanded by the user
    LIBYANG_MODEL = "{self.yang_module}";
    YANGUI_TITLE = "{self.TITLE}";
</script>
<style>
.yangui-spinner {{
  z-index: 99;
  position: fixed;
  overflow: automatic;
  left: 0px;
  top: 0px;
  width: 100%;
  height: 100%;
  background: white;
  opacity: 0.8;
  padding-top: 25%;
  padding-left: 45%;
}}
// this is here so we don't fail to show the spinner while waiting for the CSS to be downloaded
// we don't yet send any instructions from torando to ask for caching of elements.
// This is a symptom of Torando not being multi-threaded?
</style>
</head>\n"""
        )
        self.close_indent()

    def callback_write_open_body(self, module):
        self.result.write(f"{self.open_indent()}<body>\n")

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


        <div id="yanguiDebugModal" class="modal" tabindex="-1" role="dialog" >
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Debug Modal</h5>
              </div>
              <div class="modal-body">
                <textarea id='yangui-content-debug' rows=20 cols=40 style='font-style: monospace;'></textarea>
              </div>
              <div class="modal-footer">
                <button type="button" onClick="yangui_debug_close()" class="btn btn-secondary" data-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        </div>

        <div id="yanguiUploadModal" class="modal" tabindex="-1" role="dialog">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Upload a saved file</h5>
              </div>
              <div class="modal-body">
                <form action="{self.AJAX_BASE_SERVER_URL}/{self.yang_module}/upload" method="post" enctype="multipart/form-data">
                    <div class="custom-file">
                      <input id="yangui-file-input" type="file" name='payload' class="custom-file-input" accept='application/json'>
                      <label class="custom-file-label" for="customFileLang">JSON instance data (RFC7159)</label>
                    </div><hr/>
                    <p class='text-danger'>If you upload any unsaved data on this page will be lost</p>
                  </div>
                  <div class="modal-footer">
                    <button type="submit" id="yangui-file-button" class="btn btn-primary">Upload</button>
                    <button type="button" onClick="modal_visibility('yanguiUploadModal', 'hide')" class="btn btn-secondary" data-dismiss="modal">Close</button>
                  </div>
                </form>
            </div>
          </div>
        </div>


        <div id="yanguiNewItemModal" class="modal" tabindex="-1" role="dialog">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Add a new item <span id='yanguiNewItem-item'></span></h5>
              </div>
              <div class="modal-body">


                <div id='yanguiNewItemContents' class='form-input'>
                </div>

                <hr/>
              </div>
              <div class="modal-footer">
                <button type="submit" onClick="yangui_create_new_list_element_or_leaflist_item()" data-yangui-for-type="" data-yangui-for-list="" id="yangui-create-list-button" class="btn btn-primary">Create</button>
                <button type="button" onClick="modal_visibility('yanguiNewItemModal', 'hide')" class="btn btn-secondary" data-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        </div>



        <!-- wrapper -->
        <div class='wrapper'>

        """
        )

        self.result.write(
            f"""
        <nav id="sidebar">
        <div class='yangui-floating-left-buttons'>
          <div id='yangui-new'>
            <a class="btn btn-primary" href="javascript:yangui_new_payload()" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Start new payload (y n)">
                <i class="fa fa-file" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-undo' class='yangui-disable'>
            <a class="btn btn-primary" id="yangui-undo-button" href="javascript:yangui_undo()" role="button" data-toggle="tooltip" data-placement="top" data-html="true" title="Undo the last change (ctrl+z)" tabindex="-1">
                <i class="fa fa-undo" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-validate' class='yangui-disable'>
            <a class="btn btn-primary" id="yangui-validate-button" href="javascript:yangui_validate_payload()" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Validate data (y s)">
              <i class="fa fa-microscope" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-save' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:yangui_save(false)" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Download the contents of this form (ctrl+s)">
                <i class="fa fa-download" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-export' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:yangui_save(true)" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Export a YANG compliant JSON encoding (ctrl+shitf+s)">
                <i class="fa fa-file-export" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-debug' class='yangui-disable'>
            <a class="btn btn-primary" href="javascript:yangui_debug_payload()" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Show a JSON payload (y d)">
                <i class="fa fa-bug" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-submit'>
            <a class="btn btn-primary" id="yangui-upload-button" href="javascript:yangui_upload_payload()" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Upload a saved payload (ctrl+o)">
                <i class="fa fa-upload" aria-hidden="true"></i>
            </a>
          </div>
          <hr/>
          <div id='yangui-upload'>
            <a class="btn btn-primary" href="javascript:yangui_submit_payload()" role="button" tabindex="-1" data-toggle="tooltip" data-placement="top" data-html="true" title="Submit a payload (y c)">
                <i class="fa fa-sun" aria-hidden="true"></i>
            </a>
          </div>
        </div>
        </nav>
"""
        )

        self.result.write(
            f"""{self.open_indent()}<div class='container mt-12 yangui-main-wrapper'>\n

            <div class="yangui-messages fixed-bottom">
                <div class="yangui-messages-danger" id="yangui-msg-danger" data-yangui-hide-at="0"></div>
                <div class="yangui-messages-success" id="yangui-msg-success" data-yangui-hide-at="0"></div>
                <div class="yangui-messages-normal" id="yangui-msg-normal"></div>

            </div>


            <div class="tab-content" id="nav-tabContent">
                          """
        )

    def callback_write_close_body(self, module):
        self.result.write(f"{self.close_indent()}</div> <!-- close nav tab content -->\n")
        self.result.write(f"{self.close_indent()}</div> <!-- close container -->\n")
        self.result.write(f"{self.close_indent()}</div> <!-- close wrapper -->\n")
        self.result.write(f"{self.close_indent()}</body>\n")

    def callback_write_footer(self, module):
        self.result.write("<hr/><script language=Javascript>\n")
        if self.data_loaded:
            self.result.write(f"LIBYANG_USER_PAYLOAD = {self.data_ctx.dumps(2)};\n")
        self.result.write("stop_yangui_spinner();\n")
        self.result.write("yangui_default_mousetrap();\n")
        self.result.write("yangui_welcome();\n")
        self.result.write("</script>")

    #
    #
    # Callback methods for writing page contents
    #
    #

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
        extra_label = ""
        if presence in (True, False):
            this_container_expand_javascript = " yangui-field-type='presence-container' "
        else:
            this_container_expand_javascript = " yangui-field-type='container' "

        if presence is True:
            extra_label = " &nbsp; <span class='yangui-has-contents'>(exists)</span>"

        if not self._should_container_be_visible(node, presence):
            this_container_collapse_or_show = "collapse"
            if not self._exists("".join(self.data_path_trail), child_contents=True):
                this_container_disable = "yangui-disable"
            else:
                if presence is True:
                    extra_label = " &nbsp; <span class='yangui-has-contents'>(exists)</span>"
                else:
                    extra_label = " &nbsp; <span class='yangui-has-contents'>(has contents)</span>"
            this_container_expand_javascript += self._get_html_attr(
                "onClick", "presence_container_expand", data=True, uuid=True
            )

        self._write_anchor("Container")
        self._write_open_first_div("structure_container", extra_class=this_container_disable)
        self._write_button("th-large", on_click=this_container_expand_javascript)
        self._write_label(node, "structure_containerlabel", linebreak=True, extra_label=extra_label)
        self._write_open_second_div(node, "structure_indent", collapse=this_container_collapse_or_show)

    def callback_close_containing_node(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_write_leaf(self, node, value, quote, explicit, default, key, template, node_id):
        """
        Write an input box to capture input from a leaf.

        - Enumerations are represented as drop-down boxes.
        - Booleans and Empty leaves are represented as c
        """
        if key and not template:
            return
        disabled = ""

        basetype = node.type().base()
        if basetype in self.LEAF_MAPPING:
            getattr(self, self.LEAF_MAPPING[basetype])(node, value, quote, disabled, template=template)
        else:
            self._write_textbox(node, value, quote, disabled, template=template)

        if self.SHOW_DESCRIPTIONS == "inline":
            if node.description():
                self.result.write("<blockquote>")
                for word in self.block_quotify(node.description(), 200, "", newline="<br>"):
                    self.result.write(word)
                self.result.write("</blockquote>")

    def _write_checkbox(self, node, value, quote, disabled, extra_button="", template=False):
        """
        Write a checkbox to handle a boolean - within libyang booleans are stored as `true` and `false`
        """
        if value is True:
            checked = "checked"
        else:
            checked = ""

        self.result.write(f"{self.get_indent()}<div class='form-switch fix-margin-left-switch-1'>\n")
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")

        self.result.write(
            f"{self.get_indent()}<input class='fix-margin-left-switch-2 form-check-input' role='switch' type='checkbox'"
        )
        self.result.write(f" id={self.get_id()} ")
        self.result.write(f' data-yangui-keyname="{node.name()}" ')
        if value:
            self.result.write(f" data-yangui-start-val='on' ")
        else:
            self.result.write(f" data-yangui-start-val='off' ")
        self.result.write(" data-yangui-field-type='checkbox' ")
        if not template:
            self.result.write(f"{self._get_html_attr('onChange', 'yangui_checkbox_change', this=True, data=True)} ")
        self.result.write(f"{checked} {disabled}><br/>\n")
        self.result.write(f"{self.get_indent()} {extra_button}</div>\n")

    def _write_checkbox_empty(self, node, value, quote, disabled, extra_button="", template=False):
        """
        Write a checkbox to handle an empty leaf - within libyang an empty leaf is represented as
        a blank string - ''
        """
        if value:
            checked = "checked"
        else:
            checked = ""
        self.result.write(f'{self.get_indent()}<div class="form-switch fix-margin-left-switch-1">\n')
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")
        self.result.write(
            f"{self.open_indent()}<input class='fix-margin-left-switch-2 form-check-input' role='switch' type='checkbox'"
        )
        self.result.write(f" id={self.get_id()} ")
        self.result.write(f' data-yangui-keyname="{node.name()}" ')
        if not template:
            self.result.write(f"{self._get_html_attr('onChange', 'yangui_empty_leaf_change', this=True, data=True)} ")
        if value:
            self.result.write(f" data-yangui-start-val='on' ")
        else:
            self.result.write(f" data-yangui-start-val='off' ")
        self.result.write(" data-yangui-field-type='empty' ")
        self.result.write(f"{checked} {disabled}><br/>\n")
        self.result.write(f"{self.get_indent()}</div>\n")
        self.result.write(f"{self.get_indent()} {extra_button}\n")

    def _write_dropdown(self, node, value, quote, disabled, extra_button="", template=False):
        """
        Write a drop down-box for enumerations, an enumeration *should* be implemented as a label
        and a numeric value (either explicitly assigned in the yang model, or auto-assigned).
        YANGVOODOO did not implement values for enumerations.
        """
        self.result.write(f'{self.get_indent()}<div class="form-input ">\n')
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")
        if disabled:
            self.result.write(f'{self.get_indent()}<select id="{self.get_id()}" {disabled} ')
        else:
            self.result.write(
                f'{self.get_indent()}<select id="{self.get_id()}" data-live-search="true" class="selectpicker" '
            )
        self.result.write(" data-yangui-field-type='dropdown' ")
        self.result.write(f" data-yangui-start-val={quote}{value}{quote} ")
        self.result.write(f' data-yangui-keyname="{node.name()}" ')
        if not template:
            self.result.write(f"{self._get_html_attr('onChange', 'yangui_select_change', this=True, data=True)} ")

        self.result.write(f" title='select an item'>")
        self.result.write(f"{self.get_indent()} {extra_button}\n")
        for enum, _ in node.type().enums():
            selected = ""
            if enum == value:
                selected = "selected"
            self.result.write(f"{self.get_indent()}  <option {selected}>{enum}</option>\n")
        self.result.write(f"{self.get_indent()}</select>\n")
        self.result.write(f"{self.get_indent()} {extra_button} </div>\n")

    def _write_textbox(self, node, value, quote, disabled, extra_button="", template=False):
        """
        Write a text box - this is used for strings and integers.
        """
        self.result.write(f"{self.get_indent()}<div class='form-input'      >\n")
        self._write_label(node, "structure_leaflabel", linebreak=False, label_icon="fa-leaf")

        self.result.write(f"{self.get_indent()}<input type='text' id={self.get_id()} ")
        self.result.write(f"value={quote}{value}{quote} ")
        self.result.write(f"data-yangui-start-val={quote}{value}{quote} ")
        self.result.write(" data-yangui-field-type='text' ")

        if not template:
            self.result.write(f"{self._get_html_attr('onChange', 'yangui_leaf_change', this=True, data=True)} ")
            self.result.write(f"{self._get_html_attr('onKeyUp', 'yangui_leaf_change', this=True, data=True)} ")
            self.result.write(f"{self._get_html_attr('onBlur', 'yangui_leaf_blur', this=True, data=True)} {disabled} ")
        self.result.write(f' data-yangui-keyname="{node.name()}" ')

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
        self._write_button("list", on_click=self._get_html_attr("onClick", "yangui_expand_list", data=True, uuid=True))

        this_list_collapse_or_show = ""
        if not self._should_list_be_visible(node):
            this_list_collapse_or_show = "collapse"

        if not self.READONLY:
            self._write_extra_button(
                self._get_html_attr(
                    "href", "javascript:yangui_add_list_element_dialog", data=True, schema=True, uuid=True
                ),
                "plus",
            )
        self._write_label(node, "structure_listlabel", linebreak=False)

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id='count-{self.get_hybrid_id(as_uuid=True)}'>{count} "
        )
        self.result.write(f"item{self.pluralise(count)}:")
        self.result.write("</span>")
        keys = [n.name() for n in node.keys()]
        self.result.write(f"&nbsp;&nbsp;<span class='not-important-info'>key{self.pluralise(keys)}: ")
        for comma, key in self.commaify(keys):
            self.result.write(f"{comma}{key}")
        self.result.write("</span>")

        self._write_open_second_div(node, "structure_null", collapse=this_list_collapse_or_show)

    def callback_open_list_element(self, node, key_values, empty_list_element, force_open, node_id):
        self.result.write(f"{self.open_indent()}<div id='list-element-{self.get_hybrid_id()}'>\n")
        self.result.write(f"{self.get_indent()}<hr/>")
        self._write_anchor("ListElements")
        self._write_open_first_div("structure_listelement")
        self._write_button(
            "angle-right", on_click=self._get_html_attr("onClick", "yangui_list_element_expand", data=True, uuid=True)
        )

        if empty_list_element:
            self.result.write("Template for a list element")
        else:
            for comma, val in self.commaify([v for _, v in key_values]):
                self.result.write(f"{comma}<b>{val}</b>")

        if not self.READONLY:
            self._write_extra_button(
                self._get_html_attr("href", "javascript:yangui_soft_delete_list_element", data=True),
                "times",
                "danger",
                "Delete this list element all the descendant data",
            )

        this_list_element_collapse_or_show = ""
        if not self._should_listelement_be_visible(node, force_open):
            this_list_element_collapse_or_show = "collapse"

        self._write_open_second_div(
            node,
            "structure_indent",
            collapse=this_list_element_collapse_or_show,
            no_description=True,
            force_open=force_open,
        )

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
        self._write_open_second_div(node, "structure_null")

    def callback_open_case(self, node, active_case, no_active_case, node_id):
        self._disable_input_fields = True
        this_case_collapse_or_show = self.default_collapse_state
        div_disable = ""
        if not active_case and not self.READONLY:
            this_case_collapse_or_show = "collapse"
            div_disable = "yangui-disable"

        self._write_anchor("Case")
        self._write_open_first_div("structure_case")
        self._write_button("bullseye")

        if not self.READONLY:
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

        if not self.READONLY:
            self._write_extra_button(
                self._get_html_attr("href", "javascript:enable_case", hybrid=True, parent=True),
                "expand",
                "success",
                "Cases within a choice are mutually exclusive - enable this case",
                name="enable-case",
                visible=no_active_case,
            )

        self._write_label(node, "structure_caselabel", linebreak=False)
        self._write_open_second_div(node, "structure_null")
        self.result.write(
            f"\n{self.open_indent()}<div class='{div_disable} {this_case_collapse_or_show}' id='case-{self.get_hybrid_id()}'>\n"
        )

    def callback_close_case(self, node):
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
        if not self.READONLY:
            self._write_extra_button(
                self._get_html_attr("href", "javascript:add_leaflist_item", data=True, schema=True, uuid=True), "plus"
            )
        self._write_label(node, "structure_leaflistlabel", linebreak=False)

        self.result.write(
            f"&nbsp;&nbsp;<span class='not-important-info' id='count-{self.get_hybrid_id(as_uuid=True)}'>{count} item{self.pluralise(count)}:"
        )
        self.result.write("</span>")

        self._write_open_second_div(node, "structure_null")

    def callback_close_leaflist(self, node):
        self._write_close_second_div()
        self._write_close_first_div()

    def callback_write_leaflist_item(self, node, value, quote, explicit, template, node_id):
        self.result.write(f"{self.open_indent()}<div id='leaflist-item-{self.get_hybrid_id()}'>\n")
        extra_button = ""
        disabled = ""
        if not template and not self.READONLY:
            disabled = "disabled"
            extra_button = f"{self.get_indent()}&nbsp;&nbsp;<a class='btn btn-danger' {self._get_html_attr('href', 'javascript:yangui_soft_delete_leaflist_item', data=True)}><i class='fa fa-times warning'></i></a>&nbsp;\n"
        basetype = node.type().base()
        if basetype in self.LEAF_MAPPING:
            getattr(self, self.LEAF_MAPPING[basetype])(node, value, quote, disabled, extra_button=extra_button)
        else:
            self._write_textbox(node, value, quote, disabled, extra_button=extra_button, template=template)
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

    #
    #
    # Helper tools for consistently writing HTML elements of the page.
    #
    #
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
            f"<a class='btn' data-bs-toggle='collapse' role='button' id='button-{self.get_hybrid_id(as_uuid=True)}' href='#collapse-{self.get_hybrid_id(as_uuid=True)}'"
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
        self.result.write(f"&nbsp;<a class='btn btn-{theme}' {action} id='{icon}-{self.get_hybrid_id(as_uuid=True)}' ")
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

    def _write_open_second_div(
        self, node, structure_class, extra_class="", collapse="", no_description=False, force_open=False
    ):
        if self.SHOW_DESCRIPTIONS == "inline" and not no_description:
            if node.description():
                self.result.write("<blockquote>")
                for word in self.block_quotify(node.description(), 200, "", newline="<br>"):
                    self.result.write(word)
                self.result.write("</blockquote>")

        self.result.write(f"{self.open_indent()}<div class='{structure_class} {extra_class} {collapse}' ")
        if force_open:
            self.result.write("data-yangui-ever-expanded='true' ")
        self.result.write(f"data-yangui-collapse='{collapse}' id='collapse-{self.get_hybrid_id(as_uuid=True)}'>\n")
        self.open_indent()

    def _write_label(self, node, css_class, linebreak=True, label_icon=None, extra_label=""):
        if label_icon:
            self.result.write(
                f"{self.get_indent()}<i class='fa {label_icon} yang_icon' aria-hidden='true'></i>&nbsp;\n"
            )
        self.result.write(f"{self.get_indent()}<label class='{css_class}' ")

        if self.SHOW_DESCRIPTIONS == "tooltip":
            if node.description():
                self.result.write(
                    f'data-toggle="tooltip" data-placement="top" data-html="true" title="{self._get_tooltip(node.description())}"'
                )
        self.result.write(f">{node.name()}</label> {extra_label}")
        if linebreak:
            self.result.write(" <br/>")
        self.result.write("\n")

    def _write_close_second_div(self):
        self.result.write(f"{self.close_indent()}</div>\n")
        self.close_indent()

    def _write_close_first_div(self):
        self.result.write(f"{self.close_indent()}</div>\n")


if __name__ == "__main__":
    log = logging.getLogger("test")
    logging.basicConfig()
    log.setLevel(55)

    format = "xml"
    generator = HtmlFormExpander("testforms", log)
    filename = "templates/forms/default.json"
    generator.process(open(filename).read(), format=format)
    generator.dumps()
    generator.dump("examples/htmlforms/test.html")
