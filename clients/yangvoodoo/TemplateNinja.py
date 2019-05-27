import re
import yangvoodoo
from jinja2 import Template
from lxml import etree
from yangvoodoo import Common


class TemplateNinja:

    def __init__(self):
        self.log = Common.Utils.get_logger("TemplateNinja")

    def from_template(self, root, template, **kwargs):

        variables = {'root': root}
        for variable_name in kwargs:
            variables[variable_name] = kwargs[variable_name]

        xmlstr = ""
        with open(template) as file_handle:
            t = Template(file_handle.read())
            xmlstr = t.render(variables)

        dal = root.__dict__['_context'].dal
        yangctx = root.__dict__['_context'].schemactx
        module = root.__dict__['_context'].module

        self._import_xml_to_datastore(module, yangctx, xmlstr, dal)

    def _import_xml_to_datastore(self, module, yangctx, xmlstr, dal):
        """
        The state object contains flags to help us traverse and build paths through
        the xmldocument.
        """
        state = yangvoodoo.Common.PlainObject()
        state.path = []
        state.spath = []
        state.next_time_loop = ""
        state.module = module
        state.yangctx = yangctx
        state.dal = dal

        xmldoc = etree.fromstring(xmlstr)
        self._recurse_xmldoc(xmldoc,  state)

    def _recurse_xmldoc(self,  xmldoc, state):
        """
        Each time we _recurse_xmldoc we will take a list of etree nodes.
        We will keep building state.path up with the current path, as we come back up we will
        pop off the end of the path. (Hopefully this gives us consistent lists throughout)

        We have to maintatin two lists of paths, one with predicates (path) and one without (spath)
        they are used to interact with the datstore and libyang respectively.
        """
        children = yangvoodoo.Common.PlainIterator(xmldoc.getchildren())
        for child in children:

            if state.next_time_loop:
                (list_nodeschema, list_path) = state.next_time_loop
                state.next_time_loop = None
                (predicates, keys, values) = self._build_predicates(list_nodeschema, list_path, child, children, state)
                self.log.debug('Creating %s %s, %s', list_path+predicates, keys, values)
                state.dal.create(list_path + predicates, keys, values)
                state.path[-1] = state.path[-1] + predicates
                continue

            this_node = state.module + ':' + child.tag
            this_path = ''.join(state.spath) + '/' + this_node
            # value_path = ''.join(state.path) + '/' + this_node

            if len(state.path) == 0:
                value_path = ''.join(state.path) + '/' + this_node
            else:
                value_path = ''.join(state.path) + '/' + child.tag

            node_schema = next(state.yangctx.find_path(this_path))
            node_type = node_schema.nodetype()

            if node_type == 1:  # Container / Lis
                pass
            elif node_type == 16:
                state.next_time_loop = (node_schema, value_path)
            elif node_type == 8:
                yang_type = Common.Utils.get_yang_type(node_schema.type(), child.text, this_path)
                state.dal.add(value_path, Common.Utils.convert_string_to_python_val(child.text, yang_type), yang_type)
            else:
                yang_type = Common.Utils.get_yang_type(node_schema.type(), child.text, this_path)
                val = Common.Utils.convert_string_to_python_val(child.text, yang_type)
                self.log.debug('setting. %s => %s %s', value_path, val, yang_type)
                state.dal.set(value_path, val, yang_type)

            if len(state.path) == 0:
                state.path.append('/' + this_node)
            else:
                state.path.append('/' + child.tag)

            state.spath.append('/' + this_node)

            self._recurse_xmldoc(child, state)

            state.path.pop()
            state.spath.pop()

        # for child in xmldoc.getchildren():

    def _build_predicates(self, node_schema, this_path,  child, children, state):
        """
        Return a tuple of:
         - predicate string for the list element
         - tuple of keys
         - tuple of values with the associated value type)

        Example:
         ("[integrationtest:numberkey='5']", ['numberkey'], [(5, 19)])

        """

        keys = []
        values = []
        value_types = []
        predicates = ""
        first_key = True
        for k in node_schema.keys():
            keys.append(k.name())

            if first_key:
                xml_key = child
                first_key = False
            else:
                xml_key = next(children)
            if not xml_key.tag == k.name():
                raise ValueError('Expecting key name %s, got %s at %s' % (k.name(), xml_key.tag, this_path))
            # next_xml_node = next(children)
            # print(next_xml_node.tag, k.name())
            yang_type = Common.Utils.get_yang_type(k.type())
            # key_node_schema = next(yangctx.find_path(this_path + "/" + module+":"+k.name()))
            values.append((Common.Utils.convert_string_to_python_val(xml_key.text, yang_type), yang_type))

            predicates = predicates + Common.Utils.encode_xpath_predicate(xml_key.tag, xml_key.text)
        return (predicates, keys, values)
