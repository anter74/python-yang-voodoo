# import libyang
# from yangvoodoo.Common import Utils, PlainIterator
# from mock import Mock
# import unittest
#
#
# class test_common(unittest.TestCase):
#
#     def setUp(self):
#         self.maxDiff = None
#
#     def test_convert_path_to_schema_path(self):
#         result = Utils.convert_path_to_schema_path("/path/abc/def[g='sdf']/xyz/sdf[fdsf='fg']/zzz", 'module')
#         expected_result = ("/module:path/module:abc/module:def/module:xyz/module:sdf/module:zzz",
#                            "/module:path/module:abc/module:def/module:xyz/module:sdf")
#         self.assertEqual(result, expected_result)
#
#         result = Utils.convert_path_to_schema_path("/path/abc/def[g='sdf']", 'module')
#         expected_result = ("/module:path/module:abc/module:def", "/module:path/module:abc")
#         self.assertEqual(result, expected_result)
#
#         result = Utils.convert_path_to_schema_path("/path/abc", 'module')
#         expected_result = ("/module:path/module:abc", "/module:path")
#         self.assertEqual(result, expected_result)
#
#         with self.assertRaises(ValueError) as context:
#             result = Utils.convert_path_to_schema_path("/path/abc/", 'module')
#         self.assertEqual(str(context.exception), "Path is not valid as it ends with a trailing slash. (/path/abc/)")
#
#     def test_convert_path_to_value_path(self):
#         result = Utils.convert_path_to_value_path("/path/abc/def[g='sdf']/xyz/sdf[fdsf='fg'][hhhh='hh']/zzz", 'module')
#         expected_result = ("/module:path/abc/def[g='sdf']/xyz/sdf[fdsf='fg'][hhhh='hh']/zzz", "/module:path/abc/def[g='sdf']/xyz/sdf")
#
#         self.assertEqual(result, expected_result)
#
#         result = Utils.convert_path_to_value_path("/path/abc/def[g='sdf'][h='sdf']/sdsd", 'module')
#         expected_result = ("/module:path/abc/def[g='sdf'][h='sdf']/sdsd", '/module:path/abc/def')
#         self.assertEqual(result, expected_result)
#
#         result = Utils.convert_path_to_value_path("/path/abc", 'module')
#         expected_result = ("/module:path/abc", "/module:path")
#         self.assertEqual(result, expected_result)
#
#         with self.assertRaises(ValueError) as context:
#             result = Utils.convert_path_to_value_path("/path/abc/", 'module')
#         self.assertEqual(str(context.exception), "Path is not valid as it ends with a trailing slash. (/path/abc/)")
