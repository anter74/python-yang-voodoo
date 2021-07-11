import libyang
from jinja2 import Template
import unittest
import yangvoodoo
import yangvoodoo.stublydal


"""
This set of unit tests uses the stub backend datastore, which is not preseeded with
any data.
"""


class test_new(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.stub = yangvoodoo.stublydal.StubLyDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(
            data_abstraction_layer=self.stub, disable_proxy=True
        )
        self.subject.connect("integrationtest", yang_location="yang")
        self.root = self.subject.get_node()

    #
    # def test_a(self):
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.leaf63636363 = 'af11'
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.leaf63636363 = 63
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.leaf63636363 = 0
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.leaf63636363 = 'precedence'
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.list63636363.create(4)
    #     self.root.morecomplex.inner.list63636363.create('af41')
    #     self.root.morecomplex.inner.list63636363.create('precedence')
    #     print(self.subject.dumps())
    #
    # def test_b(self):
    #     x = """
    #     <morecomplex xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><inner><leaf63636363>precedence</leaf63636363><list63636363><key63636363>4</key63636363></list63636363><list63636363><key63636363>af41</key63636363></list63636363><list63636363><key63636363>precedence</key63636363></list63636363></inner></morecomplex>
    #     """
    #     self.subject.loads(x, trusted=True)
    #     print(self.subject.dumps())
    #
    # def test_c(self):
    #     print(self.root.morecomplex.inner.leaf63636363)
    #     self.root.morecomplex.inner.leaf63636363 = 10
    #     print(self.subject.dumps())
    #
    # def test_d(self):
    #     x = """
    #     <morecomplex xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><inner><leaf63636363>10</leaf63636363><list63636363><key63636363>4</key63636363></list63636363><list63636363><key63636363>af41</key63636363></list63636363><list63636363><key63636363>precedence</key63636363></list63636363></inner></morecomplex>
    #     """
    #     self.subject.loads(x, trusted=True)
    #     print(self.subject.dumps())
    #
    # def test_e(self):
    #     self.root.validator.types.u_int_8 = 0
    #     print(self.subject.dumps())
    #
    # def test_f(self):
    #     self.subject.loads("""<validator xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><types><u_int_8>0</u_int_8></types></validator>""")
    #     print(self.subject.dumps())
    #
    # def test_g(self):
    #     x = self.root.morecomplex.inner.uint8keylist.create(1)
    #     x.nonkey = 'o'
    #     self.assertEqual(x._path, "/integrationtest:morecomplex/inner/uint8keylist[mykey='1']")
    #     x = self.root.morecomplex.inner.uint8keylist.create(0)
    #     x.nonkey = 'z'
    #     self.assertEqual(x._path, "/integrationtest:morecomplex/inner/uint8keylist[mykey='0']")
    #     print(self.subject.dumps())
    #
    # def test_h(self):
    #     print('from the merged in case')
    #     self.subject.loads("""<morecomplex xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest"><inner><uint8keylist><mykey>1</mykey><nonkey>o</nonkey></uint8keylist><uint8keylist><mykey>0</mykey><nonkey>z</nonkey></uint8keylist></inner></morecomplex>""", trusted=True)
    #     print(self.subject.dumps())


#
#     def test_i(self):
#         class pythondata:
#             def __getattr__(self, attr):
#                 return 0
#
#             def __getitem__(self, attr):
#                 return 0
#
#         class crap:
#
#             @staticmethod
#             def as_string(i):
#                 if i is None:
#                     return '0'
#                 return str(i)
#
#         self.root.simpleleaf = 0
#         self.root.validator.types.int_8 = 0
#         x = self.root.morecomplex.inner.uint8keylist.create(1).nonkey = 'O'
#         x = self.root.morecomplex.inner.uint8keylist.create(0).nonkey = 'Z'
#         template = """
# root.simpleleaf {{ root.simpleleaf }}  this should be 0 - this is a ynag string
# root.validator.types.int_8 {{ root.validator.types.int_8 }}  this should be 0 - this is a ynan uint_8 ***IT COMES AS None ***
# root.validator.types.int_8 {{ workarounds.as_string(root.validator.types.int_8) }}  this should be 0 - this is a ynan uint_8
#
# {% for x in root.morecomplex.inner.uint8keylist %}
#     {{ x.mykey }} this should be either 1 or 0 ***THIS IS BROKEN FOR a number 0 ***
#     {{ x.nonkey }} this should be either 0 or Z
# {% endfor %}
# {{ pythondata['x'] }} getitem
# {{ pythondata.x }} this is from the python datamodel so the problem is somewhere between Jinja2 and yangvoodoo
#
#         """
#         template = Template(template)
#         answer = template.render(root=self.root, pythondata=pythondata(), workarounds=crap())
#
#         print(answer)
#         assert answer == ''

# def test_i(self):
#         x = self.root.morecomplex.inner.uint8keylist.create(1)
#         x = self.root.morecomplex.inner.uint8keylist.create(0)
#         template = """
#     {% for x in root.morecomplex.inner.uint8keylist %}
#     {{root.morecomplex.inner.uint8keylist[x.mykey].nonkey}}
#     {% endfor %}
#         """
#         template = Template(template)
#         answer = template.render(root=self.root)
#
#         print(answer)
#         assert answer == ''
