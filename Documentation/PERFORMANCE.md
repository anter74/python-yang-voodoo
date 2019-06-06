# Summary

- The results below are center towards reading and list iteration, the average speed is from 20,000 operations.
- The results are based on the test scenario in `timing.py`, the benefits from any of the optimisation is only gained if data that has been cached/pre-fetched is actually accessed.


These values come from sysrepo running within Docker on a Intel i7-7820HQ (approx 23% slower in docker)


| Speed (ms per operation)     | Scenario                       |
|------------------------------|--------------------------------|
| 1.21                         | sysrepo alone                  |
| 0.66                         | with proxy lazy cache*         |
| 0.21                         | with proxy and type-blind speculative creation of list keys\** |
| 0.38                         | with proxy and type-correct speculative creation of list keys\***  |
| 0.12                         | stub based datastore (python dict based)       |
| 0.14                         | stub based datastore with proxy and type-correct speculative creation of list keys\*** |
| 0.9                          | sysrepo with proxy lazy cache and refactored libyang lookups - but no speculative creating of list keys |
| 0.35                         | sysrepo with proxy lazy cache and refactored libyang lookups - and type correct speculative lookups |
| 0.07                         | stub with proxy lazy cache and refactored libyang lookups - but no speculative creating of list keys |
| 0.09                         | stub with proxy lazy cache and refactored libyang lookups - and type correct speculative lookups \**** |


- \* the first version of the proxy cache is lazy, when deleting, adding items to lists parts of the cache are flushed.

- \** around 20 us per key to pre-populate *if* we don't care about the type of keys, i.e. if we re-enable this we will show list-keys as, integers

- \*** when we pre-populate list keys with the correct type it's a bit slower

- \**** because this is slower with speculative caching of list keys now we categorise the DAL as IN MEMORY or not - we only do specualtive_caching of list_keys for DAL's that are not IN MEMORY


## Test

 - Opening a session and getting a root node (1-3ms)
 - Simple get of leaves CACHE-MISS (~ 1ms per item)
 - Spin around a list CACHE-MISS (4.3ms for a list of 250 elements)
 - Spin around a list CACHE-HIT (0.3ms for a list of 250 elements)
 - Length of a list CACHE-HIT (0.1ms)


# Slight improvement with caching the schema nodes - 30 microseconds
