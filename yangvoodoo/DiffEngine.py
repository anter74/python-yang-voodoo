#!/usr/bin/env python3
# from dictdiffer import diff, patch, swap, revert
from dictdiffer import diff
import yangvoodoo
import yangvoodoo.stubdal


class DiffIterator:

    """
    This call return a diffset for a particular part of a dataset.

    The return value is an ordered set of
        (path, old-value, new-value, operation)

    Example usage:

        differ = DiffIterator(dataset_A, dataset_B, filter='/integrationtest:diffs', end_filter='/name')

    The resulting object can be used with.

        differ.all()        - return all results from remove, add and modify
        differ.remove()     - return only XPATH's that have been removed from dataset_B (in dataset_A)
        differ.add()        - return only XPATH's that have been added from dataset_B (not in dataset_A)
        differ.modified()   - return only XPATH's that have been modified (different values in dataset_A and dataset_B)
        differ.remove_modify_then_add()  - a convenience function of the above
        differ.modify_then_add()  - a convenience function of the above
        differ.remove_then_modify()  - a convenience function of the above

    The filters
    TODO: this implementation is not optimal - the format data comes back from dictdiffer is a little different depending
    on the exact nature of the diff. Leaf-lists are more difficult.

    """

    ADD = 1
    MODIFY = 2
    REMOVE = 3

    def __init__(self, dataset_a, dataset_b, start_filter="", end_filter=""):
        if isinstance(dataset_a, yangvoodoo.VoodooNode.Node):
            dataset_a = dataset_a._context.dal.dump_xpaths()
        if isinstance(dataset_b, yangvoodoo.VoodooNode.Node):
            dataset_b = dataset_b._context.dal.dump_xpaths()

        self.a = dataset_a
        self.b = dataset_b
        self.start_filter = start_filter
        self.end_filter = end_filter
        self.diffset = diff(self.a, self.b)
        self.results = []

        for (op, path, values) in self.diffset:
            if isinstance(path, list):
                path = path[0]

            if op == "change":
                if not DiffIterator.is_filtered(path, start_filter, end_filter):
                    self._handle_modify(path, values)
            else:
                self._handle_add_or_remove(op, path, values)

    @staticmethod
    def is_filtered(path, filter, end_filter):
        if path[0 : len(filter)] == filter and (
            end_filter == "" or path[-len(end_filter) :] == end_filter
        ):
            return False
        return True

    def _handle_add_or_remove(self, op, path, values):
        for (leaf_path, value) in values:
            if isinstance(leaf_path, str):
                path = leaf_path
            if DiffIterator.is_filtered(path, self.start_filter, self.end_filter):
                continue

            # This is specific to stub_store which uses lists/tuples for things it creates as covenient
            # lookups.
            if isinstance(value, tuple):
                continue
            if op == "remove":
                if isinstance(value, list):
                    pass
                else:
                    value = [value]
                for v in value:
                    self.results.append((path, v, None, self.REMOVE))
            else:
                if isinstance(value, list):
                    pass
                else:
                    value = [value]
                for v in value:
                    self.results.append((path, None, v, self.ADD))

    def _handle_modify(self, path, values):
        (old, new) = values
        # This is specific to stub_store which uses lists/tuples for things it creates as covenient
        # lookups.
        if not isinstance(new, tuple):
            self.results.append((path, old, new, self.MODIFY))

    def all(self, start_filter="", end_filter=""):
        for (path, oldval, newval, op) in self.results:
            if self.is_filtered(path, start_filter, end_filter):
                continue
            yield (path, oldval, newval, op)

    def remove(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.REMOVE and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)

    def add(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.ADD and not self.is_filtered(path, start_filter, end_filter):
                yield (path, old, new, op)

    def modified(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.MODIFY and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)

    def remove_modify_then_add(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.REMOVE and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)
        for (path, old, new, op) in self.results:
            if op == self.MODIFY and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)
        for (path, old, new, op) in self.results:
            if op == self.ADD and not self.is_filtered(path, start_filter, end_filter):
                yield (path, old, new, op)

    def modify_then_add(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.MODIFY and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)
        for (path, old, new, op) in self.results:
            if op == self.ADD and not self.is_filtered(path, start_filter, end_filter):
                yield (path, old, new, op)

    def remove_then_modify(self, start_filter="", end_filter=""):
        for (path, old, new, op) in self.results:
            if op == self.REMOVE and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)
        for (path, old, new, op) in self.results:
            if op == self.MODIFY and not self.is_filtered(
                path, start_filter, end_filter
            ):
                yield (path, old, new, op)
