class Cache:
    def __init__(self):
        self.items = {}

    def is_path_cached(self, path):
        if path in self.items:
            return True
        return False

    def get_item_from_cache(self, path):
        return self.items[path]

    def remove_entry(self, path):
        if path in self.items:
            del self.items[path]

    def add_entry(self, path, cache_object):
        """
        Add an entry into the cache.

        key = an XPATH path (e.g. /simpleleaf)
        cache_object = Whatever it wants to be.
        """

        self.items[path] = cache_object

    def empty(self):
        self.items.clear()
