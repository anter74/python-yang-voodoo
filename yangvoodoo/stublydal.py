from typing import Generator, Tuple
from yangvoodoo.Errors import InvalidValueError, NotConnect, PathIsNotALeaf
from yangvoodoo.basedal import BaseDataAbstractionLayer
from yangvoodoo.Common import PlainObject, Types, Utils, YangNode

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
        """
        Validate the pending changes against the data in the backend datatstore without actually
        committing the data. The full set of rules within the YANG model/datatstore must be
        checked such that a user calling validate(), commit() in short sucession should get a
        failure to commit.

        Depending on the datastore invalid data may return an exception.

        returns: True or False
        """
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
        # self.log.trace("CONTAINER: %s", xpath)
        results = list(self.libyang_data.get_xpath(xpath))
        return bool(len(results))

    def create_container(self, xpath):
        """
        To create a presence container.

        xpath:     /integrationtest:simplecontainer
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("CREATE_CONTAINER: %s", xpath)
        self.libyang_data.set_xpath(xpath, None)

    def get_attribute(self, xpath: str, attribute_name: str) -> str:
        """
        Get attribute from the data at XPATH - if the data node or attribute
        does not exist python None will be returned
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace(
        #     "Get ATRIBUTE: %s, %s",
        #     xpath,
        #     attribute_name,
        # )
        return self.libyang_data.get_attribute(xpath, attribute_name)

    def get_attributes(self, xpath: str) -> Tuple[str, str]:
        """
        Get list of attribute from the data at XPATH as tuple of name/value
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace(
        #     "Get ATRIBUTES: %s",
        #     xpath,
        # )
        return self.libyang_data.get_attributes(xpath)

    def insert_attribute(self, xpath: str, module: str, attribute_name: str, attribute_value) -> bool:
        """
        Add an attribute to an existing libyang data node.
        This function is a pass through to libyang.

         returns: VoodooListElement()
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace(
        #     "ADD ATRIBUTE: %s, %s, %s, %s",
        #     xpath,
        #     module,
        #     attribute_name,
        #     attribute_value,
        # )
        return self.libyang_data.insert_attribute(xpath, module, attribute_name, attribute_value)

    def remove_attribute(self, xpath: str, attribute_name: str, attribute_value: str = None) -> bool:
        """
        Remove an attribute from an existing libyang node

         returns: VoodooListElement()
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace(
        #     "REMOVE ATRIBUTE: %s, %s, %s", xpath, attribute_name, attribute_value
        # )
        return self.libyang_data.remove_attribute(xpath, attribute_name, attribute_value)

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
        # self.log.trace("CREATE: %s (keys: %s) (values: %s)", xpath, keys, values)
        self.libyang_data.set_xpath(xpath, "")

    def uncreate(self, xpath):
        """
        To remove a list item from the list /simplelist with the key sf

        xpath:   /integrationtest:simplelist[simplekey='sf']
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("UNCREATE: %s", xpath)
        self.libyang_data.delete_xpath(xpath)

    def set(self, xpath, value, valtype=18, nodetype=4):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        valtype defaults to 18 (STRING), see Types.DATA_ABSTRACTION_MAPPING for the
        full set of value types.

        returns: value
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("SET: StubLy Datastore- %s => %s", xpath, value)
        self._libyang_errors.clear()
        self.libyang_data.set_xpath(xpath, value)
        if self._libyang_errors:
            raise InvalidValueError(value, xpath, "; ".join(self._libyang_errors))

    def libyang_get_xpath(self, xpath):
        """
        Return a libyang-cffi DataNode directly - this must be called with a specific XPATH
        as only the first result will be returned.
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("LIBYANG-GET: %s", xpath)
        try:
            return next(self.libyang_data.get_xpath(xpath))
        except libyang.util.LibyangError:
            return None

    def libyang_gets_xpath(self, xpath):
        """
        Return a libyang-cffi DataNode directly, returning a generator of all entries that match
        the XPATH.
        """
        if not self.connected:
            raise NotConnect()
        return self.libyang_data.get_xpath(xpath)

    def gets(self, xpath):
        """
        For the given XPATH (of a leaflist) return an list of values from the datastore in the
        order they were entered.

        returns: generator of Values
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("GETS: %s", xpath)
        for result in self.libyang_data.get_xpath(xpath):
            yield result.value

    def gets_len(self, xpath):
        """
        From a given XPATH list (not leaf-list) return the legnth of the list.

        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("COUNT: %s", xpath)
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
        # self.log.trace("ADD: %s => %s (valtype: %s)", xpath, value, valtype)
        self.libyang_data.set_xpath(xpath, value)

    def remove(self, xpath, value):
        """
        For the given XPATH of a leaflist remove the item from the datastore.
        Note: the xpath points to the leaf-list not the item.

        returns: None.
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("REMOVE: %s %s", xpath, value)
        self.libyang_data.delete_xpath(f"{xpath}{Utils.encode_xpath_predicate('.', value)}")

    def set_data_by_xpath(self, context, data_path, value):
        """
        This method is a backdoor way to set data in the datastore.

        Normally, we would use the python objects __setattr__ and that would do similair
        lookups to what is below. However if we want we can take the data path from a
        node (i.e. root.bronze.silver.gold._node.real_data_path) and then just append
        a child node (i.e. /platinum/deep) and set the data on the dal without bothering
        to instantiate the YangVoodoo Node for it.
        """
        # self.log.trace("SET_DATA_BY_XPATH: %s %s %s", context, data_path, value)
        node_schema = Utils.get_nodeschema_from_data_path(context, data_path)
        if node_schema.nodetype() != Types.LIBYANG_NODETYPE["LEAF"]:
            raise PathIsNotALeaf("set_raw_data only operates on leaves")
        val_type = Utils.get_yang_type(node_schema.type(), value, node_schema.real_schema_path)
        self.set(data_path, value, val_type)

    def get_raw_xpath(self, xpath: str, with_val: bool = False) -> Generator[Tuple[str, str], None, None]:
        """
        Get raw xpath
        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        schema_path: /integrationtest:web/integrationtest:bands/integrationtest:gigs

        returns a generator
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("GETS_RAW_XPATH: %s", xpath)
        for xpath in self.libyang_data.gets_xpath(xpath):
            if with_val:
                val = next(self.libyang_data.get_xpath(xpath))
                yield xpath, val.value
            else:
                yield xpath

    def get_raw_xpath_only_values(self, xpath: str) -> Generator[str, None, None]:
        """
        Get raw xpath
        xpath:       /integrationtest:web/bands[name='Idlewild']/gigs
        schema_path: /integrationtest:web/integrationtest:bands/integrationtest:gigs

        returns a generator
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("GETS_RAW_XPATH: %s", xpath)
        for xpath in self.libyang_data.gets_xpath(xpath):
            val = next(self.libyang_data.get_xpath(xpath))
            val.value

    def get_raw_xpath_single_val(self, xpath):
        # self.log.trace("GET_RAW_XPATH_SINGLE_VAL: %s", xpath)
        for result in self.get_raw_xpath(xpath, True):
            return result[1]
        return None

    def gets_sorted(self, xpath, spath, ignore_empty_lists=False):
        """
        For the given XPATH (of a list) return an sorted list of XPATHS representing every
        list element within the list.

        returns: generator of sorted XPATHS
        """

        result = list(self.gets_unsorted(xpath, spath, ignore_empty_lists))
        result.sort()
        for xpath in result:
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
        # self.log.trace(
        #     "GETS_UNSORTED: %s (schema: %s, ignore_empty: %s)",
        #     xpath,
        #     schema_path,
        #     ignore_empty_lists,
        # )
        yield from self.libyang_data.gets_xpath(xpath)

    def has_item(self, xpath):
        """
        Evaluate if the item is present in the datatsore, determines if a specific XPATH has been
        set, may be called on leaves, presence containers or specific list elements.

        returns: True or False
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("HAS_ITEM: %s", xpath)
        x = self.libyang_data.get_xpath(xpath)
        return len(list(x)) != 0

    def get(self, xpath, default_value=None):
        """
        Get a specific path (leaf nodes or presence containers), in the case of leaves a python
        primitive is returned (i.e. strings, booleans, integers).
        In the case of non-terminating nodes (i.e. Lists, Containers, PresenceContainers) this
        method will return a Voodoo object of the relevant type.

        If the caller of this method knows about a default_value that can be used to change
        the behaviour if the key does not exist in the datastore.

        FUTURE CHANGE: in future enumerations should be returned as a specific object type

        returns: value or Vooodoo<X>
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("GET: StubLy Datastore- %s (default: %s)", xpath, default_value)
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
        """
        Delete the data, and all decendants for a particular XPATH.

        returns: True
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("DELETE: %s", xpath)
        self.libyang_data.set_xpath(xpath, None)

    def dump_xpaths(self, start_xpath: str = None) -> dict:
        """
        Dump the datastore in xpath format with an optional start_xpath.
        """
        if not self.connected:
            raise NotConnect()
        data_node = None
        if start_xpath:
            try:
                data_node = next(self.libyang_data.get_xpath(start_xpath))
            except StopIteration:
                pass

        return {node.xpath: node.value for node in self.libyang_data.dump_datanodes(start_node=data_node)}

    def empty(self):
        """
        Somewhat dangerous option - but attempt to empty the entire datastore.

        returns: True
        """
        raise NotImplementedError("empty not implemented with the libyang based datastore")

    def dump(self, filename, format=1):
        """
        Return data to the filename in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("DUMP: %s (format: %s)", filename, format)
        self.libyang_data.dump(filename, format)

    def load(self, filename, format=1, trusted=False):
        """
        Load data from the filename in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']

        If the trusted flag is set to True libyang will not evaluate when/must/mandatory conditions
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("LOAD: %s (format: %s)", filename, format)
        self.libyang_data.load(filename, format, trusted)

    def subdumps(self, xpath: str, format: int = 1):
        """
        Return a sub portion of the data tree in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("DUMPS: (xpath: %s, format: %s)", xpath, format)
        return self.libyang_data.subdumps(xpath, format)

    def dumps(self, format: int = 1):
        """
        Return the root data tree in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("DUMPs: (format: %s)", format)
        return self.libyang_data.dumps(format)

    def loads(self, payload, format=1, trusted=False):
        """
        Load data from the payload in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']

        If the trusted flag is set to True libyang will not evaluate when/must/mandatory conditions
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("LOADS: (format: %s)", format)
        self.libyang_data.loads(payload, format, trusted)

    def merge(self, filename, format=1, trusted=True):
        """
        Merge data from the filename in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']

        If the trusted flag is set to True libyang will not evaluate when/must/mandatory conditions
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("MERGE: (format: %s)", format)
        with open(filename) as fh:
            self.libyang_data.merges(fh.read(), format, trusted)

    def merges(self, payload, format=1, trusted=True):
        """
        Merge data from the payload in the format specified.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']

        If the trusted flag is set to True libyang will not evaluate when/must/mandatory conditions
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("MERGES: (format: %s)", format)
        self.libyang_data.merges(payload, format, trusted)

    def advanced_merges(self, payload, format=1, trusted=True):
        """
        Merge data from the payload in the format specified, implementing replace/delete netconf
        tags in the process.

        Types.FORMAT['XML'] or Types.FORMAT['JSON']

        If the trusted flag is set to True libyang will not evaluate when/must/mandatory conditions
        """
        if not self.connected:
            raise NotConnect()
        # self.log.trace("ADVANCED-MERGES: (format: %s)", format)
        self.libyang_data.advanced_merges(payload, format, trusted)

    def advanced_merge(self, filename, format=1, trusted=True):
        if not self.connected:
            raise NotConnect()
        # self.log.trace("ADVANCED-MERGE: (format: %s)", format)
        self.libyang_data.advanced_merge(filename, format, trusted)
