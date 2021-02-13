from yangvoodoo import Cache, Common, Errors, Types


class Context:

    def __init__(self, module, data_access_layer, yang_schema, yang_ctx, log=None):
        self.module = module
        self.schema = yang_schema
        self.schemactx = yang_ctx
        self.dal = data_access_layer
        self.schemacache = Cache.Cache()
        self.log = log
        self.yang_module = module

    def _trace(self, vnt, yn, context, p):
        self.log.trace("%s: %s %s\nschema: %s\ndata: %s\nparent of: %s", vnt, context, yn.libyang_node,
                       yn.real_schema_path,  yn.real_data_path, p)


class Node:

    """
    Constraints:

    Node based access is provided for a particular yang module, whenever we run 'get_node'
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

    Things held on node
    --------------------
      - real_data_path   = an XPATH expression for the path - with prefixes and values pointing to exact instances
                           of data. This is used for fetching data.... e.g.
                           integrationtest:outsidelist[leafo='its cold outside']/integrationtest:otherinsidelist
                           [otherlist1='uno'][otherlist2='due'][otherlist3='tre']/integrationtest:language
      - real_schema_path = an XPATH expression for the path - with prefixes but no specific instances of data
                           included. This is used for looking up schema definitions.... e.g.
                           /integrationtest:outsidelist/integrationtest:otherinsidelist/integrationtest:language
      - libyang_node     = The libyang node for this schema path of the yang model.
    """

    _NODE_TYPE = 'Node'

    def __init__(self, context, node, parent_self=None):
        self.__dict__['_context'] = context
        self.__dict__['_node'] = node
        self.__dict__['_parent'] = parent_self
        self.__dict__['_path'] = node.real_data_path
        self._specific_init()

    def __name__(self):
        return 'VoodooNode'

    def __repr__(self):
        return self._base_repr()

    def _base_repr(self):
        return 'Voodoo%s{%s}' % (self._NODE_TYPE, self._node.real_data_path)

    def __del__(self):
        pass
        # path = self.__dict__['_path']

    def _specific_init(self):
        pass

    def __setitem__(self, arg, val):
        if not isinstance(arg, str):
            raise ValueError("node['child'] only supports a single argument.")
        return self.__setattr__(arg, val)

    def __getitem__(self, arg):
        if not isinstance(arg, str):
            raise ValueError("node['child'] only supports a single argument.")
        return self.__getattr__(arg)

    def __getattr__(self, attr):
        if attr in ('_ipython_canary_method_should_not_exist_', '_repr_mimebundle_'):
            raise AttributeError('Go Away!')
        context = self.__dict__['_context']
        node = self.__dict__['_node']
        context.log.trace("__getattr__ %s %s", attr, node.real_schema_path)

        # path = self.__dict__['_path']
        # spath = self.__dict__['_spath']

        node_schema = Common.Utils.get_yangnode(node, context, attr)
        node_type = node_schema.nodetype()

        if node_type == 1:
            # assume this is a container (or a presence container)
            if node_schema.presence() is None:
                # Return Object
                context._trace("Container", node_schema, context, self)
                return Container(context, node_schema, self)
            else:
                # Return Object
                context._trace("PresenceContainer", node_schema, context, self)
                return PresenceContainer(context, node_schema, self)
        elif node_type == Types.LIBYANG_NODETYPE['LEAF']:
            # TODO: need to consider unions of enum's in future - there is already a plan for a formalValidator class
            leaf_type = node_schema.type().base()
            if leaf_type == 5:
                # Return Object
                context._trace("Empty", node_schema, context, None)
                return Empty(context, node_schema)
            # if leaf_type == 6:
            #    return Enum(context, new_xpath, new_spath, node_schema)
            context.log.trace("Returning Literal value from datastore for %s", node_schema.real_data_path)
            dal_value = context.dal.get(node_schema.real_data_path, default_value=node_schema.default())
            if dal_value is None and leaf_type in Types.NUMBERS:
                return 0
            if leaf_type == Types.DATA_ABSTRACTION_MAPPING['BOOLEAN']:
                if dal_value == 'true':
                    return True
                elif dal_value == 'false':
                    return False
            return dal_value
        elif node_type == Types.LIBYANG_NODETYPE['LIST']:
            # Return Object
            context._trace("List", node_schema, context, self)
            return List(context, node_schema, self)
        elif node_type == Types.LIBYANG_NODETYPE['LEAFLIST']:
            # Return Object
            context._trace("LeafList", node_schema, context, self)
            return LeafList(context, node_schema, self)
        elif node_type == Types.LIBYANG_NODETYPE['CHOICE']:
            """
            Note: for choices in terms of data we don't render the 'case'
            beertype = "/integrationtest:morecomplex/integrationtest:inner/integrationtest:beer-type/"
            list(yangctx.find_path(beertype + "integrationtest:craft/integrationtest:brewdog"))

            However: when rendering the lookups for libyang schema we must include the case, which
            means the following is invalid.
            list(yangctx.find_path(beertype + "integrationtest:brewdog"))
            """
            context._trace("Choice", node_schema, context, self)
            return Choice(context, node_schema, self)
        elif node_type == Types.LIBYANG_NODETYPE['CASE']:
            context._trace("Case", node_schema, context, self)
            return Case(context, node_schema, self)

        context.log.error("The nodetype %s for schema %s is not supported.", node_type, node_schema.real_schema_path)
        raise NotImplementedError("The YANG structure at %s of type %s is not supported." % (node_schema.real_schema_path, node_type))

    def __setattr__(self, attr, val):
        context = self.__dict__['_context']
        node = self.__dict__['_node']
        node_schema = Common.Utils.get_yangnode(node, context, attr)
        context.log.trace("__setattr__ %s=%s %s", attr, val, node.real_data_path)

        if context.readonly:
            raise Errors.ReadonlyError()

        if not node_schema.nodetype() == Types.LIBYANG_NODETYPE['LEAF']:
            raise Errors.CannotAssignValueToContainingNode(attr)

        if node_schema.is_key():
            raise Errors.ListKeyCannotBeChanged(node_schema.real_data_path, attr)

        leaf_type = node_schema.type().base()
        # Enumeration:
        if leaf_type == 6:
            match = False
            for (enum_valid_val, _) in node_schema.type().enums():
                if str(enum_valid_val) == str(val):
                    match = True
            if not match:
                self._raise_ValueDoesMatchEnumeration(node_schema, val)

        if val is None:
            context.dal.delete(node_schema.real_data_path)
            return

        backend_type = Common.Utils.get_yang_type(node_schema.type(), val, node_schema.real_data_path)
        context.dal.set(node_schema.real_data_path, val, backend_type)

    @staticmethod
    def _raise_ValueDoesMatchEnumeration(node_schema, val):
        raise Errors.ValueDoesMatchEnumeration(node_schema.real_data_path, val)

    def __dir__(self, no_translations=False):
        node = self._node
        context = self._context
        context.log.trace("__dir__ %s", node.real_schema_path)

        if node.real_schema_path == "":
            search_path = "/" + context.module + ":*"
        else:
            search_path = node.real_schema_path + "/*"

        answer = []
        for child in context.schemactx.find_path(search_path):
            child_name = child.name()
            if child_name in Types.RESERVED_PYTHON_KEYWORDS:
                child_name = child_name + '_'
            if '-' in child_name and not no_translations:
                new_child_name = child_name.replace('-', '_')
                child_name = new_child_name
            answer.append(child_name)
        answer.sort()
        return answer


