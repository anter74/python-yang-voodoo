import yangvoodoo.stubdal
import unittest
from mock import Mock, call


class test_xml_to_xpath(unittest.TestCase):

    maxDiff = 23948230

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.session.connect("integrationtest")
        self.root = self.session.get_node()
        self.subject = yangvoodoo.TemplateNinja.TemplateNinja()

        self.schemactx = self.root._context.schemactx
        self.module = self.root._context.module

    def test_from_template_A(self):
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
        self.subject._import_xml_to_datastore(self.module, self.schemactx, template, self.stub)

        # assert
        self.assertEqual(len(self.root.container_and_lists.multi_key_list['a', 'b'].inner.level3list), 1)
        self.assertEqual(self.root.container_and_lists.multi_key_list['a', 'b'].inner.level3list['33333'].level3key, '33333')
        self.assertEqual(self.root.container_and_lists.multi_key_list['a', 'b'].level2list['22222'].level2key, '22222')
        self.assertFalse('2' in self.root.container_and_lists.multi_key_list.level2list)

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

        dal = Mock()

        # Act
        self.subject._import_xml_to_datastore(self.module, self.schemactx, template, dal)

        # Assert
        self.assertEqual(dal.create.call_count, 2)
        dal.create.assert_has_calls([
            call(
                "/integrationtest:container-and-lists/integrationtest:numberkey-list[numberkey='5']", ['numberkey'], [(5, 19)], 'integrationtest'),
            call("/integrationtest:container-and-lists/integrationtest:multi-key-list[A='a'][B='b']", [
                 'A', 'B'], [('a', 18), ('b', 18)], 'integrationtest')
        ])

    def test_from_template_with_leaflists(self):
        # Build

        template = """<integrationtest>
          <morecomplex>
            <leaflists>
                <simple>A</simple>
                <simple>Z</simple>
                <simple>M</simple>
            </leaflists>
        </morecomplex>
        </integrationtest>
        """

        dal = Mock()

        # Act
        self.subject._import_xml_to_datastore(self.module, self.schemactx, template, dal)

        # Assert
        self.assertEqual(dal.create.call_count, 0)
        self.assertEqual(dal.add.call_count, 3)
        dal.add.assert_has_calls([
            call("/integrationtest:morecomplex/integrationtest:leaflists/integrationtest:simple", 'A', 18),
            call("/integrationtest:morecomplex/integrationtest:leaflists/integrationtest:simple", 'Z', 18),
            call("/integrationtest:morecomplex/integrationtest:leaflists/integrationtest:simple", 'M', 18)
        ])

    def test_from_template_with_leaflists_with_stub_dal(self):
        # Build

        template = """<integrationtest>
          <morecomplex>
            <leaflists>
                <simple>A</simple>
                <simple>Z</simple>
                <simple>M</simple>
            </leaflists>
        </morecomplex>
        </integrationtest>
        """

        # Act
        self.subject._import_xml_to_datastore(self.module, self.schemactx, template, self.stub)

        # Assert
        expected_items = ['A', 'Z', 'M']
        self.assertEqual(len(self.root.morecomplex.leaflists.simple), 3)
        for item in self.root.morecomplex.leaflists.simple:

            self.assertEqual(expected_items[0], item)
            expected_items.pop(0)

    def test_from_template_with_list_number(self):
        # Build

        template = """<integrationtest>
          <container-and-lists>
            <numberkey-list>
              <numberkey>5</numberkey>
            </numberkey-list>
            <numberkey-list>
              <numberkey>6</numberkey>
              <description>SIX</description>
            </numberkey-list>
            <numberkey-list>
              <numberkey>7</numberkey>
              <description>SEVEN</description>
            </numberkey-list>
          </container-and-lists>
        </integrationtest>
        """
        # Act
        self.subject._import_xml_to_datastore(self.module, self.schemactx, template, self.stub)

        self.assertEqual(len(self.root.container_and_lists.numberkey_list), 3)

        self.assertEqual(self.root.container_and_lists.numberkey_list[5].numberkey, 5)
        self.assertEqual(self.root.container_and_lists.numberkey_list[6].numberkey, 6)
        self.assertEqual(self.root.container_and_lists.numberkey_list[7].numberkey, 7)
        self.assertEqual(['description', 'numberkey'], list(dir(self.root.container_and_lists.numberkey_list[6])))
        self.assertEqual(("/integrationtest:container-and-lists/integrationtest:numberkey-list"
                          "[numberkey='6']"),
                         self.root.container_and_lists.numberkey_list[6]._path)

        self.assertEqual(self.root.container_and_lists.numberkey_list[6].description, 'SIX')
        self.assertEqual(self.root.container_and_lists.numberkey_list[7].description, 'SEVEN')

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
