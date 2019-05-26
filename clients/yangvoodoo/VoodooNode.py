import libyang
import yangvoodoo.Errors
from yangvoodoo import Cache, Common, TemplateNinja


class Context:

    def __init__(self, module, data_access_layer, yang_schema, yang_ctx, cache=None, log=None):
        self.module = module
        self.schema = yang_schema
        self.schemactx = yang_ctx
        self.dal = data_access_layer
        if cache is None:
            self.schemacache = Cache.Cache()
        else:
            self.schemacache = cache
        self.log = log
        self.yang_module = module


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

    def __getattr__(self, attr):
        if attr in ('_ipython_canary_method_should_not_exist_', '_repr_mimebundle_'):
            raise AttributeError('Go Away!')
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        if attr == '_xpath_sorted' and self._NODE_TYPE == 'List':
            # Return Object
            return SortedList(context, path, spath, self)

        new_spath = Common.Utils.form_schema_xpath(spath, attr, context.module)
        node_schema = Common.Utils.get_schema_of_path(new_spath, context)

        new_xpath = Common.Utils.form_value_xpath(path, attr, context.module, node_schema)
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
        elif node_type == 8:
            # Return Object
            return LeafList(context, new_xpath, new_spath, self)

        raise ValueError('Get - not sure what the type is...%s' % (node_type))

    def __setattr__(self, attr, val):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        spath = Common.Utils.form_schema_xpath(spath, attr, context.module)
        node_schema = Common.Utils.get_schema_of_path(spath, context)
        xpath = Common.Utils.form_value_xpath(path, attr, context.module, node_schema)

        if val is None:
            context.dal.delete(xpath)
            return

        backend_type = Common.Utils.get_yang_type(node_schema.type(), val, xpath)

        context.dal.set(xpath, val, backend_type)

    def __dir__(self):
        spath = self.__dict__['_spath']
        context = self.__dict__['_context']
        node_schema = Common.Utils.get_schema_of_path(spath, context)

        answer = []
        for child in node_schema.children():
            answer.append(child.name().replace('-', '_'))
        answer.sort()
        return answer


