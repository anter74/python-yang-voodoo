import yangvoodoo
from yangvoodoo.Common import Utils, PlainIterator, PlainObject
from yangvoodoo import Errors
from mock import Mock
import unittest


class test_common(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.Common.Utils

    def test_regex(self):

        expected_match_result = [
            ("/", "integrationtest:sf", "[abcABC='val1'][abc='sdf']")
        ]

        input = (
            "/integrationtest:sf/integrationtest:sf/abc:asd[abcABC='val1'][abc='sdf']/"
            "integrationtest:sf/integrationtest:sf/integrationtest:sf[abcABC='val1'][abc='sdf']"
        )
        result = Utils.LAST_LEAF_AND_PREDICTAES.findall(input)
        self.assertEqual(result[0][1], expected_match_result[0][1])
        self.assertEqual(result[0][2], expected_match_result[0][2])

        input = "/integrationtest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(
            Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result
        )

        # Invalid silly inputs
        expected_no_match_result = []

        input = "/integratio\"ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(
            Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result
        )

        input = "/inte]gratio[ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(
            Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result
        )

        input = "[key1=\"va'''][]][][][][][sadasdl1\"]"
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [("key1", "va'''][]][][][][][sadasdl1")])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [("key1", "val1"), ("key2", "val2")])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [])

        input = "[KEY1='val1'][key2='val2']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [("KEY1", "val1"), ("key2", "val2")])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [("KeY1", "val1"), ("abc3ABC", "val3")])

        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [("abc", "sdf")])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.FIND_KEYS.findall(input)
        self.assertEqual(result, ["KeY1", "abc", "abc3ABC"])

        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        expected_match_result = [
            (
                "/integrationtest:web/bands[name='Longpigs']/",
                "gigs",
                "[year='1999'][month='9'][day='1'][venue='SHU Nelson "
                "Mandella'][location='Sheffield']",
            )
        ]
        self.assertEqual(
            Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result
        )

    def test_decoding_xpath(self):
        input = "/abc:xyz/abc:abc[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = (
            "/abc:xyz/abc:abc",
            ("KeY1", "abc", "abc3ABC"),
            ("val1", "sdf", "val3"),
        )

        self.assertEqual(result, expected_result)

        input = "/abc:abc[KeY1='val1']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/abc:abc", ("KeY1",), ("val1",))

        self.assertEqual(result, expected_result)

        # Act
        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = (
            "/integrationtest:web/bands[name='Longpigs']/gigs",
            ("year", "month", "day", "venue", "location"),
            ("1999", "9", "1", "SHU Nelson Mandella", "Sheffield"),
        )
        self.assertEqual(result, expected_result)

        with self.assertRaises(Errors.XpathDecodingError):
            Utils.decode_xpath_predicate("/xpath/but/not/quite/right")

    def test_encode_xpath_predciates(self):
        result = Utils.encode_xpath_predicates(
            "attri-bute", keys=["k1", "k2"], values=[("v1", 10), ("v2", 10)]
        )
        self.assertEqual(result, "attri-bute[k1='v1'][k2='v2']")

    def test_get_original_name(self):
        # Setup
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()

        result = Utils.get_original_name("", context, "attribute")
        self.assertEqual(result, "attribute")
        context.schemactx.find_path.assert_not_called()

    def test_get_original_name_with_underscore(self):
        # Setup
        node = Mock()
        node.name.return_value = "attribute-here"
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()
        context.schemactx.find_path.return_value = PlainIterator([node])

        result = Utils.get_original_name("", context, "attribute_here")
        self.assertEqual(result, "attribute-here")

    def test_convert_path_to_schema_path(self):
        result = Utils.convert_path_to_schema_path(
            "/path/abc/def[g='sdf']/xyz/sdf[fdsf='fg']/zzz", "module"
        )
        expected_result = (
            "/module:path/module:abc/module:def/module:xyz/module:sdf/module:zzz",
            "/module:path/module:abc/module:def/module:xyz/module:sdf",
        )
        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_schema_path("/path/abc/def[g='sdf']", "module")
        expected_result = (
            "/module:path/module:abc/module:def",
            "/module:path/module:abc",
        )
        self.assertEqual(result, expected_result)

        result = Utils.convert_path_to_schema_path("/path/abc", "module")
        expected_result = ("/module:path/module:abc", "/module:path")
        self.assertEqual(result, expected_result)

        with self.assertRaises(ValueError) as context:
            result = Utils.convert_path_to_schema_path("/path/abc/", "module")
        self.assertEqual(
            str(context.exception),
            "Path is not valid as it ends with a trailing slash. (/path/abc/)",
        )

    def test_xpath_splitter_simple(self):

        # Act
        xpath = "/bronze"
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [("/bronze", "bronze", "", "/integrationtest:bronze", "")]

        self.assertEqual(result, expected_result)

    def test_xpath_splitter_simple_deep(self):

        # Act
        xpath = "/bronze/silver/gold/platinum"
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            ("/bronze", "bronze", "", "/integrationtest:bronze", ""),
            (
                "/bronze/silver",
                "silver",
                "",
                "/integrationtest:bronze/integrationtest:silver",
                "/bronze",
            ),
            (
                "/bronze/silver/gold",
                "gold",
                "",
                "/integrationtest:bronze/integrationtest:silver/integrationtest:gold",
                "/bronze/silver",
            ),
            (
                "/bronze/silver/gold/platinum",
                "platinum",
                "",
                "/integrationtest:bronze/integrationtest:silver/integrationtest:gold/integrationtest:platinum",
                "/bronze/silver/gold",
            ),
        ]

        self.assertEqual(result, expected_result)

    def test_xpath_with_xpath_val_in_a_list(self):

        # Act
        xpath = """/integrationtest:simplelist[simplekey='/xpath/inside[dsf="sdf"]/dsfsdf']"""
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                "/simplelist[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']",
                "simplelist",
                "[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']",
                "/integrationtest:simplelist",
                "",
            )
        ]

        self.assertEqual(result, expected_result)

    def test_xpath_with_xpath_val_in_a_listv2(self):

        # Act
        xpath = """/integrationtest:simplelist[simplekey='/xpath/inside[dsf="sdf"]/dsfsdf']/sdfsdf"""
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                "/simplelist[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']",
                "simplelist",
                "[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']",
                "/integrationtest:simplelist",
                "",
            ),
            (
                "/simplelist[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']/sdfsdf",
                "sdfsdf",
                "",
                "/integrationtest:simplelist/integrationtest:sdfsdf",
                "/simplelist[simplekey='/xpath/inside[dsf=\"sdf\"]/dsfsdf']",
            ),
        ]
        self.assertEqual(result, expected_result)

    def test_xpath_with_xpath_val_in_a_listv3(self):

        # Act
        xpath = """/integrationtest:simplelist[simplekey="/xpath/inside[dsf='sdf']/dsfsdf"]/sdfsdf"""
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                "/simplelist[simplekey=\"/xpath/inside[dsf='sdf']/dsfsdf\"]",
                "simplelist",
                "[simplekey=\"/xpath/inside[dsf='sdf']/dsfsdf\"]",
                "/integrationtest:simplelist",
                "",
            ),
            (
                "/simplelist[simplekey=\"/xpath/inside[dsf='sdf']/dsfsdf\"]/sdfsdf",
                "sdfsdf",
                "",
                "/integrationtest:simplelist/integrationtest:sdfsdf",
                "/simplelist[simplekey=\"/xpath/inside[dsf='sdf']/dsfsdf\"]",
            ),
        ]
        self.assertEqual(result, expected_result)

    def test_xpath_with_xpath_val_in_a_listv4(self):

        # Act
        xpath = """/integrationtest:simplelist[simplekey="/xpath/inside[dsf='sdf']/dsfsdf"][a="b"]/sdfsdf"""
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                '/simplelist[simplekey="/xpath/inside[dsf=\'sdf\']/dsfsdf"][a="b"]',
                "simplelist",
                '[simplekey="/xpath/inside[dsf=\'sdf\']/dsfsdf"][a="b"]',
                "/integrationtest:simplelist",
                "",
            ),
            (
                '/simplelist[simplekey="/xpath/inside[dsf=\'sdf\']/dsfsdf"][a="b"]/sdfsdf',
                "sdfsdf",
                "",
                "/integrationtest:simplelist/integrationtest:sdfsdf",
                '/simplelist[simplekey="/xpath/inside[dsf=\'sdf\']/dsfsdf"][a="b"]',
            ),
        ]
        self.assertEqual(result, expected_result)

    def test_xpath_splitter_simple_list(self):

        # Act
        xpath = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']"
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                "/container-and-lists",
                "container-and-lists",
                "",
                "/integrationtest:container-and-lists",
                "",
            ),
            (
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']",
                "multi-key-list",
                "[A='aaaa'][B='bbb']",
                "/integrationtest:container-and-lists/integrationtest:multi-key-list",
                "/container-and-lists",
            ),
        ]

        self.assertEqual(result, expected_result)

    def test_xpath_splitter_simple_list_deeper(self):

        # Act
        xpath = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner/C"
        result = list(self.subject.convert_xpath_to_list_v4(xpath))

        # Assert
        expected_result = [
            (
                "/container-and-lists",
                "container-and-lists",
                "",
                "/integrationtest:container-and-lists",
                "",
            ),
            (
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']",
                "multi-key-list",
                "[A='aaaa'][B='bbb']",
                "/integrationtest:container-and-lists/integrationtest:multi-key-list",
                "/container-and-lists",
            ),
            (
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner",
                "inner",
                "",
                "/integrationtest:container-and-lists/integrationtest:multi-key-list/integrationtest:inner",
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']",
            ),
            (
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner/C",
                "C",
                "",
                "/integrationtest:container-and-lists/integrationtest:multi-key-list/integrationtest:inner/integrationtest:C",
                "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner",
            ),
        ]

        self.assertEqual(result, expected_result)

    def test_xpath_drop_predicates(self):
        # Arrange
        xpath = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner/C"

        # Act
        result = Utils.return_until_first_predicate(xpath)

        # Assert
        expected_result = "/container-and-lists/multi-key-list"
        self.assertEqual(result, expected_result)

    def test_drop_last_node(self):
        # Arrange
        xpath = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner/C"

        # Act
        result = Utils.drop_last_node(xpath)

        # Assert
        expected_result = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner"
        self.assertEqual(result, expected_result)

    def test_get_last_node_name(self):
        # Arrange
        xpath = "/container-and-lists/multi-key-list[A='aaaa'][B='bbb']/inner/C"

        # Act
        result = Utils.get_last_node_name(xpath)

        # Assert
        expected_result = "C"
        self.assertEqual(result, expected_result)

    def test_drop_module_name_from_xpath(self):
        # Act
        result = Utils.drop_module_name_from_xpath(
            "/integrationtest:sdfsdfsfdsdf/sdf/sdf/sdfsdfdsf/sdf", "integrationtest"
        )

        # Assert
        expected_result = "/sdfsdfsfdsdf/sdf/sdf/sdfsdfdsf/sdf"
        self.assertEqual(result, expected_result)

    def test_drop_module_name_from_xpath_without_prefix(self):
        # Act
        result = Utils.drop_module_name_from_xpath(
            "/sdfsdfsfdsdf/sdf/sdf/sdfsdfdsf/sdf", "integrationtest"
        )

        # Assert
        expected_result = "/sdfsdfsfdsdf/sdf/sdf/sdfsdfdsf/sdf"
        self.assertEqual(result, expected_result)

    def test_module_and_leaf(self):
        # Act
        xpath = "/integrationtest:container-and-lists/multi-key-list[A='primary-leaf'][B='secondary-leaf']/inner/level3list[level3key='key3']"
        result = Utils.return_module_name_and_leaf(xpath)

        # Assert
        expected_result = ("integrationtest", "container-and-lists")
        self.assertEqual(result, expected_result)

    def test_module_and_leaf_without_module(self):
        # Act
        xpath = "/container-and-lists/multi-key-list[A='primary-leaf'][B='secondary-leaf']/inner/level3list[level3key='key3']"
        result = Utils.return_module_name_and_leaf(xpath)

        # Assert
        expected_result = (None, "container-and-lists")
        self.assertEqual(result, expected_result)

    def test_module_and_leaf_without_module_without_suffix(self):
        # Act
        xpath = "/container-and-lists"
        result = Utils.return_module_name_and_leaf(xpath)

        # Assert
        expected_result = (None, "container-and-lists")
        self.assertEqual(result, expected_result)

    def test_module_and_leaf_with_module_without_suffix(self):
        # Act
        xpath = "/integrationtest:container-and-lists"
        result = Utils.return_module_name_and_leaf(xpath)

        # Assert
        expected_result = ("integrationtest", "container-and-lists")
        self.assertEqual(result, expected_result)

    def test_extracting_keys(self):
        # Act
        xpath = "/path/to/somewhere[k1='v1'][k2=\"v2\"]/sdf[k3='v3']/sdf"
        result = Utils.extract_all_keys(xpath)

        # Assert
        self.assertEqual(result, [("k1", "v1"), ("k2", "v2"), ("k3", "v3")])

        # Act
        xpath = "/path/to/somewhere[k1='v1'][k2=\"/this/is/xpath[inside='here']\"]/sdf[k3='v3']/sdf"
        result = Utils.extract_all_keys(xpath)

        # Assert
        self.assertEqual(
            result,
            [("k1", "v1"), ("k2", "/this/is/xpath[inside='here']"), ("k3", "v3")],
        )

    def test_convert_path_to_nodelist(self):
        # Arrange
        xpath = "/path/to/somewhere[k1='v1'][k2=\"/this/is/xpath[inside='here']\"]/sdf[k3='v3']/sdf"

        # Act
        result = Utils.convert_path_to_nodelist(xpath)

        # Assert
        expected_result = ["path", "to", "somewhere", "sdf", "sdf"]
        self.assertEqual(result, expected_result)

    def test_convert_datapath_to_schemapath_v4(self):
        # Arrange
        xpath = "/integration:path/to/somewhere[k1='v1'][k2=\"/this/is/xpath[inside='here']\"]/sdf[k3='v3']/sdf"

        # Act
        result = Utils.convert_path_to_schema_path(xpath, "integrationtest")

        # Assert
        expected_result = (
            "/integrationtest:path/integrationtest:to/integrationtest:somewhere/integrationtest:sdf/integrationtest:sdf",
            "/integrationtest:path/integrationtest:to/integrationtest:somewhere/integrationtest:sdf",
        )
        self.assertEqual(result, expected_result)
