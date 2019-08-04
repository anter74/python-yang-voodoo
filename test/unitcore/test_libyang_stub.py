import unittest
import yangvoodoo
import yangvoodoo.stublydal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_new_stuff(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stubly = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly, disable_proxy=True)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def test_basic_insantiation(self):
        pass

    def test_basic_set(self):
        # Act
        self.root.simpleleaf = "A"

        # Assert
        self.assertEqual(self.root.simpleleaf, "A")

    def test_basic_list(self):
        # Act
        list_element = self.root.simplelist.create("ABC")
        list_element.nonleafkey = 5

        # Assert
        self.assertEqual('ABC' in self.root.simplelist, True)
        self.assertEqual(self.root.simplelist['ABC'].nonleafkey, 5)

    def test_delete_list(self):
        # Arrange
        self.root.simplelist.create("ABC")
        self.root.simplelist.create("DEF")

        # Assert
        self.assertFalse('A' in self.root.simplelist)
        self.assertEqual(len(self.root.simplelist), 2)

        # Act
        del self.root.simplelist['ABC']

        # Assert
        self.assertFalse('A' in self.root.simplelist)
        self.assertEqual(len(self.root.simplelist), 1)

    def test_list_iteration(self):
        # Arrange
        list_element = self.root.simplelist.create("ABC")
        list_element.nonleafkey = 5
        list_element = self.root.simplelist.create("DEF")
        list_element.nonleafkey = 6
        list_element = self.root.simplelist.create("GHI")
        list_element.nonleafkey = 7
        list_element = self.root.simplelist.create("JKL")
        list_element.nonleafkey = 8
        list_element = self.root.simplelist.create("MNO")
        list_element.nonleafkey = 9

        # Act
        results = list(self.root.simplelist)

        # Assert
        self.assertEqual(len(self.root.simplelist), 5)
        expected_results = [
            "VoodooListElement{/integrationtest:simplelist[simplekey='ABC']}",
            "VoodooListElement{/integrationtest:simplelist[simplekey='DEF']}",
            "VoodooListElement{/integrationtest:simplelist[simplekey='GHI']}",
            "VoodooListElement{/integrationtest:simplelist[simplekey='JKL']}",
            "VoodooListElement{/integrationtest:simplelist[simplekey='MNO']}"
        ]

        for result in results:
            self.assertEqual(repr(result), expected_results.pop(0))

    def test_container_presence_explicit(self):
        # Act
        self.root.bronze.silver.gold.platinum.deeper.create()

        # Assert
        self.assertTrue(self.root.bronze.silver.gold.platinum.deeper.exists())

    def test_container_presence_false(self):
        # Act
        self.root.bronze.silver.gold.platinum.deep = "Some value close by"

        # Assert
        self.assertFalse(self.root.bronze.silver.gold.platinum.deeper.exists())

    def test_container_presence_implicit(self):
        # Act
        self.root.bronze.silver.gold.platinum.deeper.gone_too_far = "Inner value"

        # Assert
        self.assertTrue(self.root.bronze.silver.gold.platinum.deeper.exists())

        self.subject.dump("/tmp/xyz.json", 2)

    def not_implementedtest_dump_xpaths(self):
        """
        # search_path = "/%s:*" % (self.module)
        # self.log.trace("DUMP_XPATHS: %s", search_path)
        # for xpath in self.libyang_data.dump_xpaths(search_path):
        #     yield xpath

        This gave us
        - ["/integrationtest:simplelist[simplekey='ABC']", '/integrationtest:bronze']

        """
        list_element = self.root.simplelist.create("ABC")
        list_element.nonleafkey = 5
        self.root.bronze.silver.gold.platinum.deeper.gone_too_far = "Inner value"

        # Act
        results = list(self.subject.dump_xpaths())

        # Assert
        expected_results = ['sdf']
        self.assertEqual(results, expected_results)

    def test_leaf_list(self):
        # Act
        self.root.morecomplex.leaflists.simple.create('ABC')
        self.root.morecomplex.leaflists.simple.create('ABC')
        self.root.morecomplex.leaflists.simple.create('DEF')
        self.root.morecomplex.leaflists.simple.create('GHI')
        results = list(self.root.morecomplex.leaflists.simple)

        # Assert
        expected_results = ['ABC', 'DEF', 'GHI']
        self.assertEqual(results, expected_results)

        # Act
        del self.root.morecomplex.leaflists.simple['ABC']
        expected_results = ['DEF', 'GHI']
        results = list(self.root.morecomplex.leaflists.simple)

        # Assert
        self.assertEqual(results, expected_results)

    def test_list(self):
        # Arrange
        self.root.simpleleaf = 'ABC'
        self.assertEqual(self.root.simpleleaf, "ABC")

        # Act
        self.root.simpleleaf = None

        # Assert
        self.assertEqual(self.root.simpleleaf, None)

    def test_leaf_empty(self):
        # Arrange
        self.root.empty.create()
        self.assertEqual(self.root.empty.exists(), True)

        self.subject.dump("/tmp/xyz.json", 2)
        # Act
        self.root.simpleleaf = None

        # Assert
        self.assertEqual(self.root.simpleleaf, None)

    def test_leaf_empty_not_existing(self):
        # Act
        self.assertEqual(self.root.empty.exists(), False)

        # Assert
        self.assertEqual(self.root.simpleleaf, None)
