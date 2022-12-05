import json
import time


import tornado.ioloop
import tornado.web
import logging

from examples.htmlforms.HtmlForms import HtmlFormExpander
from yangvoodoo.Merger import DataTree, DataTreeChanges, base64_tostring

PORT = 8099

FORMAT = "%(asctime)-15s - %(name)-20s %(levelname)-12s  %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger("app")


class AjaxHandler(tornado.web.RequestHandler):

    """
    The AJAX handler works on the basis of separate actions part of the URI
    (i.e. /ajax/remove-leaf-list-item) - this translates to methods in this
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
        "/ajax/validate": "_validate",
        "/ajax/download": "_download",
        "/ajax/get-list-create-page": "_get_list_create_page",
        "/ajax/get-leaf-list-create-page": "_get_leaf_list_create_page",
        "/ajax/create-leaf-list": "_create_leaflist_item",
        "/ajax/create-list": "_create_list_element",
    }

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def _create_list_element(self, input):
        instance = HtmlFormExpander(input["yang_model"], log)
        list_element_predicates = instance.data_tree_add_list_element(
            base64_tostring(input["base64_data_path"]), input["key_values"]
        )
        instance.subprocess_list(
            list_data_xpath=base64_tostring(input["base64_data_path"]), predicates=list_element_predicates
        )
        self.write(instance.dumps())
        self.finish()

    def _create_leaflist_item(self, input):
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.data_tree_add_list_element(base64_tostring(input["base64_data_path"]), input["key_values"])
        instance.subprocess_leaflist(
            leaflist_xpath=base64_tostring(input["base64_schema_path"]), value=input["key_values"][0][1]
        )
        self.write(instance.dumps())
        self.finish()

    def _get_list_create_page(self, input):
        """ """
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.subprocess_create_list(base64_tostring(input["data_xpath"]), base64_tostring(input["schema_xpath"]))
        self.write(instance.dumps())
        self.finish()

    def _get_leaf_list_create_page(self, input):
        """ """
        instance = HtmlFormExpander(input["yang_model"], log)
        instance.subprocess_create_leaf_list(
            base64_tostring(input["data_xpath"]), base64_tostring(input["schema_xpath"])
        )
        self.write(instance.dumps())
        self.finish()

    def _validate(self, input):
        """
        Validate a YANG payload, it can be provided either as a direct yang payload *or*
        wrapped with a list of changes.

            {
                "payload": A JSON encoded payload ( starting with {"testforms:topleaf": ....}
                "xml": Treat payload as XML instead of JSON
                "changes": [ {"action": "...", "path":"...", "value": "..."}]
            }

        Example:
            `curl -d @keep-me-safe\ \(4\).json -X POST http://127.0.0.1:8099/ajax/validate`

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
                changes = DataTreeChanges.convert(input["changes"])
            session, _, _ = DataTree.process_data_tree_against_libyang(
                input["payload"], changes=changes, format=format, log=log
            )
        else:
            session, _, _ = DataTree.process_data_tree_against_libyang(input, changes=[], format="json", log=log)
        session.validate()

        self.write(json.dumps(result))
        self.finish()

    def _download(self, input):
        """
        Args:
            input: A JSON payload
        """
        result = {"status": True}

        session, new_payload, _ = DataTree.process_data_tree_against_libyang(
            input["payload"], DataTreeChanges.convert(input["changes"]), log=log
        )
        session.validate()
        result["new_payload"] = new_payload

        self.write(json.dumps(result, indent=4))
        self.finish()

    def post(self):
        self.set_header("Content-Type", "text/html")

        time.sleep(0.2)
        input = json.loads(self.request.body.decode("utf-8"))
        print(f"AjaxHandler POST: {self.request.uri} {input}")

        if self.request.uri in self.AJAX_METHODS:
            try:
                getattr(self, self.AJAX_METHODS[self.request.uri])(input)
                return
            except Exception as err:
                log.exception("Error processing %s", self.request.uri)
                self.set_status(500)
                self.finish(str(err))
                return
        # if self.request.uri == "/ajax/add-leaf-list-element-form":
        #     instance._get_keys_for_list_element(base64_tostring(input["schema_xpath_b64"]))
        #     self.write("<p>fs</p>")
        #     return

        self.set_status(500)
        self.finish(f"Not Implemented - {self.request.uri}")


class StaticHandler(tornado.web.RequestHandler):
    def get(self):
        if self.request.uri in ("/static/css/yangui.css", "/static/js/yangui.js"):
            with open(f"examples/htmlforms/{self.request.uri}") as fh:
                self.write(fh.read())
        else:
            self.clear()
            self.set_status(400)
            self.finish("<html><body>Forbidden - not a static resource we want to serve.</body></html>")


class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def get(self):
        instance = HtmlFormExpander("testforms", log)
        with open("templates/forms/simplelist4.xml") as start_data_payload_fh:
            instance.process(start_data_payload_fh.read())
        self.write(instance.dumps())

    def post(self):
        input = json.loads(str(self.request.files["payload"][0]["body"].decode("utf-8")))

        yang_model = DataTree.get_root_yang_model(input)
        instance = HtmlFormExpander(yang_model, log)
        instance.process(json.dumps(input), 2)
        self.write(instance.dumps())
        self.finish()


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/ajax/.*", AjaxHandler),
            (r"/static/.*", StaticHandler),
        ]
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(PORT)
    tornado.ioloop.IOLoop.current().start()
