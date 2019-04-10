# Sysrepo - Configuration Store

The following (amd64) docker image can be used `docker pull allena29/syrepo:0.7.7`

This document provides an overview of interacting with sysrepod directly rather than via the Netopeer2 netconf server. This then quickly provided an abstraction layer which allows access via XPATH references (low-level) or a Node-based access (high-level).

Commands in this document should be run from the top-level directory containing the git clone.




## Start Docker & Sysrepod


```bash
git pull allena29/sysrepo
docker run -i  -t allena29/sysrepo:0.7.7-py /bin/bash


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

The `./launch-dbg` script in this repository will build a docker image (*first time will be slower*) mounts the current directory (i.e. this repository) as `/working` and then runs `/working-start-in-docker.sh`. This gives a quick way of getting a fresh docker instace (after the first build - which will terminate at the end).

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

An alternative branch is considering trying to provide a python-object navigation, but at the moment it is required to navigate get xpath nodes explicitly. Sysrepo by default will return `<sysrepo.Val; proxy of <Swig Object of type 'sysrepo::S_Val *' at 0x7fc985bb23f0> >` - however our own `DataAccess` object will convert this to python primitives.

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

Unfortunately setting data requires types, as a covenience the default happens to be a string.

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

# Node based python access

This is a proof of concept style quality of code at this stage.

- We allow libyang to constrain our schema, however this means some things will be **invalid** but not fail basic schema checks.
- Then `session.commit()` which wraps around sysrepo's commit will actually validate things like must, whens and leaf-ref paths.


```python
import yangvoodoo
session = yangvoodoo.DataAccess()
session.connect()
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

# Iterate around a list
for y in root.twokeylist:
    print("Object Representation:", repr(y))
    print("Leaf from listelement:", y.primary)
    print("Children of listelement:", dir(y))


# Multiple levels
root.bronze.silver.gold.platinum.deep = 'abc'

session.commit()
```



# Debug Logging

**Note: this is quick and dirty and should probably be replaced by syslog**

It's quite distracting to see log messages pop-up when interactively using ipython.

see... LogWrap() and logsink.py



# Reference:

- [Sysrepo](http://www.sysrepo.org/)
- [Libyang](https://github.com/CESNET/libyang)
- [libyang python bindings](https://pypi.org/project/libyang/)


# TODO:

- convert 'NODE_TYPE' to '_NODE_TYPE' to hide from ipython
- enumeration test cases
- underscore conversion
- deletes (of non-primitives)
- choices
