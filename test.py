#!/bin/env python3
import json
import logging

log = logging.getLogger("test")
logging.basicConfig()
log.setLevel(5)


from Expander import SchemaDataExpander

expander = SchemaDataExpander("testforms", log)

data_xml = open("resources/simplelist.xml").read()

schema = expander.process_schema()
print(schema)

combined = expander.process_data(schema, data_xml)
print(json.dumps(combined, indent=4))
