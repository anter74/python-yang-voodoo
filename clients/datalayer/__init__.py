#!/usr/bin/python3
import libyang
import sysrepo as sr
import time
import logging
import socket


class LogWrap():

    ENABLED = False
    ENABLED_INFO = True
    ENABLED_DEBUG = True

    ENABLED_REMOTE = True
    REMOTE_LOG_IP = "127.0.0.1"
    REMOTE_LOG_PORT = 6666

    def __init__(self):
        format = "%(asctime)-15s - %(name)-20s %(levelname)-12s  %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=format)
        self.log = logging.getLogger('blackhole')

        if self.ENABLED_REMOTE:
            self.log_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = self._pad_truncate_to_size("STARTED ("+str(time.time())+"):")
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    @staticmethod
    def _args_wildcard_to_printf(*args):
        if isinstance(args, tuple):
            # (('Using cli startup to do %s', 'O:configure'),)
            args = list(args[0])
            if len(args) == 0:
                return ''
            message = args.pop(0)
            if len(args) == 0:
                pass
            if len(args) == 1:
                message = message % (args[0])
            else:
                message = message % tuple(args)
        else:
            message = args
        return (message)

    def _pad_truncate_to_size(self, message, size=1024):
        if len(message) < size:
            message = message + ' '*(1024-len(message))
        elif len(message) > 1024:
            message = message[:1024]
        return message.encode()

    def info(self, *args):
        if self.ENABLED and self.ENABLED_INFO:
            self.log.info(args)
        if self.ENABLED_REMOTE and self.ENABLED_INFO:
            print('a')
            message = 'INFO ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    def error(self, *args):
        if self.ENABLED:
            self.log.error(args)
        if self.ENABLED_REMOTE:
            message = 'INFO ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    def debug(self, *args):
        if self.ENABLED and self.ENABLED_DEBUG:
            self.log.debug(args)

        if self.ENABLED_REMOTE and self.ENABLED_DEBUG:
            message = 'DEBUG ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))


class BlackArtContext:

    def __init__(self, module, data_access_layer, yang_schema, yang_ctx, cache=None, log=None):
        self.module = module
        self.schema = yang_schema
        self.schemactx = yang_ctx
        self.dal = data_access_layer
        if cache is None:
            self.schemacache = BlackHoleCache()
        else:
            self.schemacache = cache
        self.log = LogWrap()


class Types:

    UINT32 = sr.SR_UINT32_T
    UINT16 = sr.SR_UINT16_T
    UINT8 = sr.SR_UINT8_T
    INT32 = sr.SR_INT32_T
    INT16 = sr.SR_INT16_T
    INT8 = sr.SR_INT8_T
    STRING = sr.SR_STRING_T
    DECIMAL64 = sr.SR_DECIMAL64_T
    BOOLEAN = sr.SR_BOOL_T
    ENUM = sr.SR_ENUM_T
    EMPTY = sr.SR_LEAF_EMPTY_T
    PRESENCE_CONTAINER = sr.SR_CONTAINER_PRESENCE_T

    LIBYANG_MAPPING = {
        'string': sr.SR_STRING_T,
        'enumeration': sr.SR_ENUM_T,
        'boolean': sr.SR_BOOL_T
    }


class BlackHoleCache:

    def __init__(self):
        self.items = {}

    def is_path_cached(self, path):
        if path in self.items:
            return True
        return False

    def get_item_from_cache(self, path):
        return self.items[path]

    def add_entry(self, path, cache_object):
        """
        Add an entry into the cache.

        key = an XPATH path (e.g. /simpleleaf)
        cache_object = Whatever it wants to be.
        """

        self.items[path] = cache_object

    def empty(self):
        self.items.clear()


