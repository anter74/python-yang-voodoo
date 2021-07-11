import libyang
import unittest
import yangvoodoo
from yangvoodoo.Errors import (
    NodeAlreadyProvidedCannotChangeSchemaError,
    ValueDoesMatchEnumeration,
)
import yangvoodoo.stublydal


class test_deviations(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stublydal.StubLyDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect("integrationtest", yang_location="yang")

    def test_load_module_with_deviations(self):
        self.subject.add_module("test-deviation")
        self.root = self.subject.get_node()

        self.assertFalse(
            "to_make_not_supported" in dir(self.root.morecomplex.inner.deviant)
        )

        with self.assertRaises(ValueDoesMatchEnumeration):
            self.root.morecomplex.inner.deviant.a_string = (
                "ThisShoudlBeRejectedBecauseOfTheDeviation"
            )

        value = self.subject.get_extension(self.root, "info", "simpleenum")
        self.assertEqual(value, "this came from a deviation")

    def test_load_module_without_deviations(self):
        self.root = self.subject.get_node()

        self.assertTrue(
            "to_make_not_supported" in dir(self.root.morecomplex.inner.deviant)
        )

        self.root.morecomplex.inner.deviant.a_string = (
            "This is just a string becuase it is not deviated"
        )

        value = self.subject.get_extension(self.root, "info", "simpleenum")
        self.assertEqual(value, None)

    def test_load_module_after_node_used(self):
        self.root = self.subject.get_node()
        with self.assertRaises(NodeAlreadyProvidedCannotChangeSchemaError):
            self.subject.add_module("test-deviation")
