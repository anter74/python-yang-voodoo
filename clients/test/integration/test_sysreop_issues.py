import time
import unittest
import yangvoodoo
import subprocess

command = 'sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest'
process = subprocess.Popen(["bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
(out, err) = process.communicate(command.encode('UTF-8'))
if err:
    raise ValueError('Unable to import data\n%s\n%s' % (out, err))


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.subject = yangvoodoo.DataAccess(disable_proxy=False)
        self.subject.connect('integrationtest')
        self.root = self.subject.get_node()

    def test_classifier_example(self):
        rule1 = self.root.morecomplex.inner.classifier_example.rules.create(1)
        rule1.protocol = 'ip'
        rule1.ports.source.port = 234
        with self.assertRaises(yangvoodoo.Errors.BackendDatastoreError) as context:
            self.subject.validate()
        self.assertEqual(str(context.exception), """1 Errors occured
Error 0: When condition "../protocol!='ip'" not satisfied. (Path: /integrationtest:morecomplex/inner/classifier-example/rules[id='1']/ports)
""")

        rule1.protocol = 'tcp'
        self.subject.validate()

        self.subject.commit()
