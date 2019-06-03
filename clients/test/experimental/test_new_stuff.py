# import unittest
# import yangvoodoo
# import yangvoodoo.stubdal
#
#
# """
# This set of unit tests uses the stub backend datastore, which is not preseeded with
# any data.
# """
#
#
# class test_new_stuff(unittest.TestCase):
#
#     def setUp(self):
#         self.maxDiff = None
#         self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
#         self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
#         self.subject.connect('integrationtest')
#         self.root = self.subject.get_node()
#
#     def test_x(self):
#         self.root.underscoretests.deeper_down_here.simple = 'A'
