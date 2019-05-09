#!/usr/bin/python3
import libyang
import time
import logging
import socket
import importlib
import yangvoodoo.VoodooNode


class LogWrap():

    ENABLED_INFO = True
    ENABLED_DEBUG = True

    REMOTE_LOG_IP = "127.0.0.1"
    REMOTE_LOG_PORT = 6666

    def __init__(self, local_log=False, remote_log=False):
        self.ENABLED = local_log
        self.ENABLED_REMOTE = remote_log

        if self.ENABLED:
            format = "%(asctime)-15s - %(name)-20s %(levelname)-12s  %(message)s"
            logging.basicConfig(level=logging.DEBUG, format=format)
            self.log = logging.getLogger('blackhole')

        if self.ENABLED_REMOTE:
            self.log_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = self._pad_truncate_to_size("STARTED ("+str(time.time())+"):")
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    @staticmethod
    def _args_wildcard_to_printf(*args):
        if isinstance(args, tuple):
            # (('Using cli startup to do %s', 'O:configure'),)
            args = list(args[0])
            if len(args) == 0:
                return ''
            message = args.pop(0)
            if len(args) == 0:
                pass
            if len(args) == 1:
                message = message % (args[0])
            else:
                message = message % tuple(args)
        else:
            message = args
        return (message)

    def _pad_truncate_to_size(self, message, size=1024):
        if len(message) < size:
            message = message + ' '*(1024-len(message))
        elif len(message) > 1024:
            message = message[:1024]
        return message.encode()

    def info(self, *args):
        if self.ENABLED and self.ENABLED_INFO:
            self.log.info(args)
        if self.ENABLED_REMOTE and self.ENABLED_INFO:
            print('a')
            message = 'INFO ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    def error(self, *args):
        if self.ENABLED:
            self.log.error(args)
        if self.ENABLED_REMOTE:
            message = 'INFO ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))

    def debug(self, *args):
        if self.ENABLED and self.ENABLED_DEBUG:
            self.log.debug(args)

        if self.ENABLED_REMOTE and self.ENABLED_DEBUG:
            message = 'DEBUG ' + LogWrap._args_wildcard_to_printf(args)
            message = self._pad_truncate_to_size('INFO: %s %s' % (str(time.time()), message))
            self.log_socket.sendto(message, (self.REMOTE_LOG_IP, self.REMOTE_LOG_PORT))


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
    """

    def __init__(self, log=None, local_log=False, remote_log=False, data_abstraction_layer=None):
        if not log:
            log = LogWrap(local_log=local_log, remote_log=remote_log)
        self.log = log
        self.session = None
        self.conn = None
        if data_abstraction_layer:
            self.data_abstraction_layer = data_abstraction_layer
        else:
            self.data_abstraction_layer = self._get_data_abastraction_layer(log)

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
        except Exception as err:
            pass

    def get_root(self, module, yang_location="../yang/"):
        """
        Instantiate Node-based access to the data stored in the backend defined by a yang
        schema. The data access will be constraint to the YANG module chosen when invoking
        this method.

        We must have access to the same YANG module loaded within in sysrepo, which can be
        set by modifying yang_location argument.
        """
        yang_ctx = libyang.Context(yang_location)
        yang_schema = yang_ctx.load_module(module)
        context = yangvoodoo.VoodooNode.Context(module, self, yang_schema, yang_ctx, log=self.log)

        self.help = self._help

        return yangvoodoo.VoodooNode.Root(context)

    def connect(self, tag='client'):
        """
        Connect to the datastore.
        """
        connect_status = self.data_abstraction_layer.connect()
        self.session = self.data_abstraction_layer.session
        self.conn = self.data_abstraction_layer.conn
        return connect_status

    def commit(self):
        """
        Commit pending changes to the datastore backend.
        """
        return self.data_abstraction_layer.commit()

    def validate(self):
        """
        Validate the pending changes against the data in the backend datatstore without actually committing
        the data.
        """
        return self.data_abstraction_layer.validate()

    def create_container(self, xpath):
        return self.data_abstraction_layer.create_container(xpath)

    def create(self, xpath):
        """
        Create a list item by XPATH including keys
         e.g. / path/to/list[key1 = ''][key2 = ''][key3 = '']
        """
        return self.data_abstraction_layer.create(xpath)

    def set(self, xpath, value, valtype=18):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        It is required to provide the value and the type of the field in most cases.
        In the case of Decimal64 we cannot use a value type
            v=sr.Val(2.344)

        18 is the sysrepo value sr.SR_STRING_T
        """
        return self.data_abstraction_layer.set(xpath, value, valtype)

    def gets_sorted(self, xpath, ignore_empty_lists=False):
        """
        Get a generator providing a sorted list of xpaths, which can then be used for fetch data frmo
        within the list.
        """
        return self.data_abstraction_layer.gets_sorted(xpath, ignore_empty_lists)

    def gets_unsorted(self, xpath, ignore_empty_lists=False):
        """
        Get a generator providing xpaths for each items in the list, this can then be used to fetch data
        from within the list.

        By default we look to actually get the specific item, however if we are using this
        function from an iterator with a blank list we do not want to throw an exception.
        """
        return self.data_abstraction_layer.gets_unsorted(xpath, ignore_empty_lists)

    def get(self, xpath):
        return self.data_abstraction_layer.get(xpath)

    def delete(self, xpath):
        return self.data_abstraction_layer.delete(xpath)

    def refresh(self):
        """
        Ensure we are still connected to sysrepo and using the latest dataset.

        Note: if we are ever disconnected it is possible to simply just call
        the connect() method of this object.
        """
        return self.data_abstraction_layer.refresh()
