import unittest
import yangvoodoo
import yangvoodoo.stublydal
from libyang.diff import Differ

"""
This tests the integration of libyang based stubs.
"""


class test_new_stuff(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

        self.stubly = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly)
        self.subject.connect('integrationtest')
        yang_ctx = self.subject.yang_ctx
        self.root = self.subject.get_node()

        self.stubly2 = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject2 = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly2)
        self.subject2.connect('integrationtest', yang_ctx=yang_ctx)
        self.root2 = self.subject2.get_node()

    def test_internal(self):
        self.assertEqual(self.subject.yang_ctx, self.subject2.yang_ctx)

    def test_scenario(self):
        self.root.simpleleaf = 'NonEmptyDoc'

        self.root2.diff.adds.a_leaf = 'A Leaf Value'
        self.root2.diff.adds.a_2nd_leaf = 'A second leaf'
        self.root2.diff.adds.a_list.create('KEY1').listnonkey = 'VAL1'
        self.root2.diff.adds.a_list.create('KEY2').listnonkey = 'VAL2'
        self.root2.diff.adds.a_list.create('KEY3').listnonkey = 'VAL3'
        self.root2.diff.adds.a_leaf_list.create('A')
        self.root2.diff.adds.a_leaf_list.create('B')
        self.root2.diff.adds.a_leaf_list.create('C')
        self.root2.diff.adds.presence_container.create()
        self.root2.diff.adds.empty_leaf.create()
        self.root2.diff.adds.boolean = True

        result = self.subject2.dumps()
        expected_result = ('<diff xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><adds>'
                           '<a-leaf>A Leaf Value</a-leaf><a-2nd-leaf>A second leaf</a-2nd-leaf><a-list>'
                           '<listkey>KEY1</listkey><listnonkey>VAL1</listnonkey></a-list><a-list>'
                           '<listkey>KEY2</listkey><listnonkey>VAL2</listnonkey></a-list><a-list>'
                           '<listkey>KEY3</listkey><listnonkey>VAL3</listnonkey></a-list>'
                           '<a-leaf-list>A</a-leaf-list><a-leaf-list>B</a-leaf-list>'
                           '<a-leaf-list>C</a-leaf-list><presence-container/><empty-leaf/>'
                           '<boolean>true</boolean></adds></diff>')
        self.assertEqual(result, expected_result)

        result = self.subject2.dumps(2)
        expected_result = ('{"integrationtest:diff":{"adds":{"a-leaf":"A Leaf Value",'
                           '"a-2nd-leaf":"A second leaf","a-list":[{"listkey":"KEY1",'
                           '"listnonkey":"VAL1"},{"listkey":"KEY2","listnonkey":"VAL2"},'
                           '{"listkey":"KEY3","listnonkey":"VAL3"}],"a-leaf-list":["A","B","C"],'
                           '"presence-container":{},"empty-leaf":[null],"boolean":true}}}')

        self.assertEqual(result, expected_result)

        # [('/integrationtest:simpleleaf', 'NonEmptyDoc', None, 3),
        # ('/integrationtest:diff/adds/a-leaf', None, 'A Leaf Value', 1),

        self.root2.simplelist.create('C')
        # [('/integrationtest:simpleleaf', 'NonEmptyDoc', None, 3),
        # ('/integrationtest:diff/adds/a-leaf', None, 'A Leaf Value', 1),
        # ("/integrationtest:simplelist[simplekey='C']/simplekey", None, 'C', 1),

        self.root2.morecomplex.extraboolean = False
        # [('/integrationtest:simpleleaf', 'NonEmptyDoc', None, 3),
        # ('/integrationtest:diff/adds/a-leaf', None, 'A Leaf Value', 1),
        # ("/integrationtest:simplelist[simplekey='C']/simplekey", None, 'C', 1),
        # ('/integrationtest:morecomplex/extraboolean', None, False, 1)]

        d = Differ(self.subject.yang_ctx)
        result = d.diff(self.stubly.libyang_data, self.stubly2.libyang_data)

        # Note: things are not quite right here, if we have lots of siblings under a node we only
        # get the first match - this will be because of the way the diff result works.
        # This also explains the symptom with libyang returning less hits when comparing an empty
        # document.... ->next probably is the answer
        raise ValueError(list(result))
        print(result)
