
class BaseDataAbstractionLayer:

    """
    This module provides the base definition of the data abstraction layer.

    Log         - a standard python logger
    session     - represents the session to the data access layer

    conneciton  - represents the socket/connection uses to access the data access layer.
    dirty       - indicates a parallel transaction has changed data in the datastore.
    """

    def __init__(self, log=None):
        self.log = log
        self.session = None
        self.conn = None
        self.dirty = None
        self.module = None
        self._initdal()

    def _initdal(self):
        """
        Initialise specific class attributes for a particular dal.
        """
        pass

    def setup_root(self):
        """
        If required may be used to carry out to do any preparation before a root object
        is obtained.
        """
        pass

    def connect(self, tag='client'):
        raise NotImplementedError('connect not implemented')

    def disconnect(self):
        raise NotImplementedError('disconnect not implemented')

    def commit(self):
        raise NotImplementedError('commit not implemented')

    def validate(self):
        raise NotImplementedError('validate not implemented')

    def create_container(self, xpath):
        raise NotImplementedError('create_container not implemented')

    def create(self, xpath, keys=None, values=None, module=None):
        raise NotImplementedError("create not implemented")

    def set(self, xpath, value, valtype=18):
        raise NotImplementedError("set not implemented")

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        raise NotImplementedError("gets_sorted not implemented")

    def gets(self, xpath):
        raise NotImplementedError("gets not implemented")

    def add(self, xpath, value, valtype=18):
        raise NotImplementedError("add not implemented")

    def remove(self, xpath, value):
        raise NotImplementedError("remove not implemented")

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        raise NotImplementedError("gets_unsorted not implemented")

    def has_item(self, xpath):
        raise NotImplementedError("has_item not implemented")

    def get(self, xpath):
        raise NotImplementedError("get not implemented")

    def delete(self, xpath):
        raise NotImplementedError("delete not implemented")

    def refresh(self):
        raise NotImplementedError("refresh not implemented")

    def is_session_dirty(self):
        raise NotImplementedError("is_session_dirty not implemented")
