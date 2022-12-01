import base64
import json
import logging
import tornado.ioloop
import tornado.web
from examples.htmlforms.HtmlForms import HtmlFormExpander

PORT = 8099


log = logging.getLogger("tornado.application")


def base64_tostring(input_string):
    return base64.b64decode(input_string.encode("utf-8")).decode("utf-8")


class AjaxHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def post(self):
        self.set_header("Content-Type", "text/html")
        import time

        time.sleep(0.2)
        input = json.loads(self.request.body.decode("utf-8"))
        print(f"AjaxHandler POST: {input}")
        if not hasattr(self, "user_instance"):
            self.set_status(500)
            self.finish("No data instance")
            return

        if self.request.uri == "/ajax/add-leaf-list-element-form":
            self.user_instance._get_keys_for_list_element(base64_tostring(input["schema_xpath_b64"]))

            self.write("<p>fs</p>")
            return

        self.set_status(500)
        self.finish(f"Not Implemented - {self.request.uri} - {base64_tostring(input['data_xpath_b64'])}")


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
        self.user_instance = HtmlFormExpander("testforms", log)
        with open("templates/forms/simplelist4.xml") as start_data_payload_fh:
            self.user_instance.process(start_data_payload_fh.read())
        self.write(self.user_instance.dumps())


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
