
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
session.connect("integrationtest")


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