class Empty():

    """
    This represents a YANG Empty Leaf, which can be create()d, and remove()d, however they do
    not actually store a value.

    The presence of the empty leaf can be tested with exists()

    In an XML representation they appear as
        <emptyleaf/>

    """

    _NODE_TYPE = "Empty"

    def __init__(self, context, node_schema):
        self.__dict__['_context'] = context
        self.__dict__['_node'] = node_schema

    def __dir__(self):
        return []

    def create(self):
        context = self._context
        node = self._node

        if context.readonly:
            raise Errors.ReadonlyError()

        context.dal.set(node.real_data_path, None, 5)

    def exists(self):
        context = self._context
        node = self._node
        exists = context.dal.get(node.real_data_path)
        return exists is not None

    def remove(self):
        context = self._context
        node = self._node
        context.dal.uncreate(node.real_data_path)

    def __repr__(self):
        node = self._node
        path = node.real_data_path
        if self.exists():
            return "VoodooEmpty{%s} - Exists" % (path)
        return "VoodooEmpty{%s} - Does Not Exist" % (path)


class ContainingNode(Node):

    pass


class Choice(Node):

    _NODE_TYPE = "Choice"

    def __repr__(self):
        node = self._node
        return 'Voodoo%s{%s/...%s}' % (self._NODE_TYPE, node.real_data_path, node.real_schema_path.split(":")[-1])