class BlackArtNode:

    """
    Constraints:

    Node based access is provided for a particular yang module, whenever we run 'get_root'
    we bind to a particular yang module.

    At 10,000ft level this module acts as a facade around the DataAccess methods get(), gets()
    set() and delete(). We depend heavily on libyang to inspect the schema on each method.

    On calling __getatttr_
      a) non-Primitives (i.e. Containers and Lists) return another Object
      b) Primtiives return the value itself.

    Each time we instantiate an object we store
        - module (the name of the yang module - used when forming the xpath)
        - path (the fully qualified path, maintaining reference to specific elements of lists)
                i.e. /integrationtest:s


    Internal Notes:

    Things held of a BlackArtContext
    --------------------------------
      - module    = the name of the yang module (e.g integrationtest)
      - dal       = An instantiated object of DataAccess() - one object used for all access.
      - schema    = A libyang object of the top-level yang module.
      - schemactx = A libyang context object
      - cache     = A cache object to store the schema (assumption here is libyang lookups are expesnive - but
                    that may not be true. For sysrepo data lookup even if it's expensive we would never choose
                    to cache that data.
      - log       = A Log instance which behaves like the python standard logging library.

    Things specific to a particular node
    ------------------------------------
      - path      = an XPATH expression for the path - with prefixes and values pointing to exact instances
                    of data. This is used for fetching data.... e.g.
                    integrationtest:outsidelist[leafo='its cold outside']/integrationtest:otherinsidelist
                          [otherlist1='uno'][otherlist2='due'][otherlist3='tre']/integrationtest:language
      - spath     = an XPATH expression for the path - with prefixes but no specific instances of data
                    included. This is used for looking up schema definitions.... e.g.
                    /integrationtest:outsidelist/integrationtest:otherinsidelist/integrationtest:language
    """

    _NODE_TYPE = 'Node'

    def __init__(self, context, path='', spath=''):
        self.__dict__['_context'] = context
        self.__dict__['_path'] = path
        self.__dict__['_spath'] = spath

    def __name__(self):
        return 'BlackArtNode'

    def __repr__(self):
        return self._base_repr()

    def _base_repr(self):
        path = self.__dict__['_path']
        return 'BlackArt%s{%s}' % (self._NODE_TYPE, path)

    def __del__(self):
        path = self.__dict__['_path']

    def _form_xpath(self, path, attr, node_schema=None):
        """
        When using the schema xpath lookup we need to use the module prefix
        across every part of the path.

        Inside the integrationtest which imports from the yang module teschild we still
        reference those imported elements by the parent module.
         '/integrationtest:imports-in-here/integrationtest:name'
        """
        context = self.__dict__['_context']
        if node_schema and node_schema.underscore_translated:
            return path + '/' + context.module + ":" + attr.replace('_', '-')

        return path + '/' + context.module + ":" + attr

    def __getattr__(self, attr):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        # Schema Path is a combination of the previous schema path + the attribute
        # This order of things is pretty important
        # - get_schema_of_path lets us convert '_' to '-' if the leaf doesn't exist
        # to take account of the conversions
        node_schema = self._get_schema_of_path(self._form_xpath(spath, attr))
        new_spath = self._form_xpath(spath, attr, node_schema)
        new_xpath = self._form_xpath(path, attr, node_schema)
        node_type = node_schema.nodetype()

        if node_type == 1:
            # assume this is a container (or a presence container)
            if node_schema.presence() is None:
                return BlackArtContainer(context, new_xpath, new_spath)
            else:
                return BlackArtPresenceContainer(context, new_xpath, new_spath)
        elif node_type == 4:
            # Assume this is always a primitive
            return context.dal.get(new_xpath)
        elif node_type == 16:
            return BlackArtList(context, new_xpath, new_spath)

        raise ValueError('Get - not sure what the type is...%s' % (node_type))

    def __setattr__(self, attr, val):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        xpath = self._form_xpath(path, attr)
        spath = self._form_xpath(spath, attr)

        node_schema = self._get_schema_of_path(spath)
        if val is None:
            context.dal.delete(xpath)
            return

        type = Types.LIBYANG_MAPPING[str(node_schema.type())]

        context.dal.set(xpath, val, type)

    def __dir__(self):
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        node_schema = self._get_schema_of_path(spath)

        answer = []
        for child in node_schema.children():
            answer.append(child.name().replace('-', '_'))
        answer.sort()
        return answer

    def _get_schema_of_path(self, xpath):
        context = self.__dict__['_context']
        if xpath == "":
            # Root object won't be a valid XPATH
            return context.schema

        if context.schemacache.is_path_cached(xpath):
            return context.schemacache.get_item_from_cache(xpath)
        try:
            schema_for_path = next(context.schemactx.find_path(xpath))
            schema_for_path.underscore_translated = False
            return schema_for_path
        except libyang.util.LibyangError:
            pass

        try:
            schema_for_path = next(context.schemactx.find_path(xpath.replace('_', '-')))
            schema_for_path.underscore_translated = True
            return schema_for_path
        except libyang.util.LibyangError:
            pass
        raise NonExistingNode(xpath)


