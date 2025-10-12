from common import *

###############################
#       Uygulama Ayarları     #
###############################

app = NS(
    name                            = 'Sky MES',
    version                         = (1, 1, 11)
)


###############################
#         Ortak Ayarlar       #
###############################

## Cihaz Ayarları
## --------------------------------
local = NS(
    ip                              =  None,
    gateway                         =  None,
    subnet                          =  (255, 255, 255, 0),
    dns                             =  (1, 1, 1, 1),
    idleTime                        =  30 * 60_000,                       # ms
    threadLoop_globalWait_ms        =  10
)

## Ana Makine (Server) Ayarları
## --------------------------------
server = NS(
    wsPort                          =  8200,
    rawPort                         =  8199,
    updatePorts                     =  [80, 2085],
    wsPath                          =  'ws/skyMES/makineDurum',
    autoUpdate                      =  True,                               # True = Force Auto-Update | False = No Auto-Update | None = Use Device Defaults
    updateUrl_postfix               =  '/mes/update',
    statusCheckInterval             =  1.0,                                # in secs. ( <= 0 Or None ) = no status check (for LCD Display)
    socketTimeout                   =  0.01                                # in secs. default value
)

wifi = NS(
    ssid                            = '',
    passwd                          = '',
    timeout                         = 10
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
    # eth = NS(
    #     cs    = 'GP17',
    #     spi   = ['GP18', 'GP19', 'GP16'],
    #     reset = 'GP20'
    # ),
    keypad = NS(
        rows  = [12, 13, 14, 15],                   # board.(GP12..GP15)
        cols  = [7, 8, 9, 10, 11],                  # board.(GP7..GP11)
        keys  = [
            ['f1', '1', '2', '3', 'X'],
            ['f2', '4', '5', '6', 'up'],
            ['f3', '7', '8', '9', 'down'],
            ['f4', 'esc', '0', 'enter', None]
        ],
        debounce_ms = 5,
        scan_interval_ms = 20,
        simulation_interval_ms = 5_000
    ),
    rfid = NS(
        scan_interval_ms = 20,
        simulation_interval_ms = 25_000
    ),
    lcd = NS(
        rows = int(4), cols = int(20),
        rc_status = (1, -2),
        _id = 1, scl = 27, sda = 26,
        freq = 400_000, addr = 0x27
    ),
    led = NS(count = 1, pin = 22, brightness = 200),
    buzzer = NS(pin = 21, freq = 440, duration = 0.15, pause = 0.1)
)


if isLocalPy():
    local.threadLoop_globalWait_ms *= 10


from config_override import *



