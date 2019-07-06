

# Development/System version


# Updating libyang cffi bindings (Robin Jarry's bindings)

- Important reference - libyang class definitions. [https://netopeer.liberouter.org/doc/libyang/master/group__schematree.html#structlys__type__info__str](https://netopeer.liberouter.org/doc/libyang/master/group__schematree.html#structlys__type__info__str) - forked into https://github.com/allena29/libyang-cffi

First use case missing constraints for leaves in a yang mode.

### cffi/cdefs.h


```c++
// added this based on the documentation in the class reference (it has to line up)
struct lys_restr {
	const char* expr;
	const char* dsc;
	const char* ref;
	const char* eapptag;
	const char* emsg;
	...;
};

// added this based on the documentation in the class reference (it has to line up)
struct lys_type_info_str {  
	struct lys_restr* length;
	struct lys_restr* patterns;
	int pat_count;
	...;
};

// added a type_info_str.
union lys_type_info {
	struct lys_type_info_bits bits;
	struct lys_type_info_enums enums;
	struct lys_type_info_lref lref;
	struct lys_type_info_union uni;
	struct lys_type_info_str str;  
	...;
};

```

### class Leaf: in libyang/schema.py

```python
def constraints(self):
    return self.type().leaf_constraints()
```

### class Leaf: in libyang/schema.py
```python
def leaf_constraints(self):
    t = self._type
    yield c2str(t.info.str.length.emsg)
    # return t.info.str.length
```


Quick and ditry results from this are consistent without yang model.

```python
next(next(yangctx.find_path('/integrationtest:validator/integrationtest:strings/integrationtest:sillylen')).constraints())
'BOO!'
```



# Debug Logging

**Note: this is quick and dirty and should probably be replaced by syslog**

It's quite distracting to see log messages pop-up when interactively using ipython.
By default logging isn't enabled.   see... LogWrap() and logsink.py


Note: launching sysrepod so that it runs with more logging in the foreground can help troubleshoot issues, `sysrepod -d -l 4`.
