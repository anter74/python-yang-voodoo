import glob
import json
import os
import subprocess
import tempfile
import time

import tornado.ioloop
import tornado.web
import logging

from yangvoodoo.Describer import Yang2HTML
from examples.htmlforms.HtmlForms import HtmlFormExpander
from examples.singlepage.SinglePage import HtmlExpander
from examples.plantuml.Diagram import PlantUMLExpander
from yangvoodoo.Merger import DataTree, DataTreeChanges, base64_tostring

PORT = int(os.getenv("YANGUI_BIND_PORT", "8099"))
DEFAULT_YANG_DIR = "yang/"

PLANTUML_PATH = os.getenv("PLANTUML_PATH", "/tmp/plantuml.jar")

FORMAT = "%(asctime)-15s - %(name)-20s %(levelname)-12s  %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger("app")


def shell_command(command):
    process = subprocess.Popen("/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (output, error) = process.communicate(command.encode("utf-8"))
    return (output, error)


def get_upload_form(yang_model, uri):
    return f"""
            <h1>Upload {yang_model} JSON Data Instance </h1>
            <form action="{uri.replace('-upload','')}" method="post" enctype="multipart/form-data">
                    <input type="file" name='payload' class="custom-file-input" accept='application/json'>
                                        <button type="submit" class="btn btn-primary">Upload</button>

            </form>

                  """


def get_input_and_set_generator_options(request, generator):
    try:
        input = request.files["payload"][0]["body"].decode("utf-8")
    except:
        input = request.body.decode("utf-8")

    generator.include_as_subpage = "yangui_include_as_subpage" in input
    if "yangui_schema_filter_list" in input:
        generator.set_schema_filter_list(input["yangui_schema_filter_list"])
    if "yangui_payload" in input:
        input = input["yangui_payload"]

    return input


class AjaxHandler(tornado.web.RequestHandler):

    """
    The AJAX handler works on the basis of separate actions part of the URI
    (i.e. /api/<yangmodel>remove-leaf-list-item) - this translates to methods in this
    class.

    The payload
        {'payload':
            # This is the full payload stored by the client in their browser
            # LIBYANG_USER_PAYLOAD. This is a pure libyang JSON payload.
            {'testforms:toplevel':
                {'hello': 'world', 'simplelist': [{'simplekey': 'A'},
                {'simplekey': 'B', 'simplenonkey': 'brian-jonestown-massacre'}],
                 'multi': ['m', 'M'], 'tupperware': {}}
             },
         'changes':
            # This is a list of changes to the data-tree - the paths are based64
            # encoded to ensure safety in the HTML DOM.
            [{'action':
                 'set', 'base64_path': 'L3Rlc3Rmb3Jtczp0b3BsZWFm', 'value': 'b',
                  'update_field': 'L3Rlc3Rmb3Jtczp0b3BsZWFm', 'update_value': 'sdf'}
            ]
         }


    Args:
        input: the payload from the user


    """

    AJAX_METHODS = {
        "validate": "_validate",
        "download": "_download",
        "get-list-create-page": "_get_list_create_page",
        "get-leaf-list-create-page": "_get_leaf_list_create_page",
        "create-leaf-list": "_create_leaflist_item",
        "create-list": "_create_list_element",
        "create-container": "_create_container",
        "expand-list-element": "_expand_list_element",
        "expand-list": "_expand_list",
    }

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET")

    def _create_list_element(self, yang_model, input):
        """
        Called when creating a new list element (i.e. submit from the dialog box).

        The javascript is yangui_create_new_item
        """
        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.load(json.dumps(new_payload), 2, trusted=True)
        if instance._exists(base64_tostring(input["base64_data_path"]), predicates=input["key_values"]):
            raise ValueError(
                f"Cannot create list element because it already exists: {base64_tostring(input['base64_data_path'])} {input['key_values']}"
            )
        list_element_predicates = instance.data_tree_add_list_element(
            base64_tostring(input["base64_data_path"]), input["key_values"]
        )
        instance.subprocess_list(
            list_data_xpath=base64_tostring(input["base64_data_path"]), predicates=list_element_predicates
        )
        self.write(instance.dumps())
        self.finish()

    def _create_leaflist_item(self, yang_model, input):
        """
        Called when creating a new leaf list item (i.e. submit from the dialog box).

        The javascript is yangui_create_new_item
        """
        input["changes"].pop()
        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.load(json.dumps(new_payload), 2, trusted=True)
        log.warning(
            "Should we prevent duplicate leaf-list items - yangvoodoo probably doesn't allow duplicated even if they are permitted by libyang?"
        )
        leaf_list_values = list(instance._gets(base64_tostring(input["base64_data_path"])))
        if input["key_values"][0][1] in leaf_list_values:
            raise ValueError(
                f"Cannot create leaflist item because it already exists: {base64_tostring(input['base64_data_path'])} {input['key_values'][0][1]}"
            )
        instance.data_tree_add_list_element(base64_tostring(input["base64_data_path"]), input["key_values"])
        instance.subprocess_leaflist(
            leaflist_xpath=base64_tostring(input["base64_schema_path"]), value=input["key_values"][0][1]
        )
        self.write(instance.dumps())
        self.finish()

    def _create_container(self, yang_model, input):
        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )

        instance = HtmlFormExpander(input["yang_model"], log)
        instance.load(json.dumps(new_payload), 2, trusted=True)
        instance.data_tree_create_container(base64_tostring(input["base64_data_path"]))
        instance.subprocess_container(container_xpath=base64_tostring(input["base64_data_path"]))
        self.write(instance.dumps())
        self.finish()

    def _expand_list(self, yang_model, input):
        """
        Handle the user expanding a list (not an individual list element).
        This should update the UI with the list-elements (possibly none)
        """
        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )

        instance = HtmlFormExpander(input["yang_model"], log)
        instance.load(json.dumps(new_payload), 2, trusted=True)
        # by definition a list element must exist to be shown on the web page.
        instance.subprocess_existing_list(list_xpath=base64_tostring(input["base64_data_path"]))
        self.write(instance.dumps())
        self.finish()

    def _expand_list_element(self, yang_model, input):
        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )

        instance = HtmlFormExpander(input["yang_model"], log)
        instance.load(json.dumps(new_payload), 2, trusted=True)
        # by definition a list element must exist to be shown on the web page.
        instance.subprocess_listelement(list_xpath=base64_tostring(input["base64_data_path"]))
        self.write(instance.dumps())
        self.finish()

    def _get_list_create_page(self, yang_model, input):
        """ """
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.subprocess_create_list(base64_tostring(input["data_xpath"]), base64_tostring(input["schema_xpath"]))
        self.write(instance.dumps())
        self.finish()

    def _get_leaf_list_create_page(self, yang_model, input):
        """ """
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.subprocess_create_leaf_list(
            base64_tostring(input["data_xpath"]), base64_tostring(input["schema_xpath"])
        )
        self.write(instance.dumps())
        self.finish()

    def _validate(self, yang_model, input):
        """
        Validate a YANG payload, it can be provided either as a direct yang payload *or*
        wrapped with a list of changes.

            {
                "payload": A JSON encoded payload ( starting with {"testforms:topleaf": ....}
                "xml": Treat payload as XML instead of JSON
                "changes": [ {"action": "...", "path":"...", "value": "..."}]
            }

        Example:
            `curl -d @keep-me-safe\ \(4\).json -X POST http://127.0.0.1:8099/api/validate`

        Args:
            input: A JSON payload
        """
        result = {"status": True}

        if "payload" in input:
            changes = []
            format = "json"
            if "format" in input:
                format = input["format"]
            if "changes" in input:
                changes = list(DataTreeChanges.convert(input["changes"], log))
            session, _, _ = DataTree.process_data_tree_against_libyang(
                input["payload"], changes=changes, yang_model=yang_model, format=format, log=log
            )
        else:
            session, _, _ = DataTree.process_data_tree_against_libyang(
                input, changes=[], yang_model=yang_model, format="json", log=log
            )
        session.validate()

        self.write(json.dumps(result))
        self.finish()

    def _download(self, yang_model, input):
        """
        Args:
            input: A JSON payload
        """
        result = {"status": True}

        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], list(DataTreeChanges.convert(input["changes"], log)), yang_model=yang_model, log=log
        )
        session.validate()
        result["yangui"] = {"expanded": input["elements_expanded_by_user"]}
        result["libyang_json"] = new_payload

        self.write(json.dumps(result, indent=4))
        self.finish()

    def post(self, yang_model, action):
        """
        1: Handle either uploading a save form (i.e. the `libyang_json` has the payload) or a direct json).

        2: Handle the AJAX methods
        """
        self.set_header("Content-Type", "text/html")
        if self.request.uri.endswith("/upload"):
            input = json.loads(str(self.request.files["payload"][0]["body"].decode("utf-8")))
            # real_yang_model = DataTree.get_root_yang_model(input)
            # if real_yang_model != yang_model:
            # log.error("User is on a website for %s but the payload is for %s", yang_model, real_yang_model)
            # instance = HtmlFormExpander(real_yang_model, log)
            instance = HtmlFormExpander(yang_model, log)
            if "yangui" in input and "expanded" in input["yangui"]:
                instance.expanded_elements = input["yangui"]["expanded"]
            if "libyang_json" in input:
                instance.process(json.dumps(input["libyang_json"]), 2)
            else:
                instance.process(json.dumps(input), 2)
            self.write(instance.dumps())
            self.finish()
        else:
            input = json.loads(self.request.body.decode("utf-8"))
            print(f"AjaxHandler POST: {self.request.uri} {input}")

            if action in self.AJAX_METHODS:
                try:
                    getattr(self, self.AJAX_METHODS[action])(yang_model, input)
                    return
                except Exception as err:
                    log.exception("Error processing %s", self.request.uri)
                    self.set_status(500)
                    self.finish(str(err))
                    return
                self.set_status(500)
            self.finish(f"Not Implemented - {self.request.uri}")

    def get(self, yang_model, action):
        self.redirect(f"/web/{yang_model}")


