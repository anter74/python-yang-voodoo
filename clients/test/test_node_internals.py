import unittest
import os
import yangvoodoo
import subprocess
import sysrepo as sr


process = subprocess.Popen(["bash"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
(out, err) = process.communicate('sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'.encode('UTF-8'))
if err:
    raise ValueError('Unable to import data\n%s\n%s' % (our, err))


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect()
        self.root = self.subject.get_root('integrationtest')
        self.schemactx = self.root._context.schemactx

    def test_get_yang_type_simple_base_case(self):
        # Very simple leaf with base string type
        yangnode = next(self.schemactx.find_path('/integrationtest:simpleleaf'))
        result = self.root._get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.STRING, None)

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf777'))
        result = self.root._get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.STRING, None)

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf999'))
        result = self.root._get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.BOOLEAN, None)

        # More complex case where we have a leafref to a complex set of unions and we want to get an ENUm out
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf888'))
        result = self.root._get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.ENUM, 'A')

        # More complex case where we have a leafref to a complex set of unions and we want to get an STRING out
        # TODO: is it just easier to return None here?e
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf888'))
        result = self.root._get_yang_type(yangnode.type())

        self.assertEqual(result, yangvoodoo.Types.STRING, 'Aavzvs')

        # More complex case where we have a leafref to a complex set of unions and we want to get an UINT32
        # TODO: is it just easier to return None here??
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf888'))
        result = self.root._get_yang_type(yangnode.type())

        self.assertEqual(result, yangvoodoo.Types.UINT32, 234)
