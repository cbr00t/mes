from common import *
from config import app, server as srv
from time import sleep, monotonic
from traceback import print_exception

def ethWait():
    while not checkEth():
        sleep(0.05)
def ethCheck():
    dev = shared.dev; eth = dev.eth; lcd = dev.lcd
    lastTime = shared.lastTime
    if eth.isConnected():
        lastTime.ethCheckMsg = None
        return True
    if not lcdIsBusy() and (not lastTime.ethCheckMsg or monotonic() - lastTime.ethCheckMsg >= 5):
        lcd.clearLine(range(1, 3))
        lcd.write('Ethernet bekleniyor...', 1, 0)
        lastTime.ethCheckMsg = monotonic()
    return False
def connectToServerIfNot():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock
    lastTime = shared.lastTime
    if sock.isConnected():
        lastTime.srvConnectMsg = None
        return True
    if not ethCheck():
        return False
    shared._inActionsCheck = False; lastTime = shared.lastTime
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy() and (not lastTime.srvConnectMsg or monotonic() - lastTime.srvConnectMsg >= 5):
        lcd.clearLine(range(1, 3))
        lcd.write('SUNUCUYA BAGLAN:', 1, 0)
        lcd.write(f'{srvIP}:{srvPort}', 2, 1)
        lastTime.srvConnectMsg = monotonic()
    try:
        return sock.open()
    except Exception as ex:
        print('[ERROR]', ex); print_exception(ex)
        return False
    finally:
        if not lcdIsBusy():
            lcd.clearLine(range(1, 3))
def renderAppTitle():
    dev = shared.dev; lcd = dev.lcd
    lcd.clearLine(0)
    lcd.write(f'{app.name} v{version2Str(app.version)}', 0, 0)
    shared._appTitleRendered = True
