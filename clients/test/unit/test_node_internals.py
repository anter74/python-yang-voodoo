import libyang
import unittest
import yangvoodoo
from yangvoodoo.Common import IteratorToRaiseAnException, Utils
from yangvoodoo.Cache import Cache
from mock import Mock, patch


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()
        self.schemactx = self.root._context.schemactx

    def test_get_yang_node_utilise_cache(self):
        node = Mock()
        node.real_data_path = "/integrationtest:container/continer"
        node.real_schema_path = "/integrationtest:list/integrationtest:container2"
        context = Mock()
        context.schemacache = Cache()
        context.schemacache.add_entry("!/integrationtest:container/continerlist![key1='val1'][key2='val2']!/integrationtest:list/integrationtest:container2",
                                      "the-magic-cached-marker")
        # Act
        result = Utils.get_yangnode(node, context, 'list', ['key1', 'key2'], [('val1', 10), ('val2', 10)])

        self.assertEqual(result, "the-magic-cached-marker")

    @patch("yangvoodoo.Common.Utils.get_original_name")
    def test_get_yang_node_non_existing_node(self, mockGetOriginalName):
        # Build
        mockGetOriginalName.return_value = "DSFDF"

        node = Mock()
        node.real_data_path = "/integrationtest:container/continer"
        node.real_schema_path = "/integrationtest:list/integrationtest:container2"
        context = Mock()
        context.schemactx = Mock()

        context.schemactx.find_path.return_value = IteratorToRaiseAnException([], error_at=0, error_type=libyang.util.LibyangError)
        context.schemacache = Cache()
        context.module = "integrationtest"

        # Act
        with self.assertRaises(yangvoodoo.Errors.NonExistingNode) as error_context:
            Utils.get_yangnode(node, context, 'list', ['key1', 'key2'], [('val1', 10), ('val2', 10)])

        # Assert
        expected_msg = ("The path: /integrationtest:list/integrationtest:container2/integrationtest:list"
                        " does not point of a valid schema node in the yang module")

        self.assertEqual(str(error_context.exception), expected_msg)

    @patch("yangvoodoo.Common.Utils.get_original_name")
    def test_get_yang_node_existing_node(self, mockGetOriginalName):
        # Build
        mockGetOriginalName.return_value = "list-with-a-hyphen"

        node = Mock()
        node.real_data_path = "/integrationtest:container/continer"
        node.real_schema_path = "/integrationtest:list/integrationtest:container2"
        context = Mock()
        context.schemactx = Mock()

        node_schema = Mock()
        node_schema.nodetype.return_value = 4  # Leaf
        context.schemactx.find_path.return_value = IteratorToRaiseAnException([node_schema], error_at=-1)
        context.schemacache = Cache()
        context.module = "integrationtest"

        # Act
        result = Utils.get_yangnode(node, context, 'list', ['key1', 'key2'], [('val1', 10), ('val2', 10)])
        self.assertTrue(isinstance(result, yangvoodoo.Common.YangNode))
        self.assertEqual(result.libyang_node, node_schema)
        self.assertEqual(result.real_data_path, "/integrationtest:container/continer/list-with-a-hyphen[key1='val1'][key2='val2']")
        self.assertEqual(result.real_schema_path, "/integrationtest:list/integrationtest:container2/integrationtest:list-with-a-hyphen")
        self.assertEqual(list(context.schemacache.items.keys()),
                         ["!/integrationtest:container/continerlist![key1='val1'][key2='val2']!/integrationtest:list/integrationtest:container2"])

    def test_get_yang_type_simple_base_case(self):
        # Very simple leaf with base string type
        yangnode = next(self.schemactx.find_path('/integrationtest:simpleleaf'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['STRING'], None)

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf777'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['STRING'], None)

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf999'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['BOOLEAN'], None)

        # More complex case where we have a leafref to a complex set of unions and we want to get an ENUm out
        with self.assertRaises(NotImplementedError) as context:
            yangnode = next(self.schemactx.find_path(
                '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf-union-of-union'))
            result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(str(context.exception), "Union containing unions not supported (see README.md)")

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), 'A')
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['ENUM'])

        # More complex case where we have a leafref to a string
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), 'Z')
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['STRING'])

        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf000'))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), 2342342)
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['INT32'])

        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        yangnode = next(self.schemactx.find_path(
            '/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf112'))

        with self.assertRaises(yangvoodoo.Errors.ValueNotMappedToType) as context:
            yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "not-valid", "/xpath")

        # Assert
        expected_msg = "Unable to match the value 'not-valid' to a yang type for path /xpath - check the yang schema"
        self.assertEqual(str(context.exception), expected_msg)
