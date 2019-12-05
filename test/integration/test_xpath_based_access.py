import libyang
import unittest
import time
import yangvoodoo
import subprocess
import sysrepo as sr
from yangvoodoo.sysrepodal import SysrepoDataAbstractionLayer
from yangvoodoo import Types


class test_getdata(unittest.TestCase):

    def setUp(self):
        command = 'sysrepocfg --import=init-data/integrationtest.xml --format=xml --datastore=running integrationtest'
        process = subprocess.Popen(["bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (out, err) = process.communicate(command.encode('UTF-8'))
        if err:
            raise ValueError('Unable to import data\n%s\n%s' % (out, err))

        time.sleep(0.25)

        sysrepodal = SysrepoDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal)
        self.subject.connect('integrationtest', yang_location='yang')

    def test_delete_and_get(self):
        self.subject.set('/integrationtest:simpleenum', 'A', Types.DATA_ABSTRACTION_MAPPING['ENUM'])
        value = self.subject.get('/integrationtest:simpleenum')
        self.assertEqual(value, 'A')

        self.subject.delete('/integrationtest:simpleenum')

        value = self.subject.get('/integrationtest:simpleenum')
        self.assertEqual(value, None)

    def test_get_leaf(self):
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertEqual(self.subject.get(xpath), 'Inside')

    def test_set_leaves(self):
        """
        This tests setting leaves with and without commits.

        We can see commits don't persist to startup config.
        """
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"
        self.subject.set(xpath, value)
        self.assertEqual(self.subject.get(xpath), 'Outside')

        sysrepodal = SysrepoDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal)
        self.subject.connect('integrationtest', yang_location='yang')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertNotEqual(self.subject.get(xpath), 'Outside')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"
        self.subject.set(xpath, value)
        self.assertEqual(self.subject.get(xpath), 'Outside')
        self.subject.commit()

        sysrepodal = SysrepoDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal)
        self.subject.connect('integrationtest', yang_location='yang')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        self.assertEqual(self.subject.get(xpath), 'Outside')

        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Inside"
        self.subject.set(xpath, value)
        self.subject.commit()

    def test_set_leaves_multiple_transactions(self):
        """
        This tests setting values- here we can see sysrepo doesn't block a commit
        when the data changes.

        We can see commits don't persist to startup config.

        Importantly though, we can see that after subject1 has changed the value from
        Inside to Outside subject2 on it's following get picks up the new value
        instead of what it was when it created the value.
        """
        xpath = "/integrationtest:morecomplex/inner/leaf5"
        value = "Outside"

        sysrepodal1 = SysrepoDataAbstractionLayer()
        self.subject1 = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal1)
        self.subject.connect('integrationtest', yang_location='yang')
        self.subject1.connect('integrationtest', 'yang', 'a')
        sysrepodal2 = SysrepoDataAbstractionLayer()
        self.subject2 = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal2)
        self.subject2.connect('integrationtest', 'yang', 'b')

        self.subject1.set(xpath, value)
        self.assertEqual(self.subject1.get(xpath), 'Outside')
        self.subject1.commit()
        self.assertEqual(self.subject2.get(xpath), 'Outside')

        value = 'Middle'
        self.subject2.set(xpath, value)
        self.subject2.commit()
        self.assertEqual(self.subject2.get(xpath), 'Middle')

    def test_leafref(self):
        xpath = "/integrationtest:thing-that-is-leafref"
        valid_value = 'GHI'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

        xpath = "/integrationtest:thing-that-is-leafref"
        invalid_value = 'ZZZ'
        self.subject.set(xpath, invalid_value)

        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            self.subject.commit()
        self.assertEqual(str(context.exception),
                         ("1 Errors occured\n"
                          "Error 0: Leafref \"../thing-to-leafref-against\" of value \"ZZZ\" "
                          "points to a non-existing leaf. (Path: /integrationtest:thing-that-is-leafref)\n"))

        sysrepodal = SysrepoDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(disable_proxy=True, data_abstraction_layer=sysrepodal)
        self.subject.connect('integrationtest', yang_location='yang')

        xpath = "/integrationtest:thing-that-is-a-list-based-leafref"
        valid_value = 'I'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

        valid_value = 'W'
        self.subject.set(xpath, valid_value)
        self.subject.commit()

    def test_non_existing_element(self):
        with self.assertRaises(RuntimeError) as context:
            xpath = "/integrationtest:thing-that-never-does-exist-in-yang"
            self.subject.get(xpath)
        self.assertEqual(str(context.exception), 'Request contains unknown element')

    def test_containers_and_non_existing_data(self):
        with self.assertRaises(yangvoodoo.Errors.NodeHasNoValue) as context:
            xpath = "/integrationtest:morecomplex"
            self.subject.get(xpath)
        self.assertEqual(str(context.exception), 'The node: container at /integrationtest:morecomplex has no value')

        xpath = "/integrationtest:morecomplex/inner"
        value = self.subject.get(xpath)
        self.assertTrue(value)

        xpath = "/integrationtest:simplecontainer"
        value = self.subject.get(xpath)
        self.assertEqual(value, None)

        xpath = "/integrationtest:empty"
        self.subject.set(xpath, None, Types.DATA_ABSTRACTION_MAPPING['EMPTY'])

    def test_numbers(self):
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:bronze/silver/gold/platinum/deep"
            self.subject.set(xpath, 123, Types.DATA_ABSTRACTION_MAPPING['UINT16'])
        self.assertEqual(str(context.exception), "1 Errors occured\nError 0: Invalid argument (Path: None)\n")

        xpath = "/integrationtest:bronze/silver/gold/platinum/deep"
        self.subject.set(xpath, "123", Types.DATA_ABSTRACTION_MAPPING['STRING'])

        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:morecomplex/leaf3"
            self.subject.set(xpath, 123, Types.DATA_ABSTRACTION_MAPPING['UINT16'])
        self.assertEqual(str(context.exception), '1 Errors occured\nError 0: Invalid argument (Path: None)\n')

        xpath = "/integrationtest:morecomplex/leaf3"
        self.subject.set(xpath, 123, Types.DATA_ABSTRACTION_MAPPING['UINT32'])

    def test_other_types(self):
        xpath = "/integrationtest:morecomplex/leaf2"
        value = self.subject.get(xpath)
        self.assertTrue(value)

        xpath = "/integrationtest:morecomplex/leaf2"
        self.subject.set(xpath, False, Types.DATA_ABSTRACTION_MAPPING['BOOLEAN'])

        value = self.subject.get(xpath)
        self.assertFalse(value)

        # this leaf is a union of two different typedef's
        xpath = "/integrationtest:morecomplex/leaf4"
        self.subject.set(xpath, 'A', Types.DATA_ABSTRACTION_MAPPING['ENUM'])

        xpath = "/integrationtest:morecomplex/leaf4"
        self.subject.set(xpath, 23499, Types.DATA_ABSTRACTION_MAPPING['UINT32'])

    def test_lists(self):
        """
        We can choose to create list entries or allow them to be created by setting something deeper.
        <container-and-lists xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
          <multi-key-list>
            <A>a</A>
            <B>B</B>
          </multi-key-list>
          <multi-key-list>
            <A>aa</A>
            <B>bb</B>
            <inner>
              <C>C</C>
            </inner>
          </multi-key-list>
        </container-and-lists>
        """

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']"  # [B='b']"
        self.subject.create(xpath, keys=('A', 'B'), values=(('a', Types.DATA_ABSTRACTION_MAPPING['STRING']), ('B', Types.DATA_ABSTRACTION_MAPPING['STRING'])))

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']"  # [B='b']"
        self.subject.set(xpath,  None, None,  Types.DATA_NODE_MAPPING['LIST'])

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='aa'][B='bb']/inner/C"  # [B='b']"
        self.subject.set(xpath,  'cc', Types.DATA_ABSTRACTION_MAPPING['STRING'])

        xpath = "/integrationtest:container-and-lists/multi-key-list[A='xx'][B='xx']/inner/C"  # [B='b']"
        value = self.subject.get(xpath)
        self.assertEqual(value, None)

        # Missing key
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            xpath = "/integrationtest:twokeylist[primary='true']"
            self.subject.set(xpath,  None, None, Types.DATA_NODE_MAPPING['LIST'])
        self.assertEqual(str(context.exception), '1 Errors occured\nError 0: Invalid argument (Path: None)\n')

        xpath = "/integrationtest:container-and-lists/multi-key-list"
        spath = "/integrationtest:container-and-lists/integrationtest:multi-key-list"
        items = self.subject.gets_unsorted(xpath, spath)
        self.assertNotEqual(items, None)

        expected = [
            ["/integrationtest:container-and-lists/multi-key-list[A='a'][B='B']", 'a', 'B', None],
            ["/integrationtest:container-and-lists/multi-key-list[A='aa'][B='bb']", 'aa', 'bb', 'cc']
        ]

        idx = 0
        for item in items:
            (expected_xpath, expected_a_val, expected_b_val, expected_c_val) = expected[idx]
            self.assertEqual(expected_xpath, item)

            item_xpath = item + "/A"
            self.assertEqual(self.subject.get(item_xpath), expected_a_val)

            item_xpath = item + "/B"
            self.assertEqual(self.subject.get(item_xpath), expected_b_val)

            item_xpath = item + "/inner/C"
            self.assertEqual(self.subject.get(item_xpath), expected_c_val)

            idx = idx + 1
        with self.assertRaises(StopIteration) as context:
            next(items)

    def test_lists_ordering(self):

        xpath = "/integrationtest:simplelist[simplekey='A']"
        self.subject.create(xpath, keys=('simplekey',), values=(('A', Types.DATA_ABSTRACTION_MAPPING['STRING']),))

        xpath = "/integrationtest:simplelist[simplekey='Z']"
        self.subject.create(xpath, keys=('simplekey',), values=(('Z', Types.DATA_ABSTRACTION_MAPPING['STRING']),))

        xpath = "/integrationtest:simplelist[simplekey='middle']"
        self.subject.create(xpath, keys=('simplekey',), values=(('middle', Types.DATA_ABSTRACTION_MAPPING['STRING']),))

        xpath = "/integrationtest:simplelist[simplekey='M']"
        self.subject.create(xpath, keys=('simplekey',), values=(('M', Types.DATA_ABSTRACTION_MAPPING['STRING']),))

        xpath = "/integrationtest:simplelist"

        # GETS is based on user defined order
        items = self.subject.gets_unsorted(xpath, xpath)
        expected_results = ["/integrationtest:simplelist[simplekey='A']",
                            "/integrationtest:simplelist[simplekey='Z']",
                            "/integrationtest:simplelist[simplekey='middle']",
                            "/integrationtest:simplelist[simplekey='M']"]
        self.assertEqual(list(items), expected_results)

        # GETS_SORTED is based on xpath sorted order
        items = self.subject.gets_sorted(xpath, xpath)
        expected_results = ["/integrationtest:simplelist[simplekey='A']",
                            "/integrationtest:simplelist[simplekey='M']",
                            "/integrationtest:simplelist[simplekey='Z']",
                            "/integrationtest:simplelist[simplekey='middle']"]
        self.assertEqual(list(items), expected_results)

    def _set_type(self, xpath, value, valtype):
        self.subject.set("/integrationtest:validator/integrationtest:types/integrationtest:" + xpath, value, valtype)

    def test_types_from_node(self):
        self._set_type("u_int_8", 0, libyang.schema.Type.UINT8)
        self._set_type("u_int_8", 255, libyang.schema.Type.UINT8)
        self._set_type("u_int_16", 65535, libyang.schema.Type.UINT16)
        self._set_type("u_int_32", 4294967295, libyang.schema.Type.UINT32)
        # self._set_type("u_int_64", 18446744073709551615, libyang.schema.Type.UINT64)
        self._set_type("int_8", 0, libyang.schema.Type.INT8)
        self._set_type("int_8", 2128, libyang.schema.Type.INT8)
        self._set_type("int_16", -32768, libyang.schema.Type.INT16)
        self._set_type("int_16", 32767, libyang.schema.Type.INT16)
        self._set_type("int_32", -2147483648, libyang.schema.Type.INT32)
        self._set_type("int_32", 2147483647, libyang.schema.Type.INT32)
        self._set_type("int_64", - 9223372036854775808, libyang.schema.Type.INT64)
        # self._set_type("int_64",  9223372036854775807, libyang.schema.Type.INT64)
        self._set_type("str", "A", libyang.schema.Type.STRING)
        self._set_type("bool", True, libyang.schema.Type.BOOL)
        self._set_type("void", None, libyang.schema.Type.EMPTY)
        self._set_type("enumeratio", "A", libyang.schema.Type.ENUM)
        self._set_type("dec_64", 234.234234, libyang.schema.Type.DEC64)
        self.subject.validate()
