from common import *
from config import local, server, wifi



###############################
#         Ortak Ayarlar       #
###############################

## Ana Makine (Server) Ayarları
## --------------------------------
server.ip                           =  (192, 168, 1, 7)





if not isLocalPy():


###############################
#    Gerçek Ortam Ayarları    #
###############################

## Cihaz Ayarları
## --------------------------------
    local.ip                        =  (192, 168, 1, 123)
    local.gateway                   =  (192, 168, 1, 1)
    wifi.ssid                       =  'Keenetic-2432'
    wifi.passwd                     =  'iAQTYhK9'



else:


###############################
#     Test Ortamı Ayarları    #
###############################

## Cihaz Ayarları
## --------------------------------
    local.ip                        =  (192, 168, 1, 123)
    local.gateway                   =  (192, 168, 1, 1)

