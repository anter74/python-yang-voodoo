# Release History:


- v0.0.1 - Initial version
  -  Proof of concept implementation
- v0.0.2 - Enhancements before
  - FIX: accessing empty lists would raise exception
  - FEATURE: `session.help(node)` returns YANG description if present.
  - FEATURE: `node._parent` returns the parent object
  - FEATURE: `for x in list._xpath_sorted` returns items sorted by xpath `for x in list` rerturns items based on the datastore order (which should be the order they were added)
