import libyang
import yangvoodoo.Errors
from yangvoodoo import Types


class Context:

    def __init__(self, module, data_access_layer, yang_schema, yang_ctx, cache=None, log=None):
        self.module = module
        self.schema = yang_schema
        self.schemactx = yang_ctx
        self.dal = data_access_layer
        if cache is None:
            self.schemacache = Cache()
        else:
            self.schemacache = cache
        self.log = log
        self.yang_module = module


class Cache:

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


class Node:

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

    Things held of a Context
    ------------------------
      - module    = the name of the yang module (e.g integrationtest)
      - dal       = An instantiated object of DataAccess() - one object used for all access.
                    Note: it is possible to access sysrepo diretly via root._context.dal.session
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

    def __init__(self, context, path='', spath='', parent_self=None):
        self.__dict__['_context'] = context
        self.__dict__['_path'] = path
        self.__dict__['_spath'] = spath
        self.__dict__['_parent'] = parent_self
        self._specific_init()

    def __name__(self):
        return 'VoodooNode'

    def __repr__(self):
        return self._base_repr()

    def _base_repr(self):
        path = self.__dict__['_path']
        return 'Voodoo%s{%s}' % (self._NODE_TYPE, path)

    def __del__(self):
        pass
        # path = self.__dict__['_path']

    def _specific_init(self):
        pass

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
        if attr in ('_ipython_canary_method_should_not_exist_', '_repr_mimebundle_'):
            raise AttributeError('Go Away!')
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        if attr == '_xpath_sorted' and self._NODE_TYPE == 'List':
            # Return Object
            return SortedList(context, path, spath, self)

        # Schema Path is a combination of the previous schema path + the attribute
        # This order of things is pretty important
        # - get_schema_of_path lets us convert '_' to '-' if the leaf doesn't exist
        # to take account of the conversions
        node_schema = self._get_schema_of_path(self._form_xpath(spath, attr))

        # Note: when we call get_schema_of_path we will be given a <libyang> instance
        # with an additioanl attribute 'underscore_translated'
        # format_xpath understands this and if it sees underscore_translated it will
        # then adjust this on the fly.
        new_spath = self._form_xpath(spath, attr, node_schema)
        new_xpath = self._form_xpath(path, attr, node_schema)
        node_type = node_schema.nodetype()

        if node_type == 1:
            # assume this is a container (or a presence container)
            if node_schema.presence() is None:
                # Return Object
                return Container(context, new_xpath, new_spath, self)
            else:
                # Return Object
                return PresenceContainer(context, new_xpath, new_spath, self)
        elif node_type == 4:
            # Assume this is always a primitive
            return context.dal.get(new_xpath)
        elif node_type == 16:
            # Return Object
            return List(context, new_xpath, new_spath, self)

        raise ValueError('Get - not sure what the type is...%s' % (node_type))

    def _get_yang_type(self, node_schema, value=None, xpath=None):
        """
        Map a given yang-type (e.g. string, decimal64) to a type code for the backend.

        Sysrepo has a few cases- centered around the sr.Val() class
         1) For most types we can provide just the value
         2) For enumerations we must provide sr.SR_ENUM_T
         3) For uint32 (and other uints) we need to provide the type still (we can form the Val object without, but
            sysrepo will not accept the data)
         4) For decimal64 we must not provide any type
         5) As long as a uint8/16/32/64 int8/16/32/64 fits the range constraints sysrepo doesn't strictly enforce it
            (when considering a union of all 8 types). For simple leaves sysrepo is strict.

        Libyang gives us the following type from
            node = next(yangctx.find_path(`'/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf666'`))
            node.type().base()


        Unless we find a Union (11) or leafref (9) then we can just map directly.
        """
        base_type = node_schema.base()
        if base_type in Types.LIBYANG_MAPPING:
            return Types.LIBYANG_MAPPING[base_type]

        if base_type == 9:  # LEAF REF
            base_type = node_schema.leafref_type().base()
            node_schema = node_schema.leafref_type()
            if base_type in Types.LIBYANG_MAPPING:
                return Types.LIBYANG_MAPPING[base_type]

        if base_type == 11:  # Uninon
            """
            Note: for sysrepo if we are a union of enumerations and other types
            then we must set the data as sr.SR_ENUM_T if it matches the enumeration.
            e.g. leaf666/type6
            """

            u_types = []
            for union_type in node_schema.union_types():
                if union_type.base() == 11:
                    raise NotImplementedError('Union containing unions not supported (see README.md)')
                elif union_type.base() == 9:
                    raise NotImplementedError('Union containing leafrefs not supported (see README.md)')
                elif union_type.base() == 6:
                    # TODO: we need to lookup enumerations
                    for (val, validx) in union_type.enums():
                        if str(val) == str(value):
                            return Types.DATA_ABSTRACTION_MAPPING['ENUM']
                u_types.append(union_type.base())

            if 10 in u_types and isinstance(value, str):
                return Types.DATA_ABSTRACTION_MAPPING['STRING']
            elif isinstance(value, float):
                return Types.DATA_ABSTRACTION_MAPPING['DECIMAL64']
            if isinstance(value, int):
                if 12 in u_types and value >= -127 and value <= 128:
                    return Types.DATA_ABSTRACTION_MAPPING['INT8']
                elif 13 in u_types and value >= 0 and value <= 255:
                    return Types.DATA_ABSTRACTION_MAPPING['UINT8']
                elif 14 in u_types and value >= -32768 and value <= 32767:
                    return Types.DATA_ABSTRACTION_MAPPING['INT16']
                elif 15 in u_types and value >= 0 and value <= 65535:
                    return Types.DATA_ABSTRACTION_MAPPING['UINT16']
                elif 16 in u_types and value >= -2147483648 and value <= 2147483647:
                    return Types.DATA_ABSTRACTION_MAPPING['INT32']
                elif 17 in u_types and value >= 0 and value <= 4294967295:
                    return Types.DATA_ABSTRACTION_MAPPING['UINT32']
                elif 19 in u_types and value >= 0:
                    return Types.DATA_ABSTRACTION_MAPPING['UINT64']
                else:
                    return Types.DATA_ABSTRACTION_MAPPING['INT64']

        raise NotImplementedError('Unable to handle the yang type at path %s (this may be listed as a corner-case on the README already' % (xpath))

    def __setattr__(self, attr, val):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        context.log.debug('spath for setattr %s', spath)
        spath = self._form_xpath(spath, attr)
        node_schema = self._get_schema_of_path(spath)
        xpath = self._form_xpath(path, attr, node_schema)

        if val is None:
            context.dal.delete(xpath)
            return

        backend_type = self._get_yang_type(node_schema.type(), val, xpath)

        context.dal.set(xpath, val, backend_type)

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
        raise yangvoodoo.Errors.NonExistingNode(xpath)


