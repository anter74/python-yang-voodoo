# Internal notes about how voodoo node works.

Every node is instantiated with a **context** - (yangctx, log, module name etc), and **node**, (<yangvoodoo.Common.YangNode object at 0x10dfbb1d0>) The YangNode is 98% a wrapper around libyang, however there are two extra attributes.

 - real\_data\_path - the full path to use in a datastore, the yang module name appears only in the first node, and the predicates to specify a particular list element will be included. The node names will not have underscores translated.
 - real\_schema\_path - the full path to use when looking up with libyang, every node is prefixed with the yang module and there will be no predicates specifying a particular list element.

The most important method is `Common.get_schema_and_set_paths()` which takes a node, context, list of keys and list of values.

Values are usually a tuple of (value + the datastore type id).


### Set a value

```python
self.root.simpleleaf = 'sdf'
```

```
__setattr__ simpleleaf
..._get_schema_and_path_of_node   simpleleaf [] []
```

### Set a value deeper down

```python
root.bronze.silver.gold.platinum.deep ='ab'
```

We can see here \__getattr__ is called for every containing node right up until the the final leaf deep when \__setattr__ is called.

```
__getattr__ bronze
..._get_schema_and_path_of_node   bronze [] []
__getattr__ silver /integrationtest:bronze /integrationtest:bronze
..._get_schema_and_path_of_node /integrationtest:bronze /integrationtest:bronze silver [] []
__getattr__ gold /integrationtest:bronze/integrationtest:silver /integrationtest:bronze/silver
..._get_schema_and_path_of_node /integrationtest:bronze/integrationtest:silver /integrationtest:bronze/silver gold [] []
__getattr__ platinum /integrationtest:bronze/integrationtest:silver/integrationtest:gold /integrationtest:bronze/silver/gold
..._get_schema_and_path_of_node /integrationtest:bronze/integrationtest:silver/integrationtest:gold /integrationtest:bronze/silver/gold platinum [] []
__setattr__ deep /integrationtest:bronze/integrationtest:silver/integrationtest:gold/integrationtest:platinum /integrationtest:bronze/silver/gold/platinum
..._get_schema_and_path_of_node /integrationtest:bronze/integrationtest:silver/integrationtest:gold/integrationtest:platinum /integrationtest:bronze/silver/gold/platinum deep [] []
```


### Accessing non-existing nodes

When trying to access a non-existing node which cannot be found in the schema the following exception is raised.


```
NonExistingNode: The path: /integrationtest:sdf does not point of a valid schema node in the yang module
```



### Creating a ListEelement

```python
a=root.simplelist.create('a')
```

We see \__getattr__ called followed by create

```
In [1]: a=root.simplelist.create('a')
__getattr__ simplelist
..._get_schema_and_path_of_node   simplelist [] []
create %s %s /integrationtest:simplelist ('a',) simplelist [simplekey]
..._get_schema_and_path_of_node /integrationtest:simplelist /integrationtest:simplelist  ['simplekey'] [('a', 18)] simplelist [simplekey]
```

We can also see the schema and data paths are different

```
a._node.real_schema_path
'/integrationtest:simplelist'

a._node.real_data_path
"/integrationtest:simplelist[simplekey='a']"
```
