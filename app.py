from common import *
from config import app, local, server as srv
from update import *
from app_ovl01 import *
from app_ovl02 import *
from app_ovl03 import *

async def init():
    global localIP, srvIP, srvPort, dev, wifi, sock, lcd, keypad, h
    localIP = ip2Str(local.ip); srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawSocket: [{srvIP}:{srvPort}]')
    dev = initDevice(); h = initHandlers()
    wifi = dev.wifi; lcd = dev.lcd; sock = dev.sock; keypad = dev.keypad
    shared._onKeyPressed = onKeyPressed
    shared._onKeyReleased = onKeyReleased
    asyncio.create_task(keypad.loop())

async def run():
    # wifi.connect()
    lcd.off(); lcd.on()
    lcd.clearIfReady(); sock.close()
    print('app started')
    while True:
        try:
            await loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)
    lcd.clear(); lcd.write('SHUTDOWN', 1,1)
    sock.close()

async def loop():
    global cpuHaltTime
    cpuHaltTime = 3 if isIdle() else 1; await asleep(cpuHaltTime)
    # if not shared._appTitleRendered: renderAppTitle()
    # if lcd._lastWriteTime: lcd.clearLineIfReady(2)
    
    lastGC = shared.lastTime.gc
    if not lastGC or monotonic() - lastGC >= 2:
        gc.collect(); shared.lastTime.gc = monotonic()
    updateMainScreen(); await sock.wsHeartbeatIfNeed()
    if await wifiCheck():
        if await connectToServerIfNot():
            if not shared._updateCheckPerformed: updateFiles()
            await sock.wsCheckStatusIfNeed()
        await actionsCheckAndExec()
        updateMainScreen()
        await actionsCheckAndExec()
        await processQueues()
    else:
        updateMainScreen()

def initDevice():
    print('    init device')
    dev = shared.dev
    if dev is None:
        from config import mod
        modName_device = mod.device or ('local' if isLocalPy() else 'rasppico')
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
    sleep(0.5); srv.autoUpdate = True
    updateFiles(); reboot()
def reboot():
    import machine
    print('rebooting...')
    lcd.clearLine(3); lcd.write('REBOOTING...', 3, 2)
    sleep(.5); machine.reset()
