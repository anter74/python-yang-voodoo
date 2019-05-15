- optimise with get_items() or sr_get_items_iter() so that list fetches are not painfuly slow
  - the former makes mention about having to call free_items. the latter probably doesn't
    - get_items()
    All data elements are transferred within one message from the datastore, which is much more efficient that calling multiple sr_get_item calls.
    - get_items_iter()
    Requested data elements are transferred from the datastore in larger chunks of pre-defined size, which is much more efficient that calling multiple sr_get_item calls, and may be less memory demanding than calling sr_get_items on very large datasets.
  - is it possible to cache XPATH look ups right now `connect()` is doing `sr.Session(sr.Connection("xxx"))` so we can probably subscribe for module changes in order to clear the cahce.
     - **THIS COULD HAVE AN UNINTENDED CONSEQUENCE/BENEFIT** that sysrepo has a requirement of having a subscriber, this would count as a subscriber.
