import re
import yangvoodoo
from jinja2 import Template
from lxml import etree


class TemplateNinja:

    def from_template(self, root, template, **kwargs):

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
            if not value:
                root.__dict__['_context'].dal.create(xpath)
            else:
                root.__dict__['_context'].dal.set(xpath, value, valuetype)

    def _convert_xml_to_xpaths(self, root, xmlstr):
        """
        TODO: move these methods into a new utility class.
        """
        xpaths = {}
        xmldoc = etree.fromstring(xmlstr)
        tree = etree.ElementTree(xmldoc)

        module = xmldoc.tag
        path = "//"
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

            print('there are %s paths in the list_predicates cache' % (len(list_predicates)))
            for p in list_predicates:
                print(p, list_predicates[p])
            #
            # # The schema never ever takes predicates in the path
            node_schema = root._get_schema_of_path(path)
            node_type = node_schema.nodetype()

            value_path = path

            value_path = self._find_predicate_match(list_predicates, value_path)

            if node_schema.nodetype() == 16:
                # believe this to be safe.
                predicates = self._lookahead_for_list_keys(node_schema, xmldoc_iterator, module, path, list_predicates)
                xpaths[value_path + predicates] = (None, yangvoodoo.Types.DATA_ABSTRACTION_MAPPING['LIST'])

            if node_schema.nodetype() == 1 and not node_schema.presence():
                continue

            if node_type == 4 or (node_type == 1 and node_schema.presence()):
                type = root._get_yang_type(node_schema.type(), child.text, path)
                xpaths[value_path] = (child.text, type)

        return xpaths

    def _lookahead_for_list_keys(self, node_schema, xmldoc_iterator, module, path, list_predicates):
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
        # Note: this is the only place we set new predicates into the prefix matching dict

        list_predicates[path] = predicates

        """
        The result of this preidctes above is is ok ....
        And is respondible for working what to do with mlutple lists
                before
                after [integrationtest:numberkey='5']

                before
                after [integrationtest:numberkey='2']

                before
                after [integrationtest:numberkey='6']
        """
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

        """
        In the broken case
        -------------------------------------------------------------------------
/integrationtest:container-and-lists
-------------------------------------------------------------------------
/integrationtest:container-and-lists/integrationtest:numberkey-list
-------------------------------------------------------------------------
/integrationtest:container-and-lists/integrationtest:numberkey-list
POTENTIAL /integrationtest:container-and-lists/integrationtest:numberkey-list
          /integrationtest:container-and-lists/integrationtest:numberkey-list
-------------------------------------------------------------------------
/integrationtest:container-and-lists/integrationtest:numberkey-list
POTENTIAL /integrationtest:container-and-lists/integrationtest:numberkey-list
          /integrationtest:container-and-lists/integrationtest:numberkey-list
POTENTIAL /integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']
          /integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']
/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5']
/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5'][integrationtest:numberkey='2']
/integrationtest:container-and-lists/integrationtest:numberkey-list[integrationtest:numberkey='5'][integrationtest:numberkey='2'][integrationtest:numberkey='6']
        """

        value_path = path
        for predicate in list_predicates:
            if predicate in value_path:  # and predicate in list_predicates:
                start_pos = value_path.find(predicate)
                end_pos = start_pos + len(predicate)
                value_path = value_path[start_pos:start_pos+len(predicate)] + list_predicates[predicate] + value_path[end_pos:]
                last_answer = value_path[start_pos:start_pos+len(predicate)] + list_predicates[predicate] + value_path[end_pos:]

        return value_path
