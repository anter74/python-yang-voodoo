import unittest
import yangvoodoo


class test_stub_datastore(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.stubdal.StubDataAbstractionLayer()

    def test_create(self):
        self.subject.create("/integrationtest:simplelist[integrationtest:simplekey='sdf']",
                            keys=('simplekey',), values=('sdf',), module='integrationtest')

        expected_result = {
            '/integrationtest:simplelist[integrationtest:simplekey':
            ["/integrationtest:simplelist[integrationtest:simplekey='sdf']"],

            '/integrationtest:simplelist[integrationtest:simplekey/integrationtest:simplekey':
            'sdf'
        }

        self.assertEqual(self.subject.stub_store, expected_result)
