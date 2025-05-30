from common import *


###############################
#         Ortak Ayarlar       #
###############################

## Cihaz Ayarları
## --------------------------------
local = NS(
    subnet                          =  (255, 255, 255, 0),
    dns                             =  (1, 1, 1, 1),
    idleTime                        =  60
)

## Ana Makine (Server) Ayarları
## --------------------------------
server = NS(
    wsPort                          =  8200,
    rawPort                         =  8199,
    updatePorts                     =  [2085],
    wsPath                          =  'ws/skyMES/makineDurum',
    autoUpdate                      =  True,
    updateUrl_postfix               =  '/mes/update',
    hearbeatInterval                =  15                                 # in secs. ( <= 0 Or None ) = no heartbeat
)

## Modül Ayarları
## --------------------------------
mod = NS(
    ### device: [ None, 'local', 'rasppico' ]
    device                          =  None
)



if isCircuitPy():

###############################
#    Gerçek Ortam Ayarları    #
###############################

## Cihaz Ayarları
## --------------------------------
    local.ip                        =  (192, 168, 2, 50)
    local.gateway                   =  (192, 168, 2, 1)


## Ana Makine (Server) Ayarları
## --------------------------------
    server.ip                       =  (192, 168, 2, 2)


else:

###############################
#     Test Ortamı Ayarları    #
###############################

## Cihaz Ayarları
## --------------------------------
    local.ip                        =  (192, 168, 1, 50)
    local.gateway                   =  (192, 168, 1, 1)


## Ana Makine (Server) Ayarları
## --------------------------------
    server.ip                       =  (192, 168, 1, 48)






