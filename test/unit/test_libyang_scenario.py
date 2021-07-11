import unittest
import yangvoodoo
import yangvoodoo.stublydal
from yangvoodoo.DiffEngine import DiffIterator

"""
This tests the integration of libyang based stubs.
"""


class test_new_stuff(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        self.stubly = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly)
        self.subject.connect("integrationtest", yang_location="yang")
        yang_ctx = self.subject.yang_ctx
        self.root = self.subject.get_node()

        self.stubly2 = yangvoodoo.stublydal.StubLyDataAbstractionLayer(log_level=2)
        self.subject2 = yangvoodoo.DataAccess(data_abstraction_layer=self.stubly2)
        self.subject2.connect(
            "integrationtest", yang_location="yang", yang_ctx=yang_ctx
        )
        self.root2 = self.subject2.get_node()

    def test_internal(self):
        self.assertEqual(self.subject.yang_ctx, self.subject2.yang_ctx)

    def test_scenario(self):
        self.root.simpleleaf = "NonEmptyDoc"

        self.root2.diff.adds.a_leaf = "A Leaf Value"
        self.root2.diff.adds.a_2nd_leaf = "A second leaf"
        self.root2.diff.adds.a_list.create("KEY1").listnonkey = "VAL1"
        self.root2.diff.adds.a_list.create("KEY2").listnonkey = "VAL2"
        self.root2.diff.adds.a_list.create("KEY3").listnonkey = "VAL3"
        self.root2.diff.adds.a_leaf_list.create("A")
        self.root2.diff.adds.a_leaf_list.create("B")
        self.root2.diff.adds.a_leaf_list.create("C")
        self.root2.diff.adds.presence_container.create()
        self.root2.diff.adds.empty_leaf.create()
        self.root2.diff.adds.boolean = True

        result = self.subject2.dumps()
        expected_result = (
            '<diff xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><adds>'
            "<a-leaf>A Leaf Value</a-leaf><a-2nd-leaf>A second leaf</a-2nd-leaf><a-list>"
            "<listkey>KEY1</listkey><listnonkey>VAL1</listnonkey></a-list><a-list>"
            "<listkey>KEY2</listkey><listnonkey>VAL2</listnonkey></a-list><a-list>"
            "<listkey>KEY3</listkey><listnonkey>VAL3</listnonkey></a-list>"
            "<a-leaf-list>A</a-leaf-list><a-leaf-list>B</a-leaf-list>"
            "<a-leaf-list>C</a-leaf-list><presence-container/><empty-leaf/>"
            "<boolean>true</boolean></adds></diff>"
        )
        self.assertEqual(result, expected_result)

        result = self.subject2.dumps(2)
        expected_result = (
            '{"integrationtest:diff":{"adds":{"a-leaf":"A Leaf Value",'
            '"a-2nd-leaf":"A second leaf","a-list":[{"listkey":"KEY1",'
            '"listnonkey":"VAL1"},{"listkey":"KEY2","listnonkey":"VAL2"},'
            '{"listkey":"KEY3","listnonkey":"VAL3"}],"a-leaf-list":["A","B","C"],'
            '"presence-container":{},"empty-leaf":[null],"boolean":true}}}'
        )

        self.assertEqual(result, expected_result)

        """
        Note: this is the moment we realised that libyang diff's are a bit problematic because
        it tracks insertion order :-(

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
        """

        xpaths = self.subject.dump_xpaths()

        xpaths2 = self.subject2.dump_xpaths()

        # Assert
        expected_xpaths = {"/integrationtest:simpleleaf": "NonEmptyDoc"}

        expected_xpaths2 = {
            "/integrationtest:diff": "",
            "/integrationtest:diff/adds": "",
            "/integrationtest:diff/adds/a-2nd-leaf": "A second leaf",
            "/integrationtest:diff/adds/a-leaf": "A Leaf Value",
            "/integrationtest:diff/adds/a-leaf-list[.='A']": "A",
            "/integrationtest:diff/adds/a-leaf-list[.='B']": "B",
            "/integrationtest:diff/adds/a-leaf-list[.='C']": "C",
            "/integrationtest:diff/adds/a-list[listkey='KEY1']/listkey": "KEY1",
            "/integrationtest:diff/adds/a-list[listkey='KEY1']/listnonkey": "VAL1",
            "/integrationtest:diff/adds/a-list[listkey='KEY2']/listkey": "KEY2",
            "/integrationtest:diff/adds/a-list[listkey='KEY2']/listnonkey": "VAL2",
            "/integrationtest:diff/adds/a-list[listkey='KEY3']/listkey": "KEY3",
            "/integrationtest:diff/adds/a-list[listkey='KEY3']/listnonkey": "VAL3",
            "/integrationtest:diff/adds/boolean": True,
            "/integrationtest:diff/adds/empty-leaf": "",
            "/integrationtest:diff/adds/presence-container": "",
        }

        self.assertEqual(xpaths, expected_xpaths)
        self.assertEqual(xpaths2, expected_xpaths2)

        differ = yangvoodoo.DiffEngine.DiffIterator(xpaths, xpaths2)

        expected_diff_results = {
            "/integrationtest:diff": (None, "", 1),
            "/integrationtest:diff/adds": (None, "", 1),
            "/integrationtest:diff/adds/a-leaf": (None, "A Leaf Value", 1),
            "/integrationtest:diff/adds/a-2nd-leaf": (None, "A second leaf", 1),
            "/integrationtest:diff/adds/a-list[listkey='KEY1']/listkey": (
                None,
                "KEY1",
                1,
            ),
            "/integrationtest:diff/adds/a-list[listkey='KEY1']/listnonkey": (
                None,
                "VAL1",
                1,
            ),
            "/integrationtest:diff/adds/a-list[listkey='KEY2']/listkey": (
                None,
                "KEY2",
                1,
            ),
            "/integrationtest:diff/adds/a-list[listkey='KEY2']/listnonkey": (
                None,
                "VAL2",
                1,
            ),
            "/integrationtest:diff/adds/a-list[listkey='KEY3']/listkey": (
                None,
                "KEY3",
                1,
            ),
            "/integrationtest:diff/adds/a-list[listkey='KEY3']/listnonkey": (
                None,
                "VAL3",
                1,
            ),
            "/integrationtest:diff/adds/a-leaf-list[.='A']": (None, "A", 1),
            "/integrationtest:diff/adds/a-leaf-list[.='B']": (None, "B", 1),
            "/integrationtest:diff/adds/a-leaf-list[.='C']": (None, "C", 1),
            "/integrationtest:diff/adds/empty-leaf": (None, "", 1),
            "/integrationtest:diff/adds/boolean": (None, True, 1),
            "/integrationtest:diff/adds/presence-container": (None, "", 1),
            "/integrationtest:simpleleaf": ("NonEmptyDoc", None, 3),
        }

        # Unfortunately libyang based stub's do not appear to be order determinsitic.
        for (xpath, oldval, newval, op) in list(differ.all()):
            if xpath not in expected_diff_results:
                self.fail("%s is not expected but received in the diff" % (xpath))
            (expected_oldval, expected_newval, expected_op) = expected_diff_results[
                xpath
            ]
            self.assertEqual(
                "%s_%s" % (xpath, expected_oldval), "%s_%s" % (xpath, oldval)
            )
            self.assertEqual(
                "%s_%s" % (xpath, expected_newval), "%s_%s" % (xpath, newval)
            )
            self.assertEqual("%s_%s" % (xpath, expected_op), "%s_%s" % (xpath, op))
            del expected_diff_results[xpath]

        if len(expected_diff_results):
            self.fail(
                "Not all diff results were found in the diff\n%s"
                % (expected_diff_results)
            )

    def test_json(self):
        list_element = self.root.listgroup1.create("A", "B", 500)
        list_element.contain.leafa = "ABC"
        list_element.contain.leafb = 4
        # Act
        result = self.subject.dumps(2)

        # Act
        expected_result = (
            '{"integrationtest:listgroup1":[{"key1":"A","key2":"B","key3":"500",'
            '"contain":{"leafa":"ABC","leafb":4}}]}'
        )
        self.assertEqual(result, expected_result)

    def test_json2(self):
        # Act
        json = (
            '{"integrationtest:listgroup1":[{"key1":"A","key2":"B","key3":"500",'
            '"contain":{"leafa":"ABCDEF","leafb":44}}]}'
        )
        self.subject.loads(json, 2)

        list_element = self.root.listgroup1.get("A", "B", 500)

        # Assert
        expected_result = "VoodooListElement{/integrationtest:listgroup1[key1='A'][key2='B'][key3='500']}"
        self.assertEqual(len(self.root.listgroup1), 1)
        self.assertEqual(repr(list_element), expected_result)
        self.assertEqual(list_element.contain.leafa, "ABCDEF")
        self.assertEqual(list_element.contain.leafb, 44)

    def test_multiple_json_loads(self):
        # Act
        json = (
            '{"integrationtest:listgroup1":[{"key1":"A","key2":"B","key3":"500",'
            '"contain":{"leafa":"ABCDEF","leafb":44}}]}'
        )
        self.subject.loads(json, 2)

        list_element = self.root.listgroup1.get("A", "B", 500)

        # Assert
        expected_result = "VoodooListElement{/integrationtest:listgroup1[key1='A'][key2='B'][key3='500']}"
        self.assertEqual(len(self.root.listgroup1), 1)
        self.assertEqual(repr(list_element), expected_result)
        self.assertEqual(list_element.contain.leafa, "ABCDEF")
        self.assertEqual(list_element.contain.leafb, 44)

        # Act 2
        json = (
            '{"integrationtest:listgroup1":[{"key1":"aa","key2":"bb","key3":"500",'
            '"contain":{"leafa":"abcdef","leafb":444}}]}'
        )
        self.subject.merges(json, 2)

        list_element1 = self.root.listgroup1.get("A", "B", 500)
        list_element2 = self.root.listgroup1.get("aa", "bb", 500)

        expected_result1 = "VoodooListElement{/integrationtest:listgroup1[key1='A'][key2='B'][key3='500']}"
        expected_result2 = "VoodooListElement{/integrationtest:listgroup1[key1='aa'][key2='bb'][key3='500']}"

        self.assertEqual(len(self.root.listgroup1), 2)
        self.assertEqual(repr(list_element1), expected_result1)
        self.assertEqual(repr(list_element2), expected_result2)
        self.assertEqual(list_element.contain.leafa, "ABCDEF")
        self.assertEqual(list_element.contain.leafb, 44)

    def test_destroy_presence_container(self):
        self.root.validator.mandatories.create()

        # Assert
        result = self.subject.dumps()
        expected_result = (
            '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">'
            "<mandatories/></validator>"
        )
        self.assertEqual(result, expected_result)

        # Second Act
        self.root.validator.mandatories.destroy()

        # Assert
        result = self.subject.dumps()
        expected_result = '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"/>'
        self.assertEqual(result, expected_result)

    def test_destroy_presence_container_with_child_data(self):
        self.root.validator.mandatories.create()
        self.root.validator.mandatories.this_is_mandatory = "bob"
        # Assert
        result = self.subject.dumps()
        expected_result = (
            '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">'
            "<mandatories><this-is-mandatory>bob</this-is-mandatory></mandatories></validator>"
        )
        self.assertEqual(result, expected_result)

        # Second Act
        self.root.validator.mandatories.destroy()

        # Assert
        result = self.subject.dumps()
        expected_result = '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"/>'
        self.assertEqual(result, expected_result)

    def test_deleting_an_empty_node(self):
        self.root.validator.types.void.create()

        # Assert
        result = self.subject.dumps()
        expected_result = (
            '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">'
            "<types><void/></types></validator>"
        )
        self.assertEqual(result, expected_result)

        # Second Act
        self.root.validator.types.void.remove()

        # Assert
        result = self.subject.dumps()
        expected_result = (
            '<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">'
            "<types/></validator>"
        )
        self.assertEqual(result, expected_result)
