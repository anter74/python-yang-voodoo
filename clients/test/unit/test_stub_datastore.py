import unittest
import yangvoodoo


class test_stub_datastore(unittest.TestCase):

    maxDiff = 50000

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.stubdal.StubDataAbstractionLayer()

    def test_create(self):
        self.subject.create("/integrationtest:simplelist[simplekey='sdf']",
                            keys=('simplekey',), values=(('sdf', 10),), module='integrationtest')

        expected_result = {
            '/integrationtest:simplelist':
                ["/integrationtest:simplelist[simplekey='sdf']"],

            "/integrationtest:simplelist[simplekey='sdf']":
                (1, '/integrationtest:simplelist'),
            "/integrationtest:simplelist[simplekey='sdf']/integrationtest:simplekey":
            'sdf'
        }

        self.assertEqual(self.subject.stub_store, expected_result)
