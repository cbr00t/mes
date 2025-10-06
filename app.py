from common import *
from config import local, server as srv
from update import *
from menu import SubMenu, MenuItem
from app_infoPart import *
from app_menus import *

async def init():
    global _aborted, localIP, srvIP, srvPort, dev, wifi, ws, lcd, keypad, h
    localIP = ip2Str(local.ip); srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawwset: [{srvIP}:{srvPort}]')
    _aborted = False
    dev = initDevice(); h = initHandlers()
    wifi = dev.wifi; lcd = dev.lcd; ws = dev.ws; keypad = dev.keypad
    shared._onKeyPressed = onKeyReleased
    shared._onKeyReleased = onKeyPressed
    
async def run():
    global _aborted
    # wifi.connect()
    lcd.off(); lcd.on()
    lcd.clearIfReady(); await ws.close()
    print('app started')
    if keypad is not None:
        keypad.set_onPressed(shared._onKeyPressed)
        keypad.set_onReleased(shared._onKeyReleased)
        thread(keypad.loop)
    while not _aborted:
        try:
            await loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)
    _aborted = True
    lcd.clear(); lcd.write('SHUTDOWN', 1,1)
    await ws.close()

async def loop():
    global cpuHaltTime
    cpuHaltTime = .5 if isIdle() else .1
    await asleep(cpuHaltTime)
    # if not shared._appTitleRendered: renderAppTitle()
    # if lcd._lastWriteTime: lcd.clearLineIfReady(2)
    lastGC = shared.lastTime.gc
    if not lastGC or monotonic() - lastGC >= 2:
        gc.collect(); shared.lastTime.gc = monotonic()
    updateMainScreen()
    if wifiCheck():
        if await connectToServerIfNot():
            if not shared._updateCheckPerformed:
                await updateFiles()
            await wsCheckStatusIfNeed()
            await actionsCheckAndExec()
            await processQueues()
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
async def updateSelf():
    lcd.clearLine(3); lcd.write('GUNCELLENIYOR...', 3, 2)
    sleep(0.5); srv.autoUpdate = True
    await updateFiles(); reboot()
def reboot():
    import machine
    print('rebooting...')
    lcd.clearLine(3); lcd.write('REBOOTING...', 3, 2)
    sleep(.5); machine.reset()

def wifiWait():
    while not wifiCheck():
        sleep(.1)
def wifiCheck():
    if not wifi.isConnected():
        wifi.connect()
    lastTime = shared.lastTime
    if wifi.isConnected():
        lastTime.wifiCheckMsg = None
        return True
    if not lcdIsBusy() and (not lastTime.wifiCheckMsg or monotonic() - lastTime.wifiCheckMsg >= 5):
        # lcd.clearLineIfReady(range(1, 3))
        lcd.writeLineIfReady('WiFi bekleniyor...', 1, 0)
        lastTime.wifiCheckMsg = monotonic()
    return False
async def connectToServerIfNot():
    lastTime = shared.lastTime
    if ws.isConnected():
        lastTime.srvConnectMsg = None
        return True
    shared._appTitleRendered = False
    lastTime.updateMainScreen = shared._updateMainScreen_lastDebugText = None
    if not wifiCheck():
        return False
    shared._inActionsCheck = False; lastTime = shared.lastTime
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy() and (not lastTime.srvConnectMsg or monotonic() - lastTime.srvConnectMsg >= 5):
        lcd.writeLineIfReady('SUNUCUYA BAGLAN:', 1, 0)
        lcd.writeLineIfReady(f'{srvIP}:{srvPort}', 2, 1)
        lastTime.srvConnectMsg = monotonic()
    try:
        return await ws.open()
    except Exception as ex:
        print('[ERROR]', ex); print_exception(ex)
        return False

