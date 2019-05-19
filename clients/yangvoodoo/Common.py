from yangvoodoo import Types


class Utils:

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