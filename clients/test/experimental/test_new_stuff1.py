import unittest
import yangvoodoo
import yangvoodoo.stubdal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_new_stuff(unittest.TestCase):

    def setUp(self):
        self.subject = yangvoodoo.Common.Utils
