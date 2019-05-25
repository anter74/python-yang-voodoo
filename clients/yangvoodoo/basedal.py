from yangvoodoo.Common import Utils


class BaseDataAbstractionLayer:

    """
    This module provides the base definition of the data abstraction layer.

    Log         - a standard python logger
    session     - represents the session to the data access layer

    conneciton  - represents the socket/connection uses to access the data access layer.
    dirty       - indicates a parallel transaction has changed data in the datastore.
    """

    DAL_ID = "BASE"

    def __init__(self, log=None):
        if not log:
            log = Utils.get_logger(self.DAL_ID)
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

    def load_xpaths(self, xpaths):
        """
        Given a dictionary of XPATH's import them to the datastore.

        xpath[key] = (value, valuetype, nodetype)

        valuetype  - see Types.DATA_ABSTRACTION_MAPPING
        nodetype   - see Types.LIBYANG_NODETYPE
        """
        for xpath in xpaths:
            (value, valuetype, nodetype) = xpaths[xpath]
            if isinstance(value, list):
                for (value, valuetype, nodetype) in xpaths[xpath]:
                    print('INNIN Leaf list add required', xpath)
                    self.add(xpath, value, valuetype)
            else:
                print('INNIN', xpath, nodetype)
                (value, valuetype, nodetype) = xpaths[xpath]
                if nodetype == 16:  # list

                    self.create(xpath)
                    print('INNIN - list create', xpath)
                elif value:
                    print('INNIN - value', xpath, value)
                    self.set(xpath, value, valuetype)

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
