import unittest
import yangvoodoo
import yangvoodoo.stubdal


class test_data_access_session(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def test_set_raw_data(self):
        # Build
        base_xpath = self.root.bronze.silver.gold._node.real_data_path
        sub_xpath = "/platinum/deep"
        value = "hello"
        context = self.root._context

        # Act
        self.subject.set_raw_data(context, base_xpath + sub_xpath, value)

        # Assert
        expected_result = {'/integrationtest:bronze/silver/gold/platinum/deep': 'hello'}
        self.assertDictEqual(self.subject.dump_xpaths(), expected_result)
