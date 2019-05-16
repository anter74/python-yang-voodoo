import unittest
import yangvoodoo
from mock import Mock


class test_xml_to_xpath(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.session = yangvoodoo.DataAccess()
        self.session.connect("integrationtest")
        self.root = self.session.get_root()
        self.subject = yangvoodoo.TemplateNinja.TemplateNinja()

        self.schemactx = self.root._context.schemactx

    def test_look_ahead_for_list_keys(self):
        # Build
        list_predicates = {}

        key1 = Mock()
        key1.name.return_value = 'key1'
        node_schema = dummy_iterator([key1])

        node = Mock()
        node.tag = 'key1'
        node.text = 'value-for-key1'

        xmldoc_iterator = dummy_iterator([node])

        module = 'integrationtest'
        value_path = '/integrationtest:simplelist'

        # Action
        self.subject._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, value_path, list_predicates)

        # Assert
        expected_result = {'/integrationtest:simplelist': "[integrationtest:key1='value-for-key1']"}
        self.assertEqual(list_predicates, expected_result)

    def test_look_ahead_for_list_keys_when_keys_are_missing(self):
        # Build
        list_predicates = {}

        key1 = Mock()
        key1.name.return_value = 'key1'
        node_schema = dummy_iterator([key1])

        xmldoc_iterator = dummy_iterator([])

        module = 'integrationtest'
        value_path = '/integrationtest:simplelist'

        # Action
        with self.assertRaises(yangvoodoo.Errors.XmlTemplateParsingBadKeys) as context:
            self.subject._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, value_path, list_predicates)

        # Assert
        self.assertEqual(str(context.exception), "Expecting to find list key 'key1' but found 'nothing' instead")

    def test_look_ahead_for_list_keys_when_keys_are_in_the_wrong_order(self):
        # Build
        list_predicates = {}

        key1 = Mock()
        key1.name.return_value = 'key1'
        key2 = Mock()
        key2.name.return_value = 'key2'
        node_schema = dummy_iterator([key1, key2])

        node1 = Mock()
        node1.tag = 'key1'
        node1.text = 'value-for-key1'

        node2 = Mock()
        node2.tag = 'key2'
        node2.text = 'value-for-key2'
        xmldoc_iterator = dummy_iterator([node2, node1])

        module = 'integrationtest'
        value_path = '/integrationtest:simplelist'

        # Action
        with self.assertRaises(yangvoodoo.Errors.XmlTemplateParsingBadKeys) as context:
            self.subject._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, value_path, list_predicates)

        # Assert
        self.assertEqual(str(context.exception), "Expecting to find list key 'key1' but found 'key2' instead")

    def test_look_ahead_for_list_keys_when_keys_are_in_the_right_order(self):
        # Build
        list_predicates = {}

        key1 = Mock()
        key1.name.return_value = 'key1'
        key2 = Mock()
        key2.name.return_value = 'key2'
        node_schema = dummy_iterator([key1, key2])

        node1 = Mock()
        node1.tag = 'key1'
        node1.text = 'value-for-key1'

        node2 = Mock()
        node2.tag = 'key2'
        node2.text = 'value-for-key2'

        node3 = Mock()
        node3.tag = 'nonkey'
        node3.text = 'value-for-nonkey'
        xmldoc_iterator = dummy_iterator([node1, node2, node3])

        module = 'integrationtest'
        value_path = '/integrationtest:simplelist'

        # Action
        self.subject._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, value_path, list_predicates)

        # Assert
        expected_result = {
            '/integrationtest:simplelist':
            "[integrationtest:key1='value-for-key1'][integrationtest:key2='value-for-key2']"
        }

        self.assertDictEqual(list_predicates, expected_result)

    def test_find_predicate_match(self):
        # Build
        path = "/integrationtest:simplelist"
        list_predicates = {
            '/integrationtest:simplelist':
            "[integrationtest:key1='value-for-key1'][integrationtest:key2='value-for-key2']"
        }

        # Act
        result = self.subject._find_predicate_match(list_predicates, path)

        # Assert
        expected_result = ("/integrationtest:simplelist"
                           "[integrationtest:key1='value-for-key1'][integrationtest:key2='value-for-key2']")
        self.assertEqual(result, expected_result
                         )

    def test_find_predicate_match_list_within_a_list(self):
        # Build
        path = "/integrationtest:container-and-lists/integrationtest:multi-key-list/integrationtest:level2list"
        list_predicates = {
            '/integrationtest:container-and-lists/integrationtest:multi-key-list':
            "[integrationtest:A='a'][integrationtest:B='b']",

            "/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
            "[integrationtest:B='b']/integrationtest:level2list":
            "[integrationtest:level2key='22222']"
        }

        # Act
        result = self.subject._find_predicate_match(list_predicates, path)
        # Assert
        expected_result = ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
                           "[integrationtest:B='b']/integrationtest:level2list[integrationtest:level2key='22222']")
        self.assertEqual(result, expected_result)

    def test_from_template(self):
        # Build

        template = """<integrationtest>
          <container-and-lists>
            <numberkey-list>
              <numberkey>5</numberkey>
              <description>FIVE</description>
            </numberkey-list>
            <multi-key-list>
              <A>a</A>
              <B>b</B>
              <inner>
                <level3list>
                  <level3key>33333</level3key>
                  <level3-nonkey>three</level3-nonkey>
                </level3list>
              </inner>
              <level2list>
                <level2key>22222</level2key>
              </level2list>
            </multi-key-list>
          </container-and-lists>
        </integrationtest>
        """
        # Act
        results = self.subject._convert_xml_to_xpaths(self.root, template)
        expected_answer = {
            ("/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']"):
            (None, 2),
            ("/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']"
             "/integrationtest:description"): ('FIVE', 18),
            ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
             "[integrationtest:B='b']"): (None, 2),
            ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
             "[integrationtest:B='b']/integrationtest:inner/integrationtest:level3list[integrationtest:"
             "level3key='33333']"): (None, 2),
            ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
             "[integrationtest:B='b']/integrationtest:inner/integrationtest:level3list[integrationtest:"
             "level3key='33333']/integrationtest:level3-nonkey"): ('three', 18),
            ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
             "[integrationtest:B='b']/integrationtest:level2list[integrationtest:level2key='22222']"): (None, 2)
        }
        self.assertEqual(results, expected_answer)

    def test_from_template_with_only_keys(self):
        # Build

        template = """<integrationtest>
          <container-and-lists>
            <numberkey-list>
              <numberkey>5</numberkey>
            </numberkey-list>
            <multi-key-list>
              <A>a</A>
              <B>b</B>
            </multi-key-list>
          </container-and-lists>
        </integrationtest>
        """
        # Act
        results = self.subject._convert_xml_to_xpaths(self.root, template)
        expected_answer = {
            ("/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']"):
            (None, 2),
            ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
             "[integrationtest:B='b']"): (None, 2),
        }
        self.assertEqual(results, expected_answer)
    #
    # def test_from_template_with_only_two_list_items(self):
    #     # Build
    #
    #     template = """<integrationtest>
    #       <container-and-lists>
    #         <numberkey-list>
    #           <numberkey>5</numberkey>
    #         </numberkey-list>
    #         <numberkey-list>
    #           <numberkey>6</numberkey>
    #         </numberkey-list>
    #       </container-and-lists>
    #     </integrationtest>
    #     """
    #     # Act
    #     results = self.subject._convert_xml_to_xpaths(self.root, template)
    #     expected_answer = {
    #         ("/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']"):
    #         (None, 2),
    #         ("/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='6']"):
    #         (None, 2),
    #     }
    #     self.assertEqual(results, expected_answer)

    def test_from_template_with_jinja2_processing(self):
        # Build
        self.root.simpleleaf = 'GOODBYE'

        # Act
        self.root.from_template('test/unit/test.xml')

        # Assert
        self.assertEqual(self.root.simpleleaf, 'HELLO')
        self.assertEqual(self.root.default, 'GOODBYE')


class dummy_iterator:

    def __init__(self, list_items):
        self.list_items = list_items
        self.i = 0

    def keys(self):
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= len(self.list_items):
            raise StopIteration()
        self.i = self.i + 1
        return self.list_items[self.i-1]
