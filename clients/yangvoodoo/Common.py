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

        (list_element_path_a, list_element_path_b, predicates) = results[0]

        predicates = {}
        for (key, val) in self.PREDICATE_KEY_VALUES_SINGLE.findall(path):
            predicates[key] = val
        for (key, val) in self.PREDICATE_KEY_VALUES_DOUBLE.findall(path):
            predicates[key] = val

        keys = []
        values = []
        for key in self.FIND_KEYS.findall(path):
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
    def form_value_xpath(path, attr, module, node_schema=None):
        """
        Sysrepo is much less strict compared to libyang, it only requires the first node
        to be prefixed within the module. Moreover sysrepo returns XPATH's in this
        form to us when calling for the list elements.

        Inside the integrationtest which imports from the yang module teschild we still
        reference those imported elements by the parent module.
         '/integrationtest:imports-in-here/integrationtest:name'
        """
        if path == '':
            return Utils.form_schema_xpath(path, attr, module, node_schema)

        if node_schema and node_schema.underscore_translated:
            return path + '/' + attr.replace('_', '-')

        return path + '/' + attr

    @staticmethod
    def form_schema_xpath(path, attr, module, node_schema=None):
        """
        When using the schema xpath lookup we need to use the module prefix
        across every part of the path for the libyang library.

        Inside the integrationtest which imports from the yang module teschild we still
        reference those imported elements by the parent module.
         '/integrationtest:imports-in-here/integrationtest:name'
        """
        if node_schema and node_schema.underscore_translated:
            return path + '/' + module + ":" + attr.replace('_', '-')

        return path + '/' + module + ":" + attr

    @staticmethod
    def get_schema_of_path(xpath, context):
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
        raise Errors.NonExistingNode(xpath)