class StaticHandler(tornado.web.RequestHandler):
    def get(self):
        if self.request.uri in ("/static/css/yangui.css", "/static/js/yangui.js", "/static/js/your-actions.js"):
            with open(f"examples/htmlforms/{self.request.uri}") as fh:
                self.write(fh.read())
        else:
            self.clear()
            self.set_status(400)
            self.finish("<html><body>Forbidden - not a static resource we want to serve.</body></html>")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(418)
        self.write(
            """Add a landing page here instead of claiming to be a teapot

<pre>
GET /web/{yangmodel}             : Returns an empty form for the given yang model

GET /pyang/{yangmodel}           : Returns a pyang tree of the yang model (schema only)

GET /text/{yangmodel}            : Returns a plain text representation of the given yang model (schema only)
POST /text/{yangmodel}           : Returns a plain text representation of the given yang model and data tree

GET /html/{yangmodel}            : Returns a html (readonly) representation of the given yang model (schema only)
POST /html/{yangmodel}           : Returns a html (readonly) representation of the given yang model and data tree

GET /plantuml/{yangmodel}        : Returns a PlantUML JSON representation of the yang model (schema only)
POST /plantuml/{yangmodel}       : Returns a PlantUML JSON representation of the yang model and data tree
"""
        )
        if os.path.exists(PLANTUML_PATH):
            self.write(
                """
GET /plantuml-png/{yangmodel}    : Returns a PlantUML PNG image representation of the yang model (schema only)
POST /plantuml-png/{yangmodel}   : Returns a PlantUML PNG image representation of the yang model and data tree

GET /plantuml-svg/{yangmodel}    : Returns a PlantUML SVG image representation of the yang model (schema only)
POST /plantuml-svg/{yangmodel}   : Returns a PlantUML SVG image representation of the yang model and data tree

POST /api/{yangmodel}/validate   : Validate the payload in the JSON POSTED.
POST /api/{yangmodel}/upload     : Returns a form for the given yang model with the JSON POSTED data loaded

</pre>
<hr/>
    """
            )
        if os.path.exists(DEFAULT_YANG_DIR):
            for yang_file in glob.glob(f"{DEFAULT_YANG_DIR}/*.yang"):
                y = yang_file.split(".yang")[0].split("/")[-1]
                self.write(
                    f"<li> {y} <a href='/web/{y}'>web form</a> <a href='/text/{y}'>text</a> <a href='/html/{y}'>html</a>(<a href='/html-upload/{y}'>upload</a>) <a href='/plantuml/{y}'>plantuml-json(<a href='/plantuml-upload/{y}'>upload</a>)</a>"
                )
                if os.path.exists(PLANTUML_PATH):
                    self.write(
                        f" <a href='/plantuml-png/{y}'>plantuml-png((<a href='/plantuml-png-upload/{y}'>upload</a>))</a>"
                    )
                    self.write(
                        f" <a href='/plantuml-png/{y}'>plantuml-svg((<a href='/plantuml-svg-upload/{y}'>upload</a>))</a>"
                    )
                self.write(f" <a href='/pyang/{y}'>pyang tree</a>")

        self.finish()


class WebHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def get(self, yang_model):
        instance = HtmlFormExpander(yang_model, log)
        instance.process()
        self.write(instance.dumps())


class PyangHandler(tornado.web.RequestHandler):
    def get(self, yang_model):
        self.set_header("Content-Type", "text/plain")
        instance = HtmlFormExpander(yang_model, log)
        self.write(str(instance.ctx.get_module(yang_model)))


class TextHandler(tornado.web.RequestHandler):
    def get(self, formatter, yang_model):
        if formatter.endswith("upload"):
            self.set_header("Content-Type", "text/html")
            self.write(
                f"""
                <h1>Upload {yang_model} JSON Data Instance </h1>
                <form action="{self.request.uri.replace('-upload','')}" method="post" enctype="multipart/form-data">
                        <input type="file" name='payload' class="custom-file-input" accept='application/json'>
                                            <button type="submit" class="btn btn-primary">Upload</button>

                </form>

                      """
            )
        else:

            if formatter.startswith("html"):
                self.set_header("Content-Type", "text/html")
            else:
                self.set_header("Content-Type", "text/plain")
            try:
                if formatter.startswith("html"):
                    generator = HtmlExpander(yang_model, log)
                else:
                    generator = Yang2HTML(yang_model, log)
                    generator.options = Yang2HTML.Options()
                    generator.display = Yang2HTML.Display
                result = generator.process()
                self.write(generator.dumps())
            except Exception as err:
                self.set_status(500)
                self.write(str(err))
        self.finish()

    def post(self, formatter, yang_model):
        if formatter.endswith("upload"):
            self.set_header("Content-Type", "text/html")
            self.write(get_upload(yang_modle, self.request.uri))

        else:
            if formatter.startswith("html"):
                self.set_header("Content-Type", "text/html")
            else:
                self.set_header("Content-Type", "text/plain")

            try:
                if formatter.startswith("html"):
                    generator = HtmlExpander(yang_model, log)
                else:
                    generator = Yang2HTML(yang_model, log)
                    generator.options = Yang2HTML.Options()
                    generator.display = Yang2HTML.Display
                payload = get_input_and_set_generator_options(self.request, generator)
                result = generator.process(payload, 2)
                self.write(generator.dumps())
            except Exception as err:
                self.set_status(500)
                self.write(str(err))
            self.finish()


