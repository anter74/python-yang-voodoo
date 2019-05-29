import unittest
import yangvoodoo
import subprocess

"""
Integration tests making use of python-yang-voodoo and the sysrepo backend.

The upside of this testing is we test the integration into sysrepo (which
gives us the ability to test complex yang validation dependant upon the
data (i.e. must, when, leafrefs).

The downside is that cleaning the datastore between every test becomes a
little expensive, so there is bleed between each individual test.
"""

command = 'sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'
process = subprocess.Popen(["bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
(out, err) = process.communicate(command.encode('UTF-8'))
if err:
    raise ValueError('Unable to import data\n%s\n%s' % (out, err))


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def test_simplest_leaf(self):
        self.assertEqual(self.root.simpleleaf, 'duke')

        self.root.simpleleaf = 'spirit'
        self.assertEqual(self.root.simpleleaf, 'spirit')

        self.root.simpleleaf = None
        # TODO: assert here that the leaf is not persisted in the sysrepo data.
        # (The data access here will give us None if something doesn't exist, but
        # it would also give us None if we have no lookup stuff)
        # Ideally we would have the data access into sysrepo completely mocked.
        self.assertEqual(self.root.simpleleaf, None)

        self.subject.commit()

    def test_containers(self):
        morecomplex = self.root.morecomplex
        self.assertEqual(repr(morecomplex), "VoodooContainer{/integrationtest:morecomplex}")

        self.assertEqual(morecomplex.leaf3, 12345)
        self.assertEqual(morecomplex.inner.leaf7, 'this-is-a-default')

        inner = morecomplex.inner
        self.assertEqual(repr(inner),
                         'VoodooPresenceContainer{/integrationtest:morecomplex/inner} Exists')
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

    def test_complex(self):
        outside = self.root.outsidelist.create('its cold outside')
        italian_numbers = outside.otherinsidelist.create('uno', 'due', 'tre')
        italian_numbers.language = 'italian'

        expected_children = ['language', 'otherlist1', 'otherlist2', 'otherlist3', 'otherlist4', 'otherlist5']
        self.assertEqual(repr(
            italian_numbers), ("VoodooListElement{/integrationtest:outsidelist[leafo='its cold outside']/"
                               "otherinsidelist"
                               "[otherlist1='uno'][otherlist2='due'][otherlist3='tre']}"))
        self.assertEqual(dir(italian_numbers), expected_children)
        self.assertEqual(italian_numbers.language, 'italian')
        value = self.subject.get(
            ("/integrationtest:outsidelist[leafo='its cold outside']/integrationtest:otherinsidelist"
             "[otherlist1='uno'][otherlist2='due'][otherlist3='tre']/language"))
        self.assertEqual(value, "italian")
        self.subject.commit()

    def test_undercore_translation(self):
        """
        This test produces the following XML
        <psychedelia xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
          <psychedelic-rock>
            <noise-pop>
              <dream-pop>
                <bands>
                  <band>Mazzy Star</band>
                  <favourite>true</favourite>
                </bands>
              </dream-pop>
              <shoe-gaze>
                <bands>
                  <band>Slowdive</band>
                  <favourite>false</favourite>
                </bands>
                <bands>
                  <band>The Brian Jonestown Massacre</band>
                  <favourite>true</favourite>
                </bands>
              </shoe-gaze>
              <bands>
                <band>The Jesus and Mary Chain</band>
              </bands>
            </noise-pop>
            <bands>
              <band>The 13th Floor Elevators</band>
            </bands>
          </psychedelic-rock>
        </psychedelia>
        """
        self.root.underscoretests.underscore_only
        self.root.underscoretests.hyphen_only

        # Note a node can either have hyphen's or underscore's. If we have both the basic
        # translation logic will fail. This can be seen from get_schema_for_path and __diir__
        with self.assertRaises(yangvoodoo.Errors.NonExistingNode) as context:
            self.root.underscoretests.underscore_and_hyphen
        self.assertEqual(str(context.exception),
                         ("The path: /integrationtest:underscoretests/integrationtest:underscore_and_hyphen does not "
                          "point of a valid schema node in the yang module"))

        psychedelia = self.root.psychedelia
        psychedelic_rock = psychedelia.psychedelic_rock
        x = psychedelic_rock.bands.create('The 13th Floor Elevators')
        x = psychedelic_rock.bands['The 13th Floor Elevators']
        psychedelic_rock.noise_pop.bands.create('The Jesus and Mary Chain')
        psychedelic_rock.noise_pop.dream_pop.bands.create('Mazzy Star').favourite = True
        psychedelic_rock.noise_pop.shoe_gaze.bands.create('Slowdive').favourite = False
        psychedelic_rock.noise_pop.shoe_gaze.bands.create('The Brian Jonestown Massacre').favourite = True

        """
        Note sysrepo gives us this protection for free in the backend.
        """
        with self.assertRaises(yangvoodoo.Errors.ListKeyCannotBeChanged) as context:
            x.band = 'list-keys-must-not-be-renamed'
        self.assertEqual(str(context.exception),
                         ("The list key: band for "
                          "/integrationtest:psychedelia/psychedelic-rock/bands[band='The 13th Floor Elevators']/band "
                          "cannot be changed"))

        self.assertTrue(psychedelic_rock.stoner_rock.bands.get('Dead Meadow'))
        self.assertEqual(psychedelic_rock.stoner_rock.bands.get('Dead Meadow').albums.get('Old Growth').album,
                         'Old Growth')

        # We should already have Dead Meadow as a favourite in this category, and a must condition in yange
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            psychedelic_rock.stoner_rock.bands.get('Wooden Shjips').favourite = True
            self.subject.commit()
        self.assertEqual(str(context.exception),
                         ("1 Errors occured\nError 0: Must condition \"count(current()/bands[favourite='true'])<2\" "
                          "not satisfied. (Path: /integrationtest:psychedelia/psychedelic-rock/stoner-rock)\n"))

        psychedelic_rock.stoner_rock.bands.get('Wooden Shjips').favourite = False

        with self.assertRaises(yangvoodoo.Errors.ListDoesNotContainElement) as context:
            psychedelic_rock.stoner_rock.bands.get('Taylor Swift').favourite = False
        self.assertEqual(str(context.exception),
                         ("The list does not contain the list element: "
                          "/integrationtest:psychedelia/psychedelic-rock/stoner-rock/"
                          "bands[band='Taylor Swift']"))

        self.assertEqual(len(psychedelic_rock.noise_pop.shoe_gaze.bands), 2)
        self.assertEqual(repr(psychedelic_rock),
                         "VoodooContainer{/integrationtest:psychedelia/psychedelic-rock}")

    def test_iteration_of_lists(self):

        expected_answers = [
            "VoodooListElement{/integrationtest:psychedelia/psychedelic-rock/stoner-rock/bands[band='Dead Meadow']}",
            "VoodooListElement{/integrationtest:psychedelia/psychedelic-rock/stoner-rock/bands[band='Wooden Shjips']}"
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

        # Test delete item
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
                          "numberkey-list[numberkey='3']}"))
        element = number_list.get(4)
        self.assertEqual(repr(element),
                         ("VoodooListElement{/integrationtest:container-and-lists/"
                          "numberkey-list[numberkey='4']}"))
        element = number_list.get(3)
        self.assertEqual(repr(element),
                         ("VoodooListElement{/integrationtest:container-and-lists/"
                          "numberkey-list[numberkey='3']}"))

        for x in self.root.morecomplex.inner.list_that_will_stay_empty:
            self.fail('Did not expect any data in the list')

        self.assertEqual(len(self.root.morecomplex.inner.list_that_will_stay_empty), 0)

        self.assertFalse('x' in self.root.morecomplex.inner.list_that_will_stay_empty)

    def test_decimal64_and_typedef_resolving(self):
        self.root.morecomplex.superstar = 95.6
        self.assertEqual(int(self.root.morecomplex.superstar * 100), 9560)

    def test_ietf(self):
        self.root.morecomplex.inner.ietf_inet_types.ip.address = 'ff::1'
        self.root.morecomplex.inner.ietf_inet_types.ip.address = '1.2.3.4'
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError):
            self.root.morecomplex.inner.ietf_inet_types.ip.address = '1.2.3.444'

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

    def test_leaf_lists(self):
        self.assertEqual(repr(self.root.morecomplex.leaflists.simple),
                         "VoodooLeafList{/integrationtest:morecomplex/leaflists/simple}")

        ll = self.root.morecomplex.leaflists.simple
        ll.create('A')
        ll.create('Z')
        ll.create('B')

        expected = ['A', 'Z', 'B']
        received = []
        for x in self.root.morecomplex.leaflists.simple:
            received.append(x)
        self.assertEqual(received, expected)

        self.assertEqual(3, len(self.root.morecomplex.leaflists.simple))

        self.assertFalse('non-existant' in self.root.morecomplex.leaflists.simple)
        self.assertTrue('A' in self.root.morecomplex.leaflists.simple)

        del self.root.morecomplex.leaflists.simple['A']

        self.assertEqual(2, len(self.root.morecomplex.leaflists.simple))
        self.assertFalse('A' in self.root.morecomplex.leaflists.simple)
