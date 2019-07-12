import re
import yangvoodoo
from jinja2 import Template
from lxml import etree
from yangvoodoo import Common
from yangvoodoo.Common import Utils


class TemplateNinja:

    def __init__(self):
        self.log = Common.Utils.get_logger("TemplateNinja")

    def to_xmlstr(self, xpaths):
        # regex = re.compile("([a-zA-Z0-9_-]*)(/?)(\[.*?\])?")
        regex = re.compile(r"([a-zA-Z0-9_-]*)(/?)((\[.*?\])*)?")
        first_xpath = list(xpaths.keys())[0]
        module = first_xpath[1:first_xpath.find(':')]

        xmldoc = etree.Element(module)
        node_lookup = {
            '/': xmldoc
        }

        for xpath in xpaths:
            path = "/"
            for (a, _, b, _) in Common.Utils.SPLIT_XPATH.findall(xpath[xpath.find(':')+1:]):
                xmlnode = node_lookup[path]

                if a:
                    path = path + "/" + a
                    new_node = etree.Element(a)

                if b:
                    path = path + "/" + b
                    key = 'keys'

                    for (key, keyval) in Common.Utils.FIND_KEYS_AND_VALUES.findall(b):
                        key_node = etree.Element(key)
                        key_node.text = str(keyval)
                        new_node.append(key_node)
                        node_lookup[path + "/" + key] = key_node

                if path not in node_lookup:
                    xmlnode.append(new_node)
                    node_lookup[path] = new_node
                    xmlnode = str(new_node)

            xmlnode.text = str(xpaths[xpath])

        return Common.Utils.pretty_xmldoc(xmldoc)

    def to_xmlstr_v2(self, xpaths):
        # regex = re.compile("([a-zA-Z0-9_-]*)(/?)(\[.*?\])?")
        first_xpath = list(xpaths.keys())[0]
        module = first_xpath[1:first_xpath.find(':')]

        xmldoc = etree.Element(module)
        top_node = xmldoc
        node_lookup = {
            '/': xmldoc
        }

        print(xpaths)

        for xpath in xpaths:
            top_node = xmldoc

            for (path_component, path_predicates) in Utils.convert_xpath_to_list(xpath, data_based=True, without_modules=True):

                if path_predicates:
                    print(path_component, path_predicates)
                else:
                    print(path_component)

            print("*"*80)
        return Common.Utils.pretty_xmldoc(xmldoc)

    def _getTemplate(self, contents):
        return Template(contents)

    def from_template(self, root, template, **kwargs):
        variables = {'root': root}
        for variable_name in kwargs:
            variables[variable_name] = kwargs[variable_name]

        xmlstr = ""
        with open(template) as file_handle:
            template = self._getTemplate(file_handle.read())
            xmlstr = template.render(variables)

        dal = root.__dict__['_context'].dal
        yangctx = root.__dict__['_context'].schemactx
        module = root.__dict__['_context'].module

        self._import_xml_to_datastore(module, yangctx, xmlstr, dal)

    def from_xmlstr(self, root, xmlstr, **kwargs):
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
                self.log.trace('Creating %s %s, %s', list_path+predicates, keys, values)
                state.dal.create(list_path + predicates, keys, values)
                state.path[-1] = state.path[-1] + predicates
                continue

            this_node = state.module + ':' + child.tag
            this_path = ''.join(state.spath) + '/' + this_node
            # value_path = ''.join(state.path) + '/' + this_node

            node_schema = next(state.yangctx.find_path(this_path))
            node_type = node_schema.nodetype()

            if node_type == 2 or node_type == 64:
                value_path = ''.join(state.path)
            else:
                if len(state.path) == 0:
                    value_path = ''.join(state.path) + '/' + this_node
                else:
                    value_path = ''.join(state.path) + '/' + child.tag

            # This approach works but it's a bit of a kludge -it should be easier to just append/remove things.
            value_path = value_path.replace('::not-for-data-path::', '')
            if node_type == 1:  # Container / Lis
                pass
            elif node_type == 16:
                state.next_time_loop = (node_schema, value_path)
            elif node_type == 8:
                yang_type = Common.Utils.get_yang_type(node_schema.type(), child.text, this_path)
                state.dal.add(value_path, Common.Utils.convert_string_to_python_val(child.text, yang_type), yang_type)
            elif node_type == 2:    # Choice
                pass
            elif node_type == 64:   # Case
                pass
            else:
                yang_type = Common.Utils.best_guess_of_yang_type(node_schema.type(), child.text, this_path)

                val = Common.Utils.convert_string_to_python_val(child.text, yang_type)
                self.log.trace('setting. %s => %s %s', value_path, val, yang_type)
                state.dal.set(value_path, val, yang_type)

            if node_type == 2:
                state.path.append('::not-for-data-path::')
            elif node_type == 64:
                state.path.append('::not-for-data-path::')
            else:
                if len(state.path) == 0:
                    state.path.append('/' + this_node)
                else:
                    state.path.append('/' + child.tag)

            state.spath.append('/' + this_node)

            self._recurse_xmldoc(child, state)

            state.path.pop()
            state.spath.pop()

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
            yang_type = Common.Utils.get_yang_type(k.type(), default_to_string=True)
            # key_node_schema = next(yangctx.find_path(this_path + "/" + module+":"+k.name()))
            values.append((Common.Utils.convert_string_to_python_val(xml_key.text, yang_type), yang_type))

            predicates = predicates + Common.Utils.encode_xpath_predicate(xml_key.tag, xml_key.text)
        return (predicates, keys, values)
