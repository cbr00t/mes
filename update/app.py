from common import *
from config import app, local, server as srv
from update import *
from app_ovl01 import *
from app_ovl02 import *
from app_ovl03 import *
from time import sleep, monotonic
import json
import gc
from traceback import print_exception

def init():
    global localIP, srvIP, srvPort, dev, eth, sock, lcd, keypad, h
    localIP = ip2Str(local.ip); srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawSocket: [{srvIP}:{srvPort}]')
    dev = initDevice(); h = initHandlers()
    eth = dev.eth; lcd = dev.lcd; sock = dev.sock; keypad = dev.keypad
    shared._onKeyPressed = onKeyPressed; shared._onKeyReleased = onKeyReleased

def run():
    lcd.off(); lcd.on()
    lcd.clearIfReady(); sock.close()
    print('app started')
    while True:
        try:
            loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)
    lcd.clear(); lcd.write('SHUTDOWN', 1,1)
    sock.close()

def loop():
    global cpuHaltTime
    cpuHaltTime = 0.2 if isIdle() else 0.05; sleep(cpuHaltTime)
    # if not shared._appTitleRendered: renderAppTitle()
    # if lcd._lastWriteTime: lcd.clearLineIfReady(2)
    lastGC = shared.lastTime.gc 
    if not lastGC or monotonic() - lastGC >= 2:
        gc.collect(); shared.lastTime.gc = monotonic()
    updateMainScreen(); sock.wsHeartbeatIfNeed();
    if connectToServerIfNot():
        if not shared._updateCheckPerformed: updateFiles()
        sock.wsCheckStatusIfNeed()
    updateMainScreen(); keypad.update()
    keypad.update(); actionsCheckAndExec()
    processQueues(); keypad.update()

def initDevice():
    print('    init device')
    dev = shared.dev
    if dev is None:
        from config import mod
        modName_device = mod.device or ('rasppico' if isCircuitPy() else 'local')
        print(f'Device Module = {modName_device}')
        dynImport(f'dev_{modName_device}', 'mod_dev')
        print(f'    import dev_{modName_device} as mod_dev')
        dev = shared.dev; print(f'    dev: {dev}')
    return dev
def initHandlers():
    print('    init handlers')
    h = shared.handlers
    if h is None:
        from appHandlers import AppHandlers
        h = shared.handlers = AppHandlers()
    return h
def updateSelf():
    lcd.clearLine(3); lcd.write('GUNCELLENIYOR...', 3, 2)
    sleep(0.5)
    srv.autoUpdate = True
    updateFiles()
    lcd.clearLine(3); lcd.write('REBOOTING...', 3, 2)
    h.reboot()
