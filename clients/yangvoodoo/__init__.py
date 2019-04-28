#!/usr/bin/python3
import libyang
import sysrepo as sr
import time
import logging
import socket
import yangvoodoo.BlackArtNodes


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

    The backend supported by this module is sysrepo (without netopeer2), however the
    basic constructs decribed by this class could be ported to other backends.

    Dependencies:
     - sysrepo 0.7.7 python3  bindings (https://github.com/sysrepo/sysrepo)
     - libyang 0.16.78 (https://github.com/rjarry/libyang-cffi/)
    """

    def __init__(self, log=None, local_log=False, remote_log=False):
        if not log:
            log = LogWrap(local_log=local_log, remote_log=remote_log)
        self.log = log

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
        context = yangvoodoo.BlackArtNodes.Context(module, self, yang_schema, yang_ctx, log=self.log)
        return yangvoodoo.BlackArtNodes.Root(context)

    def connect(self, tag='client'):
        """
        Connect to the datastore.
        """
        self.conn = sr.Connection("%s%s" % (tag, time.time()))
        self.session = sr.Session(self.conn)

    def commit(self):
        try:
            self.session.commit()
        except RuntimeError as err:
            self._handle_error(None, err)

    def validate(self):
        try:
            self.session.validate()
        except RuntimeError as err:
            self._handle_error(None, err)
        return True

    def create_container(self, xpath):
        try:
            self.set(xpath, None, sr.SR_CONTAINER_PRESENCE_T)
        except RuntimeError as err:
            self._handle_error(xpath, err)

    def _handle_error(self, xpath, err):
        sysrepo_errors = self.session.get_last_errors()
        errors = []
        for index in range(sysrepo_errors.error_cnt()):
            sysrepo_error = sysrepo_errors.error(index)
            if sysrepo_error.xpath() == xpath:
                if sysrepo_error.message() == "The node is not enabled in running datastore":
                    raise yangvoodoo.Errors.SubscriberNotEnabledOnBackendDatastore(xpath)
            errors.append((sysrepo_error.message(), sysrepo_error.xpath()))

        raise yangvoodoo.Errors.BackendDatastoreError(errors)

    def create(self, xpath):
        """
        Create a list item by XPATH including keys
         e.g. / path/to/list[key1 = ''][key2 = ''][key3 = '']
        """
        try:
            self.set(xpath, None, sr.SR_LIST_T)
        except RuntimeError as err:
            self._handle_error(xpath, err)

    def set(self, xpath, value, valtype=sr.SR_STRING_T):
        """
        Set an individual item by XPATH.
          e.g. / path/to/item

        It is required to provide the value and the type of the field in most cases.
        In the case of Decimal64 we cannot use a value type
            v=sr.Val(2.344)
        """
        self.log.debug('SET: %s => %s (%s)' % (xpath, value, valtype))
        if valtype:
            v = sr.Val(value, valtype)
        else:
            v = sr.Val(value)

        try:
            self.session.set_item(xpath, v)
        except RuntimeError as err:
            self._handle_error(xpath, err)

    def gets(self, xpath, ignore_empty_lists=False):
        """
        Get a list of xpaths for each items in the list, this can then be used to fetch data
        from within the list.

        By default we look to actually get the specific item, however if we are using this
        function from an iterator with a blank list we do not want to throw an exception.
        """
        vals = self.session.get_items(xpath)
        if not vals:
            if ignore_empty_lists:
                return
            raise yangvoodoo.Errors.ListDoesNotContainElement(xpath)
        else:
            for i in range(vals.val_cnt()):
                v = vals.val(i)
                try:
                    yield v.xpath()
                except RuntimeError as err:
                    self._handle_error(xpath, err)

    def get(self, xpath):
        sysrepo_item = self.session.get_item(xpath)
        try:
            return self._get_python_datatype_from_sysrepo_val(sysrepo_item, xpath)
        except RuntimeError as err:
            self._handle_error(xpath, err)

    def delete(self, xpath):
        try:
            self.session.delete_item(xpath)
        except RuntimeError as err:
            self._handle_error(xpath, err)

    def _get_python_datatype_from_sysrepo_val(self, valObject, xpath=None):
        """
        For now this is copied out of providers/dataprovider/__init__.py, if this carries on as a good
        idea then would need to combined.

        Note: there is a limitation here, we can't return False for a container presence node that doesn't
        exist becuase we never will get a valObject for it. Likewise boolean's and empties that dont' exist.

        This is a wrapped version of a Val Object object
        http: // www.sysrepo.org/static/doc/html/classsysrepo_1_1Data.html
        http: // www.sysrepo.org/static/doc/html/group__cl.html  # ga5801ac5c6dcd2186aa169961cf3d8cdc

        These don't map directly to the C API
        SR_UINT32_T 20
        SR_CONTAINER_PRESENCE_T 4
        SR_INT64_T 16
        SR_BITS_T 7
        SR_IDENTITYREF_T 11
        SR_UINT8_T 18
        SR_LEAF_EMPTY_T 5
        SR_DECIMAL64_T 9
        SR_INSTANCEID_T 12
        SR_TREE_ITERATOR_T 1
        SR_CONTAINER_T 3
        SR_UINT64_T 21
        SR_INT32_T 15
        SR_ENUM_T 10
        SR_UNKNOWN_T 0
        SR_STRING_T 17
        SR_ANYXML_T 22
        SR_INT8_T 13
        SR_LIST_T 2
        SR_INT16_T 14
        SR_BOOL_T 8
        SR_ANYDATA_T 23
        SR_UINT16_T 19
        SR_BINARY_T 6

        """
        if not valObject:
            return None
        type = valObject.type()
        if type == sr.SR_STRING_T:
            return valObject.val_to_string()
        elif type == sr.SR_UINT64_T:
            return valObject.data().get_uint64()
        elif type == sr.SR_UINT32_T:
            return valObject.data().get_uint32()
        elif type == sr.SR_UINT16_T:
            return valObject.data().get_uint16()
        elif type == sr.SR_UINT8_T:
            return valObject.data().get_uint8()
        elif type == sr.SR_UINT64_T:
            return valObject.data().get_uint8()
        elif type == sr.SR_INT64_T:
            return valObject.data().get_int64()
        elif type == sr.SR_INT32_T:
            return valObject.data().get_int32()
        elif type == sr.SR_INT16_T:
            return valObject.data().get_int16()
        elif type == sr.SR_INT64_T:
            return valObject.data().get_int8()
        elif type == sr.SR_BOOL_T:
            return valObject.data().get_bool()
        elif type == sr.SR_ENUM_T:
            return valObject.data().get_enum()
        elif type == sr.SR_CONTAINER_PRESENCE_T:
            return True
        elif type == sr.SR_CONTAINER_T:
            raise yangvoodoo.Errors.NodeHasNoValue('container', xpath)
        elif type == sr.SR_LEAF_EMPTY_T:
            raise yangvoodoo.Errors.NodeHasNoValue('empty-leaf', xpath)
        elif type == sr.SR_LIST_T:
            return None
        elif type == sr.SR_DECIMAL64_T:
            return valObject.data().get_decimal64()

        raise yangvoodoo.Errors.NodeHasNoValue('unknown', xpath)

    def refresh(self):
        """
        Ensure we are still connected to sysrepo and using the latest dataset.

        Note: if we are ever disconnected it is possible to simply just call
        the connect() method of this object.
        """
        try:
            self.session.refresh()
        except RuntimeError:
            raise yangvoodoo.Errors.NotConnect()
