# Disabled

- Caching of schema lookups might be slower - the reason being is libyang-cffi actually caches for us.

- validation of number of keys has dropped
- speculative creating of list keys (proxydal)
- `get_extensions`
- list get\_first get\_last
- help test has been lost somewhere in another branch probably in chocies/cases

- encode xpath predicates won't convert boolean True to XPATH true
# Common/get_schema_for_path

This is definetely not right..

The concept is probably about right, however we need to be much tighter at how get_schema is dones and managed.

It look like even when we access a node directly we call getattr every time.

So it looks like A hybrid of this (where we only care about _ in the last part) and node is right.

Ideally node_schema itself now will be passed around instead of of spath/vpath.


Work out this stuff without updating voodoonode first.

```

    @staticmethod
    def get_schema_of_path(spath, context):
        if spath == "":
            # Root object won't be a valid XPATH
            return context.schema

        if context.schemacache.is_path_cached(spath):
            return context.schemacache.get_item_from_cache(spath)

        if '_' in spath:
            # Utils.underscore_handling(spath, context)
            first_part_of_path = '/'.join(spath.split('/')[0:-1])
            last_part_of_path = spath.split('/')[-1]
            last_node_name = last_part_of_path.split(':')[-1]
            if '_' in last_part_of_path:
                real_path = None
                if first_part_of_path == "":
                    children = context.schemactx.find_path("/" + context.module + ":*")
                else:
                    children = context.schemactx.find_path(first_part_of_path + "/*")
                for child in children:
                    if child.name().replace('-', '_') == last_node_name:
                        real_path = first_part_of_path + "/" + context.module + ":" + child.name()
                    print(real_path)
                    # try:
                    schema_for_path = next(context.schemactx.find_path(real_path))
                    schema_for_path.under_pre_translated_name = child.name()
                    context.schemacache.add_entry(spath, schema_for_path)
                    return schema_for_path
                    # except libyang.util.LibyangError:
                    #     pass

                raise NotImplementedError("Underscore translation for path %s failed (calculated path %s)" % (spath, real_path))


```


- keys that are typedefs - fails (definetely in template ninja but propbably elsewhere)



Readonly dataaccess
