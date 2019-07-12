import unittest
import yangvoodoo
from yangvoodoo.TemplateNinja import TemplateNinja
import yangvoodoo.stubdal
import time


class test_nested_list_stuff(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.session = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.session.connect('integrationtest')
        self.root = self.session.get_node()
        self.template_ninja = TemplateNinja()

    def assertExecutionTime(self, start_time, end_time, limit, threshold=0.75):
        if end_time - start_time > limit:
            self.fail("Execution time: %s wanted less than %s" % (end_time-start_time, limit))
        if (end_time - start_time) < limit * threshold:
            self.fail("TOO GOOD TO BE TRUE.. execution was %s%% of expeciton (actual: %s, execpted: %s)" % (threshold,
                                                                                                            end_time-start_time, limit))

    def test_add_one_entry_to_thirty_nested_lists(self):
        """
        This test is against sysrepo datastore, when we proxy read/requests from the proxy data store.
        """
        start_time = time.time()
        this_node = self.root.scaling
        for c in range(30):
            if c == 2:
                key = ('created%s' % (c), 'extrakey')
            else:
                key = ('created%s' % (c))
            this_node = this_node['scale%s' % (c)].create(key)

            if c > 1:
                this_node = this_node._parent.get(key)

        end_time = time.time()

        self.assertExecutionTime(start_time, end_time, 0.005, 0.6)

    def test_add_one_hundred_entries_to_thirty_nested_lists(self):
        """
        This test is against sysrepo datastore, when we proxy read/requests from the proxy data store.
        """
        start_time = time.time()
        for d in range(100):
            this_node = self.root.scaling
            for c in range(30):
                if c == 2:
                    key = ('created%sx%s' % (c, d), 'extrakey')
                else:
                    key = ('created%sx%s' % (c, d))
                this_node = this_node['scale%s' % (c)].create(key)
                if c > 1:
                    this_node = this_node._parent.get(key)

        end_time = time.time()

        self.assertExecutionTime(start_time, end_time, 0.39, 0.6)

    def test_add_three_thousand_entries_to_one_list(self):
        """
        This test is against sysrepo datastore, when we proxy read/requests from the proxy data store.
        """
        start_time = time.time()
        for d in range(3000):
            this_node = self.root.scaling
            for c in range(1):
                key = ('created%sx%s' % (c, d))
                this_node = this_node['scale%s' % (c)].create(key)
                if c > 1:
                    this_node = this_node._parent.get(key)

        end_time = time.time()
        self.assertExecutionTime(start_time, end_time, 0.17, 0.6)

    def test_change_leaf_3000_times(self):
        """
        This test is against sysrepo datastore, when we proxy read/requests from the proxy data store.
        """
        start_time = time.time()
        for d in range(3000):
            self.root.simpleleaf = "X" + str(d)
            _ = self.root.simpleleaf

        end_time = time.time()
        self.assertExecutionTime(start_time, end_time, 0.06, 0.6)

    # def texst_add_one_entry_to_thirty_nested_lists_with_template_ninja(self):
    #     """
    #     This test is against sysrepo datastore, when we proxy read/requests from the proxy data store.
    #     """
        # start_time = time.time()
        # this_node = self.root.scaling
        # for c in range(2):
        #     if c == 2:
        #         key = ('created%s' % (c), 'extrakey')
        #     else:
        #         key = ('created%s' % (c))
        #     this_node = this_node['scale%s' % (c)].create(key)
        #
        #     if c > 1:
        #         this_node = this_node._parent.get(key)
        #
        # end_time = time.time()
        #
        # #self.assertExecutionTime(start_time, end_time, 0.0055, 0.5)
        #
        # start_time = time.time()
        # xpaths = self.session.dump_xpaths()
        #
        # resulting_template = self.template_ninja.to_xmlstr_v2(xpaths)
        # end_time = time.time()
        # self.assertExecutionTime(start_time, end_time, 0.005, 0.6)
