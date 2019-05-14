
DATA_ABSTRACTION_MAPPING = {
    # Note: if the backend does not like these values
    # mapping into more acceptable values should be
    # done in the respective data_abstraction_layer
    'UINT32': 21,
    'UINT16': 20,
    'UINT8': 19,
    'INT32': 16,
    'INT16': 15,
    'INT8': 14,
    'STRING': 18,
    'DECIMAL64': 10,
    'BOOLEAN': 9,
    'ENUM': 11,
    'EMPTY': 5,
    'PRESENCE_CONTAINER': 4,
}

LIBYANG_MAPPING = {
    3: DATA_ABSTRACTION_MAPPING['BOOLEAN'],
    4: DATA_ABSTRACTION_MAPPING['DECIMAL64'],
    5: DATA_ABSTRACTION_MAPPING['EMPTY'],
    6: DATA_ABSTRACTION_MAPPING['ENUM'],
    10: DATA_ABSTRACTION_MAPPING['STRING'],
    12: DATA_ABSTRACTION_MAPPING['INT8'],
    13: DATA_ABSTRACTION_MAPPING['UINT8'],
    14: DATA_ABSTRACTION_MAPPING['INT16'],
    15: DATA_ABSTRACTION_MAPPING['UINT16'],
    16: DATA_ABSTRACTION_MAPPING['INT32'],
    17: DATA_ABSTRACTION_MAPPING['UINT32']
}


# To populate from lys_nodetype
LIBYANG_NODETYPE = {
    1: 'CONTAINER',
    4: 'LEAF',
}