class Case(Node):

    _NODE_TYPE = "Case"

    def __repr__(self):
        node = self.__dict__['_node']
        return 'Voodoo%s{%s/...%s}' % (self._NODE_TYPE, node.real_data_path, node.real_schema_path.split(":")[-1])


class LeafList(Node):

    """
    Represents a Leaf List
    """

    _NODE_TYPE = "LeafList"

    def __dir__(self):
        return []

    def create(self, value):
        """
        Create an entry into a leaf list, returning the value.

        If the item already exists in the list this operation will silenty
        do nothing.

        libyang supports creating leaf-list elements with both single/double quotes,
        however when using XPATH to select leaf-list elements this isn't possible.
        """
        context = self._context
        node = self._node

        if context.readonly:
            raise Errors.ReadonlyError()

        if value == "":
            raise Errors.ListItemCannotBeBlank(node.real_data_path)

        backend_type = Common.Utils.get_yang_type_from_path(context, node.real_schema_path, value)
        context.dal.add(node.real_data_path, value, backend_type)

        return value

    def __iter__(self):
        context = self._context
        node = self._node
        # Return Object
        return LeafListIterator(context, node,  self)

    def __len__(self):
        context = self._context
        node = self._node
        results = context.dal.gets(node.real_data_path)
        return len(list(results))

    def __delitem__(self, arg):
        context = self._context
        node = self._node

        if context.readonly:
            raise Errors.ReadonlyError()

        context.dal.remove(node.real_data_path, arg)

        return None

    def get_index(self, index):
        """
        Get an item from the list by index.

        Example:
            node.get_index(0)               - returns the value for the leaf-list at the index requested.
        """
        context = self._context
        node = self._node

        results = list(context.dal.gets(node.real_data_path))
        try:
            result = results[index]
        except IndexError:
            raise Errors.LeafListDoesNotContainIndexError(len(results), index, node.real_data_path)

        return result


