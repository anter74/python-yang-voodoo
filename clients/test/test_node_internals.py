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
        with self.assertRaises(NotImplementedError) as context:
            result = self.root._get_yang_type(yangnode.type())
        self.assertEqual(str(context.exception), "Union containing unions not supported (see README.md)")

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8'))
        result = self.root._get_yang_type(yangnode.type(), 'A')
        self.assertEqual(result, yangvoodoo.Types.ENUM)

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8'))
        result = self.root._get_yang_type(yangnode.type(), 'Z')
        self.assertEqual(result, yangvoodoo.Types.STRING)

        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        yangnode = next(self.schemactx.find_path('/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf000'))
        result = self.root._get_yang_type(yangnode.type(), 2342342)
        self.assertEqual(result, yangvoodoo.Types.INT32)
