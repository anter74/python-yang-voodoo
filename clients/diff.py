#!/usr/bin/env python3
from dictdiffer import diff, patch, swap, revert

import yangvoodoo

import yangvoodoo.stubdal
stub_a = yangvoodoo.stubdal.StubDataAbstractionLayer()
session_a = yangvoodoo.DataAccess(remote_log=True, data_abstraction_layer=stub_a)
session_a.connect('integrationtest')
root_a = session_a.get_node()

stub_b = yangvoodoo.stubdal.StubDataAbstractionLayer()
session_b = yangvoodoo.DataAccess(remote_log=True, data_abstraction_layer=stub_b)
session_b.connect('integrationtest')
root_b = session_b.get_node()


root_a.diff.deletes.a_list.create('Avril Lavigne')
root_a.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm'
root_a.diff.deletes.a_leaf = 'a'
root_a.diff.modifies.a_leaf = 'original value'
root_a.diff.modifies.a_2nd_leaf = 'original value2'

root_b.diff.modifies.a_leaf = 'new value'
root_b.diff.modifies.a_2nd_leaf = 'new value2'
root_b.diff.adds.a_list.create('Ghouls')
root_b.diff.modifies.a_list.create('Lissie').listnonkey = 'earworm!'
root_b.diff.adds.a_leaf = 'b'
root_b.diff.adds.a_2nd_leaf = 'b2'

diffset = diff(stub_a.stub_store, stub_b.stub_store)

for (op, path, values) in diffset:
    if op == 'change':
        (old, new) = values
        print(op, path, old, '=>', new)
    else:
        for (path, value) in values:
            print(op, path, value)
"""
ipython3  diff.py
change /integrationtest:diff/integrationtest:modifies/integrationtest:a-list[listkey='Lissie']/integrationtest:listnonkey earworm => earworm!
change /integrationtest:diff/integrationtest:modifies/integrationtest:a-leaf original value => new value
change /integrationtest:diff/integrationtest:modifies/integrationtest:a-2nd-leaf original value2 => new value2
add /integrationtest:diff/integrationtest:adds/integrationtest:a-list ["/integrationtest:diff/integrationtest:adds/integrationtest:a-list[listkey='Ghouls']"]
add /integrationtest:diff/integrationtest:adds/integrationtest:a-list[listkey='Ghouls'] (1, '/integrationtest:diff/integrationtest:adds/integrationtest:a-list')
add /integrationtest:diff/integrationtest:adds/integrationtest:a-list[listkey='Ghouls']/integrationtest:listkey Ghouls
add /integrationtest:diff/integrationtest:adds/integrationtest:a-leaf b
add /integrationtest:diff/integrationtest:adds/integrationtest:a-2nd-leaf b2
remove /integrationtest:diff/integrationtest:deletes/integrationtest:a-list ["/integrationtest:diff/integrationtest:deletes/integrationtest:a-list[listkey='Avril Lavigne']"]
remove /integrationtest:diff/integrationtest:deletes/integrationtest:a-list[listkey='Avril Lavigne'] (1, '/integrationtest:diff/integrationtest:deletes/integrationtest:a-list')
remove /integrationtest:diff/integrationtest:deletes/integrationtest:a-list[listkey='Avril Lavigne']/integrationtest:listkey Avril Lavigne
remove /integrationtest:diff/integrationtest:deletes/integrationtest:a-leaf a
"""
