from common import *
from config import app, server as srv

async def wifiWait():
    while not await wifiCheck():
        await asleep(0.05)
async def wifiCheck():
    dev = shared.dev; wifi = dev.wifi; lcd = dev.lcd; lastTime = shared.lastTime
    if not wifi.isConnected():
        wifi.connect()
    if wifi.isConnected():
        lastTime.wifiCheckMsg = None
        return True
    if not lcdIsBusy() and (not lastTime.wifiCheckMsg or monotonic() - lastTime.wifiCheckMsg >= 5):
        # lcd.clearLineIfReady(range(1, 3))
        lcd.writeLineIfReady('WiFi bekleniyor...', 1, 0)
        lastTime.wifiCheckMsg = monotonic()
    return False
async def connectToServerIfNot():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock; lastTime = shared.lastTime
    if sock.isConnected(): lastTime.srvConnectMsg = None; return True
    shared._appTitleRendered = False
    shared.lastTime.updateMainScreen = shared._updateMainScreen_lastDebugText = None
    if not await wifiCheck(): return False
    shared._inActionsCheck = False; lastTime = shared.lastTime
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy() and (not lastTime.srvConnectMsg or monotonic() - lastTime.srvConnectMsg >= 5):
        lcd.writeLineIfReady('SUNUCUYA BAGLAN:', 1, 0)
        lcd.writeLineIfReady(f'{srvIP}:{srvPort}', 2, 1)
        lastTime.srvConnectMsg = monotonic()
    try:
        return await sock.open()
    except Exception as ex:
        print('[ERROR]', ex); print_exception(ex)
        return False
    finally:
        lcd.clearLineIfReady(range(1, 3))