class List(ContainingNode):

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
        context = self._context
        node = self._node
        (keys, values) = Common.Utils.get_key_val_tuples(context, node, list(args))

        node = Common.Utils.get_yangnode(node, context, keys=keys, values=values)
        if context.readonly:
            raise Errors.ReadonlyError()

        context.dal.create(node.real_data_path, keys=keys, values=values)
        # Return Object
        new_node = Common.YangNode(node.libyang_node, node.real_schema_path, node.real_data_path)
        return ListElement(context, new_node, self)

    def __getattr__(self, attr):
        node = self._node
        context = self._context

        if attr == '_xpath_sorted':
            # Return Object
            context._trace("SortedList", node, context, self)
            return SortedList(context, node, self)

        raise Errors.ListItemsMustBeAccesssedByAnElementError(node.real_data_path, attr)

    def __setattr__(self, attr, value):
        node = self._node
        raise Errors.ListItemsMustBeAccesssedByAnElementError(node.real_data_path, attr)

    def __len__(self):
        context = self.__dict__['_context']
        return context.dal.gets_len(self._node.real_data_path)

    def elements(self, sorted_by_xpath=False):
        """
        Return a generator of xpaths for each value in the list.

        The datastore will maintain the order entries were originally added into the list.
        The sorted_by_xpath argument can be used to sort the list by xpath.
        """
        context = self._context
        node = self._node

        if sorted_by_xpath:
            results = context.dal.gets_sorted(node.real_data_path, node.real_schema_path,  ignore_empty_lists=True)
        else:
            results = context.dal.gets_unsorted(node.real_data_path, node.real_schema_path, ignore_empty_lists=True)

        # Return Object
        return results

    def keys(self, sorted_by_xpath=False):
        """
        Return a list of keys in the list.

        This is currently not supported.
        """
        node = self._node
        keys = Common.Utils.get_keys_from_a_node(node)
        translated_keys = []
        for k in keys:
            if k in Types.RESERVED_PYTHON_KEYWORDS:
                translated_keys.append(k.replace('-', '_') + '_')
            else:
                translated_keys.append(k.replace('-', '_'))
        translated_keys.sort()
        return translated_keys

    def __dir__(self):
        return self.keys()

    def get(self, *args):
        """
        Get an item from the list

        Example:
          node.get(value)                   - fetch item where there is a single key.
          node.get(value1, value2)          - fetch item where there is a composite key.

        Returns a ListElement Node.

        Alternatively access data by node[value] or node[value1, value2]
        """
        context = self._context
        node = self._node
        (keys, values) = Common.Utils.get_key_val_tuples(context, node, list(args))
        predicates = Common.Utils.encode_xpath_predicates('', keys, values)
        if not context.dal.has_item(node.real_data_path + predicates):
            raise Errors.ListDoesNotContainElement(node.real_data_path + predicates)
        # Return Object
        new_node = Common.YangNode(node.libyang_node, node.real_schema_path, node.real_data_path+predicates)
        return ListElement(context, new_node, self)

    def get_index(self, index):
        """
        Get an item from the list by index.

        Example:
            node.get_index(0)               - returns the first list element assuming the list is big enough
        """
        context = self._context
        node = self._node

        results = list(context.dal.gets_unsorted(node.real_data_path, node.real_schema_path,
                                                 ignore_empty_lists=True))

        try:
            result = results[index]
        except IndexError:
            raise Errors.ListDoesNotContainIndexError(len(results), index, node.real_data_path)

        # Return Object
        new_node = Common.YangNode(node.libyang_node, node.real_schema_path, result)
        return ListElement(context, new_node, self)

    def __iter__(self):
        context = self._context
        node = self._node
        # Return Object
        return ListIterator(context, node, self, xpath_sorted=self._SORTED_LIST)

    def __contains__(self, *args):
        context = self._context
        node = self._node
        (keys, values) = Common.Utils.get_key_val_tuples(context, node, list(args))
        predicates = Common.Utils.encode_xpath_predicates('', keys, values)

        return context.dal.has_item(node.real_data_path + predicates)

    def __getitem__(self, *args):
        context = self._context
        node = self._node
        (keys, values) = Common.Utils.get_key_val_tuples(context, node, list(args))
        predicates = Common.Utils.encode_xpath_predicates('', keys, values)
        if not context.dal.has_item(node.real_data_path + predicates):
            raise Errors.ListDoesNotContainElement(node.real_data_path + predicates)

        # Return Object
        new_node = Common.YangNode(node.libyang_node, node.real_schema_path, node.real_data_path+predicates)
        return ListElement(context, new_node, self)

    def __delitem__(self, *args):
        context = self._context
        node = self._node
        if context.readonly:
            raise Errors.ReadonlyError()

        (keys, values) = Common.Utils.get_key_val_tuples(context, node, list(args))
        predicates = Common.Utils.encode_xpath_predicates('', keys, values)
        context.dal.uncreate(node.real_data_path + predicates)

        return None


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

    def __init__(self, context, node, parent_self, xpath_sorted=False):
        self.__dict__['_context'] = context
        self.__dict__['_node'] = node
        self.__dict__['_parent'] = parent_self
        self.__dict__['_xpath_sorted'] = xpath_sorted
        if xpath_sorted:
            self.__dict__['_iterator'] = context.dal.gets_sorted(node.real_data_path, node.real_schema_path, ignore_empty_lists=True)
        else:
            self.__dict__['_iterator'] = context.dal.gets_unsorted(node.real_data_path, node.real_schema_path, ignore_empty_lists=True)

    def __next__(self):
        context = self._context
        node = self._node
        parent = self._parent
        this_xpath = next(self._iterator)
        # Return Object
        new_node = Common.YangNode(node.libyang_node, node.real_schema_path, this_xpath)
        return ListElement(context, new_node, parent)

    def __repr__(self):
        base_repr = self._base_repr()
        if self.__dict__['_xpath_sorted']:
            return base_repr + " Sorted By XPATH"
        return base_repr + " Sorted By User (datastore)"


