import yangvoodoo
import yangvoodoo.basedal
import yangvoodoo.stubdal
from yangvoodoo.Common import Utils


class ProxyDataAbstractionLayer(yangvoodoo.basedal.BaseDataAbstractionLayer):

    """
    This method will provide a cache around a datastore.
    """

    DAL_ID = "ProxyDAL"

    def __init__(self, realstore, log=None):
        super().__init__(log)
        if not log:
            log = Utils.get_logger("Proxy" + realstore.DAL_ID)
        self.log = log
        self.cache = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.store = realstore
        self.refresh()

    def connect(self, module, tag='<id-tag>'):
        self.cache.connect(module, tag)
        return self.store.connect(module, tag)

    def disconnect(self):
        self.cache.disconnect()
        return self.store.disconnect()

    def commit(self):
        self.cache.commit()
        return self.store.commit()

    def validate(self):
        self.cache.validate()
        return self.store.validate()

    def container(self, xpath):
        if xpath not in self.value_cached:
            result = self.store.container(xpath)
            self.value_cached[xpath] = result
        return self.value_cached[xpath]

    def create_container(self, xpath):
        self.cache.create_container(xpath)
        self.value_cached[xpath] = True
        return self.store.create_container(xpath)

    def create(self, xpath, keys=[], values=[], module=None):
        self.has_item_cached = {}
        self.unsorted_cached = {}
        self.sorted_cached = {}
        self.cache.create(xpath, keys, values, module)
        return self.store.create(xpath, keys, values, module)

    def uncreate(self, xpath, keys=[], values=[], module=None):
        self.has_item_cached = {}
        self.unsorted_cached = {}
        self.sorted_cached = {}
        self.cache.uncreate(xpath)
        return self.store.uncreate(xpath)

    def add(self, xpath, value, valtype):
        self.cache.add(xpath, value, valtype)
        return self.store.add(xpath, value, valtype)

    def remove(self, xpath, value):
        self.cache.remove(xpath, value)
        self.refresh()
        return self.store.remove(xpath, value)

    def gets(self, xpath):
        if xpath not in self.value_cached:
            items = list(self.store.gets(xpath))
            self.value_cached[xpath] = items
        for val in self.value_cached[xpath]:
            yield val

    def has_item(self, xpath):
        if xpath not in self.has_item_cached:
            result = self.store.has_item(xpath)
            self.has_item_cached[xpath] = result
        return self.has_item_cached[xpath]

    def set(self, xpath, value, valtype=0):
        self.cache.set(xpath, value, valtype)
        self.value_cached[xpath] = value
        return self.store.set(xpath, value, valtype)

    def gets_sorted(self, list_xpath, ignore_empty_lists=False):
        if list_xpath not in self.sorted_cached:
            items = list(self.store.gets_sorted(list_xpath, ignore_empty_lists=ignore_empty_lists))
            self.sorted_cached[list_xpath] = items
        for xpath in self.sorted_cached[list_xpath]:
            yield xpath

    def gets_unsorted(self, list_xpath, ignore_empty_lists=False):
        if list_xpath not in self.unsorted_cached:
            items = list(self.store.gets_unsorted(list_xpath, ignore_empty_lists=ignore_empty_lists))
            self.unsorted_cached[list_xpath] = items
        for xpath in self.unsorted_cached[list_xpath]:
            yield xpath

    def get(self, xpath):
        if xpath not in self.value_cached:
            item = self.store.get(xpath)
            self.value_cached[xpath] = item
        return self.value_cached[xpath]

    def delete(self, xpath):
        self.cache.delete(xpath)
        self.store.delete(xpath)
        self.refresh()

    def refresh(self):
        self.cache.empty()
        self.value_cached = {}
        self.unsorted_cached = {}
        self.sorted_cached = {}
        self.has_item_cached = {}
