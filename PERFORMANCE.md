# Summary

- The results below are center towards reading and list iteration, the average speed is from 20,000 operations.
- The results are based on the test secenario in `timing.py`, the benefits from any of the optimisation is only gained if data that has been cached/pre-fetched is actually accessed.

| Speed (ms per operation)     | Scenario                       |
|------------------------------|--------------------------------|
| 1.21                         | sysrepo alone                  |
| 0.66                         | with proxy lazy cache*         |



\* the first version of the proxy cache is lazy, when deleting, adding items to lists parts of the cache are flushed.
\** around 20 us per key to pre-populate.



# Stub within Docker

0.10 seconds

```
0.012111663818359375 milliseconds to-do yangvoodoo-session
2.6476144790649414 milliseconds to-do yangvoodoo-connect
6.150460243225098 milliseconds to-do yangvoodoo-root
0.0080108642578125 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.02727508544921875 milliseconds to-do yangvoodoo-repr(getlist)
0.01895427703857422 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.013089179992675781 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.0055789947509765625 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.011944770812988281 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.009870529174804688 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.07576942443847656 milliseconds to-do iterate but do nothign around the list
0.024819374084472656 milliseconds to-do get length of list
Iteration  0
          1.6938315497504342e-05 per listelement.name for x itmes 225
0.38573741912841797 milliseconds to-do iterate and get values -
          1.526090833875868e-05 per listelement.name for x itmes 225
0.34744739532470703 milliseconds to-do iterate and get values - same as before
          3.338177998860677e-05 per listelement.name for x itmes 225
0.7587909698486328 milliseconds to-do iterate and get values -
0.10596680641174316 seconds to do everything
```


# Sysrepo within Docker

0.93 seconds

```
1.0840177536010742 milliseconds to-do yangvoodoo-session
3.6797046661376953 milliseconds to-do yangvoodoo-connect
5.178046226501465 milliseconds to-do yangvoodoo-root
0.008821487426757812 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.014710426330566406 milliseconds to-do yangvoodoo-repr(getlist)
0.11162757873535156 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.11241436004638672 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.10516643524169922 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.10745525360107422 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.12793540954589844 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.19631385803222656 milliseconds to-do iterate but do nothign around the list
0.16188621520996094 milliseconds to-do get length of list
Iteration  0
          0.0010193549262152777 per listelement.name for x itmes 225
22.940921783447266 milliseconds to-do iterate and get values -
          0.0008535671234130859 per listelement.name for x itmes 225
19.21072006225586 milliseconds to-do iterate and get values - same as before
          0.0017596541510687934 per listelement.name for x itmes 225
39.59774971008301 milliseconds to-do iterate and get values -
0.9276523590087891 seconds to do everything
```


# Sysrepo within Docker and - Proxy

0.53 seconds

The proxy is very quick to flush it's in memory store to avoid complexity.

I.e. `dal.gets(xpath)` can be cached but the answer will be different if we create or delete new list items.

This can likely be improved further by dealing with the cache(stub) individually.


```
0.9865283966064453 milliseconds to-do yangvoodoo-session
2.4792909622192383 milliseconds to-do yangvoodoo-connect
5.3737640380859375 milliseconds to-do yangvoodoo-root
0.012421607971191406 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.012254714965820312 milliseconds to-do yangvoodoo-repr(getlist)
0.010657310485839844 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.16231536865234375 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.20015239715576172 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.008463859558105469 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.0047206878662109375 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.29799938201904297 milliseconds to-do iterate but do nothign around the list
0.02720355987548828 milliseconds to-do get length of list
Iteration  0
          0.0009769598642985027 per listelement.name for x itmes 225
21.98817729949951 milliseconds to-do iterate and get values -
          1.5842649671766493e-05 per listelement.name for x itmes 225
0.3663778305053711 milliseconds to-do iterate and get values - same as before
          0.0009229331546359592 per listelement.name for x itmes 225
20.771431922912598 milliseconds to-do iterate and get values -
0.5278565883636475 seconds to do everything
```


# With an extra loop for gigs


1.5 second for sysrepo without proxy object

