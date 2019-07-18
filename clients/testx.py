import yangvoodoo.stubdal
import yangvoodoo
from yangvoodoo.Common import Utils

# from pudb.remote import set_trace
# set_trace(term_size=(230, 50))

log = yangvoodoo.Common.Utils.get_logger('debug', 12)
log1 = yangvoodoo.Common.Utils.get_logger('stubstore', 12)
log2 = yangvoodoo.Common.Utils.get_logger('voodoo', 12)
log3 = yangvoodoo.Common.Utils.get_logger('template-ninja', 2)


# Using Stub backend
stub = yangvoodoo.stubdal.StubDataAbstractionLayer(log=log1)

session = yangvoodoo.DataAccess(log=log2, data_abstraction_layer=stub, disable_proxy=True)

session.connect('integrationtest')
root = session.get_node()
yang = root._context.schema
yangctx = root._context.schemactx
context = root._context
backend = root._context.dal.data_abstraction_layer
ninja = yangvoodoo.TemplateNinja.TemplateNinja(log=log3)
#
# # x = Utils.convert_xpath_to_list_v2("/container-and-lists/multi-key-list[A='primary-leaf'][B='secondary-leaf']/inner/C")
# # for xx in x:
# #     print(xx)
# #
# #
# # xx = root.simplelist.create('a')
# # xx.nonleafkey = "FDSF"
# # # root.simplelist.create('b')
# # root.simpleleaf = "X"
# # #
# # # #root.container_and_lists.just_a_key = "this is not a key really - its just a leaf"
# # root.twokeylist.create(True, False)
# # #root.container_and_lists.multi_key_list.create('first-leaf', 'second-leaf')
# a = root.container_and_lists.multi_key_list.create('primary-leaf', 'secondary-leaf')
# # #
# # for k in stub.cache.items.keys():
# #     print(k, stub.cache.items[k])
# #
# # #
# # log.info("\n%s\nSet simpleleaf\n%s", "*"*136, "*"*136)
# # root.simpleleaf = "Y"
# # log.info("\n%s\nGet simpleleaf\n%s", "*"*136, "*"*136)
# # print(root.simpleleaf)
# #
# a.inner.C = 'c'
#
# a.inner.level3list.create('key3').level3_nonkey = "sdf"
# b = root.container_and_lists.multi_key_list.create('another-leaf', 'another-leaf')
#
#
# # #
# root.morecomplex.leaflists.simple.create('abc')
# root.morecomplex.leaflists.simple.create('123')
# root.morecomplex.leaflists.simple.create('def')
# # # root.morecomplex.leaflists.simple.create('xyz')
# # # root.container1.create()
# # #
# # # log.info("\n%s\nSet leaf1 in container1\n%s", "*"*136, "*"*136)
# # # x = root.container1.leaf1 = 'ABC'
# # #
# # # log.info("\n%s\nSet leaf2a in container2\n%s", "*"*136, "*"*136)
# # # root.container1.container2.leaf2a = 'DEF'
# # # log.info("\n%s\nSet leaf2b in container2\n%s", "*"*136, "*"*136)
# # # root.container1.container2.leaf2b = 'GHI'
# # #
# # root.simplelist.create('a')
# # root.simplelist.create('b')
#
# this_node = root.scaling
# for c in range(5):
#     if c == 2:
#         key = ('created%s' % (c), 'extrakey')
#     else:
#         key = ('created%s' % (c))
#     this_node = this_node['scale%s' % (c)].create(key)
#
#     if c > 1:
#         this_node = this_node._parent.get(key)
#

a = root.container_and_lists.multi_key_list.create('/this/looks/a/bit/like/xpath[key="sdf"]/sdf', 'second-leaf')
a.inner.C = "C"

print(ninja.to_xmlstr(session.dump_xpaths()))
#

# breakpoint()
xpaths = session.dump_xpaths()

for xpath in xpaths:
    print(""" "%s":"%s",""" % (xpath, xpaths[xpath]))
