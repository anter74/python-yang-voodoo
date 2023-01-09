#!/usr/bin/python3
import libyang
from _libyang import ffi
from libyang.util import c2str

import os
import yangvoodoo.VoodooNode as VoodooNode
import yangvoodoo.Errors as Errors
from yangvoodoo.stublydal import StubLyDataAbstractionLayer
from yangvoodoo.Common import PlainObject, Types, Utils, YangNode


class DataAccess(StubLyDataAbstractionLayer):

    """
    This module provides two methods to access data, either XPATH based (low-level) or
    Node based (high-level).

    Earlier versions of yangvoodoo supported different backends through a data abstraction
    layer, however should another datastore backend be required this class can be extended
    and specific methods overwritten.

    Dependencies:
     - libyang v1.0.252 - so version 1.10.43 (commit 7b291d97011ddfa63b7441e582009f1b7deff4ea)
     - libyang-cffi   (https://github.com/allena29/libyang-cffi/tree/master)
    """

    # CHANGE VERSION NUMBER HERE
    __version__ = "0.0.15"

    def __init__(
        self,
        log=None,
        local_log=False,
        data_abstraction_layer=None,
        yang_model=None,
        yang_location=None,
    ):
        if not log:
            log = Utils.get_logger("yangvoodoo", 10)
        self.log = log
        self.session = None
        self.connected = False
        self.context = None
        self.node_returned = False
        self.root_voodoo = None
        self.data_abstraction_layer = self
        if hasattr(data_abstraction_layer, "libyang_data"):
            self.libyang_data = data_abstraction_layer.libyang_data
        if yang_model:
            self.connect(yang_model, yang_location)

        self._libyang_errors = []
        libyang_errors = self._libyang_errors

        @ffi.def_extern(name="lypy_log_cb")
        def libyang_c_logging_callback(level, msg, path):
            libyang_errors.append(c2str(msg))

    def __enter__(self):
        self.root_voodoo = self.get_node()
        return self.root_voodoo

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def _get_data_abastraction_layer(self, log):
        return StubLyDataAbstractionLayer(log)

    def show_example_xpaths(self, print_xpaths=True):
        if not self.connected:
            raise Errors.NotConnect()
        answer = []
        for node in self.yang_ctx.find_path(f"/{self.module}:*"):
            if print_xpaths:
                print(node.data_path())
            else:
                answer.append(node.data_path())

            try:
                for subnode in self.yang_ctx.find_path(f"/{self.module}:{node}//*"):
                    if print_xpaths:
                        print(subnode.data_path())
                    else:
                        answer.append(node.data_path())
            except libyang.util.LibyangError:
                pass
        if not print_xpaths:
            return "\n".join(answer)

    def tree(self, print_tree=True):
        """
        Print a tree representation of the YANG Schema.
        """
        if not self.connected:
            raise Errors.NotConnect()

        if print_tree:
            print(self.context.schema.dump_str())
        else:
            return self.context.schema.dump_str()

    @classmethod
    def describe(self, node, attr="", print_description=True):
        """
        Provide help text from the yang module if available.
        """
        if not isinstance(node, VoodooNode.Node):
            raise Errors.NodeProvidedIsNotAContainer()
        if node._NODE_TYPE == "Empty":
            raise Errors.NodeProvidedIsNotAContainer()

        node_schema = node._node
        context = node._context

        if attr != "":
            node_schema = Utils.get_yangnode(node_schema, context, attr)

        leaf_type = None
        node_type = node_schema.nodetype()
        description = node_schema.description()
        type = (
            Types.LIBYANG_NODETYPE[node_type][0]
            + Types.LIBYANG_NODETYPE[node_type][1:].lower()
        )
        if node_type in Types.LIBYANG_LEAF_LIKE_NODES:
            leaf_type = node_schema.type().base()
            type = (
                type
                + " of type "
                + Types.LIBYANG_LEAF_TYPES[leaf_type][0]
                + Types.LIBYANG_LEAF_TYPES[leaf_type][1:].lower()
            )
        if not description:
            description = "N/A"
        values = {
            "schema_path": node_schema.real_schema_path,
            "value_path": node_schema.real_data_path,
            "description": str(description).replace("\n", "\n  "),
            "type": type,
            "linebreak": "-" * len(node_schema.name()),
            "node_name": node_schema.name(),
        }
        description = """Description of {node_name}
---------------{linebreak}

Schema Path: {schema_path}
Value Path: {value_path}
NodeType: {type}
""".format(
            **values
        )

        if leaf_type and leaf_type == Types.LIBYANG_LEAFTYPE["ENUM"]:
            description = description + "Enumeration Values: "
            comma = ""
            for (enum, _) in node_schema.type().enums():
                description = description + comma + enum
                comma = ", "
        description = (
            description
            + """
Description:
  {description}
""".format(
                **values
            )
        )
        if attr == "":
            children = node.__dir__(no_translations=True)
        else:
            try:
                children = node[attr].__dir__(no_translations=True)
            except Exception:
                children = "[No Child Nodes]"
        description = (
            description
            + """
Children: %s"""
            % (str(children)[1:-1])
        )
        if print_description:
            print(description)
            return
        return description

    @classmethod
    def get_extensions(self, node, attr="", module=None):
        """
        Return a list of extension with the given name.

        For the root node an child attribute name must be provided, for deeper nodes
        the attribute name can be omitted which means 'this node'

        Example:
            yangvoodoo.DataAccess.get_extensions(root, 'dirty-secret')

            Looks for an extension named 'info' on root.dirty_secret
        """

        if node._NODE_TYPE == "Root" and not attr:
            raise ValueError(
                "Attribute name of a child leaf is required for 'has_extension' on root"
            )
        context = node._context
        node = node._node

        node_schema = node
        if attr != "":
            node_schema = Utils.get_yangnode(node_schema, context, attr)

        for extension in node_schema.extensions():
            if not module or extension.module().name() == module:
                arg = extension.argument()
                if arg == "true":
                    arg = True
                elif arg == "false":
                    arg = False
                yield (f"{extension.module().name()}:{extension.name()}", arg)

    @classmethod
    def get_extension(self, node, name, attr="", module=None):
        """
        Look for an extension with the given name.

        For the root node an child attribute name must be provided, for deeper nodes
        the attribute name can be omitted which means 'this node'

        Example:
            yangvoodoo.DataAccess.has_extension(root, 'info', 'dirty-secret')
            Looks for an extension named 'info' on root.dirty_secret

        If the argument of the extnesion is a string 'true' or 'false' it will be converted
        to a python boolean, otherwise the argument is returned as-is.

        If the extension is not present None is returned.
        """
        if node._NODE_TYPE == "Root" and not attr:
            raise ValueError(
                "Attribute name of a child leaf is required for 'has_extension' on root"
            )

        extensions = DataAccess.get_extensions(node, attr, module)
        for (m, a) in extensions:
            if module and m == f"{module}:{name}" or not module and f":{name}" in m:
                return a
        return None

    @classmethod
    def get_root(self, session=None, attribute=None):
        """
        A simple wrapper which has very little intelligence other than the ability to hold other
        VoodooNode's

        Return a root container (SuperRoot), this is intended for cases where the are multiple
        sibling YANG models each describing unique top-level nodes.

        i.e.
            recipes.yang       has a list of recipes
            ingrredients.yang  has a list of ingredients

        We can do the following:
            recipe_session = yangvoodoo.DataAccess()
            recipe_session.connect('recipes')

            ingredients_session = yangvoodoo.DataAccess()
            ingredients_session.connect('recipes')

            root = yangvoodoo.DataAccess.get_root(recipe_session, 'recipes')
            root.attach_node_from_session(ingredients_session, 'ingredients')

        Now we have root.ingredients and root.recipes from their respective YANG models, however they
        are independent instances and are validated(), committed() in their own ways. They currently
        will use their own individual datastores.

        It is also possible to use this method to restrict visibility.

        OUT OF SCOPE (all left to the consumer right now):
         - sharing datastores
         - sharing of session (perhaps useful to restrict visibility to two top-level nodes)
         - ordering of commits (session a creates new data that session b requires for a leafref)
         - rollbacks if one commit fails.
        """
        super_root = VoodooNode.SuperRoot()
        if session and attribute:
            super_root.attach_node_from_session(session, attribute)
        return super_root

    def _trace(self, vnt, yn, context):
        self.log.trace(
            "%s: %s %s\nschema: %s\ndata: %s",
            vnt,
            context,
            yn.libyang_node,
            yn.real_schema_path,
            yn.real_data_path,
        )

    def get_node(self, readonly=False):
        """
        Instantiate Node-based access to the data stored in the backend defined by a yang
        schema. The data access will be constraint to the YANG module chosen when invoking
        this method.

        We must have access to the same YANG module loaded within in sysrepo, which can be
        set by modifying yang_location argument.
        """
        self.log.trace("GET_NODE")
        if not self.connected:
            raise Errors.NotConnect()
        self.node_returned = True
        super().setup_root()

        yang_node = YangNode(PlainObject(), "", "", "")
        self._trace("VoodooNode.Root", yang_node, self.context)
        self.context.readonly = readonly
        return VoodooNode.Root(self.context, yang_node)

    def connect(self, module=None, yang_location=None, tag="client", yang_ctx=None):
        """
        Connect to the datastore.

        returns: True
        """
        if yang_location and not os.path.exists(
            f"{yang_location}{os.sep}{module}.yang"
        ):
            raise ValueError(f"YANG Module {module} not present in {yang_location}")
        self.module = module
        self.yang_ctx = libyang.Context(yang_location) if not yang_ctx else yang_ctx
        self.yang_schema = self.yang_ctx.load_module(self.module)
        connect_status = super().connect(self.module, yang_location, tag, self.yang_ctx)

        self.session = self
        self.connected = True

        self.context = VoodooNode.VoodooContext(
            self.module, self, self.yang_schema, self.yang_ctx, log=self.log
        )

        self.log.trace("CONNECT: module %s. yang_location %s", module, yang_location)
        self.log.trace("       : libyangctx %s ", self.yang_ctx)
        self.log.trace("       : context %s", self.context)
        return connect_status

    def add_module(self, module):
        """
        Add an aditional yang module.
        """
        self.log.trace("ADD_MODULE: %s", module)
        if not self.connected:
            raise Errors.NotConnect()
        if self.node_returned:
            raise Errors.NodeAlreadyProvidedCannotChangeSchemaError()
        if module in self.context.other_yang_modules:
            return
        self.context.other_yang_modules.append(module)
        self.libyang_ctx.load_module(module)

    def disconnect(self):
        """
        Disconnect from the datastore.

        If the datastore is an 'stub' based datastore disconnecting will lose any data.

        returns: True
        """
        self.log.trace("DISCONNECT")
        self.connected = False
        self.root_voodoo
        return super().disconnect()

    def commit(self):
        """
        Commit pending changes to the datastore backend, it is possible to call validate()
        before a commit. The datastore has the final say if the changes are valid or not,
        the only assurance that the yangvoodoo objects can provide is that the data conforms
        to the YANG schema - it cannot guarantee the values are consistent with the full
        data held in the datastore.

        returns: True
        """
        self.log.trace("COMMIT")
        if not self.connected:
            raise Errors.NotConnect()
        return super().commit()

    def refresh(self):
        """
        Ensure we are still connected to sysrepo and using the latest dataset.

        Note: if we are ever disconnected it is possible to simply just call
        the connect() method of this object.

        returns: True
        """
        if not self.connected:
            raise Errors.NotConnect()
        return super().refresh()

    def empty(self):
        """
        Somewhat dangerous option - but attempt to empty the entire datastore.

        returns: True
        """
        if not self.connected:
            raise Errors.NotConnect()
        return super().empty()

    def is_session_dirty(self):
        """
        Returns if we have changed our dataset since the time we connected, last committed
        or last refreshed against the baceknd.
        """
        if not self.connected:
            raise Errors.NotConnect()
        return super().is_session_dirty()

    def has_datastore_changed(self):
        """
        The definition of a changed backend session is one which has had data changed since we opened
        our own session.

        Example1:
          session1.connect()                     session2.connect()
          root1.simpleleaf='1'                   root2.simpleleaf='2'
          session1.commit()                      ---
                                                 This session is now considered dirty
                                                 The data we commit as part of this session
                                                 will overwrite those of the first session
                                                 where there are overlaps.
          ---                                    session2.commit()

          This session is now considered changed on the backend
          print(root1.simpleleaf)

        In this case the value 'simpleleaf' is set to 2, as session2 was committed last. There is
        no mechanism implemented to detect the conflict. The data from the first session was set
        for the moment in time between it's commit and session2's commit.

        This method 'has_datastore_changed' can be used by application to decide if they wish to
        commit.

        Example2:
          session1.connect()                     session2.commit()
          root1.simplelist.create('A')           root2.simplelist.create('B')
          root1.commit()                         ---
                                                 This session is now considered changed
                                                 session2.commit()
          len(root.simplelist)

          In this case the commit from session2 doesn't remove ListElement 'A' because the
          transaction for session2 did not make any changes.
        """
        return super().has_datastore_changed()

    @staticmethod
    def _welcome():
        if (
            os.path.exists(".colour")
            and "TERM" in os.environ
            and "xterm" in os.environ["TERM"]
        ):
            with open(".colour") as fh:
                print(fh.read())
        elif os.path.exists(".black"):
            with open(".black") as fh:
                print(fh.read())
        if os.path.exists(".buildinfo"):
            with open(".buildinfo") as fh:
                print(fh.read())
