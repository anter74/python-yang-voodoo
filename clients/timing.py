#!/usr/bin/python3
import yangvoodoo
import sys
import time
import yangvoodoo.stubdal

real_total_start = time.time()
start = 0
quiet = True


def timer(todo=''):
    global start
    # print((time.time()-start)*100, 'milliseconds to-do', todo)
    start = time.time()


for c in range(10):
    start = time.time()
    total_start = start

    stub = yangvoodoo.stubdal.StubDataAbstractionLayer()
    stub = None  # Use sysrepo

    session = yangvoodoo.DataAccess(data_abstraction_layer=stub, remote_log=False)
    timer('yangvoodoo-session')
    session.connect('integrationtest')
    timer('yangvoodoo-connect')
    root = session.get_node()

    if stub:
        root.from_template('test/unit/bands.xml')

    try:
        root.web.bands['Idlewild']
    except Exception:
        print("""
    Data is not present in the database.

    Try:
    cd ../init-data
    ./init-xml.sh running

    """)
        sys.exit(1)

    backend = session.session
    timer('yangvoodoo-root')
    yanglist = root.web.bands
    timer('yangvoodoo-getlist')
    a = repr(root.web.bands)
    timer('yangvoodoo-repr(getlist)')

    # This firest list fetch is more expensive than the next two
    # - almost certainly because of the schema lookup (factor of 4!)
    yanglist.get('Idlewild')
    timer('yangvoodoo-getlist.__getitem__[Idlewild]')

    yanglist.get('Band Of Skulls')
    timer('yangvoodoo-getlist.__getitem__[BandOfSk]')

    yanglist.get('Yuck')
    timer('yangvoodoo-getlist.__getitem__[Yuck]')

    # This is much cheaper than the first version of Idlewild and
    # somewhat equivalent to the others
    yanglist.get('Idlewild')
    timer('yangvoodoo-getlist.__getitem__[Idlewild]')

    # This is much cheaper than the first version of Idlewild and
    # somewhat equivalent to the others - sometimes this actually is
    # quicker@!
    root._context.schemacache.empty()
    yanglist.get('Idlewild')
    timer('yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear')

    for x in root.web.bands:
        X = x
    timer('iterate but do nothign around the list')

    li = len(root.web.bands)
    timer('get length of list')

    for c in range(1):
        for x in root.web.bands:
            X = x.name
        if not quiet:
            print('         ', ((time.time()-start)/li), 'per listelement.name for x itmes', li)
        timer('iterate and get values - ')

        for x in root.web.bands:
            X = x.name
        if not quiet:
            print('         ', ((time.time()-start)/li), 'per listelement.name for x itmes', li)
        timer('iterate and get values - same as before')

        for x in root.web.bands:
            X = x.name
            y = len(x.gigs)
        if not quiet:
            print('         ', ((time.time()-start)/li), 'per listelement.name for x itmes', li)
        timer('iterate and get values - ')

        for x in root.web.bands:
            X = x.name
            y = len(x.gigs)

            for g in x.gigs:
                gg = g.venue
                gg = g.location
                gg = g.year
                gg = g.month
                gg = g.day
                li = li + 5
        if not quiet:
            print('         ', ((time.time()-start)/li), 'per listelement.name for x itmes', li)
        timer('iterate and get values - ')

        for x in root.web.bands:
            x.genre = x.name
        session.validate()

    print(time.time()-total_start, " seconds for iteration", c)
x = (time.time()-real_total_start)/10
print(x, " average over 10 iterations (approx 2000 operations)")
y = x/2000
print(y*1000, " ms per operation")
