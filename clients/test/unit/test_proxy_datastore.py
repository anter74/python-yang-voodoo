import unittest
import yangvoodoo
import yangvoodoo.stubdal
import yangvoodoo.proxydal
from mock import Mock


class test_proxy_datastore(unittest.TestCase):

    maxDiff = 50000

    def setUp(self):
        self.maxDiff = None
        self.real = Mock()
        self.real.DAL_ID = "MockDAL"
        self.subject = yangvoodoo.proxydal.ProxyDataAbstractionLayer(self.real)

    def test_reading(self):
        """
        Note: these tests use side_effects which help enforce the underlying
        datastore method is not called multiple types.
        """

        self.real.get.side_effect = ['ABC']

        # Uncached
        self.assertFalse('/xpath' in self.subject.value_cached)
        result = self.subject.get('/xpath')
        self.assertEqual(result, 'ABC')
        self.assertTrue('/xpath' in self.subject.value_cached)

        # Cached
        result = self.subject.get('/xpath')
        self.assertEqual(result, 'ABC')

        # Drop cache
        self.subject.refresh()
        self.assertFalse('/xpath' in self.subject.value_cached)

    def test_reading_lists(self):
        """
        Note: these tests use side_effects which help enforce the underlying
        datastore method is not called multiple types.
        """

        self.real.gets_unsorted.side_effect = [["/listxpath[key='value'][key2='value2']"]]

        # Uncached
        self.assertFalse('/listxpath' in self.subject.unsorted_cached)
        result = self.subject.gets_unsorted('/listxpath')
        self.assertEqual(list(result), ["/listxpath[key='value'][key2='value2']"])

        # Cached
        self.assertTrue('/listxpath' in self.subject.unsorted_cached)
        result = self.subject.gets_unsorted('/listxpath')
