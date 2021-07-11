from yangvoodoo.Errors import NotConnect
from yangvoodoo.basedal import BaseDataAbstractionLayer
import libyang


class StubLyDataAbstractionLayer(BaseDataAbstractionLayer):

    """
    This data abstraction layer makes use of libyang's native data nodes to store data.

    It can easily be serialised and de-serialised out/in to XML or JSON format files with
    libyang itself. Today the existing stub makes use of the 'TemplateNinja' class to
    convert the XPATH's stored in a native python dictionary - there is however more
    processing involved in this that we can avoid with libyang.

    """

    DAL_ID = "StubLy"
    DAL_IN_MEMORY = False

    def connect(self, module, yang_location, tag="client", yang_ctx=None):
        if yang_ctx:
            self.libyang_ctx = yang_ctx
        elif yang_location:
            self.libyang_ctx = libyang.Context(yang_location)
        else:
            self.libyang_ctx = libyang.Context()
        self.libyang_ctx.load_module(module)
        self.module = module
        self.connected = True
        if not hasattr(self, "libyang_data"):
            self.libyang_data = libyang.DataTree(self.libyang_ctx)

    def disconnect(self):
        self.libyang_data = None
        self.libyang_ctx = None
        self.connected = False

    def validate(self, raise_exception=True):
        if not self.connected:
            raise NotConnect()
        try:
            return self.libyang_data.validate()
        except libyang.util.LibyangError as err:
            self.log.error("Invalid data tree: %s", str(err))
            if raise_exception:
                raise

        return False

    def container(self, xpath):
        """
        Returns if the presence container exists or not.

        xpath:     /integrationtest:simplecontainer
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("CONTAINER: %s", xpath)
        results = list(self.libyang_data.get_xpath(xpath))
        return bool(len(results))

    def create_container(self, xpath):
        """
        To create a presence container.

        xpath:     /integrationtest:simplecontainer
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("CREATE_CONTAINER: %s", xpath)
        self.libyang_data.set_xpath(xpath, None)

    def create(self, xpath, keys=None, values=None, module=None):
        """
        To create a list item in the list /simplelist

        xpath:    /integrationtest:simplelist[simplekey='sdf']
        keys:     ('simplekey',),
                    tuple of keys in the order defined within yang.
        values:   [('simpleval', 18)],
                    list of (value, valtype) tuples

        module:   integrationtest

        Returns a generator providing a list of XPATH values for each ListElement
            "/integrationtest:simplelist[simplekey='simpleval']",
            "/integrationtest:simplelist[simplekey='zsimpleval']",
            "/integrationtest:simplelist[simplekey='asimpleval']"

        If there are multiple keys the predicates are combined (e.g.)
            /integration:list[key1='val1'][key2='val2']
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("CREATE: %s (keys: %s) (values: %s)", xpath, keys, values)
        self.libyang_data.set_xpath(xpath, "")

    def uncreate(self, xpath):
        """
        To remove a list item from the list /simplelist with the key sf

        xpath:   /integrationtest:simplelist[simplekey='sf']
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("UNCREATE: %s", xpath)
        self.libyang_data.delete_xpath(xpath)

    def set(self, xpath, value, valtype=18, nodetype=4):
        if not self.connected:
            raise NotConnect()
        self.log.trace("SET: StubLy Datastore- %s => %s", xpath, value)
        self.libyang_data.set_xpath(xpath, value)

    def libyang_get_xpath(self, xpath):
        if not self.connected:
            raise NotConnect()
        self.log.trace("LIBYANG-GET: %s", xpath)
        return next(self.libyang_data.get_xpath(xpath))

    def gets(self, xpath):
        if not self.connected:
            raise NotConnect()
        self.log.trace("GETS: %s", xpath)
        for result in self.libyang_data.get_xpath(xpath):
            yield result.value

    def gets_len(self, xpath):
        """
        From a given XPATH list (not leaf-list) return the legnth of the list.

        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("COUNT: %s", xpath)
        return self.libyang_data.count_xpath(xpath)

    def add(self, xpath, value, valtype=10):
        """
        To create a leaf-list item in /morecomplex/leaflists/simple

        xpath:       /integrationtest:morecomplex/integrationtest:leaflists/integrationtest:simple
        value:       a
        valtype:     18

        Note: when creating a leaf list we do not provide the predciates.
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("ADD: %s => %s (valtype: %s)", xpath, value, valtype)
        self.libyang_data.set_xpath(xpath, value)

    def remove(self, xpath, value):
        if not self.connected:
            raise NotConnect()
        self.log.trace("REMOVE: %s %s", xpath, value)
        self.libyang_data.delete_xpath("%s[.='%s']" % (xpath, value))

    def get_raw_xpath(self, xpath, with_val=False):
        """
        Get raw xpath
        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        schema_path: /integrationtest:web/integrationtest:bands/integrationtest:gigs

        returns a generator.
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("GETS_RAW_XPATH: %s", xpath)
        for xpath in self.libyang_data.gets_xpath(xpath):
            if with_val:
                val = next(self.libyang_data.get_xpath(xpath))
                yield xpath, val.value
            else:
                yield xpath

    def gets_unsorted(self, xpath, schema_path, ignore_empty_lists=False):
        """
        To retrieve a list of XPATH's as a generator to each list element in the list.
        The order remains in the order the user added items to the list.

        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        schema_path: /integrationtest:web/integrationtest:bands/integrationtest:gigs

        returns a generator.
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace(
            "GETS_UNSORTED: %s (schema: %s, ignore_empty: %s)",
            xpath,
            schema_path,
            ignore_empty_lists,
        )
        yield from self.libyang_data.gets_xpath(xpath)

    def has_item(self, xpath):
        """
        Check to see if the list-element of a YANG list exists.

        xpath:          /integrationtest:simplelist[simplekey='b']
        """
        if not self.connected:
            raise NotConnect()
        self.log.trace("HAS_ITEM: %s", xpath)
        x = self.libyang_data.get_xpath(xpath)
        return len(list(x)) != 0

    def get(self, xpath, default_value=None):
        if not self.connected:
            raise NotConnect()
        self.log.trace("GET: StubLy Datastore- %s (default: %s)", xpath, default_value)
        try:
            val = next(self.libyang_data.get_xpath(xpath)).value
        except StopIteration:
            val = None

        if val is not None:
            return val

        if default_value:
            return default_value

        return None

    def delete(self, xpath):
        if not self.connected:
            raise NotConnect()
        self.log.trace("DELETE: %s", xpath)
        self.libyang_data.set_xpath(xpath, None)

    def dump_xpaths(self):
        """
        This is not supported because libyang does not give us a convenient data
        path. We can keep iterating around the children - but intermediate
        nodes (like, bronze, silver, gold would by default get yielded as their
        paths). We could add logic to find if they infact have values and skip
        them- but that is more work and we have dump() available now.
        """
        if not self.connected:
            raise NotConnect()
        return {node.xpath: node.value for node in self.libyang_data.dump_datanodes()}

    def empty(self):
        raise NotImplementedError("empty not implemented")

    def dump(self, filename, format=1):
        if not self.connected:
            raise NotConnect()
        self.log.trace("DUMP: %s (format: %s)", filename, format)
        self.libyang_data.dump(filename, format)

    def load(self, filename, format=1, trusted=False):
        if not self.connected:
            raise NotConnect()
        self.log.trace("LOAD: %s (format: %s)", filename, format)
        self.libyang_data.load(filename, format, trusted)

    def dumps(self, format=1):
        if not self.connected:
            raise NotConnect()
        self.log.trace("DUMPs: (format: %s)", format)
        return self.libyang_data.dumps(format)

    def loads(self, payload, format=1, trusted=False):
        if not self.connected:
            raise NotConnect()
        self.log.trace("LOADS: (format: %s)", format)
        self.libyang_data.loads(payload, format, trusted)

    def merges(self, filename, format=1, trusted=True):
        if not self.connected:
            raise NotConnect()
        self.log.trace("MERGE: (format: %s)", format)
        with open(filename) as fh:
            self.libyang_data.merges(fh.read(), format, trusted)

    def merges(self, payload, format=1, trusted=True):
        if not self.connected:
            raise NotConnect()
        self.log.trace("MERGES: (format: %s)", format)
        self.libyang_data.merges(payload, format, trusted)

    def advanced_merges(self, payload, format=1, trusted=True):
        if not self.connected:
            raise NotConnect()
        self.log.trace("ADVANCED-MERGES: (format: %s)", format)
        self.libyang_data.advancedmerge(payload, format, trusted)
