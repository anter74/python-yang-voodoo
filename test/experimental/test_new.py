import libyang
import unittest
import yangvoodoo
import yangvoodoo.stublydal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_new(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stublydal.StubLyDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub, disable_proxy=True)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()
