
UINT32 = 21
UINT16 = 20
UINT8 = 19
INT32 = 16
INT16 = 15
INT8 = 14
STRING = 18
DECIMAL64 = 10
BOOLEAN = 9
ENUM = 11
EMPTY = 5
PRESENCE_CONTAINER = 4

LIBYANG_MAPPING = {
    3: BOOLEAN,
    4: None,  # Special case of Decimal 64 not liking a value
    5: EMPTY,
    6: ENUM,
    10: STRING,
    12: INT8,
    13: UINT8,
    14: INT16,
    15: UINT16,
    16: INT32,
    17: UINT32
}

"""
    Documentation fmor libyang tree_schema.h
                  793     LY_TYPE_DER = 0,
                  794     LY_TYPE_BINARY,1
                  795     LY_TYPE_BITS,2
                  796     LY_TYPE_BOOL,3
                  797     LY_TYPE_DEC64,4
                  798     LY_TYPE_EMPTY,5
                  799     LY_TYPE_ENUM,6
                  800     LY_TYPE_IDENT,7
                  801     LY_TYPE_INST,8
                  802     LY_TYPE_LEAFREF,  9
                  803     LY_TYPE_STRING,  10
                  804     LY_TYPE_UNION,   11
                  805     LY_TYPE_INT8,    12
                  806     LY_TYPE_UINT8,13
                  807     LY_TYPE_INT16,14
                  808     LY_TYPE_UINT16,15
                  809     LY_TYPE_INT32,16
                  810     LY_TYPE_UINT32,17
                  811     LY_TYPE_INT64,18
                  812     LY_TYPE_UINT64,19
                  813     LY_TYPE_UNKNOWN,
    """