def updateMainScreen():
    if lcdIsBusy(): return False
    lastTime = shared.lastTime
    if lastTime.updateMainScreen and monotonic() - lastTime.updateMainScreen <= 0.5: return False
    renderAppTitle()
    # if lcdCanBeCleared(): lcd.clearLineIfReady(range(1, lcd.getRows() - 1))
    rec = shared.curStatus
    rec = rec and rec[0] if isinstance(rec, list) else {}
    _rec = {k: v for k, v in rec.items() if 'Sure' not in k}
    text = json.dumps(_rec)
    def str_val(key):
        return rec.get(key) or ''
    def int_val(key):
        value = rec.get(key)
        return int(value) if isinstance(value, (str, int, float)) else 0
    if text != shared._updateMainScreen_lastDebugText:
        print(f'\nstatus_check:  \n  {text}\n')
        shared._updateMainScreen_lastDebugText = text
        #  {"isNetMiktar": 15.0, "operNo": 8, "isFireMiktar": 0.0, "siradakiIsSayi": 0, "emirNox": "1688", "sonDurTS": "26.08.2025 17:35:28", "duraksamaKritik": false, "hatID": "030", "aktifCevrimSayisi": 0, "atananIsSayi": 1, "sonIslemTS": "26.08.2025 17:30:27", "sabitDuraksamami": 0, "operAciklama": "CNC DİK TORNA", "emirMiktar": 2.0, "operatorCagrimTS": null, "ip": "192.168.2.50", "onceUretMiktar": 15.0, "durumKod": "DR", "isSaymaSayisi": 1, "oemID": 9762, "urunAciklama": "9-11 KAMPANA İŞLEME", "urunKod": "KAMP01-9-11-6B", "perKod": "AR-GE01", "isSaymaInd": 0, "durNedenKod": "06", "sinyalKritik": true, "emirTarih": "25.06.2025 00:00:00", "sonAyrilmaDk": 5.22611, "perIsim": "ENES VURAL", "oemgerceklesen": 35.0, "onceCevrimSayisi": 15, "isID": 3, "aciklama": "CNC1", "ekBilgi": "", "seq": 1, "oemistenen": 2.0, "id": "CNC01", "durNedenAdi": "AYRILMA", "aktifUretMiktar": 0.0, "isIskMiktar": 0.0, "hatAciklama": "TALASLI IMALAT", "basZamanTS": "26.08.2025 17:30:14", "maxAyrilmaDk": 5.22611}
        lcd.writeLineIfReady(f"{str_val('urunKod')}", 0, 0)
        lcd.writeLineIfReady(f"{str_val('perKod')}", 1, 0)
        lcd.writeLineIfReady(f"U:{int_val('onceUretMiktar')}+{int_val('aktifUretMiktar')} | S:{int_val('isSaymaInd')}/{int_val('isSaymaSayisi')}", 2, 0)
        lcd.writeLineIfReady(f"D:{str_val('durumKod')}  |  E:{int_val('emirMiktar')}", 3, 0)
        lastTime.updateMainScreen = monotonic()
    return True
def renderAppTitle():
    # from config import app
    # lcd.writeLineIfReady(f'v{version2Str(app.version)}  ', 0, 0)
    shared._appTitleRendered = True

async def wsCheckStatusIfNeed():
    if not ws.isConnected(): return False
    if not statusShouldBeChecked(): return False
    try:
        resp = await ws.wsTalk(api='tekilTezgahBilgi', wsPath='ws/skyMES/makineDurum')
        if resp:
            shared.curStatus = resp
            shared.lastTime.statusCheck = monotonic()
            return True
    except Exception as ex:
        print("[ERROR] wsStatus:", ex)
        print_exception(ex)
    return False
async def actionsCheckAndExec():
    actions = await actionsCheck()
    await actionsExec(actions)
async def actionsCheck():
    await asleep(.1)
    localIP = ip2Str(local.ip)
    # print(f'    connected = {connected} | shared._inActionsCheck = {shared._inActionsCheck}')
    if not ws.isConnected():
        shared._inActionsCheck = False
        # if not lcdIsBusy(): lcd.clearLine(1)
        return None
    if not shared._inActionsCheck:
        # lcd.clearLineIfReady(range(1, 3));
        # lcd.writeIfReady('KOMUT BEKLENIYOR', 1, 2)
        print('awaiting remote command')
        shared._inActionsCheck = True
    resp = targetIP = actions = None
    try: resp = await ws.wsRecv()
    except (OSError, RuntimeError) as ex: resp = None
    except Exception as ex: print('[ERROR]', 'APP wsRecv:', ex); print_exception(ex)
    if not resp: return None
    print(f'rawwset interrupt: {json.dumps(resp)}')
    if isinstance(resp, list): resp = { 'actions': resp }
    targetIP = resp.get('ip'); _actions = resp.get('actions')
    if _actions: actions = _actions
    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
        actions = None
    return actions
