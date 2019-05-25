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

0.63 seconds  - 67% of sysrepo alone.

The proxy is very quick to flush it's in memory store to avoid complexity.

I.e. `dal.gets(xpath)` can be cached but the answer will be different if we create or delete new list items.

This can likely be improved further by dealing with the cache(stub) individually.


```
1.0587453842163086 milliseconds to-do yangvoodoo-session
1.947188377380371 milliseconds to-do yangvoodoo-connect
6.189131736755371 milliseconds to-do yangvoodoo-root
0.014448165893554688 milliseconds to-do yangvoodoo-getlist
VoodooList{/integrationtest:web/integrationtest:bands}
0.014257431030273438 milliseconds to-do yangvoodoo-repr(getlist)
0.02052783966064453 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.3165245056152344 milliseconds to-do yangvoodoo-getlist.__getitem__[BandOfSk]
0.39060115814208984 milliseconds to-do yangvoodoo-getlist.__getitem__[Yuck]
0.08442401885986328 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild]
0.20182132720947266 milliseconds to-do yangvoodoo-getlist.__getitem__[Idlewild] -after cache clear
0.5065202713012695 milliseconds to-do iterate but do nothign around the list
0.08728504180908203 milliseconds to-do get length of list
Iteration  0
          0.0011208534240722656 per listelement.name for x itmes 225
25.22456645965576 milliseconds to-do iterate and get values -
          1.8137825859917534e-05 per listelement.name for x itmes 225
0.41306018829345703 milliseconds to-do iterate and get values - same as before
          0.0011930592854817708 per listelement.name for x itmes 225
26.84910297393799 milliseconds to-do iterate and get values -
0.6351995468139648 seconds to do everything
```
