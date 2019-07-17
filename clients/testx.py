from pudb.remote import set_trace
set_trace(term_size=(230, 50))

import yangvoodoo
from yangvoodoo.Common import Utils


log = yangvoodoo.Common.Utils.get_logger('xmlstubstore', 2)


# Using Stub backend
import yangvoodoo.stubdal
import yangvoodoo.xmlstubdal
stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
stub = yangvoodoo.xmlstubdal.XMLStubDataAbstractionLayer(log=log)

session = yangvoodoo.DataAccess(log=log, data_abstraction_layer=stub, disable_proxy=False)

session.connect('integrationtest')
root = session.get_node()
yang = root._context.schema
yangctx = root._context.schemactx
context = root._context
backend = root._context.dal.data_abstraction_layer
ninja = yangvoodoo.TemplateNinja.TemplateNinja()

# x = Utils.convert_xpath_to_list_v2("/container-and-lists/multi-key-list[A='primary-leaf'][B='secondary-leaf']/inner/C")
# for xx in x:
#     print(xx)


xx = root.simplelist.create('a')
xx.nonleafkey = "FDSF"
# root.simplelist.create('b')
root.simpleleaf = "X"
#
# #root.container_and_lists.just_a_key = "this is not a key really - its just a leaf"
root.twokeylist.create(True, False)
#root.container_and_lists.multi_key_list.create('first-leaf', 'second-leaf')
a = root.container_and_lists.multi_key_list.create('primary-leaf', 'secondary-leaf')
#
# for k in stub.cache.items.keys():
#     print(k, stub.cache.items[k])
#
#
#root.simpleleaf = "Y"
a.inner.C = 'c'
a.inner.level3list.create('key3')

root.morecomplex.leaflists.simple.create('abc')
root.morecomplex.leaflists.simple.create('123')
root.morecomplex.leaflists.simple.create('def')
root.morecomplex.leaflists.simple.create('xyz')
print(Utils.pretty_xmldoc(stub.xmldoc))
# print(ninja.to_xmlstr_v2(session.dump_xpaths()))
#
for k in stub.cache.items.keys():
    print(k, stub.cache.items[k])
print(root.simpleleaf)
