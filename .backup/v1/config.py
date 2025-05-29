from common import *

# Cihaz Ayarları
if isCircuitPy():
    local = NS(
        ip          = (192, 168, 2, 50),
        subnet      = (255, 255, 255, 0),
        gateway     = (192, 168, 2, 1),
        dns         = (1, 1, 1, 1)
    )
else:
    local = NS(
        ip          = (192, 168, 1, 50),
        subnet      = (255, 255, 255, 0),
        gateway     = (192, 168, 1, 1),
        dns         = (1, 1, 1, 1)
    )

# Ana Makine (Server) Ayarları
server = NS(
    ip          = (192, 168, 2, 2) if isCircuitPy() \
                  else (192, 168, 1, 48),
    wsPort      = 8200,
    rawPort     = 8199,
    autoUpdate  = True
)
updatePort = 2085 if isCircuitPy() else 80
server.updateUrl = f"http://{ip2Str(server.ip)}:{updatePort}/mes/update"


mod = NS(
    # Cihaz Tipi: [ None, 'local', 'rasppico' ]
    device      = None
)

