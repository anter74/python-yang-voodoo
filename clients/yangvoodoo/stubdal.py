import yangvoodoo


class StubDataAbstractionLayer:

    """
    IMPORTANT:

    This data abstration layer is a stub which is not suitable for any real use case - it's sole
    purpose is to allow for testing without the dependency of running the sysrepo backend.

    There are two key constraints:


    1) VoodooNode utilises libyang to lookup the schema of a given yang model - this enforces the
       overall schema.
        (i.e. root.<non-existatnt-node   <-- node must exist in the yang model).
              root.<boolean-node>        <-- assigning a non-boolean value fails.)

       However,


    """

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
        self.stub_store[xpath] = None

    def create(self, xpath):
        self.stub_store[xpath] = []

    def set(self, xpath, value, valtype=0):
        if xpath[-1] == '[':
            if xpath not in self.stub_store:
                raise ValueError('Tried to set data on a listelement before it was created:\n%s' % (xpath))
            self.stub_store[xpath].append(value)
        else:
            self.stub_store[xpath] = value

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        items = self.gets(xpath, ignore_empty_lists)
        items.sort()
        return items

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        if xpath in self.stub_store:
            items = []
            for item in self.stub_store[xpath]:
                items.append(item)
            return items
        if not ignore_empty_lists:
            raise yangvoodoo.Errors.ListDoesNotContainElement(xpath)

    def get(self, xpath):
        if xpath not in self.stub_store:
            raise yangvoodoo.Errors.BackendDatastoreError('%s does not exist - cannot get' % (xpath))
        return self.stub_store[xpath]

    def delete(self, xpath):
        if xpath not in self.stub_store:
            raise yangvoodoo.Errors.BackendDatastoreError('%s does not exist - cannot delete' % (xpath))
        self.stub_store.remove(xpath)

    def refresh(self):
        pass
