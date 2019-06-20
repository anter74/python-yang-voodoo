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

        differ = DiffIterator(dataset_A, dataset_B, filter='/integrationtest:diffs')

    The resulting object can be used with.

        differ.all()        - return all results from remove, add and modify
        differ.remove()     - return only XPATH's that have been removed from dataset_B (in dataset_A)
        differ.add()        - return only XPATH's that have been added from dataset_B (not in dataset_A)
        differ.modified()   - return only XPATH's that have been modified (different values in dataset_A and dataset_B)



    TODO: this implementation is not optimal and is dependant upon the stub.
    """

    ADD = 1
    MODIFY = 2
    REMOVE = 3

    def __init__(self, dataset_a, dataset_b, filter=''):
        if isinstance(dataset_a, yangvoodoo.VoodooNode.Node):
            dataset_a = dataset_a._context.dal.dump_xpaths()
        if isinstance(dataset_b, yangvoodoo.VoodooNode.Node):
            dataset_b = dataset_b._context.dal.dump_xpaths()

        self.a = dataset_a
        self.b = dataset_b
        self.filter = filter

        self.diffset = diff(self.a, self.b)
        self.results = []
        for (op, path, values) in self.diffset:

            print(op, path, values)
            value_is_a_list = False
            if isinstance(path, list):
                value_is_a_list = True
                path = path[0]
                index_of_item_changing = path[1]

            try:
                if op == 'change':
                    if not path[0:len(filter)] == filter:
                        continue
                    (old, new) = values

                    # This is specific to stub_store which uses lists/tuples for things it creates as covenient
                    # lookups.
                    if isinstance(new, tuple):
                        continue
                    self.results.append((path, old, new, self.MODIFY))
                else:
                    for (leaf_path, value) in values:
                        if isinstance(leaf_path, str):
                            path = leaf_path
                        if not path[0:len(filter)] == filter:
                            continue

                        # This is specific to stub_store which uses lists/tuples for things it creates as covenient
                        # lookups.
                        if isinstance(value, tuple):
                            continue
                        if op == 'remove':
                            self.results.append((path, value, None, self.REMOVE))
                        else:
                            self.results.append((path, None, value, self.ADD))
            except Exception as err:
                print(err)
                print(op, path, value)
                raise ValueError("%s %s %s %s" % (op, path, value, err))

    def all(self):
        for result in self.results:
            yield result

    def remove(self):
        for (path, old, new, op) in self.results:
            if op == self.REMOVE:
                yield (path, old, new, op)

    def add(self):
        for (path, old, new, op) in self.results:
            if op == self.ADD:
                yield (path, old, new, op)

    def modified(self):
        for (path, old, new, op) in self.results:
            if op == self.MODIFY:
                yield (path, old, new, op)
