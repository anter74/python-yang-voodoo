import libyang
import unittest
import yangvoodoo
from yangvoodoo.Common import IteratorToRaiseAnException, Utils
from yangvoodoo.Cache import Cache
from mock import Mock, patch


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess()

    def test_not_connected_exception_is_raised(self):
        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.commit()

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.uncreate('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.set('/xpath', 'value')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.gets_len('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.gets_sorted('/xpath', '/spath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.gets_unsorted('/xpath', '/spath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.gets('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.add('/xpath', 'value')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.remove('/xpath', 'value')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.has_item('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.get('/xpath', 'value')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.delete('/xpath')
        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.create('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.container('/xpath')
        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.create_container('/xpath')

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.refresh()

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.empty()

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.is_session_dirty()

        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            self.subject.validate()

        with self.assertRaises(ValueError):
            self.subject.connect('yang-model-that-does-not-exist.yang', yang_location='location that does not exist')

        self.subject.connect('integrationtest', yang_location='yang')
        self.assertTrue(self.subject.connected)
        self.subject.disconnect()
        self.assertFalse(self.subject.connected)
