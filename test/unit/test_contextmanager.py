import unittest
import yangvoodoo
import yangvoodoo.stublydal


class test_new_stuff(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_context_manager(self):
        with yangvoodoo.DataAccess(
            yang_model="integrationtest",
            yang_location="yang",
        ) as root:
            root.simpleleaf = "a"
            self.assertEqual(
                root._context.dal.dumps(),
                '<simpleleaf xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">a</simpleleaf>',
            )
        with self.assertRaises(yangvoodoo.Errors.NotConnect):
            root.simpleleaf = "b"
