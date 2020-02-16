import unittest
import yangvoodoo
import yangvoodoo.stublydal
from yangvoodoo.Errors import ListItemsMustBeAccesssedByAnElementError
import libyang
from libyang.util import LibyangError
from mock import Mock

"""
This set of unit tests uses the libyang stub backend datastore, which is not preseeded with
any data.
"""


class test_libyang_stub(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stubly = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly, disable_proxy=True)
        self.subject.connect('integrationtest', yang_location='yang')
        self.root = self.subject.get_node()

    def test_basic_insantiation(self):
        pass

    def test_basic_get_based_on_yang_schema_default(self):
        # Act
        self.assertEqual(self.root.default, "statusquo")

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

    def test_connect_connects_if_libyang_data_already_exists(self):
        stubly = Mock()
        subject = yangvoodoo.DataAccess(data_abstraction_layer=stubly, disable_proxy=True)
        subject.connect('integrationtest', yang_location='yang')

        self.assertNotEqual(stubly, subject.data_abstraction_layer.libyang_data)

    def test_connect_avoids_connecting_if_libyang_data_already_exists(self):
        stubly = Mock()
        subject = yangvoodoo.DataAccess(data_abstraction_layer=stubly, disable_proxy=True)
        subject.data_abstraction_layer.libyang_data = stubly
        subject.connect('integrationtest', yang_location='yang')

        self.assertEqual(stubly, subject.data_abstraction_layer.libyang_data)

    def test_reserved_kewords(self):
        self.root.morecomplex.python_reserved_keywords.class_ = 'class'
        self.assertEqual(repr(self.root.morecomplex.python_reserved_keywords.import_),
                         "VoodooEmpty{/integrationtest:morecomplex/python-reserved-keywords/import} - Does Not Exist")
        self.root.morecomplex.python_reserved_keywords.import_.create()
        self.assertEqual(repr(self.root.morecomplex.python_reserved_keywords.import_),
                         "VoodooEmpty{/integrationtest:morecomplex/python-reserved-keywords/import} - Exists")

        self.assertEqual(len(self.root.morecomplex.python_reserved_keywords.and_), 0)
        self.root.morecomplex.python_reserved_keywords.and_.create('x', 'y')
        self.assertEqual(len(self.root.morecomplex.python_reserved_keywords.and_), 1)
        self.assertEqual(repr(list(self.root.morecomplex.python_reserved_keywords.and_)[0]),
                         "VoodooListElement{/integrationtest:morecomplex/python-reserved-keywords/and[break='x'][not-break='y']}"
                         )

        self.root.morecomplex.leaflists.simple.create('a')
        self.root.morecomplex.leaflists.simple.create('b')
        self.root.morecomplex.leaflists.simple.create('c')
        self.assertEqual(len(self.root.morecomplex.leaflists.simple), 3)
        self.assertEqual(len(self.root.morecomplex.python_reserved_keywords.global_), 0)
        self.root.morecomplex.python_reserved_keywords.global_.create('x')
        self.root.morecomplex.python_reserved_keywords.global_.create('y')
        self.assertEqual(len(self.root.morecomplex.python_reserved_keywords.global_), 2)
        self.assertEqual(list(self.root.morecomplex.python_reserved_keywords.global_), ['x', 'y'])

        # Assert
        self.assertEqual(self.root.morecomplex.python_reserved_keywords.class_, 'class')

        expected_result = {
            '/integrationtest:morecomplex': True,
            '/integrationtest:morecomplex/python-reserved-keywords': True,
            '/integrationtest:morecomplex/python-reserved-keywords/class': 'class',
            '/integrationtest:morecomplex/python-reserved-keywords/import': True,
            "/integrationtest:morecomplex/python-reserved-keywords/and[break='x'][not-break='y']/break": 'x',
            "/integrationtest:morecomplex/python-reserved-keywords/and[break='x'][not-break='y']/not-break": 'y',
            "/integrationtest:morecomplex/python-reserved-keywords/global[.='x']": 'x',
            "/integrationtest:morecomplex/python-reserved-keywords/global[.='y']": 'y',
            '/integrationtest:morecomplex/leaflists': True,
            "/integrationtest:morecomplex/leaflists/simple[.='a']": 'a',
            "/integrationtest:morecomplex/leaflists/simple[.='b']": 'b',
            "/integrationtest:morecomplex/leaflists/simple[.='c']": 'c'
        }

        self.assertEqual(self.subject.dump_xpaths(), expected_result)

    def test_json_loads_mandatories_satisified(self):
        json_payload = """
        {"integrationtest:validator":{"mandatories":{"this-is-mandatory":"abc"},"strings":{"nolen":"ABC"}}}
        """

        # Act
        self.subject.loads(json_payload, 2, trusted=False)

        # Assert
        self.assertEqual(self.root.validator.mandatories.this_is_mandatory, "abc")
        self.assertEqual(self.root.validator.strings.nolen, "ABC")

    def test_json_loads_with_missing_mandatories(self):
        json_payload = """
        {"integrationtest:validator":{"mandatories":{},"strings":{"nolen":"ABC"}}}
        """

        # Act
        with self.assertRaises(libyang.util.LibyangError):
            self.subject.loads(json_payload, 2, trusted=False)

    def test_json_loads_with_missing_mandatories_but_trusted(self):
        json_payload = """
        {"integrationtest:validator":{"mandatories":{},"strings":{"nolen":"ABC"}}}
        """

        # Act
        self.subject.loads(json_payload, 2, trusted=True)

        # Assert
        self.assertEqual(self.root.validator.mandatories.this_is_mandatory, None)
        self.assertEqual(self.root.validator.strings.nolen, "ABC")

    def test_json_merges(self):
        json_payload_first = """
        {"integrationtest:validator":{"strings":{"nolen":"XYZ"}}}
        """

        json_payload_second = """
        {"integrationtest:validator":{"mandatories":{},"strings":{"nolen":"ABC"}}}
        """

        # Act
        self.subject.loads(json_payload_first, 2, trusted=False)

        # Assert
        self.assertEqual(self.root.validator.mandatories.exists(), False)

        # Act 2
        self.subject.merges(json_payload_second, 2, trusted=True)
        self.assertEqual(self.root.validator.mandatories.exists(), True)
        self.assertEqual(self.root.validator.strings.nolen, "ABC")

    def test_validate_method(self):
        json_payload_first_invalid = """
        {"integrationtest:validator":{"mandatories":{},"strings":{"nolen":"ABC"}}}
        """

        # Act
        self.subject.loads(json_payload_first_invalid, 2, trusted=True)

        # Assert
        expected_error = ('Validation Error: /integrationtest:validator/mandatories:'
                          ' Missing required element "this-is-mandatory" in "mandatories".')
        with self.assertRaises(LibyangError) as err:
            self.subject.validate()
        self.assertEqual(str(err.exception), expected_error)

        result = self.subject.validate(raise_exception=False)
        self.assertEqual(result, False)

        json_payload_valid = """
        {"integrationtest:validator":{"mandatories":{"this-is-mandatory":"abc"},"strings":{"nolen":"ABC"}}}
        """
        self.subject.merges(json_payload_valid, 2, trusted=False)
        self.subject.validate()

    def test_accessing_via_list_instead_of_list_element(self):
        with self.assertRaises(ListItemsMustBeAccesssedByAnElementError):
            print(self.root.simplelist.simplekey)

        self.root.simplelist.create('a').nonleafkey = 59
        self.assertEqual(self.root.simplelist.get('a').simplekey, 'a')
        self.assertEqual(self.root.simplelist.get('a').nonleafkey, 59)

        with self.assertRaises(ListItemsMustBeAccesssedByAnElementError) as err:
            self.root.simplelist.simplekey = 'sdf'

    def test_load(self):
        with self.assertRaises(libyang.util.LibyangError):
            self.subject.load('test/invalid.json', 2)

        self.subject.load('test/valid.xml', 1)
        self.assertEqual(self.root.simpleenum, 'A')

    def test_get_raw_xpath(self):
        result = list(self.subject.data_abstraction_layer.get_raw_xpath('/integrationtest:simpleleaf'))
        self.assertEqual(result, [])

        result = list(self.subject.get_raw_xpath('/integrationtest:simpleleaf'))
        self.assertEqual(result, [])

        result = self.subject.get_raw_xpath_single_val('/integrationtest:simpleleaf')
        self.assertEqual(result, None)

        self.root.simpleleaf = 'abc'
        result = list(self.subject.data_abstraction_layer.get_raw_xpath('/integrationtest:simpleleaf'))
        self.assertEqual(result, ['/integrationtest:simpleleaf'])

        result = self.subject.get_raw_xpath_single_val('/integrationtest:simpleleaf')
        self.assertEqual(result, 'abc')

        self.root.simpleleaf = 'abc'
        result = list(self.subject.data_abstraction_layer.get_raw_xpath('/integrationtest:simpleleaf', with_val=True))
        self.assertEqual(result, [('/integrationtest:simpleleaf', 'abc')])

        result = list(self.subject.get_raw_xpath('/integrationtest:simpleleaf', with_val=True))
        self.assertEqual(result, [('/integrationtest:simpleleaf', 'abc')])

        result = list(self.subject.get_raw_xpath('/integrationtest:simpleleaf', with_val=True))
        self.assertEqual(result, [('/integrationtest:simpleleaf', 'abc')])
