import libyang
import unittest
import yangvoodoo
from yangvoodoo.Common import IteratorToRaiseAnException, Utils
from yangvoodoo import Errors
from yangvoodoo.Cache import Cache
from jinja2 import Template
from mock import Mock, patch


class test_node_based_access(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect("integrationtest", yang_location="yang")
        self.root = self.subject.get_node()
        self.schemactx = self.root._context.schemactx

    def test_get_yang_node_utilise_cache(self):
        node = Mock()
        node.real_data_path = "/integrationtest:container/continer"
        node.real_schema_path = "/integrationtest:list/integrationtest:container2"
        context = Mock()
        context.schemacache = Cache()
        context.schemacache.add_entry(
            "!/integrationtest:container/continerlist![key1='val1'][key2='val2']!/integrationtest:list/integrationtest:container2",
            "the-magic-cached-marker",
        )
        # Act
        result = Utils.get_yangnode(
            node, context, "list", ["key1", "key2"], [("val1", 10), ("val2", 10)]
        )

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

        context.schemactx.find_path.return_value = IteratorToRaiseAnException(
            [], error_at=0, error_type=libyang.util.LibyangError
        )
        context.schemacache = Cache()
        context.module = "integrationtest"

        # Act
        with self.assertRaises(yangvoodoo.Errors.NonExistingNode) as error_context:
            Utils.get_yangnode(
                node, context, "list", ["key1", "key2"], [("val1", 10), ("val2", 10)]
            )

        # Assert
        expected_msg = (
            "The path: /integrationtest:list/integrationtest:container2/integrationtest:list"
            " does not point of a valid schema node in the yang module"
        )

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
        context.schemactx.find_path.return_value = IteratorToRaiseAnException(
            [node_schema], error_at=-1
        )
        context.schemacache = Cache()
        context.module = "integrationtest"

        # Act
        result = Utils.get_yangnode(
            node, context, "list", ["key1", "key2"], [("val1", 10), ("val2", 10)]
        )
        self.assertTrue(isinstance(result, yangvoodoo.Common.YangNode))
        self.assertEqual(result.libyang_node, node_schema)
        self.assertEqual(
            result.real_data_path,
            "/integrationtest:container/continer/list-with-a-hyphen[key1='val1'][key2='val2']",
        )
        self.assertEqual(
            result.real_schema_path,
            "/integrationtest:list/integrationtest:container2/integrationtest:list-with-a-hyphen",
        )
        self.assertEqual(
            list(context.schemacache.items.keys()),
            [
                "!/integrationtest:container/continerlist![key1='val1'][key2='val2']!/integrationtest:list/integrationtest:container2"
            ],
        )

    def test_get_yang_type_simple_base_case(self):
        # Very simple leaf with base string type
        yangnode = next(self.schemactx.find_path("/integrationtest:simpleleaf"))
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(
            result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["STRING"], None
        )

        # More complex case where we have a leafref to a string
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf777"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(
            result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["STRING"], None
        )

        # More complex case where we have a leafref to a string
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf999"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(
            result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["BOOLEAN"], None
        )

        # More complex case where we have a leafref to a string
        with self.assertRaises(NotImplementedError) as context:
            yangnode = next(
                self.schemactx.find_path(
                    "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf5555"
                )
            )
            yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(
            str(context.exception),
            "Union containing leafrefs not supported (see README.md)",
        )

        # More complex case where we have a leafref to a complex set of unions and we want to get an ENUm out
        with self.assertRaises(NotImplementedError) as context:
            yangnode = next(
                self.schemactx.find_path(
                    "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf-union-of-union"
                )
            )
            yangvoodoo.Common.Utils.get_yang_type(yangnode.type())
        self.assertEqual(
            str(context.exception),
            "Union containing unions not supported (see README.md)",
        )

        # More complex case where we have a leafref to a string
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "A")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["ENUM"])

        # Decimal 64
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:validator/integrationtest:types/integrationtest:dec_64"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), 3.44)
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["DECIMAL64"])

        # Default as string
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:validator/integrationtest:types/integrationtest:str"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), None, "default")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["STRING"])

        # More complex case where we have a leafref to a string
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "Z")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["STRING"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf9"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "45")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT8"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf9"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "A")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["ENUM"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf9"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "34.4")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["DECIMAL64"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf9"
            )
        )
        with self.assertRaises(Errors.ValueNotMappedToTypeUnion):
            yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "B")

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf90"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "45")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT8"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf90"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "A")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["ENUM"])

        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf90"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), "34.4")
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["DECIMAL64"])

        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf000"
            )
        )
        result = yangvoodoo.Common.Utils.get_yang_type(yangnode.type(), 2342342)
        self.assertEqual(result, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT32"])

        # More complex case where we have a union of int8,int16,int32,int64, uint8,uint16,uint32,uint64
        yangnode = next(
            self.schemactx.find_path(
                "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf112"
            )
        )

        with self.assertRaises(yangvoodoo.Errors.ValueNotMappedToTypeUnion) as context:
            yangvoodoo.Common.Utils.get_yang_type(
                yangnode.type(), "not-valid", "/xpath"
            )

    def test_ipython_canary(self):
        with self.assertRaises(AttributeError):
            self.root._ipython_canary_method_should_not_exist_

        with self.assertRaises(AttributeError):
            self.root._repr_mimebundle_

    def test_name(self):
        self.assertEqual(self.root.__name__(), "VoodooNode")

    def test_find_best_number_type(self):
        result = yangvoodoo.Common.Utils._find_best_number_type([12], 40)
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT8"]

        result = yangvoodoo.Common.Utils._find_best_number_type([12, 13], 40)
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT8"]

        result = yangvoodoo.Common.Utils._find_best_number_type([13, 14], 40)
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT8"]

        result = yangvoodoo.Common.Utils._find_best_number_type([13, 14, 15], 65035)
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT16"]

        result = yangvoodoo.Common.Utils._find_best_number_type(
            [13, 14, 15, 17, 19], 4294967295
        )
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT32"]

        result = yangvoodoo.Common.Utils._find_best_number_type(
            [13, 14, 15, 19], 42949673950
        )
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["UINT64"]

        result = yangvoodoo.Common.Utils._find_best_number_type(
            [13, 14, 15, 19], -21474823648
        )
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT64"]

        result = yangvoodoo.Common.Utils._find_best_number_type([13, 14], 30000)
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT16"]

        result = yangvoodoo.Common.Utils._find_best_number_type(
            [13, 14, 15, 16, 17], 2147483640
        )
        assert result == yangvoodoo.Types.DATA_ABSTRACTION_MAPPING["INT32"]

    def test_jinja2_and_integers(self):
        # Assert
        self.root.validator.types.int_8 = 0
        template = "root.validator.types.int_8 {{ root.validator.types.int_8 }}"

        # Act
        template = Template(template)
        answer = template.render(root=self.root)

        # Assert
        expected_answer = "root.validator.types.int_8 0"

        assert answer == expected_answer
