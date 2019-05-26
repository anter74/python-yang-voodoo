from yangvoodoo.Common import Utils
import unittest


class test_common(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

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
