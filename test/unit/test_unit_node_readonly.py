import unittest
import yangvoodoo
import yangvoodoo.stublydal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_node_read_only(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stublydal.StubLyDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect("integrationtest", yang_location="yang")
        self.root = self.subject.get_node(readonly=True)

    def test_reaonly_stops_us_creating_nodes(self):
        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            self.root.simpleleaf = "ABC"

        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            self.root.simplelist.create("ABC")

        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            self.root.morecomplex.leaflists.simple.create("ABC")

        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            self.root.container1.create()

    def test_reaonly_stops_us_removing_nodes(self):
        # Prepare
        self.stub.stub_store = {
            "/integrationtest:simplelist[simplekey='ABC']": (
                1,
                "/integrationtest:simplelist",
            ),
            "/integrationtest:simplelist[simplekey='ABC']/simplekey": "ABC",
            "/integrationtest:morecomplex/leaflists/simple": ["ABC"],
        }
        self.stub.list_element_map = {
            "/integrationtest:simplelist": [
                "/integrationtest:simplelist[simplekey='ABC']"
            ]
        }
        self.stub.containers = {"/integrationtest:container1": True}

        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            del self.root.simplelist["ABC"]

        with self.assertRaises(yangvoodoo.Errors.ReadonlyError):
            del self.root.morecomplex.leaflists.simple["ABC"]
