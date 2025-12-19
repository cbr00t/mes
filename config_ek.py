from common import *
from config import local, server, wifi


###############################
#         Ortak Ayarlar       #
###############################

## Ana Makine (Server) Ayarları
## --------------------------------
server.ip                           =  (192, 168, 1, 48)
server.updatePorts                  =  [2085]


## Cihaz Ayarları
## --------------------------------
local.ip                            =  (192, 168, 1, 241)
local.gateway                       =  (192, 168, 1, 1)
local.rebootTime                    =  0.1                                 # dk
wifi.ssid                           =  'CKCK'
wifi.passwd                         =  'DAMLACIK'
