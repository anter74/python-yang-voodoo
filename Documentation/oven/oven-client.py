#!/usr/bin/env python3
import sysrepo as sr
conn = sr.Connection("test-client")
session = sr.Session(conn)

# Set item
val = sr.Val(True, sr.SR_BOOL_T)
session.set_item('/oven:oven/turned-on', val)
session.validate()
session.commit()

# Get Items
session.get_items("/oven:oven/*")
for val_num in range(vals.val_cnt()):
    val = vals.val(val_num)
    print(val.xpath())
    print(val.type())
    # to lookup at getting data. frmo val.data()

# This crashes on ARMv7 - it's the oper call.
session.get_items("/oven:*")
