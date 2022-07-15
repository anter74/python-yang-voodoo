import unittest
import yangvoodoo
import yangvoodoo.stublydal
from yangvoodoo.Errors import ListItemsMustBeAccesssedByAnElementError
import libyang
from libyang.util import LibyangError
from mock import Mock

"""
This set of unit tests uses the libyang stub backend datastore, which make use of multiple
yang models with augments into the parent..
"""


class test_libyang_stub(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.stubly = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly)
        self.subject.connect("integrationtest", yang_location="yang")
        self.subject.add_module("foreign")
        self.root = self.subject.get_node()

    def test_basic_set(self):
        # Act
        self.root.augments.foreign_augments.simpleleaf = "A"

        # Assert
        self.assertEqual(self.root.augments.foreign_augments.simpleleaf, "A")

    def test_dir(self):
        self.assertEqual(
            dir(self.root.augments.foreign_augments),
            [
                "hyphenated_leaf",
                "nonpresencecontainer",
                "simplecontainer",
                "simpleleaf",
                "simplelist",
            ],
        )

        listelement = self.root.augments.foreign_augments.simplelist.create("A", "B")
        self.assertEqual(dir(listelement), ["innercontainer", "key1", "key2", "nonkey"])

    def test_list(self):
        # Act
        list_element_ab = self.root.augments.foreign_augments.simplelist.create(
            "a", "b"
        )
        self.root.augments.foreign_augments.simplelist.create("A", "B").nonkey = "c"

        # Assert
        self.assertEqual(len(self.root.augments.foreign_augments.simplelist), 2)

        self.assertEqual(
            self.subject.dumps(),
            (
                '<augments xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><foreign-augments>'
                '<simplelist xmlns="uri://foreign"><key1>a</key1><key2>b</key2></simplelist>'
                '<simplelist xmlns="uri://foreign"><key1>A</key1><key2>B</key2><nonkey>c</nonkey></simplelist>'
                "</foreign-augments></augments>"
            ),
        )
        self.assertTrue(("A", "B") in self.root.augments.foreign_augments.simplelist)
        self.assertFalse(("A", "Z") in self.root.augments.foreign_augments.simplelist)
        del self.root.augments.foreign_augments.simplelist["A", "B"]
        self.assertFalse(("A", "B") in self.root.augments.foreign_augments.simplelist)
        list_element_cd = self.root.augments.foreign_augments.simplelist.create(
            "c", "d"
        )
        self.assertEqual(len(self.root.augments.foreign_augments.simplelist), 2)

        answer = []
        for listelement in self.root.augments.foreign_augments.simplelist:
            answer.append(repr(listelement))
        self.assertEqual(
            answer,
            [
                "VoodooListElement{/integrationtest:augments/foreign-augments/foreign:simplelist[key1='a'][key2='b']}",
                "VoodooListElement{/integrationtest:augments/foreign-augments/foreign:simplelist[key1='c'][key2='d']}",
            ],
        )

        list_element_ab.innercontainer.innerlist.create(1)
        list_element_cd.innercontainer.innerlist.create(1)
        list_element_cd.innercontainer.innerlist.create(2)
        list_element_cd.innercontainer.innerlist.create(3)

        self.assertEqual(list_element_cd.innercontainer.innerlist.keys(), ["key1"])
        self.assertEqual(
            list(list_element_cd.innercontainer.innerlist.elements()),
            [
                (
                    "/integrationtest:augments/foreign-augments"
                    "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='1']"
                ),
                (
                    "/integrationtest:augments/foreign-augments"
                    "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='2']"
                ),
                (
                    "/integrationtest:augments/foreign-augments"
                    "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='3']"
                ),
            ],
        )

        self.assertEqual(
            list_element_cd.innercontainer.innerlist.get_index(2)._path,
            (
                "/integrationtest:augments/foreign-augments"
                "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='3']"
            ),
        )
        self.assertEqual(
            list_element_cd.innercontainer.innerlist[3]._path,
            (
                "/integrationtest:augments/foreign-augments"
                "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='3']"
            ),
        )
        self.assertEqual(
            list_element_cd.innercontainer.innerlist.get(3)._path,
            (
                "/integrationtest:augments/foreign-augments"
                "/foreign:simplelist[key1='c'][key2='d']/innercontainer/innerlist[key1='3']"
            ),
        )
        self.assertEqual(
            self.subject.dumps(2),
            (
                '{"integrationtest:augments":{"foreign-augments":{"foreign:simplelist":'
                '[{"key1":"a","key2":"b","innercontainer":{"innerlist":[{"key1":1}]}},'
                '{"key1":"c","key2":"d","innercontainer":{"innerlist":[{"key1":1},{"key1":2},{"key1":3}]}}]}}}'
            ),
        )
        self.assertEqual(
            self.subject.dumps(1),
            (
                (
                    '<augments xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">'
                    '<foreign-augments><simplelist xmlns="uri://foreign"><key1>a</key1><key2>b</key2><innercontainer>'
                    "<innerlist><key1>1</key1></innerlist></innercontainer></simplelist>"
                    '<simplelist xmlns="uri://foreign"><key1>c</key1><key2>d</key2><innercontainer>'
                    "<innerlist><key1>1</key1></innerlist><innerlist><key1>2</key1></innerlist><innerlist>"
                    "<key1>3</key1></innerlist></innercontainer></simplelist></foreign-augments></augments>"
                )
            ),
        )

    def test_leaflist(self):
        list_element1 = self.root.augments.foreign_augments.simplelist.create("a", "b")
        list_element2 = self.root.augments.foreign_augments.simplelist.create("A", "B")

        list_element1.innercontainer.simpleleaflist.create("x1")
        list_element1.innercontainer.simpleleaflist.create("x2")
        list_element1.innercontainer.simpleleaflist.create("x3")
        list_element2.innercontainer.simpleleaflist.create("x1")
        list_element2.innercontainer.simpleleaflist.create("x3")

        self.assertEqual(
            list(list_element1.innercontainer.simpleleaflist), ["x1", "x2", "x3"]
        )
        self.assertEqual(
            list(list_element2.innercontainer.simpleleaflist), ["x1", "x3"]
        )
        self.assertEqual(len(list_element2.innercontainer.simpleleaflist), 2)

        del list_element2.innercontainer.simpleleaflist["x1"]
        self.assertEqual(len(list_element2.innercontainer.simpleleaflist), 1)
        self.assertEqual(list_element1.innercontainer.simpleleaflist.get_index(1), "x2")
        self.assertTrue("x2" in list_element1.innercontainer.simpleleaflist)
        self.assertFalse("x2" in list_element2.innercontainer.simpleleaflist)
        self.assertEqual(
            [x for x in list_element1.innercontainer.simpleleaflist], ["x1", "x2", "x3"]
        )
        self.assertEqual(
            [x for x in list_element2.innercontainer.simpleleaflist], ["x3"]
        )

    def test_presence_container(self):
        self.assertFalse(self.root.augments.foreign_augments.simplecontainer.exists())
        container0 = self.root.augments.foreign_augments.simplecontainer.create()
        self.assertTrue(self.root.augments.foreign_augments.simplecontainer.exists())
        container0.destroy()
        self.assertFalse(self.root.augments.foreign_augments.simplecontainer.exists())

        container1 = self.root.augments.foreign_augments.simplelist.create(
            "a", "b"
        ).innercontainer.create()
        container2 = self.root.augments.foreign_augments.simplelist.create(
            "c", "d"
        ).innercontainer

        self.assertTrue(container1.exists())
        self.assertFalse(container2.exists())
        container1.destroy()
        self.assertFalse(container1.exists())

    def test_nonpresence_container(self):
        self.root.augments.foreign_augments.nonpresencecontainer.leaf = "a"
        with self.assertRaises(yangvoodoo.Errors.ValueNotMappedToTypeUnion) as err:
            self.root.augments.foreign_augments.nonpresencecontainer.leaf = "z"
        self.assertTrue(
            (
                "Unable to match the value 'z' to a yang type for path "
                "/integrationtest:augments/foreign-augments/foreign:nonpresencecontainer/leaf"
            )
            in str(err.exception)
        )
        self.assertEqual(
            self.root.augments.foreign_augments.nonpresencecontainer.leaf, "a"
        )
        self.root.augments.foreign_augments.nonpresencecontainer.leaf = 4
        self.assertEqual(
            self.root.augments.foreign_augments.nonpresencecontainer.leaf, "4"
        )

    def test_choice_case_and_empty_leaves(self):
        # Act
        list_element_ab = self.root.augments.foreign_augments.simplelist.create(
            "a", "b"
        )
        list_element_ab.innercontainer.mutuallyexclusive.first.one.create()

        self.assertTrue(
            list_element_ab.innercontainer.mutuallyexclusive.first.one.exists()
        )
        list_element_ab.innercontainer.mutuallyexclusive.second.two.create()
        self.assertFalse(
            list_element_ab.innercontainer.mutuallyexclusive.first.one.exists()
        )
        self.assertTrue(
            list_element_ab.innercontainer.mutuallyexclusive.second.two.exists()
        )

    def test_forming_of_paths(self):
        list_element2 = self.root.augments.foreign_augments.simplelist.create("A", "B")
        inner_container = list_element2.innercontainer
        empty_leaf = inner_container.mutuallyexclusive.first.one

        self.assertEqual(
            self.root.augments.foreign_augments.simplelist._node.real_data_path,
            "/integrationtest:augments/foreign-augments/foreign:simplelist",
        )
        self.assertEqual(
            self.root.augments.foreign_augments.simplelist._node.real_schema_path,
            "/integrationtest:augments/integrationtest:foreign-augments/foreign:simplelist",
        )
        self.assertEqual(
            list_element2.innercontainer.innerinner._node.real_data_path,
            (
                "/integrationtest:augments/foreign-augments/foreign:simplelist[key1='A'][key2='B']"
                "/innercontainer/innerinner"
            ),
        )
        self.assertEqual(
            list_element2.innercontainer.innerinner._node.real_schema_path,
            (
                "/integrationtest:augments/integrationtest:foreign-augments/foreign:simplelist"
                "/foreign:innercontainer/foreign:innerinner"
            ),
        )
        self.assertEqual(
            empty_leaf._node.real_data_path,
            (
                "/integrationtest:augments/foreign-augments/foreign:simplelist[key1='A'][key2='B']/innercontainer/one"
            ),
        )
        self.assertEqual(
            empty_leaf._node.real_schema_path,
            (
                "/integrationtest:augments/integrationtest:foreign-augments/foreign:simplelist/"
                "foreign:innercontainer/foreign:mutuallyexclusive/foreign:first/foreign:one"
            ),
        )