class LeafListIterator(Node):

    _NODE_TYPE = 'ListIterator'

    def __init__(self, context, node, parent_self, xpath_sorted=False):
        self.__dict__['_context'] = context
        self.__dict__['_node'] = node
        self.__dict__['_parent'] = parent_self
        self.__dict__['_xpath_sorted'] = xpath_sorted
        self.__dict__['_iterator'] = context.dal.gets(node.real_data_path)

    def __next__(self):
        return next(self.__dict__['_iterator'])


class ListElement(Node):

    """
    Represents a specific instance of a list element from a yang module.
    The child nodes are accessible from this node.
    """

    _NODE_TYPE = 'ListElement'


class Container(ContainingNode):
    """
    Represents a Container from a yang module, with access to the child
    elements.
    """

    _NODE_TYPE = 'Container'


class PresenceContainer(Container):

    """
    Represents a PresenceContainer from a yang module, with access to the child
    elements. The exists() method will return True if this container exists
    (either created implicitly because of children or explicitly).
    """

    _NODE_TYPE = 'PresenceContainer'

    def exists(self):
        context = self._context
        path = self._node.real_data_path
        return context.dal.container(path)

    def create(self):
        context = self._context
        node = self._node

        if context.readonly:
            raise Errors.ReadonlyError()

        context.dal.create_container(node.real_data_path)
        return PresenceContainer(context, node, self)

    def destroy(self):
        context = self._context
        node = self._node

        if context.readonly:
            raise Errors.ReadonlyError()

        context.dal.uncreate(node.real_data_path)
        return None

    def __repr__(self):
        base_repr = self._base_repr()
        if self.exists():
            return base_repr + " Exists"
        return base_repr + " Does Not Exist"


class Root(ContainingNode):

    _NODE_TYPE = 'Root'

    def __repr__(self):
        context = self.__dict__['_context']
        return "VoodooTopNode{} YANG Module: " + context.module


class SuperRoot:

    _NODE_TYPE = "SuperRoot"

    def __init__(self):
        self._nodes = {}
        self._node = None

    def attach_node_from_session(self, session, attachment_point):
        """
        From the VooodooNode provided
        """
        node = session.get_node()
        if not hasattr(node, attachment_point):
            raise ValueError('thing isnthere')

        setattr(self, attachment_point, getattr(node, attachment_point))
        self._nodes[attachment_point] = session
        self._node = node
        return getattr(node, attachment_point)

    def __dir__(self):
        k = list(self._nodes.keys())
        k.sort()
        return k

    def __repr__(self):
        return "VoodooSuperRoot{}"
