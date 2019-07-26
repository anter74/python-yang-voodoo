import libyang
import unittest
import yangvoodoo
import yangvoodoo.stubdal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_datastore_via_node(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def _get_type(self, xpath, value):
        libyang_node = next((self.root._context.schemactx.find_path("/integrationtest:validator/integrationtest:types/integrationtest:" + xpath)))
        # print(xpath, libyang_node.type().base())
        return libyang_node.type().base()

    def test_types_from_node(self):
        self.assertEqual(self._get_type("u_int_8", 0), libyang.schema.Type.UINT8)
        self.assertEqual(self._get_type("u_int_8", 255), libyang.schema.Type.UINT8)
        self.assertEqual(self._get_type("u_int_16", 65535), libyang.schema.Type.UINT16)
        self.assertEqual(self._get_type("u_int_32", 4294967295), libyang.schema.Type.UINT32)
        self.assertEqual(self._get_type("u_int_64", 18446744073709551615), libyang.schema.Type.UINT64)
        self.assertEqual(self._get_type("int_8", 0), libyang.schema.Type.INT8)
        self.assertEqual(self._get_type("int_8", 2128), libyang.schema.Type.INT8)
        self.assertEqual(self._get_type("int_16", -32768), libyang.schema.Type.INT16)
        self.assertEqual(self._get_type("int_16", 32767), libyang.schema.Type.INT16)
        self.assertEqual(self._get_type("int_32", -2147483648), libyang.schema.Type.INT32)
        self.assertEqual(self._get_type("int_32", 2147483647), libyang.schema.Type.INT32)
        self.assertEqual(self._get_type("int_64", - 9223372036854775808), libyang.schema.Type.INT64)
        self.assertEqual(self._get_type("int_64",  9223372036854775807), libyang.schema.Type.INT64)
        self.assertEqual(self._get_type("str", "A"), libyang.schema.Type.STRING)
        self.assertEqual(self._get_type("bool", True), libyang.schema.Type.BOOL)
        self.assertEqual(self._get_type("void", None), libyang.schema.Type.EMPTY)
        self.assertEqual(self._get_type("enumeratio", "A"), libyang.schema.Type.ENUM)
        self.assertEqual(self._get_type("dec_64", 234.234234), libyang.schema.Type.DEC64)
