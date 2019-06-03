import libyang
import logging
from yangvoodoo import Types, Errors
import re


class PlainObject:
    pass


class PlainIterator:

    def __init__(self, children):
        self.children = children
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.children) > self.index:
            self.index = self.index + 1
            return self.children[self.index-1]
        raise StopIteration


class Utils:

    LOG_INFO = logging.INFO
    LOG_DEBUG = logging.DEBUG
    LOG_SILENT = 99
    LOG_ERROR = logging.ERROR
    LOG_TRACE = 7

    LAST_LEAF_AND_PREDICTAES = re.compile(r"(.*/)([A-Za-z]+[A-Za-z0-9_:-]*)(\[.*\])$")
    PREDICATE_KEY_VALUES_SINGLE = re.compile(r"\[([A-z]+[A-z0-9_\-]*)='([^']*)'\]")
    PREDICATE_KEY_VALUES_DOUBLE = re.compile(r"\[([A-z]+[A-z0-9_\-]*)=\"([^\"]*)\"\]")
    FIND_KEYS = re.compile(r"\[([A-Za-z]+[A-Za-z0-9_-]*)=.*?\]")

    @staticmethod
    def get_logger(name, level=logging.DEBUG):
        format = "%(asctime)-15s - %(name)-15s %(levelname)-12s  %(message)s"
        logging.basicConfig(level=99, format=format)
        log = logging.getLogger(name)
        log.setLevel(level)

        logging.addLevelName(7, "TRACE")

        def trace(self, message, *args, **kws):
            if self.isEnabledFor(7):
                self._log(7, message, args, **kws)
        logging.Logger.trace = trace
        return log

    @staticmethod
    def get_yang_type_from_path(context, schema_path,  value, child_attr=None):
        print('...get', schema_path, value, child_attr, context.module)
        if child_attr:
            schema_path = schema_path + "/" + context.module + ":" + child_attr
        node_schema = next(context.schemactx.find_path(schema_path))
        return Utils.get_yang_type(node_schema.type(), value, schema_path)

    @staticmethod
    def get_yang_type(node_schema, value=None, xpath=None):
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

        msg = 'Unable to handle the yang type at path ' + xpath
        msg += ' (this may be listed as a corner-case on the README already'
        raise NotImplementedError(msg)

    @staticmethod
    def encode_xpath_predicate(k, v):
        """
        TODO: xpath predciates need some kind of encoding/escaping to make them safe (or complain
        they are not.
        example - [x='X'X'] is not safe.
        """
        return "[%s='%s']" % (k, v)

    @staticmethod
    def encode_xpath_predicates(attr, keys, values):
        if not isinstance(keys, list):
            raise NotImplementedError("encode_attribute_with_xpath_predicates does not work with non-list input - %s" % (keys))
        if not isinstance(values, list):
            raise NotImplementedError("encode_attribute_with_xpath_predicates does not work with non-list input - %s" % (values))
        answer = attr
        for i in range(len(keys)):
            (val, _) = values[i]
            answer = answer + Utils.encode_xpath_predicate(keys[i], val)
        return answer

    @classmethod
    def decode_xpath_predicate(self, path):
        """
        TODO: xpath predciates need some kind of encoding/escaping to make them safe (or complain
        they are not.
        example - [x='X'X'] is not safe.
        """

        results = self.LAST_LEAF_AND_PREDICTAES.findall(path)
        if not len(results) == 1:
            raise Errors.XpathDecodingError(path)

        (list_element_path_a, list_element_path_b, last_set_of_predicates) = results[0]

        predicates = {}
        for (key, val) in self.PREDICATE_KEY_VALUES_SINGLE.findall(path):
            predicates[key] = val
        for (key, val) in self.PREDICATE_KEY_VALUES_DOUBLE.findall(path):
            predicates[key] = val

        keys = []
        values = []
        for key in self.FIND_KEYS.findall(last_set_of_predicates):
            keys.append(key)
            values.append(predicates[key])

        return (list_element_path_a + list_element_path_b, tuple(keys), tuple(values))

    @staticmethod
    def convert_string_to_python_val(value, valtype):
        """
        Give a value and a value type convert it to a python representation instead of a string from the XML
        template.

        The valtype should correspond to yangvoodoo.Types.DATA_ABSTRACTION_MAPPING.
        """
        if valtype in Types.INT_CONVERSION:
            return int(value)
        elif valtype == Types.DATA_ABSTRACTION_MAPPING['DECIMAL64']:
            return float(value)
        elif valtype == Types.DATA_ABSTRACTION_MAPPING['BOOLEAN']:
            if value.toLower() == 'false':
                return False
            return True
        return value

    @staticmethod
    def get_schema_and_set_paths(node, context, attr='', keys=[], values=[], predicates=""):
        """
        Given a node, with a child attribute name, and list of key/values return a libyang schema object
        and the value path.

        Each time we return a node we will store the following on the yang node to help with underscore
        translations. The input to this method will have hyphens converted to underscores.
        - real_schema_path
        - real_data_path

        Libyang itself has schema_path and data_path but these do not know about the underscore translations.

        Remember:
         - schemapaths must have the yang module at every component
         - values paths only require the yang module prefix at the first component.
        The cache entries are built deliberately not to be a valid path (designated by the %).
        This is done so that we can lookup the cache without having to carry out processing.
        """

        if len(keys) and len(values):
            predicates = Utils.encode_xpath_predicates('', keys, values)
            print('PREDICATES', predicates)

        if context.schemacache.is_path_cached("!"+node.real_schema_path + attr + predicates+"!"):
            return context.schemacache.get_item_from_cache("!"+node.real_schema_path+attr + predicates+"!")

        print('..._get_schema_and_path_of_node', node.real_schema_path, node.real_data_path, attr, keys, values)

        real_schema_path = node.real_schema_path
        if not attr == '':
            real_attribute_name = Utils.get_original_name(real_schema_path, context, attr)
            # print('... attr now', real_attribute_name)
            real_schema_path = real_schema_path + '/' + context.module + ":" + real_attribute_name

        try:
            node_schema = next(context.schemactx.find_path(real_schema_path))
        except libyang.util.LibyangError:
            raise Errors.NonExistingNode(node.real_schema_path + '/'+context.module+":"+attr)

        if not attr == '':
            real_data_path = node.real_data_path
            if node_schema.nodetype() not in (Types.LIBYANG_NODETYPE['CHOICE'], Types.LIBYANG_NODETYPE['CASE']):
                if node.real_data_path == '':
                    real_data_path = '/' + context.module + ':' + real_attribute_name + predicates
                else:
                    real_data_path = real_data_path + '/' + real_attribute_name + predicates
            #    print('... now ', real_schema_path, real_data_path)

        if not attr:
            real_data_path = node.real_data_path + predicates
            real_schema_path = node.real_schema_path
            node_schema = node

        node_schema.real_data_path = real_data_path
        node_schema.real_schema_path = real_schema_path

        # For now we have disabled the cache - because it's giving us the same object back each time.
        # Without this we are ok.... so we will extend libyang properly in order to re-enable the cache
        # which might noe be worth the effort after all.
        context.schemacache.add_entry("TODO!"+node.real_schema_path + attr + predicates + "!", node_schema)

        return node_schema

    @staticmethod
    def get_original_name(schema_path, context, attr):
        """
        Given a schema-path return the original name.
        """
        if '_' not in attr:
            return attr

        if schema_path == "":
            schema_path = "/" + context.module + ":*/*"
        else:
            schema_path = schema_path + "/*"
        print("about to libyang serach for", schema_path, '--', attr)
        for child in context.schemactx.find_path(schema_path):
            if child.name().replace('-', '_') == attr:
                return child.name()

        raise NotImplementedError("get_original_name could not find a matching node name for %s" % (attr))

    @staticmethod
    def underscore_handling(spath, context):
        spath_split = spath.split('/')[1:]

        current_path_inspecting = []
        for path_component in spath_split:
            print('Considering path_componeent', path_component)
            print('sdsfsfdsf', current_path_inspecting)
            path_to_search = '/' + '/'.join(current_path_inspecting)
            print('/'.join(['sd']))
            print('path_to-search', path_to_search)
            if path_to_search == '/':
                path_to_search = '/' + context.module + ':*'

            children = context.schemactx.find_path(path_to_search)
            real_name = path_component
            for child in children:
                print('have child', child.name(), child, path_component)
                if child.name().replace('-', '_') == path_component:
                    real_name = child.name()

            current_path_inspecting.append(real_name)
            print('path_to_search', path_to_search)

        first_part_of_path = '/'.join(spath.split('/')[0:-1])
        last_part_of_path = spath.split('/')[-1]
        last_node_name = last_part_of_path.split(':')[-1]
        if '_' in last_part_of_path:
            real_path = None
            if first_part_of_path == "":

                children = context.schemactx.find_path("/" + context.module + ":*")
            else:
                children = context.schemactx.find_path(first_part_of_path + "/*")
            for child in children:
                if child.name().replace('-', '_') == last_node_name:
                    real_path = first_part_of_path + "/" + context.module + ":" + child.name()
                try:
                    schema_for_path = next(context.schemactx.find_path(real_path))
                    schema_for_path.under_pre_translated_name = child.name()
                    context.schemacache.add_entry(spath, schema_for_path)
                    return schema_for_path
                except libyang.util.LibyangError:
                    pass

        raise NotImplementedError("Underscore translation for path %s failed (calculated path %s)" % (spath, real_path))
    #
    # @staticmethod
    # def underscore_handling_method_1(spath, context):
    #     first_part_of_path = '/'.join(spath.split('/')[0:-1])
    #     last_part_of_path = spath.split('/')[-1]
    #     last_node_name = last_part_of_path.split(':')[-1]
    #     if '_' in last_part_of_path:
    #         real_path = None
    #         if first_part_of_path == "":
    #
    #             children = context.schemactx.find_path("/" + context.module + ":*")
    #         else:
    #             children = context.schemactx.find_path(first_part_of_path + "/*")
    #         for child in children:
    #             if child.name().replace('-', '_') == last_node_name:
    #                 real_path = first_part_of_path + "/" + context.module + ":" + child.name()
    #             try:
    #                 schema_for_path = next(context.schemactx.find_path(real_path))
    #                 schema_for_path.under_pre_translated_name = child.name()
    #                 context.schemacache.add_entry(spath, schema_for_path)
    #                 return schema_for_path
    #             except libyang.util.LibyangError:
    #                 pass
    #
    #         raise NotImplementedError("Underscore translation for path %s failed (calculated path %s)" % (spath, real_path))
