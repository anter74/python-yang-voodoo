# Summary

- The results below are center towards reading and list iteration, the average speed is from 20,000 operations.
- The results are based on the test scenario in `timing.py`, the benefits from any of the optimisation is only gained if data that has been cached/pre-fetched is actually accessed.


These values come from sysrepo running within Docker on a Intel i7-7820HQ (approx 23% slower in docker)


| Speed (ms per operation)     | Scenario                       |
|------------------------------|--------------------------------|
| 1.21                         | sysrepo alone                  |
| 0.66                         | with proxy lazy cache*         |
| 0.21                         | with proxy and speculative creation of list keys\** |



\* the first version of the proxy cache is lazy, when deleting, adding items to lists parts of the cache are flushed.
\** around 20 us per key to pre-populate *if* we don't care about the type of keys, i.e. if we re-enable this we will show list-keys as, integers.
To make this more precise will narrow the gap.


See `proxydal.py`

```python
# """
# Pre cache
# /integrationtest:web/bands[name='Hunck']/name => Hunck
# """
# (p, keys, vals) = yangvoodoo.Common.Utils.decode_xpath_predicate(xpath)
#
#
# for index in range(len(keys)):
#     key_path = xpath + "/" + keys[index]
#     self.value_cached[key_path] = vals[index]

```

## Test

 - Opening a session and getting a root node (1-3ms)
 - Simple get of leaves CACHE-MISS (~ 1ms per item)
 - Spin around a list CACHE-MISS (4.3ms for a list of 250 elements)
 - Spin around a list CACHE-HIT (0.3ms for a list of 250 elements)
 - Length of a list CACHE-HIT (0.1ms)
