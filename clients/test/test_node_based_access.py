import unittest
import os
import yangvoodoo
import subprocess
import sysrepo as sr


process = subprocess.Popen(["bash"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
(out, err) = process.communicate('sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'.encode('UTF-8'))
if err:
    raise ValueError('Unable to import data\n%s\n%s' % (our, err))


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()
        self.subject.connect()
        self.root = self.subject.get_root('integrationtest')

    def test_root(self):
        self.assertEqual(repr(self.root), 'BlackArtRoot{} YANG Module: integrationtest')

        expected_children = ['bronze', 'container_and_lists', 'default', 'dirty_secret', 'empty',
                             'hyphen_leaf', 'imports_in_here', 'list_to_leafref_against', 'lista', 'morecomplex',
                             'numberlist', 'outsidelist', 'patternstr', 'psychedelia', 'quad', 'quarter',
                             'resolver', 'simplecontainer', 'simpleenum', 'simpleleaf', 'simplelist',
                             'thing_that_is_a_list_based_leafref', 'thing_that_is_leafref',
                             'thing_that_is_lit_up_for_A', 'thing_that_is_lit_up_for_B', 'thing_that_is_lit_up_for_C',
                             'thing_that_is_used_for_when', 'thing_to_leafref_against', 'twokeylist',
                             'underscoretests', 'whencontainer']

        self.assertEqual(dir(self.root), expected_children)

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
        self.assertEqual(repr(morecomplex), "BlackArtContainer{/integrationtest:morecomplex}")

        expected_children = ['extraboolean', 'extraboolean2', 'extraboolean3', 'inner', 'leaf2', 'leaf3', 'leaf4', 'nonconfig', 'percentage', 'superstar']
        self.assertEqual(dir(morecomplex), expected_children)

        self.assertEqual(morecomplex.leaf3, 12345)
        self.assertEqual(morecomplex.inner.leaf7, 'this-is-a-default')

        inner = morecomplex.inner
        self.assertEqual(repr(inner), 'BlackArtPresenceContainer{/integrationtest:morecomplex/integrationtest:inner} Exists')
        inner.leaf7 = 'this-is-not-a-default-now'
        self.assertEqual(morecomplex.inner.leaf7, 'this-is-not-a-default-now')
        self.assertTrue(morecomplex.inner.exists())

        simplecontainer = self.root.simplecontainer
        self.assertEqual(repr(simplecontainer), "BlackArtPresenceContainer{/integrationtest:simplecontainer} Does Not Exist")
        self.assertFalse(simplecontainer.exists())

        simplecontainer.create()
        self.assertTrue(simplecontainer.exists())

    def test_list(self):
        twolist = self.root.twokeylist
        self.assertEqual(repr(twolist), "BlackArtList{/integrationtest:twokeylist}")
        self.assertEqual(twolist._path, '/integrationtest:twokeylist')

        with self.assertRaises(yangvoodoo.Errors.ListWrongNumberOfKeys) as context:
            twolist.get('true')
        self.assertEqual(str(context.exception), 'The path: /integrationtest:twokeylist is a list requiring 2 keys but was given 1 keys')

        listelement = twolist.get(True, False)
        expected_children = ['primary', 'secondary', 'tertiary']
        self.assertEqual(repr(listelement), "BlackArtListElement{/integrationtest:twokeylist[primary='true'][secondary='false']}")
        self.assertEqual(dir(listelement), expected_children)
        self.assertEqual(listelement.tertiary, True)

        listelement.tertiary = False
        self.assertEqual(listelement.tertiary, False)

        listelement = twolist.get(True, True)
        expected_children = ['primary', 'secondary', 'tertiary']
        self.assertEqual(repr(listelement), "BlackArtListElement{/integrationtest:twokeylist[primary='true'][secondary='true']}")
        self.assertEqual(dir(listelement), expected_children)
        self.assertEqual(listelement.tertiary, True)

    def test_complex(self):
        outside = self.root.outsidelist.create('its cold outside')
        italian_numbers = outside.otherinsidelist.create('uno', 'due', 'tre')
        italian_numbers.language = 'italian'

        expected_children = ['language',  'otherlist1',  'otherlist2',  'otherlist3', 'otherlist4', 'otherlist5']
        self.assertEqual(repr(
            italian_numbers), "BlackArtListElement{/integrationtest:outsidelist[leafo='its cold outside']/integrationtest:otherinsidelist[otherlist1='uno'][otherlist2='due'][otherlist3='tre']}")
        self.assertEqual(dir(italian_numbers), expected_children)
        self.assertEqual(italian_numbers.language, 'italian')
        value = self.subject.get(
            "/integrationtest:outsidelist[leafo='its cold outside']/integrationtest:otherinsidelist[otherlist1='uno'][otherlist2='due'][otherlist3='tre']/language")
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
        underscore = self.root.underscoretests
        self.root.underscoretests.underscore_only
        self.root.underscoretests.hyphen_only

        # Note a node can either have hyphen's or underscore's. If we have both the basic
        # translation logic will fail. This can be seen from get_schema_for_path and __diir__
        with self.assertRaises(yangvoodoo.Errors.NonExistingNode) as context:
            self.root.underscoretests.underscore_and_hyphen
        self.assertEqual(str(context.exception),
                         "The path: /integrationtest:underscoretests/integrationtest:underscore_and_hyphen does not point of a valid schema node in the yang module")

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
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            x.band = 'list-keys-must-not-be-renamed'
        self.assertEqual(str(context.exception),
                         "1 Errors occured\nError 0: Value of the key can not be set (Path: /integrationtest:psychedelia/integrationtest:psychedelic-rock/integrationtest:bands[band='The 13th Floor Elevators']/integrationtest:band)\n")

        self.assertTrue(psychedelic_rock.stoner_rock.bands.get('Dead Meadow'))
        self.assertEqual(psychedelic_rock.stoner_rock.bands.get('Dead Meadow').albums.get('Old Growth').album, 'Old Growth')

        # We should already have Dead Meadow as a favourite in this category, and a must condition in yange
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            psychedelic_rock.stoner_rock.bands.get('Wooden Shjips').favourite = True
            self.subject.commit()
        self.assertEqual(str(context.exception),
                         "1 Errors occured\nError 0: Must condition \"count(current()/bands[favourite='true'])<2\" not satisfied. (Path: /integrationtest:psychedelia/psychedelic-rock/stoner-rock)\n")

        psychedelic_rock.stoner_rock.bands.get('Wooden Shjips').favourite = False

        with self.assertRaises(yangvoodoo.Errors.ListDoesNotContainElement) as context:
            psychedelic_rock.stoner_rock.bands.get('Taylor Swift').favourite = False
        self.assertEqual(str(context.exception),
                         "The list does not container the list element: /integrationtest:psychedelia/integrationtest:psychedelic-rock/integrationtest:stoner-rock/integrationtest:bands[band='Taylor Swift']")

        self.assertEqual(len(psychedelic_rock.noise_pop.shoe_gaze.bands), 2)
        self.assertEqual(repr(psychedelic_rock), "BlackArtContainer{/integrationtest:psychedelia/integrationtest:psychedelic-rock}")

    def test_iteration_of_lists(self):

        expected_answers = [
            "BlackArtListElement{/integrationtest:psychedelia/psychedelic-rock/stoner-rock/bands[band='Dead Meadow']}",
            "BlackArtListElement{/integrationtest:psychedelia/psychedelic-rock/stoner-rock/bands[band='Wooden Shjips']}"
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
        self.assertEqual(repr(element), "BlackArtListElement{/integrationtest:container-and-lists/integrationtest:numberkey-list[numberkey='3']}")
        element = number_list.get(4)
        self.assertEqual(repr(element), "BlackArtListElement{/integrationtest:container-and-lists/integrationtest:numberkey-list[numberkey='4']}")
        element = number_list.get(3)
        self.assertEqual(repr(element), "BlackArtListElement{/integrationtest:container-and-lists/integrationtest:numberkey-list[numberkey='3']}")

        for x in self.root.morecomplex.inner.list_that_will_stay_empty:
            self.fail('Did not expect any data in the list')

    def test_decimal64_and_typedef_resolving(self):
        self.root.morecomplex.superstar = 95.6
        self.assertEqual(int(self.root.morecomplex.superstar * 100), 9560)


"""sysrepocfg --export --format=xml --datastore=running integrationtest"""
