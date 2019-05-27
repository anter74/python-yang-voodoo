import unittest
import yangvoodoo
import yangvoodoo.stubdal
import yangvoodoo.DiffEngine


class test_diff_engine(unittest.TestCase):

    def setUp(self):
        self.stub_a = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session_a = yangvoodoo.DataAccess(data_abstraction_layer=self.stub_a)
        self.session_a.connect('integrationtest')
        self.root_a = self.session_a.get_node()

        self.stub_b = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session_b = yangvoodoo.DataAccess(data_abstraction_layer=self.stub_b)
        self.session_b.connect('integrationtest')
        self.root_b = self.session_b.get_node()

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
                                                    filter="/integrationtest:diff")

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
