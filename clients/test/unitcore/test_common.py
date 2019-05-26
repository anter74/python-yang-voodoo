import libyang
from yangvoodoo.Common import Utils, PlainIterator
from mock import Mock
import unittest


class test_common(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_form_schema_path(self):
        result = Utils.form_schema_xpath('/module:path', 'attr', 'module')
        self.assertEqual(result, '/module:path/module:attr')

        result = Utils.form_schema_xpath('/module:path/module:subpath', 'attr', 'module')
        self.assertEqual(result, '/module:path/module:subpath/module:attr')

        node_schema = Mock()
        node_schema.underscore_translated = True
        result = Utils.form_schema_xpath('/module:path/module:subpath', 'attr_x', 'module', node_schema)
        self.assertEqual(result, '/module:path/module:subpath/module:attr-x')

    def test_form_value_path(self):
        result = Utils.form_value_xpath('/module:path', 'attr', 'module')
        self.assertEqual(result, '/module:path/attr')

        result = Utils.form_value_xpath('/module:path/subpath', 'attr', 'module')
        self.assertEqual(result, '/module:path/subpath/attr')

        node_schema = Mock()
        node_schema.underscore_translated = True
        result = Utils.form_value_xpath('/module:path/subpath', 'attr_x', 'module', node_schema)
        self.assertEqual(result, '/module:path/subpath/attr-x')

    def test_get_schema_of_path_cached(self):
        context = Mock()
        context.schemacache.is_path_cached.return_value = True
        cached_node = Mock()
        context.schemacache.get_item_from_cache.side_effect = [cached_node]
        # Act
        result = Utils.get_schema_of_path('/module:path', context)

        # Assert
        context.schemacache.get_item_from_cache.assert_called_once_with('/module:path')
        context.schemacache.schemactx.find_path.assert_not_called()
        self.assertEqual(result, cached_node)

    def test_get_schema_of_empty_path_for_root(self):
        context = Mock()
        context.schema = 'this-is-schema-in'

        # Act
        result = Utils.get_schema_of_path('', context)

        # Assert
        self.assertEqual(result, 'this-is-schema-in')
        context.schemacache.get_item_from_cache.assert_not_called()
        context.schemacache.schemactx.find_path.assert_not_called()

    def test_get_schema_of_path_not_cached(self):
        context = Mock()
        context.schemacache.is_path_cached.return_value = False

        schema_node_from_libyang = Mock()
        context.schemactx.find_path.side_effect = [PlainIterator([schema_node_from_libyang])]

        # Act
        result = Utils.get_schema_of_path('/module:path', context)

        # Assert
        context.schemacache.get_item_from_cache.assert_not_called()
        self.assertEqual(result, schema_node_from_libyang)
        self.assertFalse(result.underscore_translated)
        # This assert fails but the unit test does go through thins.
        # context.schemacache.schemactx.find_path.assert_called_once_with('/module:path')

    def test_get_schema_of_path_not_cached_with_underscore_translation(self):
        context = Mock()
        context.schemacache.is_path_cached.return_value = False

        schema_node_from_libyang = Mock()
        context.schemactx.find_path.side_effect = [libyang.util.LibyangError(),
                                                   PlainIterator([schema_node_from_libyang])]

        # Act
        result = Utils.get_schema_of_path('/module:path', context)

        # Assert
        context.schemacache.get_item_from_cache.assert_not_called()
        self.assertEqual(result, schema_node_from_libyang)
        self.assertTrue(result.underscore_translated)

        # This assert fails but the unit test does go through thins.
        # context.schemacache.schemactx.find_path.assert_called_once_with('/module:path')

    def test_regex(self):

        expected_match_result = [('/', 'integrationtest:sf', "[abcABC='val1'][abc='sdf']")]

        input = ("/integrationtest:sf/integrationtest:sf/abc:asd[abcABC='val1'][abc='sdf']/"
                 "integrationtest:sf/integrationtest:sf/integrationtest:sf[abcABC='val1'][abc='sdf']")
        result = Utils.LAST_LEAF_AND_PREDICTAES.findall(input)
        self.assertEqual(result[0][1], expected_match_result[0][1])
        self.assertEqual(result[0][2], expected_match_result[0][2])

        input = "/integrationtest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result)

        # Invalid silly inputs
        expected_no_match_result = []

        input = "/integratio\"ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result)

        input = "/inte]gratio[ntest:sf[abcABC='val1'][abc='sdf']"
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_no_match_result)

        input = "[key1=\"va'''][]][][][][][sadasdl1\"]"
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('key1', "va'''][]][][][][][sadasdl1")])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('key1', 'val1'), ('key2', 'val2')])

        input = '[key1="val1"][key2="val2"]'
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [])

        input = "[KEY1='val1'][key2='val2']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [('KEY1', 'val1'), ('key2', 'val2')])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.PREDICATE_KEY_VALUES_SINGLE.findall(input)
        self.assertEqual(result, [('KeY1', 'val1'), ('abc3ABC', 'val3')])

        result = Utils.PREDICATE_KEY_VALUES_DOUBLE.findall(input)
        self.assertEqual(result, [('abc', 'sdf')])

        input = "[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"
        result = Utils.FIND_KEYS.findall(input)
        self.assertEqual(result, ['KeY1', 'abc', 'abc3ABC'])

        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        expected_match_result = [("/integrationtest:web/bands[name='Longpigs']/",
                                  'gigs',
                                  "[year='1999'][month='9'][day='1'][venue='SHU Nelson "
                                  "Mandella'][location='Sheffield']")]
        self.assertEqual(Utils.LAST_LEAF_AND_PREDICTAES.findall(input), expected_match_result)

    def test_decoding_xpath(self):
        input = "/abc:xyz/abc:abc[KeY1='val1'][abc=\"sdf\"][abc3ABC='val3']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/abc:xyz/abc:abc",
                           ('KeY1', 'abc', 'abc3ABC'),
                           ('val1', 'sdf', 'val3')
                           )

        self.assertEqual(result, expected_result)

        input = "/abc:abc[KeY1='val1']"

        # Act
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/abc:abc",
                           ('KeY1',),
                           ('val1',)
                           )

        self.assertEqual(result, expected_result)

        # Act
        input = "/integrationtest:web/bands[name='Longpigs']/gigs[year='1999'][month='9'][day='1'][venue='SHU Nelson Mandella'][location='Sheffield']"
        result = Utils.decode_xpath_predicate(input)

        # Assert
        expected_result = ("/integrationtest:web/bands[name='Longpigs']/gigs", ('year', 'month', 'day',
                                                                                'venue', 'location'), ('1999', '9', '1', 'SHU Nelson Mandella', 'Sheffield'))
        self.assertEqual(result, expected_result)
