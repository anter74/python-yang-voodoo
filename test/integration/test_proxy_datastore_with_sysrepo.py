import unittest
import yangvoodoo
import yangvoodoo.stubdal
import subprocess
import time
import yangvoodoo.proxydal
from yangvoodoo.sysrepodal import SysrepoDataAbstractionLayer
from mock import Mock, patch


class test_proxy_datastore_with_sysrepo(unittest.TestCase):

    maxDiff = 50000

    def setUp(self):
        self.maxDiff = None
        command = "sysrepocfg --import=init-data/integrationtest.xml --format=xml --datastore=running integrationtest"
        process = subprocess.Popen(
            ["bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        (out, err) = process.communicate(command.encode("UTF-8"))
        if err:
            raise ValueError("Unable to import data\n%s\n%s" % (out, err))

        time.sleep(0.25)

        sysrepodal = SysrepoDataAbstractionLayer()
        self.session = yangvoodoo.DataAccess(
            disable_proxy=False, data_abstraction_layer=sysrepodal
        )
        self.session.connect("integrationtest", yang_location="yang")
        self.root = self.session.get_node()
        self.subject = yangvoodoo.proxydal.ProxyDataAbstractionLayer(
            self.session.data_abstraction_layer
        )
        self.subject.context = Mock()
        self.subject.context.module = "integrationtest"

    def test_reading(self):
        xpath = "/integrationtest:simpleleaf"
        # Uncached
        self.assertFalse(xpath in self.subject.value_cached)
        result = self.subject.get(xpath)
        self.assertEqual(result, "duke")
        self.assertTrue(xpath in self.subject.value_cached)

        # Cached
        result = self.subject.get(xpath)
        self.assertEqual(result, "duke")

        # Drop cache
        self.subject.refresh()
        self.assertFalse(xpath in self.subject.value_cached)

    def test_setting_then_reading(self):
        xpath = "/integrationtest:simpleleaf"
        # Uncached
        self.assertFalse(xpath in self.subject.value_cached)
        result = self.subject.set(xpath, "ABC", 10)
        self.assertTrue(xpath in self.subject.value_cached)
        self.assertEqual(result, "ABC")
        self.assertTrue(xpath in self.subject.value_cached)

        # Drop cache
        self.subject.refresh()
        self.assertFalse(xpath in self.subject.value_cached)

    @patch("yangvoodoo.Common.Utils.get_yang_type_from_path")
    def test_lists(self, mockGetYangType):
        self.subject.module = "integrationtest"
        mockGetYangType.return_value = 10
        xpath = "/integrationtest:simplelist"
        xpath1 = xpath + "[simplekey='simpleval']"
        xpath2 = xpath + "[simplekey='zsimpleval']"
        xpath3 = xpath + "[simplekey='asimpleval']"

        self.subject.create(xpath1, ("simplekey",), (("simpleval", 10),))
        self.subject.create(xpath2, ("simplekey",), (("zsimpleval", 10),))
        self.subject.create(xpath3, ("simplekey",), (("asimpleval", 10),))

        # Uncached
        self.assertFalse(xpath in self.subject.unsorted_cached)

        list(self.subject.gets_unsorted(xpath, xpath, True))
        self.assertTrue(xpath in self.subject.unsorted_cached)

        expected_result = {xpath: [xpath1, xpath2, xpath3]}
        self.assertEqual(expected_result, self.subject.unsorted_cached)

    def test_leaf_lists(self):
        xpath = "/integrationtest:morecomplex/integrationtest:leaflists/integrationtest:simple"
        val1 = "Z"
        val2 = "A"
        val3 = "C"

        self.subject.add(xpath, val1, 10)
        self.subject.add(xpath, val2, 10)
        self.subject.add(xpath, val3, 10)

        # Uncached
        self.assertFalse(xpath in self.subject.value_cached)

        list(self.subject.gets(xpath))
        self.assertTrue(xpath in self.subject.value_cached)

        expected_result = {xpath: [val1, val2, val3]}
        self.assertEqual(expected_result, self.subject.value_cached)
