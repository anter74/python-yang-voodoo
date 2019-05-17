import yangvoodoo
import yangvoodoo.basedal
import re


class StubDataAbstractionLayer(yangvoodoo.basedal.BaseDataAbstractionLayer):

    """
    IMPORTANT:

    This data abstration layer is a stub which is not suitable for any real use case - it's sole
    purpose is to allow for testing without the dependency of running the sysrepo backend.

    In general this means that whilst manipulating the data as part of yangvoodoo node it is
    only a candidate transaction. The follow up committing the data allows the backend datastore
    to have the final say on it's validity

    There are some key constraints:


    1) VoodooNode utilises libyang to lookup the schema of a given yang model - this enforces the
       overall schema.
        (i.e. root.<non-existatnt-node   <-- node must exist in the yang model).
              root.<boolean-node>        <-- assigning a non-boolean value fails.)

    2) Default values are provided by the backend datastore.

    3) Validating expressions from MUST and WHEN's is implemented by the backend datastore.


    """
    # REGEX_LIST_XPATH = re.compile('(.*:[A-Za-z0_-]+)(.*)')

    LIST_POINTER = 1

    def dump_xpaths(self):
        new_dict = {}
        for key in self.stub_store:
            if isinstance(self.stub_store[key], list):
                new_dict[key] = None
            else:
                new_dict[key] = str(self.stub_store[key])
        return new_dict

    def _initdal(self):
        self.stub_store = {}

    def connect(self, module, tag='<id-tag>'):
        self.module = module
        return True

    def disconnect(self):
        return True

    def commit(self):
        return True

    def validate(self):
        return True

    def create_container(self, xpath):
        self.stub_store[xpath] = True

    def _list_xpath(self, xpath, ignore_empty_lists=False):
        """
        Convert a list operation into a path without the last set of predictes

        This is specific to the way we organise lists in the stub node.
        """
        if xpath not in self.stub_store:
            if ignore_empty_lists:
                return None
            raise ValueError('Path does not exist %s' % (xpath))
        (itemtype, item) = self.stub_store[xpath]
        if not itemtype == self.LIST_POINTER:
            if ignore_empty_lists:
                return None
            raise ValueError('Path is not a list %s' % (xpath))

        return item

    def create(self, xpath, keys=[], values=[], module=None):
        """
        The xpath coming in should include the full predicates
            /integrationtest:simplelist[integrationtest:simplekey='sdf']

        However in the stub to speed up iteration we create a structure
            self.stub_store[xpath_without_predicates]

        In the stub we create a python list, this holds precise XPATH's to each list element
            /integrationtest:simplelist = []
        The keys/values are used to create, this is a specific list element for each key and matches sysrepo
            /integrationtest:simplelist[integrationtest:simplekey='sdf']/integrationtest:<key0> = <value0>

        We also create the following keys- pointing back the list without any predicates
            "/integrationtest:simplelist[integrationtest:simplekey='sdf']": = (1, "list path")

        """
        predicates = ""
        for index in range(len(keys)):
            (value, valuetype) = values[index]
            predicates = predicates + "["+keys[index]+"='"+str(value)+"']"

        list_xpath = xpath.replace(predicates, '')
        if list_xpath not in self.stub_store:
            self.stub_store[list_xpath] = []
        self.stub_store[list_xpath].append(xpath)
        self.stub_store[xpath] = (self.LIST_POINTER, list_xpath)

        for index in range(len(keys)):
            (value, valuetype) = values[index]
            self.set(xpath + "/" + module+":"+keys[index], value, valuetype)

    def add(self, xpath, value, valtype):
        if xpath not in self.stub_store:
            self.stub_store[xpath] = []
        self.stub_store[xpath].append(value)

    def remove(self, xpath, value):
        if xpath not in self.stub_store:
            raise yangvoodoo.Errors.BackendDatastoreError([('path does not exist - cannot remove', xpath)])
        if value not in self.stub_store[xpath]:
            raise yangvoodoo.Errors.BackendDatastoreError([('values does not exist at path - cannot remove', xpath)])
        self.stub_store[xpath].remove(value)

    def gets(self, xpath):
        items = []
        if xpath in self.stub_store:
            items = self.stub_store[xpath]
        for item in items:
            yield item

    def has_item(self, xpath):
        list_xpath = self._list_xpath(xpath, ignore_empty_lists=True)
        if list_xpath in self.stub_store:
            if xpath in self.stub_store[list_xpath]:
                return True
        return False

    def set(self, xpath, value, valtype=0):
        self.stub_store[xpath] = value

    def gets_sorted(self, list_xpath, ignore_empty_lists=False):
        if list_xpath in self.stub_store:
            items = []
            for item in self.stub_store[list_xpath]:
                items.append(item)
            items.sort()
            for item in items:
                yield item

    def gets_unsorted(self, list_xpath, ignore_empty_lists=False):
        if list_xpath in self.stub_store:
            items = []
            for item in self.stub_store[list_xpath]:
                items.append(item)
            for item in items:
                yield item
        if not ignore_empty_lists:
            raise yangvoodoo.Errors.ListDoesNotContainElement(xpath)

    def get(self, xpath):
        if xpath not in self.stub_store:
            return None
        return self.stub_store[xpath]

    def delete(self, xpath):
        if xpath in self.stub_store:
            # Logic for lists
            if xpath[-1] == "]":
                list_xpath = self._list_xpath(xpath)
                if list_xpath not in self.stub_store:
                    raise yangvoodoo.Errors.BackendDatastoreError([('path does not exist - cannot get', xpath)])
                elif xpath not in self.stub_store[list_xpath]:
                    raise yangvoodoo.Errors.BackendDatastoreError([('path does not exist - cannot get', xpath)])
                else:
                    self.stub_store[list_xpath].remove(xpath)
                    return True

        del self.stub_store[xpath]
        return True

    def refresh(self):
        pass
