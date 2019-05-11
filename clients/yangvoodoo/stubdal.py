import yangvoodoo
import re


class StubDataAbstractionLayer:

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
    REGEX_LIST_XPATH = re.compile('(.*:[A-Za-z0_-]+)(.*)')

    def __init__(self):
        self.stub_store = {}
        self.session = None
        self.conn = None

    def connect(self, tag='<id-tag>'):
        pass

    def commit(self):
        return True

    def validate(self):
        return True

    def create_container(self, xpath):
        self.stub_store[xpath] = True

    def _list_xpath(self, xpath):
        return self.REGEX_LIST_XPATH.sub('\g<1>', xpath)

    def create(self, xpath):
        # sysrepo backend takes in the entire xpath
        # ie. /integrationtest:psychedelia/integrationtest:psychedelic-rock/integrationtest:stoner-rock/integrationtest:bands[band='Dead Meadow']
        # However for the stub to easily deal with membership tests without iterating the entire stub_store the list
        # does make a little more sense.
        # .*:[A-Za-z0_-]+

        # This is too simplisitc in sysrepo we can call
        # /path/list1[key1]/thing/list2[key2
        # and even if list1 doesn't exist it will be created on demand.
        list_xpath = self._list_xpath(xpath)
        if list_xpath not in self.stub_store:
            self.stub_store[list_xpath] = []
        self.stub_store[list_xpath].append(xpath)

    def has_item(self, xpath):
        list_xpath = self._list_xpath(xpath)
        if list_xpath in self.stub_store:
            if xpath in self.stub_store[list_xpath]:
                return True
        return False

    def set(self, xpath, value, valtype=0):
        if xpath[-1] == '[':
            if xpath not in self.stub_store:
                raise ValueError('Tried to set data on a listelement before it was created:\n%s' % (xpath))
            self.stub_store[xpath].append(value)
        else:
            self.stub_store[xpath] = value

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        list_xpath = self._list_xpath(xpath)
        if list_xpath in self.stub_store:
            items = []
            for item in self.stub_store[list_xpath]:
                items.append(item)
            items.sort()
            for item in items:
                yield item

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        list_xpath = self._list_xpath(xpath)
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
        if xpath not in self.stub_store:
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
