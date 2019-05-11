import unittest
from mock import Mock
import os
import yangvoodoo
import subprocess
from yangvoodoo import Types

# process = subprocess.Popen(["bash"],
#                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
# (out, err) = process.communicate('sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'.encode('UTF-8'))
# if err:
#     raise ValueError('Unable to import data\n%s\n%s' % (our, err))
#


class test_sysrepodal(unittest.TestCase):

    def setUp(self):
        self.subject = yangvoodoo.sysrepodal.SysrepoDataAbstractionLayer()
        self.subject.session = Mock()

    def test_handle_error_no_subscribers(self):
        error_mock = Mock()
        error_mock.xpath.return_value = "/path"
        error_mock.message.return_value = "The node is not enabled in running datastore"
        errors_mock = Mock()
        errors_mock.error_cnt.return_value = 1
        errors_mock.error.return_value = error_mock
        self.subject.session.get_last_errors = Mock(return_value=errors_mock)

        with self.assertRaises(yangvoodoo.Errors.SubscriberNotEnabledOnBackendDatastore) as context:
            self.subject._handle_error('/path', 'err')
        self.assertEqual(str(context.exception), "There is no subscriber connected able to process data for the following path.\n /path")

    def test_handle_error_no_other_backend_error(self):
        error_mock = Mock()
        error_mock.xpath.return_value = "/path"
        error_mock.message.return_value = "Someother stuff went wrong"
        errors_mock = Mock()
        errors_mock.error_cnt.return_value = 1
        errors_mock.error.return_value = error_mock
        self.subject.session.get_last_errors = Mock(return_value=errors_mock)

        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            self.subject._handle_error('/path', 'err')
        self.assertEqual(str(context.exception), "1 Errors occured\nError 0: Someother stuff went wrong (Path: /path)\n")