```
1.0092496871948242 milliseconds to-do yangvoodoo-session
2.091336250305176 milliseconds to-do yangvoodoo-connect
6.1997175216674805 milliseconds to-do yangvoodoo-root
0.009489059448242188 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.008440017700195312 milliseconds to-do yangvoodoo-repr(getlist)
0.23910999298095703 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.3141641616821289 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.4052877426147461 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.2151012420654297 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.3176689147949219 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.3144502639770508 milliseconds to-do iterate but do nothign around the list
0.3578662872314453 milliseconds to-do get length of list
Iteration  0
          0.0008148172166612414 per listelement.name for x itmes 225
18.354225158691406 milliseconds to-do iterate and get values -
          0.0008433066474066841 per listelement.name for x itmes 225
18.980979919433594 milliseconds to-do iterate and get values - same as before
          0.0015187793307834202 per listelement.name for x itmes 225
34.178900718688965 milliseconds to-do iterate and get values -
          0.0018125481209166404 per listelement.name for x itmes 397
71.96481227874756 milliseconds to-do iterate and get values -
1.5511574745178223 seconds to do everything
```

0.63 seconds for sysrepo  and proxy

```
0.937199592590332 milliseconds to-do yangvoodoo-session
2.218341827392578 milliseconds to-do yangvoodoo-connect
6.317710876464844 milliseconds to-do yangvoodoo-root
0.008153915405273438 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.007176399230957031 milliseconds to-do yangvoodoo-repr(getlist)
0.0055789947509765625 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.09202957153320312 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.07865428924560547 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.004220008850097656 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.00438690185546875 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.18050670623779297 milliseconds to-do iterate but do nothign around the list
0.0064373016357421875 milliseconds to-do get length of list
Iteration  0
          0.0007172150082058377 per listelement.name for x itmes 225
16.142630577087402 milliseconds to-do iterate and get values -
          2.2507773505316842e-05 per listelement.name for x itmes 225
0.5127906799316406 milliseconds to-do iterate and get values - same as before
          0.0008136876424153646 per listelement.name for x itmes 225
18.31340789794922 milliseconds to-do iterate and get values -
          0.00044043538552387534 per listelement.name for x itmes 397
17.490625381469727 milliseconds to-do iterate and get values -
0.6238057613372803 seconds to do everything
```


# Interesting use case.

If we consider a 5 key list.

If we want to access all the elements of the list it would be better to break-apart the XPATH
with regular expressions and pre-cache the data.

However, if we do not want to access the data that is wasted effort.

### without pre-caching of list keys

```
0.9662151336669922 milliseconds to-do yangvoodoo-session
2.2542953491210938 milliseconds to-do yangvoodoo-connect
5.67164421081543 milliseconds to-do yangvoodoo-root
0.01862049102783203 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.023984909057617188 milliseconds to-do yangvoodoo-repr(getlist)
0.029802322387695312 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.1196146011352539 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.1102447509765625 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.022673606872558594 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.008463859558105469 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
27.17299461364746 milliseconds to-do iterate but do nothign around the list
0.011944770812988281 milliseconds to-do get length of list
Iteration  0
          0.0008992216322157118 per listelement.name for x itmes 225
20.23775577545166 milliseconds to-do iterate and get values -
          3.3084021674262154e-05 per listelement.name for x itmes 225
0.7503509521484375 milliseconds to-do iterate and get values - same as before
          0.0009609116448296441 per listelement.name for x itmes 225
21.625804901123047 milliseconds to-do iterate and get values -
          0.0006917599708803239 per listelement.name for x itmes 1085
75.06134510040283 milliseconds to-do iterate and get values -
1.5414268970489502 seconds to do everything
```

### with pre-caching of list keys

```
0.9741306304931641 milliseconds to-do yangvoodoo-session
2.4421215057373047 milliseconds to-do yangvoodoo-connect
5.671072006225586 milliseconds to-do yangvoodoo-root
0.008273124694824219 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.029540061950683594 milliseconds to-do yangvoodoo-repr(getlist)
0.012254714965820312 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.115966796875 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.10993480682373047 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.00438690185546875 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.004291534423828125 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.4208803176879883 milliseconds to-do iterate but do nothign around the list
0.16672611236572266 milliseconds to-do get length of list
Iteration  0
          0.0009453095330132378 per listelement.name for x itmes 225
21.274542808532715 milliseconds to-do iterate and get values -
          2.586470709906684e-05 per listelement.name for x itmes 225
0.586390495300293 milliseconds to-do iterate and get values - same as before
          0.0008620760175916883 per listelement.name for x itmes 225
19.402432441711426 milliseconds to-do iterate and get values -
          0.0007454852354691325 per listelement.name for x itmes 1085
80.8906078338623 milliseconds to-do iterate and get values -
1.321990728378296 seconds to do everything
```


# Not actually convinced the pre-caching is workings - need to profile the regex overhead vs sysrepo call.
