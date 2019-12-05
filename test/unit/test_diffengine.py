import unittest
import yangvoodoo
import yangvoodoo.stubdal
import yangvoodoo.DiffEngine


class test_diff_engine(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub_a = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session_a = yangvoodoo.DataAccess(data_abstraction_layer=self.stub_a)
        self.session_a.connect('integrationtest', yang_location='yang')
        self.root_a = self.session_a.get_node()

        self.stub_b = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session_b = yangvoodoo.DataAccess(data_abstraction_layer=self.stub_b)
        self.session_b.connect('integrationtest', yang_location='yang')
        self.root_b = self.session_b.get_node()

    def test_diff_engine_modifies_the_adds(self):
        self.root_a.simpleleaf = 'a'
        self.root_a.simpleenum = 'A'
        self.root_b.simpleleaf = 'b'
        self.root_b.bronze.silver.gold.platinum.deep = 'c'
        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b)

        # Assert
        self.assertEqual(list(differ.all()), [('/integrationtest:simpleleaf', 'a', 'b', 2),
                                              ('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1),
                                              ('/integrationtest:simpleenum', 'A', None, 3)])

        self.assertEqual(list(differ.modified()), [('/integrationtest:simpleleaf', 'a', 'b', 2)])
        self.assertEqual(list(differ.remove()), [('/integrationtest:simpleenum', 'A', None, 3)])
        self.assertEqual(list(differ.add()), [('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1)])

        self.assertEqual(list(differ.modify_then_add()), [('/integrationtest:simpleleaf', 'a', 'b', 2),
                                                          ('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1)])

    def test_diff_engine_removes_then_modifies_the_adds(self):
        self.root_a.simpleleaf = 'a'
        self.root_a.simpleenum = 'A'
        self.root_b.simpleleaf = 'b'
        self.root_b.bronze.silver.gold.platinum.deep = 'c'
        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b)

        # Assert
        self.assertEqual(list(differ.all()), [('/integrationtest:simpleleaf', 'a', 'b', 2),
                                              ('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1),
                                              ('/integrationtest:simpleenum', 'A', None, 3)])

        self.assertEqual(list(differ.modified()), [('/integrationtest:simpleleaf', 'a', 'b', 2)])
        self.assertEqual(list(differ.remove()), [('/integrationtest:simpleenum', 'A', None, 3)])
        self.assertEqual(list(differ.add()), [('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1)])

        self.assertEqual(list(differ.remove_modify_then_add()), [('/integrationtest:simpleenum', 'A', None, 3),
                                                                 ('/integrationtest:simpleleaf', 'a', 'b', 2),
                                                                 ('/integrationtest:bronze/silver/gold/platinum/deep', None, 'c', 1)])

    def test_diff_engine_with_simpleleaf(self):
        self.root_a.simpleleaf = 'a'
        self.root_b.simpleleaf = 'b'

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b)

        # Assert
        self.assertEqual(list(differ.all()), [('/integrationtest:simpleleaf', 'a', 'b', 2)])
    #

    def test_diff_engine_with_simpleleaf_filtered(self):
        self.root_a.bronze.silver.gold.platinum.deep = 'a'

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b, start_filter="/integrationtest:simplelist")

        # Assert
        self.assertEqual(list(differ.all()), [])

    def test_diff_engine_with_leaflist_version_modify(self):
        self.root_a.morecomplex.leaflists.simple.create('e')

        self.root_b.morecomplex.leaflists.simple.create('E')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [('/integrationtest:morecomplex/leaflists/simple', 'e', 'E', 2)]
        self.assertEqual(list(differ.all()), expected_results)
    #

    def test_diff_engine_with_leaflist_version1(self):
        self.root_a.morecomplex.leaflists.simple.create('e')

        self.root_b.morecomplex.leaflists.simple.create('e')
        self.root_b.morecomplex.leaflists.simple.create('f')
        self.root_b.morecomplex.leaflists.simple.create('g')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [
            ('/integrationtest:morecomplex/leaflists/simple', None, 'f', 1),
            ('/integrationtest:morecomplex/leaflists/simple', None, 'g', 1)
        ]
        self.assertEqual(list(differ.all()), expected_results)

    def test_diff_engine_with_leaflist_version2(self):
        self.root_a.morecomplex.leaflists.simple.create('e')
        self.root_a.morecomplex.leaflists.simple.create('d')

        self.root_b.morecomplex.leaflists.simple.create('e')
        self.root_b.morecomplex.leaflists.simple.create('f')
        self.root_b.morecomplex.leaflists.simple.create('g')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [
            ('/integrationtest:morecomplex/leaflists/simple', 'd', 'f', 2),
            ('/integrationtest:morecomplex/leaflists/simple', None, 'g', 1)
        ]
        self.assertEqual(list(differ.all()), expected_results)

    def test_diff_engine_with_leaflist_version3(self):
        self.root_a.morecomplex.leaflists.simple.create('e')
        self.root_a.morecomplex.leaflists.simple.create('d')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [
            ('/integrationtest:morecomplex/leaflists/simple', 'e', None, 3),
            ('/integrationtest:morecomplex/leaflists/simple', 'd', None, 3)
        ]
        self.assertEqual(list(differ.all()), expected_results)

    def test_diff_engine_with_leaflists(self):
        self.root_a.morecomplex.leaflists.simple.create('a')
        self.root_a.morecomplex.leaflists.simple.create('b')
        self.root_a.morecomplex.leaflists.simple.create('c')
        self.root_a.morecomplex.leaflists.simple.create('d')
        self.root_a.morecomplex.leaflists.simple.create('e')

        self.root_b.morecomplex.leaflists.simple.create('A')
        self.root_b.morecomplex.leaflists.simple.create('b')
        self.root_b.morecomplex.leaflists.simple.create('C')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [
            ('/integrationtest:morecomplex/leaflists/simple', 'a', 'A', 2),
            ('/integrationtest:morecomplex/leaflists/simple', 'c', 'C', 2),
            ('/integrationtest:morecomplex/leaflists/simple', 'e', None, 3),
            ('/integrationtest:morecomplex/leaflists/simple', 'd', None, 3)
        ]
        self.assertEqual(list(differ.all()), expected_results)

    def test_diff_engine_with_leaflists_justadd(self):
        self.root_b.morecomplex.leaflists.simple.create('A')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = [
            ('/integrationtest:morecomplex/leaflists/simple', None, 'A', 1),
        ]
        self.assertEqual(list(differ.all()), expected_results)

    def test_diff_engine(self):
        self.root_a.diff.deletes.a_list.create('Avril Lavigne')
        self.root_a.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm'
        self.root_a.diff.deletes.a_leaf = 'a'
        self.root_a.diff.modifies.a_leaf = 'original value'
        self.root_a.diff.modifies.a_2nd_leaf = 'original value2'
        self.root_a.simpleleaf = 'A'

        self.root_b.diff.modifies.a_leaf = 'new value'
        self.root_b.diff.modifies.a_2nd_leaf = 'new value2'
        self.root_b.diff.adds.a_list.create('Ghouls')
        self.root_b.diff.adds.a_list.create('Jim Lockey')
        self.root_b.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm!'
        self.root_b.diff.adds.a_leaf = 'b'
        self.root_b.diff.adds.a_2nd_leaf = 'b2'
        self.root_b.simpleleaf = 'B'

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.stub_a.stub_store, self.stub_b.stub_store,
                                                    start_filter="/integrationtest:diff")

        expected_results = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3)
        ]

        self.assertEqual(list(differ.all()), expected_results)

        expected_results = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
        ]
        self.assertEqual(list(differ.modified()), expected_results)

        expected_results = [
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3)
        ]
        self.assertEqual(list(differ.remove()), expected_results)

        expected_results = [
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
        ]
        self.assertEqual(list(differ.add()), expected_results)

    def test_filter(self):
        self.assertFalse(yangvoodoo.DiffEngine.DiffIterator.is_filtered('start-----', 'start', ''))
        self.assertFalse(yangvoodoo.DiffEngine.DiffIterator.is_filtered('------end', '', 'end'))
        self.assertFalse(yangvoodoo.DiffEngine.DiffIterator.is_filtered('start------end', 'start', 'end'))
        self.assertTrue(yangvoodoo.DiffEngine.DiffIterator.is_filtered('----------end', 'start', 'end'))
        self.assertTrue(yangvoodoo.DiffEngine.DiffIterator.is_filtered('start----------', 'start', 'end'))

    def test_diff_engine_with_filtering_sent_in_later(self):
        self.root_a.diff.deletes.a_list.create('Avril Lavigne')
        self.root_a.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm'
        self.root_a.diff.deletes.a_leaf = 'a'
        self.root_a.diff.modifies.a_leaf = 'original value'
        self.root_a.diff.modifies.a_2nd_leaf = 'original value2'
        self.root_a.simpleleaf = 'A'

        self.root_b.diff.modifies.a_leaf = 'new value'
        self.root_b.diff.modifies.a_2nd_leaf = 'new value2'
        self.root_b.diff.adds.a_list.create('Ghouls')
        self.root_b.diff.adds.a_list.create('Jim Lockey')
        self.root_b.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm!'
        self.root_b.diff.adds.a_leaf = 'b'
        self.root_b.diff.adds.a_2nd_leaf = 'b2'
        self.root_b.simpleleaf = 'B'

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.stub_a.stub_store, self.stub_b.stub_store)

        expected_results = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
            ('/integrationtest:simpleleaf', 'A', 'B', 2),
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3)
        ]

        self.assertEqual(list(differ.all()), expected_results)

        expected_results_when_filtering_on_all = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3)
        ]

        self.assertEqual(list(differ.all(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_all)
        self.assertEqual(list(differ.all(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_all)

    def test_diff_engine_with_filtering_sent_in_later(self):
        self.root_a.diff.deletes.a_list.create('Avril Lavigne')
        self.root_a.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm'
        self.root_a.diff.deletes.a_leaf = 'a'
        self.root_a.diff.modifies.a_leaf = 'original value'
        self.root_a.diff.modifies.a_2nd_leaf = 'original value2'
        self.root_a.simpleleaf = 'A'

        self.root_b.diff.modifies.a_leaf = 'new value'
        self.root_b.diff.modifies.a_2nd_leaf = 'new value2'
        self.root_b.diff.adds.a_list.create('Ghouls')
        self.root_b.diff.adds.a_list.create('Jim Lockey')
        self.root_b.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm!'
        self.root_b.diff.adds.a_leaf = 'b'
        self.root_b.diff.adds.a_2nd_leaf = 'b2'
        self.root_b.simpleleaf = 'B'

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.stub_a.stub_store, self.stub_b.stub_store)

        expected_results_when_filtering_on_return_method = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
        ]

        self.assertEqual(list(differ.modify_then_add(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)

        expected_results_when_filtering_on_return_method = [
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3),
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
        ]

        self.assertEqual(list(differ.remove_modify_then_add(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)

        expected_results_when_filtering_on_return_method = [
            ("/integrationtest:diff/modifies/a-list[listkey='Lissie']/listnonkey", 'earworm', 'earworm!', 2),
            ('/integrationtest:diff/modifies/a-leaf', 'original value', 'new value', 2),
            ('/integrationtest:diff/modifies/a-2nd-leaf', 'original value2', 'new value2', 2),
        ]

        self.assertEqual(list(differ.modified(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)
        self.assertEqual(list(differ.modified(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)

        expected_results_when_filtering_on_return_method = [
            ("/integrationtest:diff/adds/a-list[listkey='Ghouls']/listkey", None, 'Ghouls', 1),
            ("/integrationtest:diff/adds/a-list[listkey='Jim Lockey']/listkey", None, 'Jim Lockey', 1),
            ('/integrationtest:diff/adds/a-leaf', None, 'b', 1),
            ('/integrationtest:diff/adds/a-2nd-leaf', None, 'b2', 1),
        ]

        self.assertEqual(list(differ.add(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)

        expected_results_when_filtering_on_return_method = [
            ("/integrationtest:diff/deletes/a-list[listkey='Avril Lavigne']/listkey", 'Avril Lavigne', None, 3),
            ('/integrationtest:diff/deletes/a-leaf', 'a', None, 3),
        ]

        self.assertEqual(list(differ.remove(start_filter="/integrationtest:diff")), expected_results_when_filtering_on_return_method)

    def test_diff_engine_all_filtered(self):
        self.root_a.morecomplex.leaflists.simple.create('e')

        self.root_b.morecomplex.leaflists.simple.create('E')

        # Act
        differ = yangvoodoo.DiffEngine.DiffIterator(self.root_a, self.root_b,
                                                    start_filter="/integrationtest:morecomplex")

        # Assert
        expected_results = []
        self.assertEqual(list(differ.all(start_filter='/sdfsdf')), expected_results)
    #
