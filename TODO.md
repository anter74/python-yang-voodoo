# TODO:

- ~~convert 'NODE_TYPE' to '_NODE_TYPE' to hide from ipython~~
- ~~allow the location of yang's to be specified.~~
- define (with tests) further yang types in Types class (and handle a fallback better than 'keyerror')
- session revert() and session compare() would be useful functions.
- typedef's (partly resolved by using libyang's type().base() - but unions don't provide a composite base type)
- leafref's (as with typedefs type().base() from libyang doesn't tell us the type).
  - ~~leafrefs to non-unions~~
  - leafrefs to union (Partially supported - to be fully supported with libyang(swig) vs yang(cffi) changes - (ref branch: libyang-cffi-vs-libyang-swig_for_validation)
- ~~enumeration test cases~~
- ~~underscore conversion~~
- should support <object>[child-attr-name] for setting, getting data (i.e. where we want to use a variable to define child-attr-name])
- setting a list key as a blank value must be prevented.
- deletes (of non-primitives)
- choices
- testing membership of list elements is lazily done by asking for everything on the backend - implement a method to ask the backend datastore about membership.
- ~~augmentation - augment seems to just work out of the box with libyang~~
- deviations
- leaf-lists are not implemented yet.
- jinja2 templates are a little trickier accessing data on objects is trivial, invoking object (not sure how that works).
  - Consider list of bands, with a list of gis - if we want to find the the last gig we can do this.
  - In python we can do `list(root.web.bands._xpath_sorted)[-2].gigs.get_last()`
- presence nodes don't have to be explicitly created (in sysrepo backend) - this is not the correct behaviour
- investigate  https://github.com/clicon/clixon/blob/master/example/hello/README.md for a CLI instead of prompt-toolkit
- ~~enhance logging if there is no subscriber for a particular YANG module (sysrepo swig bindings are a limiting factor here - if there is a non-zero error code we just get a python runtime error).~~
  - ~~potential to open up sysrepo code to return more discrete error codes (if they aren't already) and then change the SWIG code to provide more descriptive text.~~
- method to persist running into startup configuration.
- ~~`root.simpleleaf<TAB><TAB><TAB>` calls \_\_getattr\_\_ but if there isn't a sensible attr we shouldn't call the data access methods~~
- ~~dir method of a listelement should not expose listkeys - Note: sysrepo stops us changing list keys.~~
- ~~list should implement getitem~~
- ~~iterating around an empty list gives a confusing 'NodeNotAList: The path: /integrationtest:simplelist is not a list'~~
- list should implement a friednly keys() to show the items (assuming this is easy to do against sysrepo)
- If we use netconf + sysrepo we would have to think about how in-progress transactions and sysrepo python bindings would work.
  - Assumption is the callback gives us an iterator of changed XPATHs, if we connect to sysrepo it's independent and will not include those changes.
  - This isn't a deal breaker if the pattern is asynchronous because the callback will just blindly accept syntax valid data and the trigger configuraiton, however if the implementation processes in a synchronous manner then we want to keep the ability to throw a bad error code to reject the overall NETCONF transaction.
 - Optimise Docker image so it doesn't compile the core packages, but instead sucks them in from somewhere else.
- Packaging of the sysrepo into a deb for the minimal image is very naive.
- Implement disconnect() for the data_abstraction_layer.
- Stubdal - should it satisfy default values - it probably can.



# Limitations:

The following list of known limitations are not planned to be handled until there is a strong use case, they are viewd as corner cases at this moment in time.

- Types, binary, bits, identity
  - `Types.py` will require updates, `yangvoodoo/__init__.py` and potentially `VoodooNode/__getattr__` and `VoodooNode/_get_yang_type`
- Union's containing leafref's
  - This will lead to `VoodooNode/_get_yang_type` needing updates to recursively follow unions and leafrefs.