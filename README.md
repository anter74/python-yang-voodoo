# Python access to YANG based Datastore (based on libyang/sysrepo)

The aim of this project is to provide the ability to write python code where there is a strong YANG based data model.
By providing an object based access layer it allows data to be traversed without worrying about lower level details, and
allow a stronger focus on getting the 'value add' correct.

Taking the very basic yang module below, we can imagine how it might look in a few different ways.

```
container bronze {
  container silver {
    container gold {
      container platinum {
        leaf deep {
          type string;
        }
      }
    }
  }
}
```


This project builds upon [Sysrepo](http://www.sysrepo.org/) as the **default** datastore, and [Libyang](https://github.com/CESNET/libyang) to tightly couple the data model to a set of standard yang models.



```python
root.bronze.silver.gold.platinum.deep = 'DOWN'
print(root.bronze.silver.gold.platinum.deep)
```

We can then imagine other ways we might WRITE and READ this data, if this was a database backend like SQL we might access the data as.

```sql
UPDATE bronze_silver_gold_platinum SET deep = 'DOWN';
SELECT deep FROM bronze_silver_gold_platinum;
```

Or perhaps with the sysrepo vanilla python bindings with XPATH.

```python
session.set_item('/module:bronze/silver/gold/platinum/deep', 'DOWN'. sr.SR_STRING_T)

item = session.get_item('/module:bronze/silver/gold/platinum/deep')
print(item.val_to_string)
```

Or Perhaps modelled as xml

```xml
  <bronze>
    <silver>
      <gold>
        <platinum>
          <deep>DOWN</deep>
        </platinum>
      </gold>
    </silver>
  </bronze>
```

 Or json

 ```json
  {
    "bronze" : {
      "silver": {
        "gold": {
          "platinum": {
            "deep": "down"
          }
        }
      }
    }
  }
 ```


# Overall Structure

```
+-------------------------------------------+
|                                           |
|  yangvoodoo                               |
|                                           |
|  (object based access constrained by      |
|   YANG models and mapped to specific      |
|   xpath Key/Value pairs)                  |
+------+----------------------------+-------+
       |                            |
       |                            |
+-----------------------------v---------------+     +------+---------------------------------------------------+
|                                             |     |                                                          |
| libyang (C++ library, with python bindings) |     | data_abstraction_layer  (translation layer)              |
| -  Describes the schema and constraints the |     |  - Primitive operations for setting/getting daata        |
|    basic layout and types of the data.      |     |    based upon XPATH Key/Value Paris.                     |
|                                             |     |  - Primitive transaction operations (validate, commit)   |
+---------------------------------------------+     |  - Enforces schema and data (i.e. when, must, leafrefs)  |
                                                    |    conditions of the YANG modules.                       |
                                                    |  - 2 DAL's are provided (Sysrepo and Stub)               |
                                    +---------------+                                                          |
                                    |               +------+------------------------------+--------------------+
                                    |                              ^
                 +------------------v-----------------+   +--------+--------------------------+
                 |                                    |   |                                   |
                 | sysrepo                            |   | stub                              |
                 |   - open source datastore.         |   |  - dictionary based datastore     |
                 |                                    |   |  for unit tests/prototyping       |
                 +------------------------------------+   +-----------------------------------+

```



## Abstraction of Data Access

This project was written around sysrepo for data storage, however there is no strong dependency on using sysrepo. In order to support unit testing of code there is already an alternative datastore provided as **stubdal** (although that is not production grade).

Implementing a new data_abastraction_layer is as simple as implementing the following methods.

 - **connect()** - connects to the datastore, it is expected that the datastore may provide and track a specific connection providing *transactionality*
 - **validate()** - validate pending changes are valid based on the full data of the entire datastore (VoodooNode is limited to validating the yang schema itself).
 - **refresh()** - refresh the data from the datastore, the datastore may provide us with the data present in the datastore at the time we first connected, or it may refresh in realtime everytime we access a given set of data.
 - **commit()** - commit pending datastore.


 - **get(xpath)** - get specific data by XPATH, this will not apply to non-presence containers or lists
 - **gets_unsorted(xpath, ignore_empty_lists)** - get a list of XPATH's representing the items in the list, it is expected the datastore will maintain the order the user inserts the data and this MUST return the data in that order. If the list is empty this method will normally raise an ListDoesNotContainElement exception.
 - **gets_unsorted(xpath, ignore_empty_lists)** - as gets_unsorted, but the results will be sorted by XPATH.
 - **has_item(xpath)**- returns True if the item has been populated with data.
 - **create(xpath)** - create a list item
 - **create_container(xpath)** - if a container is a presence container explicitly create the container.
 - **set(xpath, value, valuetype)** - sets the value of a specific xpath (supported for yang leaves). The valuetype is an integer (defined in Types.py/DATA_ABSTRACTION_MAPPING) based on the effective type of the yang field (*based on fuzzy matching in the case of unions*).


### SCHEMA vs DATA level constraints

There are some validation and constraints that are schema level, that is they are defined in the yang model and have no dependency on the data in the datastore. Schema based constraints are enforced by libyang without a requirement to run a full datastore (like sysrepo).
Examples of schema based constraints.

 - Creating/accessing nodes that are not part of the YANG model.
 - Setting data that does not match they type (i.e. string, uintX, intX, boolean)


Data level constraints need to be supported by the backend datastore, and this is true of sysrepo.

 - Validating enumerations
 - Validating must and when expressions
 - Validating data matches the path of a leafref.



## Example Docker instance

See below for for instructions setting up without docker.

The following (amd64) docker image can be used `docker pull allena29/yabgvoodoo:devel`

```bash
git pull allena29/yangvoodoo:devel
docker run -i  -t allena29/yangvoodoo:devel /bin/bash

# inside docker container
cd /working
git pull
sysrepod -d -l 2
sysrepo-plugind

## Install YANG & Initialise startup configuration

cd /working/yang
./install-yang.sh
cd /working/init-data
./init-xml.sh
```

The `./launch-dbg` script in this repository will build a docker image (*first time will be slower*) mounts the current directory (i.e. this repository) as `/working` and then runs `/working-start-in-docker.sh`. This gives a quick way of getting a fresh docker instace (after the first build - which will terminate at the end). This will launch into an interactive python session (CTRL+D) to exit to bash.




# Sysrepo Datastore


## Exporting Data

The datastore can be **startup** or **running**, however the running datastore can only be accessed if there is a subscriber to the yang module.

```
sysrepocfg --export --format=xml --datastore=startup integrationtest
<morecomplex xmlns="http://brewerslabng.mellon-collie.net/yang/integrationtest">
 <inner>
   <leaf5>fsf</leaf5>
 </inner>
</morecomplex>

sysrepocfg --export --format=xml --datastore=running integrationtest
Cannot operate on the running datastore for 'integrationtest' as there are no active subscriptions for it.
Canceling the operation.
```

## Subscribers

The providers folder contains basic sysrepo python based subscribers which will be invoked each time data changes. A subscriber will independently provide callbacks for config changes (module_change) and oper-data requests (dp_get_items).

```bash
cd /working/subscribers
./launch-subscribers.sh
```

Each provider is launched in a screen session `screen -list` and `screen -r providerintegrationtest.py` to see the sessions and resume.


## Importing Data

The data can be imported into the running config (with at least on subscriber active) or startup config (without requiring any subscribers). Note: the docker image doesn't have the test yang models or any data in when it launches so the instructions above always init the startup data.

```
sysrepocfg --import=../init-data/integrationtest.xml --format=xml --datastore=running integrationtest
```

**NOTE:** sysrepo does not automatically copying running configuration into startup configuration.


## Getting Data

Sysrepo by default will return `<sysrepo.Val; proxy of <Swig Object of type 'sysrepo::S_Val *' at 0x7fc985bb23f0> >` - however our own `DataAccess` object will convert this to python primitives.

Note: the docker image has `ipython3`

From this point forward change into `cd /working/clients`

```python
import yangvoodoo
session = yangvoodoo.DataAccess()
session.connect()
value = session.get('/integrationtest:simpleleaf')
print(value)
```


## Setting Data

Setting data requires types, as a convenience the default happens to be a string.

**NOTE:** the commit method from python does not persist running configuration into startup configuration (see - https://github.com/sysrepo/sysrepo/issues/966). It may be we have to sort ourselves out with regards to copying running to startup from time to time.

See Types.py for the mapping of values - STRING = 18




# XPATH access (via the Data Abstraction Layer)

The data abstraction layer uses XPATH notation for specifying access, all components of the path should include the yang module.

- `/integrationtest:leafname` - access to a leaf
- `/integrationtest:container/integrationtest:leaf` - access to a leaf in a container
- `/integrationtest:list[integrationtest:key='abc']` - access to a list element where the list has a single key named key
- `/integrationtest:twokeys[integrationtest:key1='abc'][integrationtestkey2:='def']` - access to a list element where list has two keys
- `/integrationtest:list[integrationtest:key='abc']/integrationtest:leafinsidelist` - access to an item in the list
- `/integrationtest:list[integrationtest:key='abc']/integrationtest:secondlist[integrationtest:insidekey='aa']` - access to a list within a list.


```python
import yangvoodoo
session = yangvoodoo.DataAccess()
from yangvoodoo import Types as types
session.connect()


session.set("/integrationtest:simpleleaf", "BOO!", types.SR_STRING_T)

value = session.get("/integrationtest:simpleleaf", "BOO!")
print(value)

exists = session.has_item("/integrationtest:simplelist[integrationtest:simplekey='abc123']")

session.create("/integrationtest:simplelist[integrationtest:simplekey='abc123']")

for item in session.gets_unsorted("/integrationtest:simplelist"):
  print(item)
  value = session.get(item + "/integrationtest:simplekey")
  print(value)

session.delete("/integrationtest:simpleenum")

session.commit()
```


# Object based python access

This is a proof of concept style quality of code at this stage.

- We allow libyang to constrain our schema, however this means some things will be **invalid** but not fail basic schema checks which libyang gives us as part of it's validations.
- Then `session.commit()` which wraps around sysrepo's commit will actually validate things like must, whens and leaf-ref pathss.


When running `get_root(yang_module)` the directory `../yang` will be used to find the respective yang modules. There is a 1:1 mapping between a root object and yang module - this fits with the pattern of sysrepo. An optional argument `yang_location=<>` can be passed to get_root to specify an alternative location.

```python
import yangvoodoo
session = yangvoodoo.DataAccess()
session.connect()
# this will look in ../yang for the yang module integrationtest.yang and associated dependencies.
root = session.get_root('integrationtest')

# Set a value
root.simpleleaf = 'abc'

# Delete of a leaf
root.simpleleaf = None

# Access a leaf inside a container
print(root.morecomplex.leaf3)

# Create (or return) a list element - this list has two boolean keys
listelement = root.twokeylist.create(True, True)
listelement.tertiary = True

# Access data with square brackets (both these two options are equivalent)
listelement = root.twokeylist[True, True]
listelement = root.twokeylist.get(True, True)

# Iterate around a list
for y in root.twokeylist:
    print("Object Representation:", repr(y))
    print("Leaf from listelement:", y.primary)
    print("Children of listelement:", dir(y))

# Delete list times
del root.twokeylist[True, True]

# Multiple levels
root.bronze.silver.gold.platinum.deep = 'abc'

# Accessing parents (this is root.bronze (use with care - it's intended for interactive debug)
root.bronze.silver._parent

# A special method on lists allows us to retrieve items sorted by XPATH
# instead of by the order they were added to the datastore.

for gig in root.web.bands['Yuck'].gigs._xpath_sorted:
   print(gig.year, gig.month, gig.day, gig.venue, gig.location)
   # Results in
   #  2010 10 14 Harley Sheffield
   #  2010 10 27 Lexington Islington
   #  2011 11 24 Electric Ballroom Camden
   #  2011 5 18 Scala Kings Cross

# Validate data with the sysrepo backend datastore.
session.validate()

# Refresh data from the sysrepo backend datastore.
session.refresh()
session.commit()
```



#### Using a stub and writing unit tests

When writing unit tests it is expensive to make use of the real sysrepo backend, this projectThis is a proof of concept style quality of code at this stage. This reduces the dependencies to just libyang library and the forked libyang-cffi bindings.

```python
import unittest
import yangvoodoo
import yangvoodoo.stubdal


class test_node_based_access(unittest.TestCase):

    def setUp(self):
        self.stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
        self.subject = yangvoodoo.DataAccess(data_abstraction_layer=self.stub)
        self.subject.connect()
        self.root = self.subject.get_root('integrationtest')
```




# Development/System version

If the `import yangvoodoo` is carried out in the `clients/` subdirectory the version of the library from the GIT repository will be used. If the import is carried out anywhere else the system version will be used.


# Updating libyang cffi bindings (Robin Jerry's bindings)

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



# Local development environment (without Docker)

## Dependencies

#### Linux

```
see Dockerfile - see below for sysrepo install.
```

#### Mac OSX

Tested with Mojave 10.14.3

```bash
xcode-select --install
brew install cmake        # tested with version 3.14.3
brew install protobuf-c   # tested with version 1.3.1.2
brew install libev        # tested with version 4.24
brew install pcre         # tested with version 8.43
wget http://prdownloads.sourceforge.net/swig/swig-3.0.12.tar.gz
tar xvfz swig-3.0.12.tar.gz
cd swig-3.0.12
./configure
make && sudo make install
cd ../
git clone --branch v1.0-r2  https://github.com/CESNET/libyang.git
cd libyang
mkdir build && cd build
cmake ..
make && sudo make install
cd ../
git clone https://github.com/sysrepo/libredblack.git
cd libredblack
./configure && make && sudo make install
```

## pyenv/virtualenv

The git clone has a `.python-version` file which is only important if pyenv is used for a virtual environment. To create a virtual-env the following will clone and add to a bash shell.

```bash

git clone https://github.com/pyenv/pyenv.git ~/.pyenv
PATH=~/.pyenv/bin:$PATH
  eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
  # For MAC-OSX Mojave
  export PYTHON_CONFIGURE_OPTS="--enable-framework"
  export LDFLAGS="-L/usr/local/opt/zlib/lib -L/usr/local/opt/sqlite3/lib"
  export CPPFLAGS="-I/usr/local/opt/zlib/include -I/usr/local/opt/sqlite3/include"
  export CFLAGS="-I$(xcrun --show-sdk-path)/usr/include"
pyenv install 3.6.7
eval "$(pyenv virtualenv-init -)"
pyenv virtualenv 3.6.7 yang-voodoo
pip install -r requirements.lock

echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >>~/.bashrc
echo 'eval "$(pyenv init -)"' >>~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >>~/.bashrc
echo 'export PS1="{\[\033[36m\]\u@\[\033[36m\]\h} \[\033[33;1m\]\w\[\033[m\] \$ "' >>~/.bashrc
echo 'export PYENV_VIRTUALENV_DISABLE_PROMPT=1' >>~/.bashrc

```

## libyang/sysrepo and python bindings


The following instructions install sysrepo bindings within a pyenv environment. If not using pyenv then follow the simpler steps from the docker file.

```bash
git clone --branch=v0.7.7 https://github.com/sysrepo/sysrepo.git
cd sysrepo
echo "3.6.7/envs/yang-voodoo" >.python-version
sed  -e 's/unset/#/' -i.bak swig/CMakeLists.txt
mkdir build
cd build
cmake -DPYTHON_EXECUTABLE=~/.pyenv/versions/yang-voodoo/bin/python3  -DPYTHON_LIBRARY=~/.pyenv/versions/3.6.7/lib/libpython3.6.dylib  -DPYTHON_INCLUDE_DIR=~/.pyenv/versions/3.6.7/include/python3.6m  -DGEN_LUA_BINDINGS=0 -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 ..
make && sudo make install

# Libyang
cd /tmp
git clone https://github.com/allena29/libyang-cffi
cd libyang-cffi
LIBYANG_INSTALL=system python3 setup.py install
```



# Debug Logging

**Note: this is quick and dirty and should probably be replaced by syslog**

It's quite distracting to see log messages pop-up when interactively using ipython.
By default logging isn't enabled.   see... LogWrap() and logsink.py


Note: launching sysrepod so that it runs with more logging in the foreground can help troubleshoot issues, `sysrepod -d -l 4`. 


# TODO LIST

see [TODO LIST](TODO.md)


# Reference:

- [Sysrepo](http://www.sysrepo.org/)
- [Libyang](https://github.com/CESNET/libyang)
- [libyang python bindings](https://github.com/allena29/libyang-cffi)
