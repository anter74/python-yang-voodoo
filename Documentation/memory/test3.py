import sys

sys.path.append("/home/adam/python-yang-voodoo")
sys.path.append(
    "/home/adam/.pyenv/versions/3.9.5-debug/envs/memory/lib/python3.9/site-packages"
)

import gc
import tracemalloc
import yangvoodoo


def do_snapshot():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    print("[ Top 10 ]")
    for stat in top_stats[:10]:
        print(stat)


def a():
    session = yangvoodoo.DataAccess()
    session.connect("integrationtest")
    session.load("/tmp/a.json", 2)


#    session.disconnect()

tracemalloc.start()
a()


do_snapshot()

obj = gc.collect()
print(f"Collected {obj} objects")
