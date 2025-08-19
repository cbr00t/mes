from common import *
from config import app, server as srv
from time import sleep, monotonic
from traceback import print_exception

def ethWait():
    while not checkEth():
        sleep(0.05)
def ethCheck():
    dev = shared.dev; eth = dev.eth; lcd = dev.lcd; lastTime = shared.lastTime
    if eth.isConnected(): lastTime.ethCheckMsg = None; return True
    if not lcdIsBusy() and (not lastTime.ethCheckMsg or monotonic() - lastTime.ethCheckMsg >= 2):
        # lcd.clearLineIfReady(range(1, 3))
        lcd.writeLineIfReady('Ethernet bekleniyor...', 1, 0)
        lastTime.ethCheckMsg = monotonic()
    return False
def connectToServerIfNot():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock; lastTime = shared.lastTime
    if sock.isConnected(): lastTime.srvConnectMsg = None; return True
    shared._appTitleRendered = False
    shared.lastTime.updateMainScreen = shared._updateMainScreen_lastDebugText = None
    if not ethCheck(): return False
    shared._inActionsCheck = False; lastTime = shared.lastTime
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy() and (not lastTime.srvConnectMsg or monotonic() - lastTime.srvConnectMsg >= 5):
        lcd.writeLineIfReady('SUNUCUYA BAGLAN:', 1, 0)
        lcd.writeLineIfReady(f'{srvIP}:{srvPort}', 2, 1)
        lastTime.srvConnectMsg = monotonic()
    try:
        return sock.open()
    except Exception as ex:
        print('[ERROR]', ex); print_exception(ex)
        return False
    finally:
        lcd.clearLineIfReady(range(1, 3))