async def actionsExec(actions):
    if not actions: return False
    print('  actions=', actions)
    for item in actions:
        busy(); action = item.get('action') or item.get('cmd')
        print('<< action:', action)
        if not action: continue 
        handler = getattr(h, action, None)
        if handler is None:
            print('[ERROR]  no matching handler', action)
            continue
        args = item['args'] if 'args' in item else []
        print('<<     action args:', args)
        try:
            sleep(.1); busy()
            handler(*args)                                                                                     # ← [js]  handler.call(this, ...args) karşılığı
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            # await ws.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True
async def processQueues():
    global _aborted
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    if not keyQueue:
        return
    for item in keyQueue:
        ts = item.get('ts')
        if not ts:
            continue
        item['tsDiff'] = round((monotonic() - ts) * 1000)
        item.pop('ts', None)
    result = await ws.wsTalk('fnIslemi', None, keyQueue)
    debug_result = json.dumps(result) if result else '*empty*'
    print(f'    [processQueue] - [fnIslemi] - result: {debug_result})')
    if isinstance(result, dict) and bool(result.get('isError')) == False:
        sentCount = len(keyQueue)
        lcd.writeLineIfReady(f'* [{sentCount}] GITTI', 2, 0)
        keyQueue_clear()
    else:
        lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)
def keyQueue_add(item):
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    keyQueue.append(item)
    return item
def keyQueue_pop(item):
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    keyQueue.pop(0)
    return item
def keyQueue_clear():
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    if keyQueue: keyQueue.clear()

async def onKeyPressed(key):
    part = activePart()
    return part.onKeyPressed(key) if part else await onKeyPressed_defaultAction(key)
async def onKeyReleased(key, duration):
    part = activePart()
    return part.onKeyReleased(key, duration) if part else await onKeyReleased_defaultAction(key, duration)

async def onKeyPressed_defaultAction(key):
    print(f'{key} press')
    key = key.lower(); lastTime = shared.lastTime._keySend
    delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcd.writeIfReady(f'[{key}]', lcd.getRows() - 1, lcd.getCols() - 8)
    lastTime = shared.lastTime._keySend = monotonic()
    # if key == '0':
    #    getMenu('main').run()
    if key == 'f1':
        DeviceInfoPart().run()
    elif key == 'f2':
        mnu = getMenu_duraksamaNedenleri()
        if mnu: mnu.run()
    # elif key == 'x':
    #    from part_input import InputPart
    #    InputPart(_title = 'Input Test', _val = 'cik').run()
    else:
        _id = 'secondary' if key == 'enter' else key
        try:
            await processQueues()
            if not await ws.wsTalk('fnIslemi', { 'id': _id, 'delayMS': duration }):
                raise RuntimeError()
            # lcd.writeLineIfReady(f'* [{key}] GITTI', 2, 0)
            await asleep(0.1); lcd.clearLineIfReady(lcd.getRows() - 1) 
        except Exception as ex:
            # lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)
            print_exception(ex)
            # lcd.writeLineIfReady(f'[{key}] KUYRUGA', 2, 1)
            keyQueue_add({ 'ts': monotonic(), 'id': _id, 'delayMS': duration })
    return True
async def onKeyReleased_defaultAction(key, duration):
    print(f'{key} released | duration = {duration}')
    key = key.lower()
    if lastTime and ticks_diff(monotonic(), lastTime) <= 0.3: return False
    lastTime = keypad._lastKeyPressTime; delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcd.writeIfReady(f'[{key}]', lcd.getRows() - 1, lcd.getCols() - 8)
    lastTime = shared.lastTime._keySend = monotonic()
    if key == 'esc' and duration >= 2:
        from app import updateSelf, reboot
        reboot()
    return True
