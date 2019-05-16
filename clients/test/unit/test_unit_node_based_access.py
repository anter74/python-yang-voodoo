import unittest
import yangvoodoo
import yangvoodoo.stubdal


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

    def test_root(self):
        self.assertEqual(repr(self.root), 'VoodooRoot{} YANG Module: integrationtest')

        expected_children = ['bronze', 'container_and_lists', 'default', 'dirty_secret', 'empty',
                             'hyphen_leaf', 'imports_in_here', 'list_to_leafref_against', 'lista', 'morecomplex',
                             'numberlist', 'outsidelist', 'patternstr', 'psychedelia', 'quad', 'quarter',
                             'resolver', 'simplecontainer', 'simpleenum', 'simpleleaf', 'simplelist',
                             'thing_that_is_a_list_based_leafref', 'thing_that_is_leafref',
                             'thing_that_is_lit_up_for_A', 'thing_that_is_lit_up_for_B', 'thing_that_is_lit_up_for_C',
                             'thing_that_is_used_for_when', 'thing_to_leafref_against', 'twokeylist',
                             'underscoretests', 'validator', 'web', 'whencontainer']

        self.assertEqual(dir(self.root), expected_children)

    def test_simplest_leaf(self):
        self.root.simpleleaf = 'spirit'
        self.assertEqual(self.root.simpleleaf, 'spirit')

        self.root.simpleleaf = None
        self.assertEqual(self.root.simpleleaf, None)

        self.subject.commit()

    def test_containers(self):
        morecomplex = self.root.morecomplex
        self.assertEqual(repr(morecomplex), "VoodooContainer{/integrationtest:morecomplex}")

        expected_children = ['extraboolean', 'extraboolean2', 'extraboolean3', 'inner', 'leaf2', 'leaf3', 'leaf4',
                             'nonconfig', 'percentage', 'superstar']
        self.assertEqual(dir(morecomplex), expected_children)

        inner = morecomplex.inner.create()
        self.assertEqual(repr(inner),
                         'VoodooPresenceContainer{/integrationtest:morecomplex/integrationtest:inner} Exists')
        inner.leaf7 = 'this-is-not-a-default-now'
        self.assertEqual(morecomplex.inner.leaf7, 'this-is-not-a-default-now')
        self.assertTrue(morecomplex.inner.exists())

        simplecontainer = self.root.simplecontainer
        self.assertEqual(repr(simplecontainer),
                         "VoodooPresenceContainer{/integrationtest:simplecontainer} Does Not Exist")
        self.assertFalse(simplecontainer.exists())

        simplecontainer.create()
        self.assertTrue(simplecontainer.exists())

    def test_list(self):
        # Build
        self.root.twokeylist.create(True, False).tertiary = True
        self.root.twokeylist.create(True, True).tertiary = True

        # Act
        twolist = self.root.twokeylist
        self.assertEqual(repr(twolist), "VoodooList{/integrationtest:twokeylist}")
        self.assertEqual(twolist._path, '/integrationtest:twokeylist')

        with self.assertRaises(yangvoodoo.Errors.ListWrongNumberOfKeys) as context:
            twolist.get('true')
        self.assertEqual(str(context.exception),
                         'The path: /integrationtest:twokeylist is a list requiring 2 keys but was given 1 keys')

        listelement = twolist.get(True, False)
        expected_children = ['primary', 'secondary', 'tertiary']
        self.assertEqual(repr(listelement),
                         "VoodooListElement{/integrationtest:twokeylist[primary='true'][secondary='false']}")
        self.assertEqual(dir(listelement), expected_children)
        self.assertEqual(listelement.tertiary, True)

        listelement.tertiary = False
        self.assertEqual(listelement.tertiary, False)

        listelement = twolist.get(True, True)
        expected_children = ['primary', 'secondary', 'tertiary']
        self.assertEqual(repr(listelement),
                         "VoodooListElement{/integrationtest:twokeylist[primary='true'][secondary='true']}")
        self.assertEqual(dir(listelement), expected_children)
        self.assertEqual(listelement.tertiary, True)

    def test_iteration_of_lists(self):
        # Build
        self.root.psychedelia.psychedelic_rock.stoner_rock.bands.create('Dead Meadow')
        self.root.psychedelia.psychedelic_rock.stoner_rock.bands.create('Wooden Shjips')
        self.root.twokeylist.create(True, True)

        # Act.
        expected_answers = [
            ("VoodooListElement{/integrationtest:psychedelia/integrationtest:psychedelic-rock/"
             "integrationtest:stoner-rock/integrationtest:bands[band='Dead Meadow']}"),
            ("VoodooListElement{/integrationtest:psychedelia/integrationtest:psychedelic-rock/"
             "integrationtest:stoner-rock/integrationtest:bands[band='Wooden Shjips']}")
        ]
        for band in self.root.psychedelia.psychedelic_rock.stoner_rock.bands:
            expected_answer = expected_answers.pop(0)
            self.assertEqual(repr(band), expected_answer)

        self.assertTrue("Dead Meadow" in self.root.psychedelia.psychedelic_rock.stoner_rock.bands)
        self.assertFalse("Taylor Swift" in self.root.psychedelia.psychedelic_rock.stoner_rock.bands)

        twolist = self.root.twokeylist
        self.assertTrue((True, True) in twolist)

        other_list = self.root.container_and_lists.multi_key_list
        self.assertFalse(('A', 'Z') in other_list)

        item = other_list.create('A', 'Z')
        self.assertTrue(('A', 'Z') in other_list)

        # Test __getitem__
        self.assertEqual(repr(other_list['A', 'Z']), repr(item))
        #
        # # Test delete item
        self.assertEqual(len(other_list), 1)
        other_list.create('thing', 'todelete').inner.C = 'soon'
        self.assertEqual(len(other_list), 2)
        self.assertEqual(other_list['thing', 'todelete'].inner.C, 'soon')

        del other_list['thing', 'todelete']
        self.assertEqual(len(other_list), 1)

        number_list = self.root.container_and_lists.numberkey_list
        element = number_list.create(3)
        number_list.create(4)
        self.assertEqual(repr(element),
                         ("VoodooListElement{/integrationtest:container-and-lists/"
                          "integrationtest:numberkey-list[numberkey='3']}"))
        element = number_list.get(4)
        self.assertEqual(repr(element),
                         ("VoodooListElement{/integrationtest:container-and-lists/"
                          "integrationtest:numberkey-list[numberkey='4']}"))
        element = number_list.get(3)
        self.assertEqual(repr(element),
                         ("VoodooListElement{/integrationtest:container-and-lists/"
                          "integrationtest:numberkey-list[numberkey='3']}"))

        for x in self.root.morecomplex.inner.list_that_will_stay_empty:
            self.fail('Did not expect any data in the list')

        self.assertEqual(len(self.root.morecomplex.inner.list_that_will_stay_empty), 0)

        self.assertFalse('x' in self.root.morecomplex.inner.list_that_will_stay_empty)

    def test_decimal64_and_typedef_resolving(self):
        self.root.morecomplex.superstar = 95.6
        self.assertEqual(int(self.root.morecomplex.superstar * 100), 9560)

    def test_parents_and_help_text(self):
        great_grandparent = self.root.bronze.silver.gold.platinum._parent._parent._parent

        self.assertEqual(repr(great_grandparent), "VoodooContainer{/integrationtest:bronze}")
        self.assertEqual(self.subject.help(great_grandparent), "The metallics are used to test container nesting")

        list_element = self.root.simplelist.create('newlistitem')
        self.assertEqual(repr(list_element._parent), "VoodooList{/integrationtest:simplelist}")

        obj = self.root.bronze.silver._parent.silver._parent.silver.gold
        self.assertEqual(repr(obj),
                         "VoodooContainer{/integrationtest:bronze/integrationtest:silver/integrationtest:gold}")

    def test_lists_ordering(self):
        self.root.simplelist.create('A')
        self.root.simplelist.create('Z')
        self.root.simplelist.create('middle')
        self.root.simplelist.create('M')

        # GETS is based on user defined order
        # Act
        items = list(self.root.simplelist)
        # Assert
        expected_results = ["VoodooListElement{/integrationtest:simplelist[simplekey='A']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='Z']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='middle']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='M']}"]

        for i in range(len(items)):
            self.assertEqual(repr(items[i]), expected_results[i])

        # GETS_SORTED is based on xpath sorted order
        # Act
        items = list(self.root.simplelist._xpath_sorted)

        # Assert
        expected_results = ["VoodooListElement{/integrationtest:simplelist[simplekey='A']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='M']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='Z']}",
                            "VoodooListElement{/integrationtest:simplelist[simplekey='middle']}"]

        for i in range(len(items)):
            self.assertEqual(repr(items[i]), expected_results[i])

        outside_a = self.root.outsidelist.create('a')
        outside_a.insidelist.create('1')
        outside_a.insidelist.create('2')
        outside_b = self.root.outsidelist.create('b')
        outside_b.insidelist.create('3')
        self.assertEqual(len(outside_a.insidelist), 2)
        self.assertEqual(len(outside_b.insidelist), 1)
