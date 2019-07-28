import libyang
import unittest
import yangvoodoo
import yangvoodoo.stubdal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_datastore_voodooentry_point(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.subject = yangvoodoo.basedal.BaseDataAbstractionLayer()

    def test_method_signatures_of_dal_does_not_change(self):
        """
        If the method signature changes below it is potentially  a breaking cahnge
        all DAL's need to be updated.

        Don't change the method signature!
        """
        with self.assertRaises(NotImplementedError):
            self.subject.connect('module', tag='client', yangdir=None)
        with self.assertRaises(NotImplementedError):
            self.subject.disconnect()
        with self.assertRaises(NotImplementedError):
            self.subject.validate()
        with self.assertRaises(NotImplementedError):
            self.subject.commit()
        with self.assertRaises(NotImplementedError):
            self.subject.create_container("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.create("xpath", keys=[], values=[], module=None)
        with self.assertRaises(NotImplementedError):
            self.subject.uncreate("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.set("xpath", "value", valtype=10, nodetype=4)
        with self.assertRaises(NotImplementedError):
            self.subject.gets_sorted("xpath", "schema_path", ignore_empty_lists=True)
        with self.assertRaises(NotImplementedError):
            self.subject.gets("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.add("xpath", "value", valtype=10)
        with self.assertRaises(NotImplementedError):
            self.subject.remove("xpath", "value")
        with self.assertRaises(NotImplementedError):
            self.subject.gets_unsorted("xpath", "schema_path", ignore_empty_lists=True)
        with self.assertRaises(NotImplementedError):
            self.subject.has_item("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.get("xpath", default_value="")
        with self.assertRaises(NotImplementedError):
            self.subject.refresh()
        with self.assertRaises(NotImplementedError):
            self.subject.is_session_dirty()
        with self.assertRaises(NotImplementedError):
            self.subject.has_datastore_changed()
        with self.assertRaises(NotImplementedError):
            self.subject.dump_xpaths()
        with self.assertRaises(NotImplementedError):
            self.subject.empty()
        with self.assertRaises(NotImplementedError):
            self.subject.container("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.delete("xpath")
        with self.assertRaises(NotImplementedError):
            self.subject.gets_len("xpath")
        self.subject.setup_root()
        self.subject._initdal()
        """
        If the method signature changes below it is potentially  a breaking cahnge
        all DAL's need to be updated.

        Don't change the method signature!
        """