class List(Node):

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

    The datastore will maintain the order list elements are added, if you
    prefer to see items sorted (based on XPATH) then you may iterate around
    <this object>._xpath_sorted() instead.

    Note: values for the list keys should be provided as they would in an
    XPATH express. i.e. python True > 'true', False > 'false'

    """

    _NODE_TYPE = 'List'
    _SORTED_LIST = False
    #
    # def _specific_init(self):
    #     context = self.__dict__['_context']
    #     path = self.__dict__['_path']
    #     spath = self.__dict__['_spath']
    #     # Return Object
    #     self.__dict__['_xpath_sorted'] = SortedList(context, path, spath, self)
    #

    def __dir__(self):
        return []

    def create(self, *args):
        """
        Create a list element.

        For composite-key lists then each key within the yang module must be provided
        in the same order it is defined within the yang module.

        Example:
          node.create(value)                - create item where there is a single key.
          node.create(value1, value2)       - create item where there is a composite key.

        Returns a ListElement Node of the newly created list item.

        Calling the create method a second time will not overwrite/remove data.
        """
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here

        context.dal.create(new_xpath)
        # Return Object
        return ListElement(context, new_xpath, new_spath, self)

    def __len__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        results = context.dal.gets_unsorted(path, ignore_empty_lists=True)
        return len(list(results))

    def xpaths(self, sorted_by_xpath=False):
        """
        Return a list of xpaths for each value in the list.

        The datastore will maintain the order entries were originally added into the list.
        The sorted_by_xpath argument can be used to sort the list by xpath.
        """
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        if sorted_by_xpath:
            results = context.dal.gets_sorted(spath, ignore_empty_lists=True)
        else:
            results = context.dal.gets_unsorted(spath, ignore_empty_lists=True)

        # Return Object
        return results

    def keys(self, sorted_by_xpath=False):
        """
        Return a list of keys in the list.

        This is currently not supported.
        """
        # This will need to break apart the XPATH strings into tuples of values.
        raise NotImplementedError("The keys() method is not supported")

    def get_last(self, sorted_by_xpath=False):
        """
        Return the last element from the list, the datastore will store elements in a list in
        the order they have been created.

        The optional argument sorted_by_xpath will sort the list by XPATH before returning the
        last item.
        """
        # Note by default sysrepo stores list elements in the order they are put into the
        # database.
        # list(session.gets('/integrationtest:simplelist'))
        # Out[1]:
        # ["/integrationtest:simplelist[simplekey='A']",
        #  "/integrationtest:simplelist[simplekey='Z']",
        #  "/integrationtest:simplelist[simplekey='b']"]
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        results = list(context.dal.gets_sorted(spath, ignore_empty_lists=True))

        this_xpath = results[-1]
        # Return Object
        return ListElement(context, this_xpath, spath, self)

    def get_first(self, sorted_by_xpath=False):
        """
        Return the first element from the list, the datastore will store elements in a list in
        the order they have been created.

        The optional argument sorted_by_xpath will sort the list by XPATH before returning the
        first item.
        """
        # Note by default sysrepo stores list elements in the order they are put into the
        # database.
        # list(session.gets('/integrationtest:simplelist'))
        # Out[1]:
        # ["/integrationtest:simplelist[simplekey='A']",
        #  "/integrationtest:simplelist[simplekey='Z']",
        #  "/integrationtest:simplelist[simplekey='b']"]
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        results = list(context.dal.gets_sorted(spath, ignore_empty_lists=True))

        this_xpath = results[0]
        # Return Object
        return ListElement(context, this_xpath, spath, self)

    def get(self, *args):
        """
        Get an item from the list

        Example:
          node.get(value)                   - fetch item where there is a single key.
          node.get(value1, value2)          - fetch item where there is a composite key.

        Returns a ListElement Node.

        Alternatively access data by node[value] or node[value1, value2]
        """
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here
        results = list(context.dal.gets_unsorted(new_xpath))
        # Return Object
        return ListElement(context, new_xpath, new_spath, self)

    def __iter__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        # Return Object
        return ListIterator(context, path, spath, self, xpath_sorted=self._SORTED_LIST)

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
        # TODO: optimise this, we should be able to just test membership directly on the backend
        try:
            reults = list(context.dal.gets_unsorted(new_xpath))
            return True
        except Exception as err:
            pass
        return False

    def __getitem__(self, *args):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        if isinstance(args[0], tuple):
            conditional = self._get_keys(list(args[0]))
        else:
            conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here
        list(context.dal.gets_unsorted(new_xpath))
        # Return Object
        return ListElement(context, new_xpath, new_spath, self)

    def __delitem__(self, *args):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        if isinstance(args[0], tuple):
            conditional = self._get_keys(list(args[0]))
        else:
            conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't
        context.dal.delete(new_xpath)

        return None

    def _get_keys(self, *args):
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        node_schema = self._get_schema_of_path(spath)
        keys = list(node_schema.keys())

        if not len(args[0]) == len(keys):
            raise yangvoodoo.Errors.ListWrongNumberOfKeys(path, len(keys), len(args[0]))

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


class SortedList(List):

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

    The only difference between this object and the base List type is that
    in this case we go to lengths to sort the list (based on XPATH) rather than
    the order things are defiend.
    """

    _NODE_TYPE = 'SortedList'
    _SORTED_LIST = True


