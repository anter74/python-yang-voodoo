import unittest
import yangvoodoo
import yangvoodoo.stublydal


class test_advanced_merge(unittest.TestCase):

    BASE_TEMPLATE = """
    <container-and-lists xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
      <multi-key-list>
        <A>a</A>
        <B>b</B>
        <inner>
          <C>c</C>
          <level3list>
            <level3key>c-level3-list</level3key>
            <level3-nonkey>nonkey</level3-nonkey>
          </level3list>
        </inner>
      </multi-key-list>
      <multi-key-list>
        <A>aaaa</A>
        <B>bbbb</B>
        <inner>
          <C>cccc</C>
          <level3list>
            <level3key>ccc-level3-lsit</level3key>
            <level3-nonkey>nonkey2</level3-nonkey>
          </level3list>
          <level3list>
            <level3key>ccc-level3-lsit-number2</level3key>
          </level3list>
          <level3list>
            <level3key>ccc-level3-lsit-number3</level3key>
            <level3-nonkey>nonkey3</level3-nonkey>
          </level3list>
        </inner>
      </multi-key-list>
    </container-and-lists>"""

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest', yang_location='yang')
        self.subject.add_module('ietf-netconf')
        self.root = self.subject.get_node(readonly=True)
        self.subject.loads(self.BASE_TEMPLATE)

    def test_advanced_merge(self):
        # Act

        template = """
        <container-and-lists xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">

          <multi-key-list nc:operation="replace">
            <A>zzzzz</A>
            <B>yyyyy</B>
            <inner>
              <C>cccc</C>
              <level3list>
                <level3key>ccc-level3-lsit</level3key>
                <level3-nonkey>nonkey2</level3-nonkey>
              </level3list>
            </inner>
          </multi-key-list>
        </container-and-lists>"""
        self.assertEqual(len(self.root.container_and_lists.multi_key_list), 2)

        # Act
        self.subject.advanced_merges(template)

        # Assert
        result = """<container-and-lists xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
          <multi-key-list>
            <A>zzzzz</A>
            <B>yyyyy</B>
            <inner>
              <C>cccc</C>
              <level3list>
                <level3key>ccc-level3-lsit</level3key>
                <level3-nonkey>nonkey2</level3-nonkey>
              </level3list>
            </inner>
          </multi-key-list>
        </container-and-lists>"""

        self.assertEqual(len(self.root.container_and_lists.multi_key_list), 1)
