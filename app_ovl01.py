from common import *
from config import app, server as srv
from time import sleep, monotonic
from traceback import print_exception

def ethCheck():
    dev = shared.dev; eth = dev.eth; lcd = dev.lcd
    if eth.isConnected(): return True
    lcd.clearLineIfReady(1); lcd.writeIfReady('Ethernet bekleniyor...', 1, 1)
    return False
def ethWait():
    while not checkEth():
        sleep(0.05)
def connectToServerIfNot():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock
    if sock.isConnected(): return True
    if not ethCheck(): return False
    shared._inActionsCheck = False
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy():
        lcd.clearLine(range(1, 3))
        lcd.write('SUNUCUYA BAGLAN:', 1, 0)
        lcd.write(f'{srvIP}:{srvPort}', 2, 1)
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
    lcd.clearLineIfReady(0)
    lcd.writeIfReady(f'{app.name} v{version2Str(app.version)}', 0, 0)
    shared._appTitleRendered = True
