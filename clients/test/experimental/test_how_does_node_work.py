import unittest
import yangvoodoo
import yangvoodoo.stubdal
from yangvoodoo.Common import Utils, PlainObject, PlainIterator
from mock import Mock

"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def test(self):
        l = self.root.simplelist.create('sdf')
        self.assertEqual(l._node.real_data_path, "/integrationtest:simplelist[simplekey='sdf']")
        m = self.root.simplelist.create('abc')
        self.assertEqual(m._node.real_data_path, "/integrationtest:simplelist[simplekey='abc']")
        self.assertEqual(l._node.real_data_path, "/integrationtest:simplelist[simplekey='sdf']")

    def test_encode_xpath_predciates(self):
        result = Utils.encode_xpath_predicates('attri-bute', keys=['k1', 'k2'], values=[('v1', 10), ('v2', 10)])
        self.assertEqual(result, "attri-bute[k1='v1'][k2='v2']")

    def test_get_original_name(self):
        # Setup
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()

        result = Utils.get_original_name('', context, 'attribute')
        self.assertEqual(result, 'attribute')
        context.schemactx.find_path.assert_not_called()

    def test_get_original_name_with_underscore(self):
        # Setup
        node = Mock()
        node.name.return_value = 'attribute-here'
        context = PlainObject()
        context.module = "module"
        context.schemactx = Mock()
        context.schemactx.find_path = Mock()
        context.schemactx.find_path.return_value = PlainIterator([node])

        result = Utils.get_original_name('', context, 'attribute_here')
        self.assertEqual(result, 'attribute-here')

    def test_underscore(self):
        print(self.root.underscore_and_hyphen)
        self.root.underscore_and_hyphen = 'dsf'
        self.assertEqual(self.root.underscore_and_hyphen, 'dsf')
        expected_result = ['!underscore_and_hyphen']
        self.assertEqual(list(self.root._context.schemacache.items.keys()), expected_result)

        expected_result = {'/integrationtest:underscore_and-hyphen': 'dsf'}

        self.assertDictEqual(self.stub.stub_store, expected_result)
#     def test_root(self):
#         print(self.root.bronze.silver.gold.platinum)
#
#         print(self.root.bronze.silver.gold.platinum.deep)
#
#
# """
# print(self.root.bronze.silver.gold.platinum)
# __getattr__ called bronze
# __getattr__ called silver
# __getattr__ called gold
# __getattr__ called platinum
# VoodooContainer{/integrationtest:bronze/silver/gold/platinum}
#
#
# """
