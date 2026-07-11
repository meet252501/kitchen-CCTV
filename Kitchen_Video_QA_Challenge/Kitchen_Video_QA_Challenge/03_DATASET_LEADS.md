# Dataset & Reference Video Leads

None of these are confirmed as the actual hidden scoring clips — builderr has
said the final hidden clips will be rights-cleared, anonymized, and not
discoverable online. These are the reference/candidate sources visible from
the draft spec, useful for building and testing your own pipeline against
similar footage style.

## Good style match (real fixed-camera kitchen CCTV, but short)
| Source | Length | Note |
|---|---|---|
| [Revlight Security – Kitchen View CCTV](https://www.youtube.com/watch?v=nQht56i2Xkg) | 1:53 | Real fixed kitchen CCTV, correct target style, too short to use alone |
| [Omni-Watch Systems / Restaurant Kitchen](https://www.youtube.com/watch?v=Wdspo9cMQyk) | ~1:00 | Real restaurant CCTV, good format, too short |

## Usable fallback length, but home kitchens not restaurants
| Source | Length | Note |
|---|---|---|
| [CCTV 2012-02-29 KITCHEN](https://www.youtube.com/watch?v=PTHL_GmYmeE) | 3:10 | Likely home kitchen |
| [Everyday CCTV Security Camera in Kitchen](https://www.youtube.com/watch?v=w7QPcndTUWU) | 3:14 | Home kitchen |

## Fallback only (weaker style match)
| Source | Length | Note |
|---|---|---|
| [House help kitchen CCTV](https://www.youtube.com/watch?v=j8P4P9Q6cno) | 2:09 | Home/private kitchen |
| [Security Cams: Kitchen](https://www.youtube.com/watch?v=_XHPxYGblOc) | 2:03 | Kitchenette/pantry setup |

## Rejected as leads (noted for context, don't use)
| Source | Why rejected |
|---|---|
| [CCTV Cameras in Restaurant, Guttenberg NJ](https://www.youtube.com/watch?v=if3_44TcTLw) | Promo montage, not clean raw CCTV |
| Rail Drishti | Screen recording, not actual CCTV footage |
| Bon Appetit kitchen videos | Produced/edited content, not raw |
| KitchenGuard / Wobot demo videos | Product demo footage, not raw operational footage |

## Structured dataset / academic leads
| Source | Note |
|---|---|
| [Kaggle: Kitchen Video in Restaurants](https://www.kaggle.com/datasets/naoamscoltd/kitchen-video-in-restaurants) | HACCP-focused restaurant kitchen video; check license/usage terms before relying on it |
| [COM Kitchens (NII)](https://www.nii.ac.jp/dsc/idr/en/rdata/COM_Kitchens/) | 177 fixed-view cooking videos, academic-use only |
| [EPFL Smart Kitchen](https://github.com/amathislab/EPFL-Smart-Kitchen) | Multi-view lab dataset, not restaurant setting |

## Practical takeaway
For your own dev/test loop, the two short real-CCTV clips (Revlight,
Omni-Watch) are the closest style match to what the hidden set will likely
look like — fixed angle, real working kitchen, unstaged. Use the longer home-
kitchen clips just to stress-test your pipeline on longer runtimes and
different lighting/camera conditions, since "hidden generalization" is
literally 15% of the score.
