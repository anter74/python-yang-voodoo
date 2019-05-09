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


This project builds upon [Sysrepo](http://www.sysrepo.org/) as the datastore which makes use of [Libyang](https://github.com/CESNET/libyang) and will provide a simple interface to fetching/storing data.


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



## Start Docker & Sysrepod


See below for for instructions setting up without docker.

The following (amd64) docker image can be used `docker pull allena29/syrepo:0.7.7`

Note: the docker image also includes Netopeer2 NETCONF server.

```bash
git pull allena29/yangvoodoo:devel
docker run -i  -t allena29/yangvoodoo:devel /bin/bash


# inside docker container
cd /working
git pull
sysrepod -d -l 2
sysrepo-plugind
```

## Install YANG & Initialise startup configuration

```bash
cd /working/yang
./install-yang.sh
cd /working/init-data
./init-xml.sh
```

The `./launch-dbg` script in this repository will build a docker image (*first time will be slower*) mounts the current directory (i.e. this repository) as `/working` and then runs `/working-start-in-docker.sh`. This gives a quick way of getting a fresh docker instace (after the first build - which will terminate at the end). This will launch into an interactive python session (CTRL+D) to exit to bash.

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

Unfortunately setting data requires types, as a convenience the default happens to be a string.

**NOTE:** the commit method from python does not persist running configuration into startup configuration (see - https://github.com/sysrepo/sysrepo/issues/966). It may be we have to sort ourselves out with regards to copying running to startup from time to time.

- SR_UINT32_T 20
- SR_CONTAINER_PRESENCE_T 4
- SR_INT64_T 16
- SR_BITS_T 7
- SR_IDENTITYREF_T 11
- SR_UINT8_T 18
- SR_LEAF_EMPTY_T 5
- SR_DECIMAL64_T 9
- SR_INSTANCEID_T 12
- SR_TREE_ITERATOR_T 1
- SR_CONTAINER_T 3
- SR_UINT64_T 21
- SR_INT32_T 15
- SR_ENUM_T 10
- SR_UNKNOWN_T 0
- SR_STRING_T 17
- SR_ANYXML_T 22
- SR_INT8_T 13
- SR_LIST_T 2
- SR_INT16_T 14
- SR_BOOL_T 8
- SR_ANYDATA_T 23
- SR_UINT16_T 19
- SR_BINARY_T 6


# XPATH based python access

Note: when fetching data we need to provide to provide at least a top-level module prefix, however it is


```python
import yangvoodoo
session = yangvoodoo.DataAccess()
from yangvoodoo import Types as types
session.connect()


session.set("/integrationtest:simpleleaf", "BOO!", types.SR_STRING_T)

value = session.get("/integrationtest:simpleleaf", "BOO!")
print(value)

session.create("/integrationtest:simplelist[simplekey='abc123']")

for item in session.gets("/integrationtest:simplelist"):
  print(item)
  value = session.get(item + "/simplekey")
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



# Debug Logging

**Note: this is quick and dirty and should probably be replaced by syslog**

It's quite distracting to see log messages pop-up when interactively using ipython.

By default logging isn't enabled.


see... LogWrap() and logsink.py


Note: the python bindings to sysrepo don't provide great visibility of errors. It is best to see the logging from sysrepo's perspective if something is unclear. Since the Node-based access is just wrapping around the basic sysrepo python library if there are problems with the node based access ensuring the XPATH and types are consistent with the YANG module.

One example where things are not distinct enough is the following example:

- `root.numberlist.integer.create('2')`  --> **Runtime Error: Invalid Argument**
- `root.numberlist.integer.create(2)`  --> **Runtime Error: Invalid Argument**
- `root.numberlist.integer.create(234234234234)` --> **Runtime Error: Invalid Argument**
- `root.numberlist.integer.create(234234234234)` --> **Runtime Error: Invalid Argument**

In the first two cases the Sysrepo logs show `The node is not enabled in running datastore /integrationtest:numberlist/integrationtest:integer[k='234234234234']` in this case the subscribers were not running. Sysrepo will not accept changes to the datastore without a subscriber active.

In the third case the subscribers were running because it does not match the `uint8` type.

Once the subscriber is active either of the first two cases work- however because the field is a uint8 we should use the second case.


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
echo "3.6.7/envs/yang-voodoo" >.python-version
sed  -e 's/unset/#/' -i.bak swig/CMakeLists.txt
mkdir build
cd build
cmake -DPYTHON_EXECUTABLE=~/.pyenv/versions/yang-voodoo/bin/python3  -DPYTHON_LIBRARY=~/.pyenv/versions/3.6.7/lib/libpython3.6.dylib  -DPYTHON_INCLUDE_DIR=~/.pyenv/versions/3.6.7/include/python3.6m  -DGEN_LUA_BINDINGS=0 -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 ..
make && sudo make install

# Libyang
git clone https://github.com/allena29/libyang-cffi
cd libyang-cffi
git checkout devel-node-constraints
LIBYANG_INSTALL=system python3 setup.py install
```

# Reference:

- [Sysrepo](http://www.sysrepo.org/)
- [Libyang](https://github.com/CESNET/libyang)
- [libyang python bindings](https://github.com/allena29/libyang-cffi)


# Limitations:

The following list of known limitations are not planned to be handled until there is a strong use case, they are viewd as corner cases at this moment in time.

- Types, binary, bits, identity
  - `Types.py` will require updates, `yangvoodoo/__init__.py` and potentially `VoodooNode/__getattr__` and `VoodooNode/_get_yang_type`
- Union's containing leafref's
  - This will lead to `VoodooNode/_get_yang_type` needing updates to recursively follow unions and leafrefs.
