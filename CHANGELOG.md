# Release History:


- v0.0.1 - Initial version
  -  Proof of concept implementation
- v0.0.2 - Enhancements before
  - FIX: accessing empty lists would raise exception
  - FIX: len(<OUTER_LIST>.<INNER_LIST>) return the total count of entries across both lists (becuase we used schema rather than value path)
  - FEATURE: `session.help(node)` returns YANG description if present.
  - FEATURE: `node._parent` returns the parent object
  - FEATURE: `for x in list._xpath_sorted` returns items sorted by xpath `for x in list` rerturns items based on the datastore order (which should be the order they were added)
  - Docker file split into `builder` for compiling everything from source and a smaller version (`docker/build.sh`) to build both images.
- devel -
  - FIX: return a PresenceContainer object when calling create on a presence node path.
  - FIX: implement `has_item(xpath)` asking the datastore about existence rather than getting the full list back.
  - Renamed BlackArt to Voodoo for representation of objects.
  - Implement specific `disconnect` method on the data_abstraction_layer
  - The Stub Datastore supports a `dump_xpaths` method, useful for asserting within unit tests.
  - Support for setting data using Jinja2 templates.
  - **CHANGE OF BEHAVIOUR** `session.connect()` should not be `session.connect('yang-module-name')`. `session.get_root('yang-mdoule-name')` should be `session.get_root()`. This forces a single session per yang module.
  - FIX: stubdal to create /path[key='val']/key = val to match sysrepo implementation.
