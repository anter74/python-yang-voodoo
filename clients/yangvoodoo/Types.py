import sysrepo as sr

UINT32 = sr.SR_UINT32_T
UINT16 = sr.SR_UINT16_T
UINT8 = sr.SR_UINT8_T
INT32 = sr.SR_INT32_T
INT16 = sr.SR_INT16_T
INT8 = sr.SR_INT8_T
STRING = sr.SR_STRING_T
DECIMAL64 = sr.SR_DECIMAL64_T
BOOLEAN = sr.SR_BOOL_T
ENUM = sr.SR_ENUM_T
EMPTY = sr.SR_LEAF_EMPTY_T
PRESENCE_CONTAINER = sr.SR_CONTAINER_PRESENCE_T

LIBYANG_MAPPING = {
    'string': sr.SR_STRING_T,
    'enumeration': sr.SR_ENUM_T,
    'boolean': sr.SR_BOOL_T,
    'uint8': sr.SR_UINT8_T,
    'uint16': sr.SR_UINT16_T,
    'uint32': sr.SR_UINT32_T
}
