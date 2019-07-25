# YANG Structure for testing.

```
module: integrationtest
  +--rw underscore_and-hyphen?                empty
  +--rw diff
  |  +--rw deletes
  |  |  +--rw a-leaf?               string
  |  |  +--rw a-2nd-leaf?           string
  |  |  +--rw a-list* [listkey]
  |  |  |  +--rw listkey       string
  |  |  |  +--rw listnonkey?   string
  |  |  +--rw a-leaf-list*          string
  |  |  +--rw presence-container!
  |  +--rw adds
  |  |  +--rw a-leaf?               string
  |  |  +--rw a-2nd-leaf?           string
  |  |  +--rw a-list* [listkey]
  |  |  |  +--rw listkey       string
  |  |  |  +--rw listnonkey?   string
  |  |  +--rw a-leaf-list*          string
  |  |  +--rw presence-container!
  |  +--rw modifies
  |     +--rw a-leaf?               string
  |     +--rw a-2nd-leaf?           string
  |     +--rw a-list* [listkey]
  |     |  +--rw listkey       string
  |     |  +--rw listnonkey?   string
  |     +--rw a-leaf-list*          string
  |     +--rw presence-container!
  +--rw validator
  |  +--rw strings
  |  |  +--rw nolen?                   string
  |  |  +--rw non-quatre?              length-must-not-be-4-long
  |  |  +--rw minlen?                  string
  |  |  +--rw maxlen?                  string
  |  |  +--rw minmaxlen?               string
  |  |  +--rw sillylen?                string
  |  |  +--rw pattern?                 string
  |  |  +--rw patternerror?            string
  |  |  +--rw patternandlengtherror?   string
  |  +--rw types
  |     +--rw str?                string
  |     +--rw enumeratio?         enumeration
  |     +--rw void?               empty
  |     +--rw bool?               boolean
  |     +--rw dec_64?             decimal64
  |     +--rw int_8?              int8
  |     +--rw int_16?             int16
  |     +--rw int_32?             int32
  |     +--rw int_64?             int64
  |     +--rw u_int_8?            uint8
  |     +--rw u_int_16?           uint16
  |     +--rw u_int_32?           uint32
  |     +--rw u_int_64?           uint64
  |     +--rw present!
  |     +--rw collection* [x]
  |     |  +--rw x    string
  |     +--rw simplecollection*   string
  +--rw imports-in-here
  |  +--rw name?   string
  +--rw web
  |  +--rw venues* [name location]
  |  |  +--rw name           string
  |  |  +--rw location       locations
  |  |  +--rw country?       countries
  |  |  +--rw beers* [name]
  |  |  |  +--rw name    string
  |  |  +--rw information
  |  |     +--rw profiles* [profile]
  |  |        +--rw profile       string
  |  |        +--rw doors-open?   string
  |  |        +--rw curfew?       string
  |  +--rw promoters* [name]
  |  |  +--rw name    string
  |  +--rw bands* [name]
  |  |  +--rw name     string
  |  |  +--rw genre?   string
  |  |  +--rw gigs* [year month day venue location]
  |  |     +--rw year        uint16
  |  |     +--rw month       uint8
  |  |     +--rw day         uint8
  |  |     +--rw venue       -> /web/venues/name
  |  |     +--rw location    -> /web/venues[integrationtest:name=current()/../venue]/location
  |  |     +--rw festival?   string
  |  |     +--rw missed!
  |  |     |  +--rw reason?   string
  |  |     +--rw comments?   string
  |  |     +--rw rating?     uint8
  |  |     +--rw support* [name]
  |  |        +--rw name     -> /web/bands/name
  |  |        +--rw order?   enumeration
  |  +--rw favourite?   -> ../bands/name
  +--rw underscoretests
  |  +--rw underscore_only?         string
  |  +--rw hyphen-only?             string
  |  +--rw underscore_and-hyphen?   string
  |  +--rw deeper_down-here
  |     +--rw simple?   string
  +--rw empty?                                empty
  +--rw simpleleaf?                           string
  +--rw dirty-secret?                         string
  +--rw default?                              string
  +--rw whencontainer
  |  +--rw then?   string
  +--rw thing-that-is-lit-up-for-C?           string
  +--rw thing-that-is-lit-up-for-B?           string
  +--rw thing-that-is-lit-up-for-A?           string
  +--rw thing-that-is-used-for-when?          enumeration
  +--rw thing-to-leafref-against?             string
  +--rw list-to-leafref-against* [idle]
  |  +--rw idle    string
  |  +--rw wild?   string
  +--rw thing-that-is-a-list-based-leafref?   -> ../list-to-leafref-against/wild
  +--rw thing-that-is-leafref?                -> ../thing-to-leafref-against
  +--rw quad
  |  +--rw leafinquad!
  +--rw quarter
  |  +--rw leafinquarter!
  +--rw container1!
  |  +--rw leaf1?        string
  |  +--rw container2!
  |     +--rw leaf2a?       string
  |     +--rw leaf2b?       string
  |     +--rw container3!
  |        +--rw leaf3?   string
  +--rw bronze
  |  +--rw A?        string
  |  +--rw B?        string
  |  +--rw C?        string
  |  +--rw D?        string
  |  +--rw E?        string
  |  +--rw F?        string
  |  +--rw G?        string
  |  +--rw H?        string
  |  +--rw I?        string
  |  +--rw J?        string
  |  +--rw K?        string
  |  +--rw L?        string
  |  +--rw M?        string
  |  +--rw N?        string
  |  +--rw O?        string
  |  +--rw P?        string
  |  +--rw Q?        string
  |  +--rw R?        string
  |  +--rw S?        string
  |  +--rw T?        string
  |  +--rw U?        string
  |  +--rw V?        string
  |  +--rw W?        string
  |  +--rw X?        string
  |  +--rw Y?        string
  |  +--rw Z?        string
  |  +--rw silver
  |     +--rw A?      string
  |     +--rw B?      string
  |     +--rw C?      string
  |     +--rw D?      string
  |     +--rw E?      string
  |     +--rw F?      string
  |     +--rw G?      string
  |     +--rw H?      string
  |     +--rw I?      string
  |     +--rw J?      string
  |     +--rw K?      string
  |     +--rw L?      string
  |     +--rw M?      string
  |     +--rw N?      string
  |     +--rw O?      string
  |     +--rw P?      string
  |     +--rw Q?      string
  |     +--rw R?      string
  |     +--rw S?      string
  |     +--rw T?      string
  |     +--rw U?      string
  |     +--rw V?      string
  |     +--rw W?      string
  |     +--rw X?      string
  |     +--rw Y?      string
  |     +--rw Z?      string
  |     +--rw gold
  |        +--rw A?          string
  |        +--rw B?          string
  |        +--rw C?          string
  |        +--rw D?          string
  |        +--rw E?          string
  |        +--rw F?          string
  |        +--rw G?          string
  |        +--rw H?          string
  |        +--rw I?          string
  |        +--rw J?          string
  |        +--rw K?          string
  |        +--rw L?          string
  |        +--rw M?          string
  |        +--rw N?          string
  |        +--rw O?          string
  |        +--rw P?          string
  |        +--rw Q?          string
  |        +--rw R?          string
  |        +--rw S?          string
  |        +--rw T?          string
  |        +--rw U?          string
  |        +--rw V?          string
  |        +--rw W?          string
  |        +--rw X?          string
  |        +--rw Y?          string
  |        +--rw Z?          string
  |        +--rw platinum
  |           +--rw A?        string
  |           +--rw B?        string
  |           +--rw C?        string
  |           +--rw D?        string
  |           +--rw E?        string
  |           +--rw F?        string
  |           +--rw G?        string
  |           +--rw H?        string
  |           +--rw I?        string
  |           +--rw J?        string
  |           +--rw K?        string
  |           +--rw L?        string
  |           +--rw M?        string
  |           +--rw N?        string
  |           +--rw O?        string
  |           +--rw P?        string
  |           +--rw Q?        string
  |           +--rw R?        string
  |           +--rw S?        string
  |           +--rw T?        string
  |           +--rw U?        string
  |           +--rw V?        string
  |           +--rw W?        string
  |           +--rw X?        string
  |           +--rw Y?        string
  |           +--rw Z?        string
  |           +--rw deep?     string
  |           +--rw deeper!
  |              +--rw A?   string
  |              +--rw B?   string
  |              +--rw C?   string
  |              +--rw D?   string
  |              +--rw E?   string
  |              +--rw F?   string
  |              +--rw G?   string
  |              +--rw H?   string
  |              +--rw I?   string
  |              +--rw J?   string
  |              +--rw K?   string
  |              +--rw L?   string
  |              +--rw M?   string
  |              +--rw N?   string
  |              +--rw O?   string
  |              +--rw P?   string
  |              +--rw Q?   string
  |              +--rw R?   string
  |              +--rw S?   string
  |              +--rw T?   string
  |              +--rw U?   string
  |              +--rw V?   string
  |              +--rw W?   string
  |              +--rw X?   string
  |              +--rw Y?   string
  |              +--rw Z?   string
  +--rw psychedelia
  |  +--rw bands* [band]
  |  |  +--rw band         string
  |  |  +--rw favourite?   boolean
  |  +--rw psychedelic-rock
  |     +--rw bands* [band]
  |     |  +--rw band         string
  |     |  +--rw favourite?   boolean
  |     +--rw stoner-rock
  |     |  +--rw bands* [band]
  |     |     +--rw band         string
  |     |     +--rw favourite?   boolean
  |     |     +--rw albums* [album]
  |     |        +--rw album    string
  |     +--rw noise-pop
  |        +--rw bands* [band]
  |        |  +--rw band         string
  |        |  +--rw favourite?   boolean
  |        +--rw dream-pop
  |        |  +--rw bands* [band]
  |        |     +--rw band         string
  |        |     +--rw favourite?   boolean
  |        +--rw shoe-gaze
  |           +--rw bands* [band]
  |              +--rw band         string
  |              +--rw favourite?   boolean
  +--rw twokeylist* [primary secondary]
  |  +--rw primary      boolean
  |  +--rw secondary    boolean
  |  +--rw tertiary?    boolean
  +--rw simplecontainer!
  +--rw simpleenum?                           enumeration
  +--rw patternstr?                           string
  +--rw hyphen-leaf?                          string
  +--rw outsidelist* [leafo]
  |  +--rw leafo              string
  |  +--rw insidelist* [leafi]
  |  |  +--rw leafi    string
  |  +--rw otherinsidelist* [otherlist1 otherlist2 otherlist3]
  |  |  +--rw otherlist1    string
  |  |  +--rw otherlist2    string
  |  |  +--rw otherlist3    string
  |  |  +--rw otherlist4?   string
  |  |  +--rw otherlist5?   string
  |  |  +--rw language?     enumeration
  |  +--rw other?             string
  +--rw numberlist
  |  +--rw integer* [k]
  |  |  +--rw k    uint8
  |  +--rw fraction* [k]
  |  |  +--rw k    testchild:temperature
  |  +--rw percentage* [k]
  |     +--rw k    testchild:percent-dot1
  +--rw container-and-lists
  |  +--rw just-a-key?       string
  |  +--rw lots-of-keys* [A Z Y X B C]
  |  |  +--rw C    string
  |  |  +--rw B    string
  |  |  +--rw X    string
  |  |  +--rw A    string
  |  |  +--rw Z    string
  |  |  +--rw Y    string
  |  +--rw multi-key-list* [A B]
  |  |  +--rw A             string
  |  |  +--rw B             string
  |  |  +--rw inner
  |  |  |  +--rw C?            string
  |  |  |  +--rw level3list* [level3key]
  |  |  |     +--rw level3key        string
  |  |  |     +--rw level3-nonkey?   string
  |  |  +--rw level2list* [level2key]
  |  |     +--rw level2key    string
  |  +--rw numberkey-list* [numberkey]
  |     +--rw numberkey      uint8
  |     +--rw description?   string
  +--rw lista* [firstkey]
  |  +--rw firstkey    string
  |  +--rw listb* [secondkey thirdkey]
  |     +--rw secondkey             string
  |     +--rw thirdkey              string
  |     +--rw nonkey?               string
  |     +--rw (MAKEYOURMINDUP)?
  |     |  +--:(OPTION1)
  |     |  |  +--rw FIRSTOPTION?    string
  |     |  +--:(OPTION2)
  |     |     +--rw SECONDOPTION?   string
  |     +--rw things
  |     |  +--rw thing?      string
  |     |  +--rw musthave    string
  |     +--rw nothings
  +--rw simplelist* [simplekey]
  |  +--rw simplekey     string
  |  +--rw nonleafkey?   uint32
  +--rw resolver
  |  +--rw a?        string
  |  +--rw leaf-a?   type-a
  +--rw morecomplex
  |  +--rw leaflists
  |  |  +--rw simple*       string
  |  |  +--rw viatypedef*   type3
  |  +--rw superstar?       percentile95th
  |  +--rw percentage?      decimal64
  |  +--ro nonconfig?       string
  |  +--rw extraboolean?    boolean
  |  +--rw extraboolean2?   boolean
  |  +--rw extraboolean3?   boolean
  |  +--rw leaf2?           boolean
  |  +--rw leaf3?           type2
  |  +--rw leaf4?           type4
  |  +--rw inner!
  |     +--rw siblings
  |     |  +--rw a?   string
  |     |  +--rw b?   string
  |     |  +--rw c?   string
  |     |  +--rw d?   string
  |     |  +--rw e?   string
  |     |  +--rw f?   string
  |     |  +--rw g?   string
  |     |  +--rw h?   string
  |     |  +--rw i?   string
  |     |  +--rw j?   string
  |     +--rw brewdog-beer?                numstr
  |     +--rw beer-styles* [beer-style]
  |     |  +--rw beer-style          enumeration
  |     |  +--rw (beer-choice)?
  |     |     +--:(new-england-case)
  |     |        +--rw hazy-style
  |     |           +--rw beer-chosen?   string
  |     |           +--rw rating?        uint8
  |     |           +--rw size?          enumeration
  |     +--rw classifier-example
  |     |  +--rw rules* [id]
  |     |     +--rw id          uint8
  |     |     +--rw protocol?   enumeration
  |     |     +--rw ports
  |     |        +--rw source
  |     |           +--rw port-type?    enumeration
  |     |           +--rw port?         uint8
  |     |           +--rw start-port?   uint8
  |     |           +--rw end-port?     uint8
  |     +--rw brewdog-beers* [beer]
  |     |  +--rw beer    numstr
  |     +--rw (beer-type)?
  |     |  +--:(macro)
  |     |  |  +--rw fosters?               string
  |     |  +--:(craft)
  |     |  |  +--rw brewdog?               string
  |     |  +--:(ale)
  |     |     +--rw adnams?                string
  |     +--rw list-that-will-stay-empty* [akey]
  |     |  +--rw akey    string
  |     +--rw leaf5                        string
  |     +--rw leaf6?                       string
  |     +--rw leaf7?                       string
  |     +--rw leaf8?                       type8
  |     +--rw leaf666?                     type6
  |     +--rw leaf777?                     -> ../leaf7
  |     +--rw leaf888?                     type8
  |     +--rw leaf-union-of-union?         union
  |     +--rw leaf888-withoutenum?         type8-noenum
  |     +--rw leaf8888?                    -> ../leaf666
  |     +--rw leaf999?                     -> ../../leaf2
  |     +--rw leaf000?                     sillytypedef
  |     +--rw leaf111?                     union
  |     +--rw leaf112?                     union
  |     +--rw leaf113?                     union
  |     +--rw ietf-inet-types
  |        +--rw ip
  |           +--rw address?   inet:ip-address
  +--rw scaling
     +--rw scale0* [key0-a]
        +--rw key0-a      string
        +--rw non-key0?   string
        +--rw scale1* [key1-a]
           +--rw key1-a      string
           +--rw non-key1?   string
           +--rw scale2* [key2-a key2-b]
              +--rw key2-a      string
              +--rw key2-b      string
              +--rw non-key2?   string
              +--rw scale3* [key3-a]
                 +--rw key3-a      string
                 +--rw non-key3?   string
                 +--rw alpha0
                 |  +--rw A?   string
                 |  +--rw B?   string
                 |  +--rw C?   string
                 |  +--rw D?   string
                 |  +--rw E?   string
                 |  +--rw F?   string
                 |  +--rw G?   string
                 |  +--rw H?   string
                 |  +--rw I?   string
                 |  +--rw J?   string
                 |  +--rw K?   string
                 |  +--rw L?   string
                 |  +--rw M?   string
                 |  +--rw N?   string
                 |  +--rw O?   string
                 |  +--rw P?   string
                 |  +--rw Q?   string
                 |  +--rw R?   string
                 |  +--rw S?   string
                 |  +--rw T?   string
                 |  +--rw U?   string
                 |  +--rw V?   string
                 |  +--rw W?   string
                 |  +--rw X?   string
                 |  +--rw Y?   string
                 |  +--rw Z?   string
                 +--rw alpha1
                 |  +--rw A?   string
                 |  +--rw B?   string
                 |  +--rw C?   string
                 |  +--rw D?   string
                 |  +--rw E?   string
                 |  +--rw F?   string
                 |  +--rw G?   string
                 |  +--rw H?   string
                 |  +--rw I?   string
                 |  +--rw J?   string
                 |  +--rw K?   string
                 |  +--rw L?   string
                 |  +--rw M?   string
                 |  +--rw N?   string
                 |  +--rw O?   string
                 |  +--rw P?   string
                 |  +--rw Q?   string
                 |  +--rw R?   string
                 |  +--rw S?   string
                 |  +--rw T?   string
                 |  +--rw U?   string
                 |  +--rw V?   string
                 |  +--rw W?   string
                 |  +--rw X?   string
                 |  +--rw Y?   string
                 |  +--rw Z?   string
                 +--rw scale4* [key4-a]
                    +--rw key4-a      string
                    +--rw non-key4?   string
                    +--rw scale5* [key5-a]
                       +--rw key5-a      string
                       +--rw non-key5?   string
                       +--rw scale6* [key6-a]
                          +--rw key6-a      string
                          +--rw non-key6?   string
                          +--rw scale7* [key7-a]
                             +--rw key7-a      string
                             +--rw non-key7?   string
                             +--rw scale8* [key8-a]
                                +--rw key8-a      string
                                +--rw non-key8?   string
                                +--rw scale9* [key9-a]
                                   +--rw key9-a      string
                                   +--rw non-key9?   string
                                   +--rw scale10* [key10-a]
                                      +--rw key10-a      string
                                      +--rw non-key10?   string
                                      +--rw scale11* [key11-a]
                                         +--rw key11-a      string
                                         +--rw non-key11?   string
                                         +--rw scale12* [key12-a]
                                            +--rw key12-a      string
                                            +--rw non-key12?   string
                                            +--rw scale13* [key13-a]
                                               +--rw key13-a      string
                                               +--rw non-key13?   string
                                               +--rw scale14* [key14-a]
                                                  +--rw key14-a      string
                                                  +--rw non-key14?   string
                                                  +--rw scale15* [key15-a]
                                                     +--rw key15-a      string
                                                     +--rw non-key15?   string
                                                     +--rw scale16* [key16-a]
                                                        +--rw key16-a      string
                                                        +--rw non-key16?   string
                                                        +--rw scale17* [key17-a]
                                                           +--rw key17-a      string
                                                           +--rw non-key17?   string
                                                           +--rw scale18* [key18-a]
                                                              +--rw key18-a      string
                                                              +--rw non-key18?   string
                                                              +--rw scale19* [key19-a]
                                                                 +--rw key19-a      string
                                                                 +--rw non-key19?   string
                                                                 +--rw scale20* [key20-a]
                                                                    +--rw key20-a      string
                                                                    +--rw non-key20?   string
                                                                    +--rw scale21* [key21-a]
                                                                       +--rw key21-a      string
                                                                       +--rw non-key21?   string
                                                                       +--rw scale22* [key22-a]
                                                                          +--rw key22-a      string
                                                                          +--rw non-key22?   string
                                                                          +--rw scale23* [key23-a]
                                                                             +--rw key23-a      string
                                                                             +--rw non-key23?   string
                                                                             +--rw scale24* [key24-a]
                                                                                +--rw key24-a      string
                                                                                +--rw non-key24?   string
                                                                                +--rw scale25* [key25-a]
                                                                                   +--rw key25-a      string
                                                                                   +--rw non-key25?   string
                                                                                   +--rw scale26* [key26-a]
                                                                                      +--rw key26-a      string
                                                                                      +--rw non-key26?   string
                                                                                      +--rw scale27* [key27-a]
                                                                                         +--rw key27-a      string
                                                                                         +--rw non-key27?   string
                                                                                         +--rw scale28* [key28-a]
                                                                                            +--rw key28-a      string
                                                                                            +--rw non-key28?   string
                                                                                            +--rw scale29* [key29-a]
                                                                                               +--rw key29-a      string
                                                                                               +--rw non-key29?   string
                                                                                               +--rw alpha0
                                                                                               |  +--rw A?   string
                                                                                               |  +--rw B?   string
                                                                                               |  +--rw C?   string
                                                                                               |  +--rw D?   string
                                                                                               |  +--rw E?   string
                                                                                               |  +--rw F?   string
                                                                                               |  +--rw G?   string
                                                                                               |  +--rw H?   string
                                                                                               |  +--rw I?   string
                                                                                               |  +--rw J?   string
                                                                                               |  +--rw K?   string
                                                                                               |  +--rw L?   string
                                                                                               |  +--rw M?   string
                                                                                               |  +--rw N?   string
                                                                                               |  +--rw O?   string
                                                                                               |  +--rw P?   string
                                                                                               |  +--rw Q?   string
                                                                                               |  +--rw R?   string
                                                                                               |  +--rw S?   string
                                                                                               |  +--rw T?   string
                                                                                               |  +--rw U?   string
                                                                                               |  +--rw V?   string
                                                                                               |  +--rw W?   string
                                                                                               |  +--rw X?   string
                                                                                               |  +--rw Y?   string
                                                                                               |  +--rw Z?   string
                                                                                               +--rw alpha1
                                                                                               |  +--rw A?   string
                                                                                               |  +--rw B?   string
                                                                                               |  +--rw C?   string
                                                                                               |  +--rw D?   string
                                                                                               |  +--rw E?   string
                                                                                               |  +--rw F?   string
                                                                                               |  +--rw G?   string
                                                                                               |  +--rw H?   string
                                                                                               |  +--rw I?   string
                                                                                               |  +--rw J?   string
                                                                                               |  +--rw K?   string
                                                                                               |  +--rw L?   string
                                                                                               |  +--rw M?   string
                                                                                               |  +--rw N?   string
                                                                                               |  +--rw O?   string
                                                                                               |  +--rw P?   string
                                                                                               |  +--rw Q?   string
                                                                                               |  +--rw R?   string
                                                                                               |  +--rw S?   string
                                                                                               |  +--rw T?   string
                                                                                               |  +--rw U?   string
                                                                                               |  +--rw V?   string
                                                                                               |  +--rw W?   string
                                                                                               |  +--rw X?   string
                                                                                               |  +--rw Y?   string
                                                                                               |  +--rw Z?   string
                                                                                               +--rw alpha2
                                                                                               |  +--rw A?   string
                                                                                               |  +--rw B?   string
                                                                                               |  +--rw C?   string
                                                                                               |  +--rw D?   string
                                                                                               |  +--rw E?   string
                                                                                               |  +--rw F?   string
                                                                                               |  +--rw G?   string
                                                                                               |  +--rw H?   string
                                                                                               |  +--rw I?   string
                                                                                               |  +--rw J?   string
                                                                                               |  +--rw K?   string
                                                                                               |  +--rw L?   string
                                                                                               |  +--rw M?   string
                                                                                               |  +--rw N?   string
                                                                                               |  +--rw O?   string
                                                                                               |  +--rw P?   string
                                                                                               |  +--rw Q?   string
                                                                                               |  +--rw R?   string
                                                                                               |  +--rw S?   string
                                                                                               |  +--rw T?   string
                                                                                               |  +--rw U?   string
                                                                                               |  +--rw V?   string
                                                                                               |  +--rw W?   string
                                                                                               |  +--rw X?   string
                                                                                               |  +--rw Y?   string
                                                                                               |  +--rw Z?   string
                                                                                               +--rw alpha3
                                                                                               |  +--rw A?   string
                                                                                               |  +--rw B?   string
                                                                                               |  +--rw C?   string
                                                                                               |  +--rw D?   string
                                                                                               |  +--rw E?   string
                                                                                               |  +--rw F?   string
                                                                                               |  +--rw G?   string
                                                                                               |  +--rw H?   string
                                                                                               |  +--rw I?   string
                                                                                               |  +--rw J?   string
                                                                                               |  +--rw K?   string
                                                                                               |  +--rw L?   string
                                                                                               |  +--rw M?   string
                                                                                               |  +--rw N?   string
                                                                                               |  +--rw O?   string
                                                                                               |  +--rw P?   string
                                                                                               |  +--rw Q?   string
                                                                                               |  +--rw R?   string
                                                                                               |  +--rw S?   string
                                                                                               |  +--rw T?   string
                                                                                               |  +--rw U?   string
                                                                                               |  +--rw V?   string
                                                                                               |  +--rw W?   string
                                                                                               |  +--rw X?   string
                                                                                               |  +--rw Y?   string
                                                                                               |  +--rw Z?   string
                                                                                               +--rw alpha4
                                                                                                  +--rw A?   string
                                                                                                  +--rw B?   string
                                                                                                  +--rw C?   string
                                                                                                  +--rw D?   string
                                                                                                  +--rw E?   string
                                                                                                  +--rw F?   string
                                                                                                  +--rw G?   string
                                                                                                  +--rw H?   string
                                                                                                  +--rw I?   string
                                                                                                  +--rw J?   string
                                                                                                  +--rw K?   string
                                                                                                  +--rw L?   string
                                                                                                  +--rw M?   string
                                                                                                  +--rw N?   string
                                                                                                  +--rw O?   string
                                                                                                  +--rw P?   string
                                                                                                  +--rw Q?   string
                                                                                                  +--rw R?   string
                                                                                                  +--rw S?   string
                                                                                                  +--rw T?   string
                                                                                                  +--rw U?   string
                                                                                                  +--rw V?   string
                                                                                                  +--rw W?   string
                                                                                                  +--rw X?   string
                                                                                                  +--rw Y?   string
                                                                                                  +--rw Z?   string
```
