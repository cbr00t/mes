from common import *
from config import local, server, wifi

## Cihaz Ayarları
## --------------------------------
local.ip                            =  (192, 168, 1, 123)
local.gateway                       =  (192, 168, 1, 1)
wifi.ssid                           =  'CKCK'
wifi.passwd                         =  'DAMLACIK'
# local.rebootTime                    =   1                                 # dk - test
# local.wdtTimeout                    =  8_000                              # ms

## Ana Makine (Server) Ayarları
## --------------------------------
server.ip                           =  (192, 168, 1, 48)
server.updatePorts                  =  [80]
