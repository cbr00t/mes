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
    autoUpdate                      =  None,                              # True = Force Auto-Update | False = No Auto-Update | None = Use Device Defaults
    updateUrl_postfix               =  '/mes/update',
    hearbeatInterval                =  5,                                  # in secs. ( <= 0 Or None ) = no heartbeat
    socketTimeout                   =  0.5                                 # in secs. default value
)

## Modül Ayarları
## --------------------------------
mod = NS(
    ### device: [ None, 'local', 'rasppico' ]
    device                          =  None
)

## Hardware Ayarları
## --------------------------------
hw = NS(
    keypad = NS(
        rows = ['GP12', 'GP13', 'GP14', 'GP15'],
        cols = ['GP7', 'GP8', 'GP9', 'GP10', 'GP11'],
        keys = [
            ['F1', '1', '2', '3', 'X'],
            ['F2', '4', '5', '6', '^'],
            ['F3', '7', '8', '9', 'V'],
            ['F4', 'ESC', '0', 'ENTER', None]
        ]
    ),
    lcd = NS(
        rows = 4,
        cols = 20
    )
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
    local.ip                        =  (192, 168, 1, 48)
    local.gateway                   =  (192, 168, 1, 1)


## Ana Makine (Server) Ayarları
## --------------------------------
    server.ip                       =  (192, 168, 1, 48)
  # server.ip                       =  (192, 168, 1, 200)




###############################
#     Test Ortamı Ayarları    #
###############################

app = NS(
    name                            = 'Sky MES',
    version                         = (1, 0, 0, 8)
)




