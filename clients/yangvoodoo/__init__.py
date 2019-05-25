#!/usr/bin/python3
import libyang
import os
import time
import logging
import socket
import importlib
import yangvoodoo.VoodooNode
from yangvoodoo.Common import Utils


class DataAccess:

    """
    This module provides two methods to access data, either XPATH based (low-level) or
    Node based (high-level).

    The default backend for this module is sysrepo, however when instantiating this class
    it is possible to send in an alternative 'data_abstraction_layer'. For the sysrepo based
    implementation see sysrepodal.py

    The data_abstraction_layer itself supports primitive operations such as get, set, create,
    create_container, gets_sorted, gets_unsorted, delete, commit, validate, refresh, connect.
    The key assumption is that the datastore itself will stored data based upon XPATH or
    similair path structure.


    Dependencies:
     - libyang 0.16.78 (https://github.com/rjarry/libyang-cffi/)
     - lxml
    """

    def __init__(self, log=None, local_log=False, remote_log=False, data_abstraction_layer=None):
        if not log:
            log = Utils.get_logger('yangvoodoo', 10)
        self.log = log
        self.session = None
        self.conn = None
        self.connected = False
        if data_abstraction_layer:
            self.data_abstraction_layer = data_abstraction_layer
        else:
            self.data_abstraction_layer = self._get_data_abastraction_layer(None)

    def _get_data_abastraction_layer(self, log):
        importlib.import_module('yangvoodoo.sysrepodal')
        return yangvoodoo.sysrepodal.SysrepoDataAbstractionLayer(log)

    def _help(self, node):
        """
        Provide help text from the yang module if available.
        """
        if node.__dict__['_spath'] == '':
            return None
        try:
            schema = next(node.__dict__['_context'].schemactx.find_path(node.__dict__['_spath']))
            return schema.description()
        except Exception:
            pass

    @classmethod
    def get_extensions(self, node, attr=None, module=None):
        """
        Return a list of extension with the given name.

        For the root node an child attribute name must be provided, for deeper nodes
        the attribute name can be omitted which means 'this node'

        Example:
            yangvoodoo.DataAccess.get_extensions(root, 'dirty-secret')

            Looks for an extension named 'info' on root.dirty_secret
        """

        if node._NODE_TYPE == "Root" and not attr:
            raise ValueError("Attribute name of a child leaf is required for 'has_extension' on root")

        spath = node.__dict__['_spath']

        if attr:
            node_schema = node._get_schema_of_path(node._form_xpath(spath, attr))
        else:
            node_schema = node._get_schema_of_path(spath)

        for extension in node_schema.extensions():
            if not module or extension.module().name() == module:
                arg = extension.argument()
                if arg == 'true':
                    arg = True
                elif arg == 'false':
                    arg = False
                yield (extension.module().name()+":"+extension.name(), arg)

    @classmethod
    def get_extension(self,  node, name, attr=None, module=None):
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
            raise ValueError("Attribute name of a child leaf is required for 'has_extension' on root")

        extensions = yangvoodoo.DataAccess.get_extensions(node, attr, module)
        for (m, a) in extensions:
            if module:
                if m == module + ":" + name:
                    return a
            else:
                if ":" + name in m:
                    return a
        return None

    @classmethod
    def get_root(self, session, attribute):
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

        super_root = yangvoodoo.VoodooNode.SuperRoot()
        super_root.attach_node_from_session(session, attribute)
        return super_root

    def get_node(self):
        """
        Instantiate Node-based access to the data stored in the backend defined by a yang
        schema. The data access will be constraint to the YANG module chosen when invoking
        this method.

        We must have access to the same YANG module loaded within in sysrepo, which can be
        set by modifying yang_location argument.
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()

        self.data_abstraction_layer.setup_root()

        context = yangvoodoo.VoodooNode.Context(self.module, self, self.yang_schema, self.yang_ctx, log=self.log)

        self.help = self._help

        return yangvoodoo.VoodooNode.Root(context)

    def connect(self, module=None,  yang_location="../yang/", tag='client'):
        """
        Connect to the datastore.

        returns: True
        """
        if not os.path.exists(yang_location + "/" + module + ".yang"):
            raise ValueError("YANG Module "+module+" not present in "+yang_location)

        self.module = module
        self.yang_ctx = libyang.Context(yang_location)
        self.yang_schema = self.yang_ctx.load_module(self.module)
        connect_status = self.data_abstraction_layer.connect(self.module)

        self.session = self.data_abstraction_layer.session
        self.conn = self.data_abstraction_layer.conn
        self.connected = True
        return connect_status

    def disconnect(self):
        """
        Disconnect from the datastore - losing any pending changes to data which has not yet
        been committed.

        returns: True
        """
        self.connected = False
        return self.data_abstraction_layer.disconnect()

    def commit(self):
        """
        Commit pending changes to the datastore backend, it is possible to call validate()
        before a commit. The datastore has the final say if the changes are valid or not,
        the only assurance that the yangvoodoo objects can provide is that the data conforms
        to the YANG schema - it cannot guarantee the values are consistent with the full
        data held in the datastore.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.commit()

    def validate(self):
        """
        Validate the pending changes against the data in the backend datatstore without actually
        committing the data. The full set of rules within the YANG model/datatstore must be
        checked such that a user calling validate(), commit() in short sucession should get a
        failure to commit.

        returns: True or False
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.validate()

    def create_container(self, xpath):
        """
        Create a presence container - only suitable for use on presence containers.

        returns: VoodoooPresenceContainer()
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.create_container(xpath)

    def create(self, xpath, keys=None, values=None, module=None):
        """
        Create a list item by XPATH including keys
         e.g. /path/to/list[key1='val1'][key2='val2'][key3='val3']

         returns: VoodooListElement()
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.create(xpath, keys=keys, values=values, module=module)

    def set(self, xpath, value, valtype=18):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        valtype defaults to 18 (STRING), see Types.DATA_ABSTRACTION_MAPPING for the
        full set of value types.

        returns: value
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.set(xpath, value, valtype)

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        """
        For the given XPATH (of a list) return an sorted list of XPATHS representing every
        list element within the list.

        returns: generator of sorted XPATHS
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.gets_sorted(xpath, ignore_empty_lists)

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        """
        For the given XPATH (of a list) return an unsorted list of XPATHS representing every
        list element within the list.
        This method must maintain the order that entries were added by the user into the list.

        returns: generator of XPATHS
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.gets_unsorted(xpath, ignore_empty_lists)

    def gets(self, xpath):
        """
        For the given XPATH (of a leaflist) return an list of values from the datastore in the
        order they were entered.

        returns: generator of Values
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.gets(xpath)

    def add(self, xpath, value, valtype=18):
        """
        For the given XPATH of a leaflist add an item to the datastore.

        returns: the value
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.add(xpath, value, valtype)

    def remove(self, xpath, value):
        """
        For the given XPATH of a leaflist remove the item from the datastore.
        Note: the xpath points to the leaf-list not the item.

        returns: None.
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.remove(xpath, value)

    def has_item(self, xpath):
        """
        Evaluate if the item is present in the datatsore, determines if a specific XPATH has been
        set, may be called on leaves, presence containers or specific list elements.

        returns: True or False
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.has_item(xpath)

    def get(self, xpath):
        """
        Get a specific path (leaf nodes or presence containers), in the case of leaves a python
        primitive is returned (i.e. strings, booleans, integers).
        In the case of non-terminating nodes (i.e. Lists, Containers, PresenceContainers) this
        method will return a Voodoo object of the relevant type.

        FUTURE CHANGE: in future enumerations should be returned as a specific object type


        returns: value or Vooodoo<X>
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.get(xpath)

    def delete(self, xpath):
        """
        Delete the data, and all decendants for a particular XPATH.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.delete(xpath)

    def refresh(self):
        """
        Ensure we are still connected to sysrepo and using the latest dataset.

        Note: if we are ever disconnected it is possible to simply just call
        the connect() method of this object.

        returns: True
        """
        if not self.connected:
            raise yangvoodoo.Errors.NotConnect()
        return self.data_abstraction_layer.refresh()

    def is_session_dirty(self):
        """
        The definition of a dirty session is one which has had data changed since we opened
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
          This session is now considered dirty
          print(root1.simpleleaf)

        In this case the value 'simpleleaf' is set to 2, as session2 was committed last. There is
        no mechanism implemented to detect the conflict. The data from the first session was set
        for the moment in time between it's commit and session2's commit.

        This method 'is_session_dirty' can be used by application to decide if they wish to
        commit.

        Example2:
          session1.connect()                     session2.commit()
          root1.simplelist.create('A')           root2.simplelist.create('B')
          root1.commit()                         ---
                                                 This session is now considered dirty
                                                 session2.commit()
          len(root.simplelist)

          In this case the commit from session2 doesn't remove ListElement 'A' because the
          transaction for session2 did not make any changes.
        """
        return self.data_abstraction_layer.is_session_dirty()