class BlackArtList(BlackArtNode):

    """
    Represents a list from a yang module.

    New entries can be created on this object with the create object, each
    key defined in the yang module should be passed in paying attention to
    the order of the keys.
        (e.g.
        key1 = True
        key2 = False
        root.twokeylist.create(key1, key2)

    To obtain a specific instance from the list call the get method, passing
    each key from the yang module. It is not possible to provide partial keys
    in a hope to get multiple records.

    Note: values for the list keys should be provided as they would in an
    XPATH express. i.e. python True > 'true', False > 'false'

    TOOD: interator
    """

    _NODE_TYPE = 'List'

    def create(self, *args):
        """
        Create a list element.

        For composite-key lists then each key within the yang module must be provided
        in the same order it is defined within the yang module.

        The newly created list-element is returned.

        Calling the create method a second time will not overwrite/remove data.
        """
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here

        context.dal.create(new_xpath)
        return BlackArtListElement(context, new_xpath, new_spath)

    def __len__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        results = context.dal.gets(spath)
        return len(list(results))

    def get(self, *args):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here
        results = list(context.dal.gets(new_xpath))

        return BlackArtListElement(context, new_xpath, new_spath)

    def __iter__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        return BlackArtListIterator(context, path, spath)

    def __contains__(self, *args):
        context = self.__dict__['_context']
        if isinstance(args[0], tuple):
            arglist = []
            for a in args[0]:
                arglist.append(a)
        else:
            arglist = [args[0]]
        conditional = self._get_keys(arglist)

        path = self.__dict__['_path']
        new_xpath = path + conditional
        try:
            reults = list(context.dal.gets(new_xpath))
            return True
        except:
            pass
        return False

    def _get_keys(self, *args):
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        node_schema = self._get_schema_of_path(spath)
        keys = list(node_schema.keys())

        if not len(args[0]) == len(keys):
            raise ListWrongNumberOfKeys(path, len(keys), len(args[0]))

        conditional = ""
        for i in range(len(keys)):
            value = self._get_xpath_value_from_python_value(args[0][i], keys[i].type())

            conditional = conditional + "[%s='%s']" % (keys[i].name(), value)
        return conditional

    def _get_xpath_value_from_python_value(self, v, t):
        if str(t) == 'boolean':
            return str(v).lower()
        else:
            return str(v)


class BlackArtListIterator(BlackArtNode):

    TYPE = 'BlackArtListIterator'

    def __init__(self, context, path, spath):
        self.__dict__['_context'] = context
        self.__dict__['_path'] = path
        self.__dict__['_spath'] = spath

        self.__dict__['_iterator'] = context.dal.gets(path)

    def __next__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        this_xpath = next(self.__dict__['_iterator'])

        return BlackArtListElement(context, this_xpath, spath)


class BlackArtListElement(BlackArtNode):

    """
    Represents a specific instance of a list element from a yang module.
    The child nodes are accessible from this node.
    """

    _NODE_TYPE = 'ListElement'


class BlackArtContainer(BlackArtNode):
    """
    Represents a Container from a yang module, with access to the child
    elements.
    """

    _NODE_TYPE = 'Container'


