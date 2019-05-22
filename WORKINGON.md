
 - Likely approach to solve the following is to wrap sysrepodal into a stubdal as a cache/proxy.
   - In the case of a pure stub it's all managed natively.
   - In the case of sysrepo (or other backend) each call will need to proxy to the realbackend - we rely on the backend to keep the data set the same after we connect..., until we explicitly call refresh(). The works to our advantage because we can flush to proxied values we stored once refresh() is called on the session object.
   - In this case stub needs uplifiting to provide default values from the yang schema.



- optimise with get_items() or sr_get_items_iter() so that list fetches are not painfuly slow
  - Note: Stub works in 1x10-5 for iterating lots of items, sysrepo takes 0.3 seconds. It's consistent with no caching.
  - TODO: work out if sysrepo operates in memory or on disk (if the latter it's quite good).
  - the former makes mention about having to call free_items. the latter probably doesn't
    - get_items()
    All data elements are transferred within one message from the datastore, which is much more efficient that calling multiple sr_get_item calls.
    - get_items_iter()
    Requested data elements are transferred from the datastore in larger chunks of pre-defined size, which is much more efficient that calling multiple sr_get_item calls, and may be less memory demanding than calling sr_get_items on very large datasets.
  - is it possible to cache XPATH look ups right now `connect()` is doing `sr.Session(sr.Connection("xxx"))` so we can probably subscribe for module changes in order to clear the cahce.
     - **THIS COULD HAVE AN UNINTENDED CONSEQUENCE/BENEFIT** that sysrepo has a requirement of having a subscriber, this would count as a subscriber.
