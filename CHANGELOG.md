# Release History:


# v0.0.1 - Initial version

  -  Proof of concept implementation

# v0.0.2 - Enhancements before

  - FIX: accessing empty lists would raise exception
  - FIX: len(<OUTER_LIST>.<INNER_LIST>) return the total count of entries across both lists (becuase we used schema rather than value path)
  - FEATURE: `session.help(node)` returns YANG description if present.
  - FEATURE: `node._parent` returns the parent object
  - FEATURE: `for x in list._xpath_sorted` returns items sorted by xpath `for x in list` rerturns items based on the datastore order (which should be the order they were added)
  - Docker file split into `builder` for compiling everything from source and a smaller version (`docker/build.sh`) to build both images.

# v0.0.3 - Un-optimised Version

  - FIX: return a PresenceContainer object when calling create on a presence node path.
  - FIX: implement `has_item(xpath)` asking the datastore about existence rather than getting the full list back.
  - Renamed BlackArt to Voodoo for representation of objects.
  - Implement specific `disconnect` method on the data_abstraction_layer
  - The Stub Datastore supports a `dump_xpaths` method, useful for asserting within unit tests.
  - Support for setting data using Jinja2 templates.
  - **CHANGE OF BEHAVIOUR** `session.connect()` should not be `session.connect('yang-module-name')`. `session.get_node('yang-mdoule-name')` should be `session.get_node()`. This forces a single session per yang module.
  - FIX: stubdal to create /path[key='val']/key = val to match sysrepo implementation.
  - **CHANGE OF BEHAVIOUR** `session.get_root()` renamed to `session.get_node()`
  - **CHANGE OF BEHAVIOUR** `session.get_node()` does not take in `yang_location` this has now moved to `session.connect`
  - **EXPERIMENTAL** a 'SuperRoot' to organise together multiple sessions together
    - At this stage not considerations for ordering of commits(), rollbacks on failure, dependencies between sessions.
  - Implemented leaf-list object type with integration to sysrepo backend and stub backend.
  - Implement support for `yangvoodoo.DataAccess.get_extensions(<node>, <child-attribute>)` or `yangvoodoo.DataAccess.get_extension(<node>, <extension-name>, <child-attribute>)` for 'containing nodes' to receive list of extensions or the extension istelf.
    - Example of containing nodes, Lists (but not Leaf-Lists), Containers, Root. The name of a child attribute can be provided (mandatory for root). i.e. `root.morecomplex.get_extension('info')` will look for the extension info on `/root/morecomplex` itself.
  - **EXPERIMENTAL** DiffEngine

# v0.0.4 - Optimisations and Cleanup (Stegosaurus)

   - FIX: for template applier when using lists within lists
   - Travis now working on commits.
   - Access to Datastore is proxied via a cache layer - sysrepo is designed for memory constrained environments so doesn't hold the data in memory.
   - Proxy Layer speculatively creates list-keys to avoid a read operation to the the true backend.
   - **CHANGE OF BEHAVIOUR** `list.xpath()` now `list.elements()` - now uses the correct value path for list of lists.
   - FIX: setting a list key as a blank value must be prevented
   - FIX: re-implement changing of list keys by using yang schema on \__setattr__ rather than trusting the backend to enforce it.
   - FIX: sysrepo dataa-abstraction layer dirty now captures if we have made changes (raises NoChangesToCommit) if there are no changes.
   - FEATURE: stubdal now provides default values
   - REMOVE: un-used module from list create operation
   - FEATURE: support \__getitem__ to retrieve child nodes
   - FEATURE: support for choice/case statements (initial support with no validation)
   - FEATURE: support UINT64/INT64 values.
   - FEATURE: raise an exception `Cannot assign a value to ......` when trying to assign values to containing nodes.
   - FEATURE: add `session.from_xmlstr` to import data without jinja2 processing from disk.
   - FEATURE: support for yang empty leaf type - returns an object with `create()`, `exists()` and `remove()`
   - FEATURE: nodes can now have underscore and hyphens.
   - FEATURE: `session.describe()` now shows children
   - FEATURE: `session.tree()` to print a pyang style tree


# v0.0.5 - Gap filling, Bugfixes and Cleanup (Tortoise)

  - FIX: Choices/Cases applied via a template now calculate the correct data path.
  - Sysrepo version bumped from 0.7.7 to 660552222ee6376efa560d9bcc7b832886ff460a
  - Implemented dump_xpaths() to sysrepo data abstraction layer.
  - Implement to_xmlstr in TemplateNinja to convert a list of XPATH's to XML.
  - Leaf-List entrires no-longer duplicated in the stub store.
  - Reword error message for get-yang type many times it's bad data
    - union's may not be fully supported, especially with unions (union of enumeration + uint is supported)
    - see `best_guess_of_yang_type` - need to formalise to a more precise method that interrogates unions through typedefs and leafrefs
  - FIX: caching of node_schema to be based on data+schema path to avoid choice/cases returning bad data.
  - FIX: DiffEngine fixes for leaf-lists  
  - Upgrade to python 3.7.3
  - FIX: Don't write list-keys twice when using TemplateNinja's to_xmlstr


# DEVEL

  - Docker image with jupyter notebooks and shellinabox enabled for learning
  - ENHANCEMENT: DiffEngine now gives a combined method to get removes, modifies then deletes in one call.
  - Ability to more easily set data in the back-end without using voodoo (the value type is derrived)
    (e.g session.set_data_by_xpath(context, xpath, value)
  - FIX: Template conversion into XML from XPATH (list-values which looked like xpath were affecting the structure)
  - Implement \__setitem__ so we can do root.bronze['A'] = 'AAAAA'
  - TemplateNinja: provide support for dumping XML with namespace and <data> container `to_xmlstr_with_ns`. *this is a hidden option not exposed on yangvoodoo session object*
  - valtype converted to libyang types instead of sysrepo types (sysrepodal now does this mapping)
  - `set` operation on the dal now takes node\_type as well as val\_type
  - EXPERIMENTAL: support for libyang based stub- including dump/load from file of XML or JSON.
    - dump_xpaths() not supported.
  - FIX: don't return non-list keys when dir() of a list
  - CLEANUP: remove dormant/unsafe regexes
  - Append an underscore to nodes which match the python reserved keyswords (defined in Types.py)
