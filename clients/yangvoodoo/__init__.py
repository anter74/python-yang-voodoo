#!/usr/bin/python3
import libyang
import re
import time
import logging
import socket
import importlib
import yangvoodoo.VoodooNode
from jinja2 import Template
from lxml import etree
import warnings


class LogWrap():

    ENABLED_INFO = True
    ENABLED_DEBUG = True

    REMOTE_LOG_IP = "127.0.0.1"
    REMOTE_LOG_PORT = 6666

    def __init__(self, local_log=False, remote_log=False):
        self.ENABLED = local_log
        self.ENABLED_REMOTE = remote_log

        if self.ENABLED:
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


class DataAccess:

    """
    This module provides two methods to access data, either XPATH based (low-level) or
    Node based (high-level).

    The default backend for this module is sysrepo, however when instantiating this class
    it is possible to send in an alternative 'data_abstraction_layer'. For the sysrepo based
    implementation see sysrepodal.py

    The data_abstraction_layer itself supports primitive operations such as get, set, create,
    create_container, gets_sorted, gets_unsorted, delete, commit, validate, refresh, connect.
    The key assumption is that the datastore itself will stored data based upon XPATH or
    similair path structure.


    Dependencies:
     - libyang 0.16.78 (https://github.com/rjarry/libyang-cffi/)
     - lxml
    """

    def __init__(self, log=None, local_log=False, remote_log=False, data_abstraction_layer=None):
        if not log:
            log = LogWrap(local_log=local_log, remote_log=remote_log)
        self.log = log
        self.session = None
        self.conn = None
        self.connected = False
        if data_abstraction_layer:
            self.data_abstraction_layer = data_abstraction_layer
        else:
            self.data_abstraction_layer = self._get_data_abastraction_layer(log)

    def _get_data_abastraction_layer(self, log):
        importlib.import_module('yangvoodoo.sysrepodal')
        return yangvoodoo.sysrepodal.SysrepoDataAbstractionLayer(log)

    def _help(self, node):
        """
        Provide help text from the yang module if available.
        """
        if node.__dict__['_spath'] == '':
            return None
        try:
            schema = next(node.__dict__['_context'].schemactx.find_path(node.__dict__['_spath']))
            return schema.description()
        except Exception:
            pass

    def from_template(self, root, template, **kwargs):
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

        variables = {'root': root}
        for variable_name in kwargs:
            variables[variable_name] = kwargs[variable_name]

        xmlstr = ""
        with open(template) as file_handle:
            t = Template(file_handle.read())
            xmlstr = t.render(variables)

        xpaths = self._convert_xml_to_xpaths(root, xmlstr)

        for xpath in xpaths:
            (value, valuetype) = xpaths[xpath]
            self.set(xpath, value, valuetype)

    def _convert_xml_to_xpaths(self, root, xmlstr):
        xpaths = {}
        xmldoc = etree.fromstring(xmlstr)
        tree = etree.ElementTree(xmldoc)

        module = xmldoc.tag
        path = "//"
        last_node = ''
        last_depth_count = 0
        xmldoc_iterator = xmldoc.iter()

        remove_squares = re.compile(r'\[\d+\]', re.UNICODE)
        list_predicates = {}

        for child in xmldoc_iterator:
            node = tree.getelementpath(child)
            path = '/' + node
            path = path.replace('/', '/' + module + ':')
            path = remove_squares.sub('', path)
            if node == '.':
                continue
            #
            # # The schema never ever takes predicates in the path
            node_schema = root._get_schema_of_path(path)
            node_type = node_schema.nodetype()

            value_path = path

            value_path = self._find_predicate_match(list_predicates, value_path)

            if node_schema.nodetype() == 16:
                predicates = self._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, value_path, list_predicates)
                xpaths[value_path + predicates] = (None, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['LIST'])

            if node_schema.nodetype() == 1 and not node_schema.presence():
                continue
            if node_type == 4 or (node_type == 1 and node_schema.presence()):
                type = root._get_yang_type(node_schema.type(), child.text, path)
                xpaths[value_path] = (child.text, type)

        return xpaths

    def _lookahead_for_list_keys(self, node_schema, xmldoc_iterator, module, value_path, list_predicates):
        """
        In the payloads for a NETCONF if we have the list /simplelist with a key of simplekey
        and a leaf of nonleafkey.

        The XML payload would look like

        <integrationtest>
            <simplelist>
                <simplekey>ThisIsTheKey</simplekey>
                <nonleafkey>NotTheKey</nonleafkey>
            </simplelist>
        </integrationtest>

        The XPATH for the LIST would be

            /integrationtest:simplelist[integrationtest:simplekey]

        The XPATH for the non leaf key would be

            /integrationtest:simplelist[integrationtest:simplekey]/integrationtest:nonleafkey


        Given a none_schema, this method will based on the YANG schema look for the required number
        of keys and attempt to read them from the XML.

        If we have the right number of keys we will add an entry to list_predicates

            list_predicates["/integrationtest:simplelist"] = "[integrationtest:simplekey]"

        """
        predicates = ""
        for key_required in node_schema.keys():
            try:
                next_xml_node = next(xmldoc_iterator)
            except StopIteration:
                raise yangvoodoo.Errors.XmlTemplateParsingBadKeys(key_required.name(), None)
            if not next_xml_node.tag == key_required.name():
                raise yangvoodoo.Errors.XmlTemplateParsingBadKeys(key_required.name(), next_xml_node.tag)
            predicates = predicates + "[" + module+':'+key_required.name() + "='" + next_xml_node.text + "']"
        list_predicates[value_path] = predicates

        return predicates

    def _find_predicate_match(self, list_predicates, path):
        """
        Finds if the leading part of our path has any predicates and tries to add them in.

        We expect to take in a path without any predicates (the input path), our goal is to
        return a value_path with the right predicates stitched in.
        e.g. /integrationtest:container-and-lists/integrationtest:multi-key-list/integrationtest:level2list

        In this case we have two lists, firstly 'multi-key-list' and secondly 'level2list'

        The list of predicates in list_predicates should contain, keys
         key: /integrationtest:container-and-lists/integrationtest:multi-key-list
         value: [integrationtest:A='a'][integrationtest:B='b']

        First time around the loop we will start tackle the first set of predicates for multi-key-list
         (i.e. we stitch in [integrationtest:A='a'][integrationtest:B='b'])

        Second time we lookup for a matching path with the result of our first loop
           ("/integrationtest:container-and-lists/integrationtest:multi-key-list[integrationtest:A='a']"
           "[integrationtest:B='b']/integrationtest:level2list")

        This should give us a new bit of predicates for the next list in the chain.
        "[integrationtest:level2key='22222']"

        The value path is returned.
        """
        value_path = path
        for predicate in list_predicates:
            if predicate in value_path:  # and predicate in list_predicates:
                start_pos = value_path.find(predicate)
                end_pos = start_pos + len(predicate)
                value_path = value_path[start_pos:start_pos+len(predicate)] + list_predicates[predicate] + value_path[end_pos:]

        return value_path

    def get_root(self, module=None, yang_location="../yang/"):
        """
        Instantiate Node-based access to the data stored in the backend defined by a yang
        schema. The data access will be constraint to the YANG module chosen when invoking
        this method.

        We must have access to the same YANG module loaded within in sysrepo, which can be
        set by modifying yang_location argument.
        """
        if module:
            self.data_abstraction_layer.module = module
            warnings.warn("<module> should not be sent into get_root - send into connect instead.")
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()

        yang_ctx = libyang.Context(yang_location)
        yang_schema = yang_ctx.load_module(self.module)

        self.data_abstraction_layer.setup_root()

        context = yangvoodoo.VoodooNode.Context(self.module, self, yang_schema, yang_ctx, log=self.log)

        self.help = self._help

        return yangvoodoo.VoodooNode.Root(context)

    def connect(self, module=None, tag='client'):
        """
        Connect to the datastore.

        returns: True
        """
        if not module:
            warnings.warn("<module> name should be sent into connect()")
        self.module = module
        connect_status = self.data_abstraction_layer.connect(self.module)
        self.session = self.data_abstraction_layer.session
        self.conn = self.data_abstraction_layer.conn
        self.connected = True
        return connect_status

    def disconnect(self):
        """
        Disconnect from the datastore - losing any pending changes to data which has not yet
        been committed.

        returns: True
        """
        self.connected = False
        return self.data_abstraction_layer.disconnect()

    def commit(self):
        """
        Commit pending changes to the datastore backend, it is possible to call validate()
        before a commit. The datastore has the final say if the changes are valid or not,
        the only assurance that the yangvoodoo objects can provide is that the data conforms
        to the YANG schema - it cannot guarantee the values are consistent with the full
        data held in the datastore.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.commit()

    def validate(self):
        """
        Validate the pending changes against the data in the backend datatstore without actually
        committing the data. The full set of rules within the YANG model/datatstore must be
        checked such that a user calling validate(), commit() in short sucession should get a
        failure to commit.

        returns: True or False
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.validate()

    def create_container(self, xpath):
        """
        Create a presence container - only suitable for use on presence containers.

        returns: VoodoooPresenceContainer()
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.create_container(xpath)

    def create(self, xpath):
        """
        Create a list item by XPATH including keys
         e.g. /path/to/list[key1='val1'][key2='val2'][key3='val3']

         returns: VoodooListElement()
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.create(xpath)

    def set(self, xpath, value, valtype=18):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        valtype defaults to 18 (STRING), see Types.DATA_ABSTRACTION_MAPPING for the
        full set of value types.

        returns: value
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.set(xpath, value, valtype)

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        """
        For the given XPATH (of a list) return an sorted list of XPATHS representing every
        list element within the list.

        returns: generator of sorted XPATHS
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.gets_sorted(xpath, ignore_empty_lists)

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        """
        For the given XPATH (of a list) return an unsorted list of XPATHS representing every
        list element within the list.
        This method must maintain the order that entries were added by the user into the list.

        returns: generator of XPATHS
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.gets_unsorted(xpath, ignore_empty_lists)

    def has_item(self, xpath):
        """
        Evaluate if the item is present in the datatsore, determines if a specific XPATH has been
        set, may be called on leaves, presence containers or specific list elements.

        returns: True or False
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.has_item(xpath)

    def get(self, xpath):
        """
        Get a specific path (leaf nodes or presence containers), in the case of leaves a python
        primitive is returned (i.e. strings, booleans, integers).
        In the case of non-terminating nodes (i.e. Lists, Containers, PresenceContainers) this
        method will return a Voodoo object of the relevant type.

        FUTURE CHANGE: in future enumerations should be returned as a specific object type


        returns: value or Vooodoo<X>
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.get(xpath)

    def delete(self, xpath):
        """
        Delete the data, and all decendants for a particular XPATH.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.delete(xpath)

    def refresh(self):
        """
        Ensure we are still connected to sysrepo and using the latest dataset.

        Note: if we are ever disconnected it is possible to simply just call
        the connect() method of this object.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.refresh()

    def is_session_dirty(self):
        """
        The definition of a dirty session is one which has had data changed since we opened
        our own session.

        Example1:
          session1.connect()                     session2.connect()
          root1.simpleleaf='1'                   root2.simpleleaf='2'
          session1.commit()                      ---
                                                 This session is now considered dirty
                                                 The data we commit as part of this session
                                                 will overwrite those of the first session
                                                 where there are overlaps.
          ---                                    session2.commit()
          This session is now considered dirty
          print(root1.simpleleaf)

        In this case the value 'simpleleaf' is set to 2, as session2 was committed last. There is
        no mechanism implemented to detect the conflict. The data from the first session was set
        for the moment in time between it's commit and session2's commit.

        This method 'is_session_dirty' can be used by application to decide if they wish to
        commit.

        Example2:
          session1.connect()                     session2.commit()
          root1.simplelist.create('A')           root2.simplelist.create('B')
          root1.commit()                         ---
                                                 This session is now considered dirty
                                                 session2.commit()
          len(root.simplelist)

          In this case the commit from session2 doesn't remove ListElement 'A' because the
          transaction for session2 did not make any changes.
        """
        return self.data_abstraction_layer.is_session_dirty()