class ContainingNode(Node):

    pass


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
        """
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']

        if value == "":
            raise yangvoodoo.Errors.ListItemCannotBeBlank(spath)

        node_schema = Common.Utils.get_schema_of_path(spath, context)
        backend_type = Common.Utils.get_yang_type(node_schema.type(), value, path)

        context.log.debug("about to add: %s, %s, %s", path, value, backend_type)
        context.dal.add(path, value, backend_type)

        return value

    def __iter__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        # Return Object
        return LeafListIterator(context, path, spath, self)

    def __len__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        results = context.dal.gets(path)
        return len(list(results))

    def __delitem__(self, arg):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        context.dal.remove(path, arg)

        return None


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
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        new_spath = spath   # Note: we deliberartely won't use conditionals here

        keys = tuple(self.keys())
        values = []
        i = 0
        for arg in args:
            if arg == "":
                raise yangvoodoo.Errors.ListKeyCannotBeBlank(spath, keys[i])

            node_schema = Common.Utils.get_schema_of_path(Common.Utils.form_schema_xpath(spath, keys[i], context.module), context)
            yangtype = Common.Utils.get_yang_type(node_schema.type(), arg,
                                                  Common.Utils.form_schema_xpath(spath, keys[i], context.module))
            values.append((arg, yangtype))

        context.log.debug("about to create: %s, %s, %s, %s",  new_xpath, keys, values, context.module)
        context.dal.create(new_xpath, keys=keys, values=values, module=context.module)
        # Return Object
        return ListElement(context, new_xpath, new_spath, self)

    def __len__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        return context.dal.gets_len(path)

    def elements(self, sorted_by_xpath=False):
        """
        Return a generator of xpaths for each value in the list.

        The datastore will maintain the order entries were originally added into the list.
        The sorted_by_xpath argument can be used to sort the list by xpath.
        """
        context = self.__dict__['_context']
        spath = self.__dict__['_spath']
        path = self.__dict__['_path']

        if sorted_by_xpath:
            results = context.dal.gets_sorted(path, spath,  ignore_empty_lists=True)
        else:
            results = context.dal.gets_unsorted(path, spath, ignore_empty_lists=True)

        # Return Object
        return results

    def keys(self, sorted_by_xpath=False):
        """
        Return a list of keys in the list.

        This is currently not supported.
        """
        spath = self.__dict__['_spath']
        context = self.__dict__['_context']
        node_schema = Common.Utils.get_schema_of_path(spath, context)

        keys = []
        for k in node_schema.keys():
            keys.append(k.name())
        return keys

    def get_last(self, sorted_by_xpath=False):
        """
        Return the last element from the list, the datastore will store elements in a list in
        the order they have been created.

        The optional argument sorted_by_xpath will sort the list by XPATH before returning the
        last item.
        """
        context = self.__dict__['_context']
        spath = self.__dict__['_spath']

        results = list(context.dal.gets_sorted(spath, spath,  ignore_empty_lists=True))

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
        context = self.__dict__['_context']
        spath = self.__dict__['_spath']

        results = list(context.dal.gets_sorted(spath, spath, ignore_empty_lists=True))

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
        if not context.dal.has_item(new_xpath):
            raise yangvoodoo.Errors.ListDoesNotContainElement(new_xpath)
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
        context.log.debug("has item: %s", new_xpath)
        return context.dal.has_item(new_xpath)

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

        if not context.dal.has_item(new_xpath):
            raise yangvoodoo.Errors.ListDoesNotContainElement(new_xpath)
        # Return Object
        return ListElement(context, new_xpath, new_spath, self)

    def __delitem__(self, *args):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        if isinstance(args[0], tuple):
            conditional = self._get_keys(list(args[0]))
        else:
            conditional = self._get_keys(list(args))
        new_xpath = path + conditional
        context.dal.uncreate(new_xpath)

        return None

    def _get_keys(self, *args):
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        context = self.__dict__['_context']
        node_schema = Common.Utils.get_schema_of_path(spath, context)
        keys = list(node_schema.keys())

        if not len(args[0]) == len(keys):
            raise yangvoodoo.Errors.ListWrongNumberOfKeys(path, len(keys), len(args[0]))

        conditional = ""
        for i in range(len(keys)):
            value = self._get_xpath_value_from_python_value(args[0][i], keys[i].type())

            # Sysrepo doesn't like this version
            # conditional = conditional + "[%s:%s='%s']" % (context.module, keys[i].name(), value)
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
            self.__dict__['_iterator'] = context.dal.gets_sorted(path, spath, ignore_empty_lists=True)
        else:
            self.__dict__['_iterator'] = context.dal.gets_unsorted(path, spath, ignore_empty_lists=True)

    def __next__(self):
        context = self.__dict__['_context']
        spath = self.__dict__['_spath']
        parent = self.__dict__['_parent']
        this_xpath = next(self.__dict__['_iterator'])
        # Return Object
        return ListElement(context, this_xpath, spath, parent)

    def __repr__(self):
        base_repr = self._base_repr()
        if self.__dict__['_xpath_sorted']:
            return base_repr + " Sorted By XPATH"
        return base_repr + " Sorted By User (datastore)"


class LeafListIterator(Node):

    _NODE_TYPE = 'ListIterator'

    def __init__(self, context, path, spath, parent_self, xpath_sorted=False):
        self.__dict__['_context'] = context
        self.__dict__['_path'] = path
        self.__dict__['_spath'] = spath
        self.__dict__['_parent'] = parent_self
        self.__dict__['_xpath_sorted'] = xpath_sorted
        self.__dict__['_iterator'] = context.dal.gets(path)

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
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        context.log.debug("Calling have container: %s", path)
        return context.dal.container(path)

    def create(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        spath = self.__dict__['_spath']
        context.log.debug("Calling create container: %s", path)
        context.dal.create_container(path)
        return PresenceContainer(context, path, spath, self)

    def __repr__(self):
        context = self.__dict__['_context']
        path = self.__dict__['_path']
        base_repr = self._base_repr()
        if self.exists():
            return base_repr + " Exists"
        return base_repr + " Does Not Exist"


class Root(ContainingNode):

    _NODE_TYPE = 'Root'

    def __repr__(self):
        context = self.__dict__['_context']
        return "VoodooNodeRoot{} YANG Module: " + context.module

    def from_template(self, template):
        """
        Process a template with a number of data nodes. The result of processing the template
        with Jinja2 must be a valid XML document.

        Example:
            session.from_template(root, 'template1.xml')

            Process the template from the the path specified (i.e. template1.xml)
            In the Jinja2 templates the root object is available as 'root.'

            session.from_template(root, 'template1.xml', data_a=root.morecomplex)

            In this case the Jinja2 template will receive both 'data_a' as the subset of
            data at /morecomplex and root.

        The path to the template may be specified as a relative path (to where the python
        process is running (i.e. os.getcwd) or an exact path.

        IMPORTANT to note is that variable and logic is processed in the template based upon
        the data available at the time, then the result of the entire template is applied.
        To be clear consdiering this template
            <integrationtest>
                <simpleleaf>HELLO</simpleleaf>
                <default>{{ root.simpleleaf }}</default>
            </integrationtest>

            root.simpleleaf = 'GOODBYE'
            session.from_template(root, 'hello-goodbye.xml')

        The resulting value for simpleleaf will be 'GOODBYE' not hello.

        """

        templater = TemplateNinja.TemplateNinja()
        templater.from_template(self, template)


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

    def from_template(self, template, **kwargs):
        """
        Process a template with a number of data nodes. The result of processing the template
        with Jinja2 must be a valid XML document.

        Example:
            session.from_template(root, 'template1.xml')

            Process the template from the the path specified (i.e. template1.xml)
            In the Jinja2 templates the root object is available as 'root.'

            session.from_template(root, 'template1.xml', data_a=root.morecomplex)

            In this case the Jinja2 template will receive both 'data_a' as the subset of
            data at /morecomplex and root.

        The path to the template may be specified as a relative path (to where the python
        process is running (i.e. os.getcwd) or an exact path.

        IMPORTANT to note is that variable and logic is processed in the template based upon
        the data available at the time, then the result of the entire template is applied.
        To be clear consdiering this template
            <integrationtest>
                <simpleleaf>HELLO</simpleleaf>
                <default>{{ root.simpleleaf }}</default>
            </integrationtest>

            root.simpleleaf = 'GOODBYE'
            session.from_template(root, 'hello-goodbye.xml')

        The resulting value for simpleleaf will be 'GOODBYE' not hello.

        """

        templater = TemplateNinja.TemplateNinja()
        templater.from_template(self._node, template, **kwargs)