class BlackArtPresenceContainer(BlackArtNode):

    """
    Represents a PresenceContainer from a yang module, with access to the child
    elements. The exists() method will return True if this container exists
    (either created implicitly because of children or explicitly).
    """

    _NODE_TYPE = 'PresenceContainer'

    def exists(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        return context.dal.get(path) is True

    def create(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        context.dal.create_container(path)

    def __repr__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        base_repr = self._base_repr()
        if context.dal.get(path) is True:
            return base_repr + " Exists"
        return base_repr + " Does Not Exist"


class BlackArtRoot(BlackArtNode):

    _NODE_TYPE = 'Root'


class DataAccess:

    """
    This module provides two methods to access data, either XPATH based (low-level) or
    Node based (high-level).

    The backend supported by this module is sysrepo (without netopeer2), however the
    basic constructs decribed by this class could be ported to other backends.

    Dependencies:
     - sysrepo 0.7.7 python3  bindings (https://github.com/sysrepo/sysrepo)
     - libyang 0.16.78 (https://github.com/rjarry/libyang-cffi/)
    """

    def get_root(self, module, yang_location="../yang/"):
        """
        Instantiate Node-based access to the data stored in the backend defined by a yang
        schema. The data access will be constraint to the YANG module chosen when invoking
        this method.

        We must have access to the same YANG module loaded within in sysrepo, which can be
        set by modifying yang_location argument.
        """
        yang_ctx = libyang.Context(yang_location)
        yang_schema = yang_ctx.load_module(module)

        context = BlackArtContext(module, self, yang_schema, yang_ctx)
        return BlackArtRoot(context)

    def connect(self, tag='client'):
        self.conn = sr.Connection("%s%s" % (tag, time.time()))
        self.session = sr.Session(self.conn)

        # self.subscribe = sr.Subscribe(self.session)

    def commit(self):
        # try:
        self.session.commit()
        # except RuntimeError as err:
        #    xerror = str(err)
        #raise CommitFailed(xerror)

    def create_container(self, xpath):
        self.set(xpath, None,  sr.SR_CONTAINER_PRESENCE_T)

    def create(self, xpath):
        """
        Create a list item by XPATH including keys
         e.g. / path/to/list[key1 = ''][key2 = ''][key3 = '']
        """
        self.set(xpath, None, sr.SR_LIST_T)

    def set(self, xpath, value, valtype=sr.SR_STRING_T):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        It is required to provide the value and the type of the field.
        """
        v = sr.Val(value, valtype)
        self.session.set_item(xpath, v)

    def gets(self, xpath):
        """
        Get a list of xpaths for each items in the list, this can then be used to fetch data
        from within the list.
        """
        vals = self.session.get_items(xpath)
        if not vals:
            raise NodeNotAList(xpath)
        else:
            for i in range(vals.val_cnt()):
                v = vals.val(i)
                yield v.xpath()

    def get(self, xpath):
        sysrepo_item = self.session.get_item(xpath)
        return self._get_python_datatype_from_sysrepo_val(sysrepo_item, xpath)

    def delete(self, xpath):
        self.session.delete_item(xpath)

    def _get_python_datatype_from_sysrepo_val(self, valObject, xpath=None):
        """
        For now this is copied out of providers/dataprovider/__init__.py, if this carries on as a good
        idea then would need to combined.

        Note: there is a limitation here, we can't return False for a container presence node that doesn't
        exist becuase we never will get a valObject for it. Likewise boolean's and empties that dont' exist.

        This is a wrapped version of a Val Object object
        http: // www.sysrepo.org/static/doc/html/classsysrepo_1_1Data.html
        http: // www.sysrepo.org/static/doc/html/group__cl.html  # ga5801ac5c6dcd2186aa169961cf3d8cdc

        These don't map directly to the C API
        SR_UINT32_T 20
        SR_CONTAINER_PRESENCE_T 4
        SR_INT64_T 16
        SR_BITS_T 7
        SR_IDENTITYREF_T 11
        SR_UINT8_T 18
        SR_LEAF_EMPTY_T 5
        SR_DECIMAL64_T 9
        SR_INSTANCEID_T 12
        SR_TREE_ITERATOR_T 1
        SR_CONTAINER_T 3
        SR_UINT64_T 21
        SR_INT32_T 15
        SR_ENUM_T 10
        SR_UNKNOWN_T 0
        SR_STRING_T 17
        SR_ANYXML_T 22
        SR_INT8_T 13
        SR_LIST_T 2
        SR_INT16_T 14
        SR_BOOL_T 8
        SR_ANYDATA_T 23
        SR_UINT16_T 19
        SR_BINARY_T 6

        """
        if not valObject:
            return None
        type = valObject.type()
        if type == sr.SR_STRING_T:
            return valObject.val_to_string()
        elif type == sr.SR_UINT64_T:
            return valObject.data().get_uint64()
        elif type == sr.SR_UINT32_T:
            return valObject.data().get_uint32()
        elif type == sr.SR_UINT16_T:
            return valObject.data().get_uint16()
        elif type == sr.SR_UINT8_T:
            return valObject.data().get_uint8()
        elif type == sr.SR_UINT64_T:
            return valObject.data().get_uint8()
        elif type == sr.SR_INT64_T:
            return valObject.data().get_int64()
        elif type == sr.SR_INT32_T:
            return valObject.data().get_int32()
        elif type == sr.SR_INT16_T:
            return valObject.data().get_int16()
        elif type == sr.SR_INT64_T:
            return valObject.data().get_int8()
        elif type == sr.SR_BOOL_T:
            return valObject.data().get_bool()
        elif type == sr.SR_ENUM_T:
            return valObject.data().get_enum()
        elif type == sr.SR_CONTAINER_PRESENCE_T:
            return True
        elif type == sr.SR_CONTAINER_T:
            raise NodeHasNoValue('container', xpath)
        elif type == sr.SR_LEAF_EMPTY_T:
            raise NodeHasNoValue('empty-leaf', xpath)
        elif type == sr.SR_LIST_T:
            return None
        elif type == sr.SR_DECIMAL64_T:
            return valObject.data().get_decimal64()

        raise NodeHasNoValue('unknown', xpath)


class NodeHasNoValue(Exception):

    """
    Raised when accessing a non-presence container, list, or anything which does not
    have a value.
    A decendent node is could be fetched.
    """

    def __init__(self, nodetype, xpath):
        super().__init__("The node: %s at %s has no value" % (nodetype, xpath))


class NodeNotAList(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s is not a list" % (xpath))


class ListWrongNumberOfKeys(Exception):

    def __init__(self, xpath, require, given):
        super().__init__("The path: %s is a list requiring %s keys but was given %s keys" % (xpath, require, given))


class NonExistingNode(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s does not point of a valid schema node in the yang module" % (xpath))


class CommitFailed(Exception):

    def __init__(self, message):
        super().__init__("The commit failed.\n%s" % (message))