class ListIterator(Node):

    _NODE_TYPE = 'ListIterator'

    def __init__(self, context, path, spath, parent_self, xpath_sorted=False):
        self.__dict__['_context'] = context
        self.__dict__['_path'] = path
        self.__dict__['_spath'] = spath
        self.__dict__['_parent'] = parent_self
        self.__dict__['_xpath_sorted'] = xpath_sorted
        if xpath_sorted:
            self.__dict__['_iterator'] = context.dal.gets_sorted(path, ignore_empty_lists=True)
        else:
            self.__dict__['_iterator'] = context.dal.gets_unsorted(path, ignore_empty_lists=True)

    def __next__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        parent = self.__dict__['_parent']
        this_xpath = next(self.__dict__['_iterator'])
        # Return Object
        return ListElement(context, this_xpath, spath, parent)

    def __repr__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        base_repr = self._base_repr()
        if self.__dict__['_xpath_sorted']:
            return base_repr + " Sorted By XPATH"
        return base_repr + " Sorted By User (datastore)"


class ListElement(Node):

    """
    Represents a specific instance of a list element from a yang module.
    The child nodes are accessible from this node.
    """

    _NODE_TYPE = 'ListElement'


class Container(Node):
    """
    Represents a Container from a yang module, with access to the child
    elements.
    """

    _NODE_TYPE = 'Container'


class PresenceContainer(Node):

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
        spath = self.__dict__['_spath']
        context.dal.create_container(path)
        return PresenceContainer(context, path, spath, self)

    def __repr__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        base_repr = self._base_repr()
        if context.dal.get(path) is True:
            return base_repr + " Exists"
        return base_repr + " Does Not Exist"


class Root(Node):

    _NODE_TYPE = 'Root'

    def __repr__(self):
        context = self.__dict__['_context']
        return "VoodooRoot{} YANG Module: " + context.module