class PlantUmlHandler(tornado.web.RequestHandler):
    def _provide_result(self, result, type):
        if type == "":
            self.write(result.dumps())
            return
        if type in ("-svg", "-png"):
            temp_dir = tempfile.TemporaryDirectory(prefix="yangui", suffix="plantuml", ignore_cleanup_errors=True)
            log.info("Using Plantuml inside of %s", temp_dir)
            with open(f"{temp_dir.name}/uml.txt", "w") as fh:
                fh.write(result.dumps())

            cmd = f"java {os.getenv('PLANTUML_JAVA_OPTS','')} -jar {PLANTUML_PATH} -t{type[1:]} -v {temp_dir.name}/uml.txt"
            log.info("Running plantuml... %s", cmd)
            shell_command(cmd)

            with open(f"{temp_dir.name}/uml.{type[1:]}", "rb") as fh:
                self.write(fh.read())

    def get(self, type, upload, yang_model):
        if upload:
            self.set_header("Content-Type", "text/html")
            self.write(get_upload_form(yang_model, self.request.uri))
        else:
            if type == "":
                self.set_header("Content-Type", "application/json")
            if type in ("-png", "-svg"):
                if not os.path.exists(PLANTUML_PATH):
                    self.write(f"Could not find plantuml at: {PLANTUML_PATH}")
                    self.set_status(500)
                    return
                if type == "-png":
                    self.set_header("Content-Type", "image/png")
                if type == "-svg":
                    self.set_header("Content-Type", "image/svg+xml")

            try:
                generator = PlantUMLExpander(yang_model, log)
                result = generator.process()
                self._provide_result(generator, type)
            except Exception as err:
                self.set_status(500)
                self.write(str(err))
        self.finish()

    def post(self, type, upload, yang_model):
        if type == "-png":
            self.set_header("Content-Type", "image/png")
        elif type == "-svg":
            self.set_header("Content-Type", "image/svg+xml")
        else:
            self.set_header("Content-Type", "text/html")
        try:
            generator = PlantUMLExpander(yang_model, log)
            payload = get_input_and_set_generator_options(self.request, generator)
            result = generator.process(payload, 2)
            self._provide_result(generator, type)
        except Exception as err:
            log.exception("Error building plantuml")
            self.set_status(500)
            self.write(str(err))
        self.finish()


def make_app():
    return tornado.web.Application(
        [
            (r"/api/(.+)/(.+)", AjaxHandler),
            (r"/static/.*", StaticHandler),
            (r"/plantuml(|-png|-svg)(|-upload)/(.*)", PlantUmlHandler),
            (r"/(text|html|text-upload|html-upload)/(.*)", TextHandler),
            (r"/web/(.*)", WebHandler),
            (r"/pyang/(.*)", PyangHandler),
            (r"/.*", MainHandler),
        ],
        debug=True,
    )


def do():
    app = make_app()
    app.listen(PORT)
    log.info("Starting example server: %s", PORT)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    do()
