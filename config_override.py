from common import *
from config import local, server, wifi



###############################
#         Ortak Ayarlar       #
###############################

## Ana Makine (Server) Ayarları
## --------------------------------
server.ip                           =  (192, 168, 10, 251)
server.updatePorts                  =  [80]


## Cihaz Ayarları
## --------------------------------
local.ip                            =  (192, 168, 10, 123)
local.gateway                       =  (192, 168, 1, 1)
wifi.ssid                           =  'Uysal'
wifi.passwd                         =  'Lasyu123Uysal'

local.rebootTime                    =  15                                   # dk
