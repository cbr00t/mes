from common import *


###############################
#       Uygulama Ayarları     #
###############################

app = NS(
    name                            = 'Sky MES',
    version                         = (1, 0, 20)
)


###############################
#         Ortak Ayarlar       #
###############################

## Cihaz Ayarları
## --------------------------------
local = NS(
    subnet                          =  (255, 255, 255, 0),
    dns                             =  (1, 1, 1, 1),
    idleTime                        =  500
)

## Ana Makine (Server) Ayarları
## --------------------------------
server = NS(
    wsPort                          =  8200,
    rawPort                         =  8199,
    updatePorts                     =  [2085, 80, 81],
    wsPath                          =  'ws/skyMES/makineDurum',
    autoUpdate                      =  None,                               # True = Force Auto-Update | False = No Auto-Update | None = Use Device Defaults
    updateUrl_postfix               =  '/mes/update',
    hearbeatInterval                =  0,                                  # in secs. ( <= 0 Or None ) = no heartbeat
    statusCheckInterval             =  0.8,                                  # in secs. ( <= 0 Or None ) = no status check (for LCD Display)
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
            ['F2', '4', '5', '6', 'up'],
            ['F3', '7', '8', '9', 'down'],
            ['F4', 'ESC', '0', 'ENTER', None]
        ]
    ),
    lcd = NS(
        rows = 4, cols = 20,
        clearDelay = 2
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
