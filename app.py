from common import *
from config import local, server, hw as srv
from update import *
from menu import SubMenu, MenuItem
from app_infoPart import *
from app_menus import *

async def init():
    global aborted, localIP, srvIP, srvPort, dev, wifi, ws, lcd, led, keypad, buzzer, h
    localIP = ip2Str(local.ip); srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawwset: [{srvIP}:{srvPort}]')
    aborted = False
    dev = initDevice(); h = initHandlers()
    wifi = dev.wifi; lcd = dev.lcd; led = dev.led;
    ws = dev.ws; keypad = dev.keypad; buzzer = dev.buzzer
    shared._onKeyPressed = onKeyPressed
    shared._onKeyReleased = onKeyReleased
    
async def run():
    global aborted
    lcd.off().on(); lcd.clearIfReady()
    led.write('SIYAH'); led.clear()
    for i in range(0, 2):
        await buzzer.beep(4000, .1)
    await buzzer.beep(4000, .3)
    print('app started')
    # if keypad is not None:
    #    keypad.set_onPressed(shared._onKeyPressed)
    #    keypad.set_onReleased(shared._onKeyReleased)
    # async_task(threadProc)
    thread(threadProc)
    while not aborted:
        try:
            await loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)
    aborted = True
    lcd.clear(); lcd.write('SHUTDOWN', 1,1)
    await ws.close()

def threadProc():
    global aborted
    scan_interval_secs = (hw.keypad.scan_interval_ms or 10) / 1000
    while not aborted:
        try:
            if keypad is not None:
                keypad.update()
        except KeyboardInterrupt as ex:
            aborted = True
            print("\n[thread] stopped by user (KeyboardInterrupt)")
            return
        except Exception as ex:
            print('[ERROR]', ex)
            print_exception(ex)
        sleep(scan_interval_secs * 20 if isIdle() else scan_interval_secs)

async def loop():
    await asleep(1 if isIdle() else .01)
    if not (await wifiCheck() and await connectToServerIfNot()): return
    if not shared._updateCheckPerformed: await updateFiles()
    lastTime = shared.lastTime
    await processQueues()
    if not lcdIsBusy():
        await wsCheckStatusIfNeed()
        await updateMainScreen()

def initDevice():
    print('    init device')
    dev = shared.dev
    if dev is None:
        from config import mod
        modName_device = mod.device or ('local' if isLocalPy() else 'rasppico')
        print(f'Device Module = {modName_device}')
        dynImport(f'dev_{modName_device}', 'mod_dev')
        print(f'    import dev_{modName_device} as mod_dev')
        dev = shared.dev
        print(f'    dev: {dev}')
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
    await asleep(0.5); srv.autoUpdate = True
    await updateFiles()
    reboot()
def reboot():
    if isMicroPy(): import machine
    print('rebooting...')
    lcd.clearLine(3); lcd.write('REBOOTING...', 3, 2)
    sleep(.5)
    if isMicroPy(): machine.reset()

async def wifiWait():
    while not wifiCheck():
        await asleep(.1)
async def wifiCheck():
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
    if not await wifiCheck():
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

async def updateMainScreen():
    # if True: return False
    if lcdIsBusy(): return False
    lastTime = shared.lastTime
    if lastTime.updateMainScreen and monotonic() - lastTime.updateMainScreen <= 0.5: return False
    renderAppTitle()
    # if lcdCanBeCleared(): lcd.clearLineIfReady(range(1, lcd.getRows() - 1))
    rec = shared.curStatus
    rec = rec and rec[0] if isinstance(rec, list) else \
          rec if isinstance(rec, dict) else {}
    _rec = {k: v for k, v in rec.items() if 'Sure' not in k}
    text = json.dumps(_rec)
    def str_val(key):
        return rec.get(key) or ''
    def int_val(key):
        value = rec.get(key)
        return int(value) if isinstance(value, (str, int, float)) else 0
    # print('text = ', text)
    # print('shared._updateMainScreen_lastDebugText = ', shared._updateMainScreen_lastDebugText)
    urunKod = str_val('urunKod'); perKod = str_val('perKod'); emirMiktar = int_val('emirMiktar')
    onceUretMiktar = int_val('onceUretMiktar'); aktifUretMiktar = int_val('aktifUretMiktar')
    isSaymaInd = int_val('isSaymaInd'); isSaymaSayisi = int_val('isSaymaSayisi')
    durumKod = str_val('durumKod'); 
    if not urunKod:    # empty data
        return False
    hashStr = (
        f"{urunKod}|{perKod}|{onceUretMiktar}|{aktifUretMiktar}",
        f"{isSaymaInd}|{isSaymaSayisi}|{durumKod}|{emirMiktar}"
    )
    if hashStr != shared._updateMainScreen_lastHashStr:
        print(f'status_check cur  hash:  [{hashStr}]')
        print(f'status_check prev hash:  [{shared._updateMainScreen_lastHashStr}]')
        shared._updateMainScreen_lastHashStr = hashStr
        shared._updateMainScreen_lastDebugText = text
        lastTime.updateMainScreen = monotonic()
        #  {"isNetMiktar": 15.0, "operNo": 8, "isFireMiktar": 0.0, "siradakiIsSayi": 0, "emirNox": "1688", "sonDurTS": "26.08.2025 17:35:28", "duraksamaKritik": false, "hatID": "030", "aktifCevrimSayisi": 0, "atananIsSayi": 1, "sonIslemTS": "26.08.2025 17:30:27", "sabitDuraksamami": 0, "operAciklama": "CNC DİK TORNA", "emirMiktar": 2.0, "operatorCagrimTS": null, "ip": "192.168.2.50", "onceUretMiktar": 15.0, "durumKod": "DR", "isSaymaSayisi": 1, "oemID": 9762, "urunAciklama": "9-11 KAMPANA İŞLEME", "urunKod": "KAMP01-9-11-6B", "perKod": "AR-GE01", "isSaymaInd": 0, "durNedenKod": "06", "sinyalKritik": true, "emirTarih": "25.06.2025 00:00:00", "sonAyrilmaDk": 5.22611, "perIsim": "ENES VURAL", "oemgerceklesen": 35.0, "onceCevrimSayisi": 15, "isID": 3, "aciklama": "CNC1", "ekBilgi": "", "seq": 1, "oemistenen": 2.0, "id": "CNC01", "durNedenAdi": "AYRILMA", "aktifUretMiktar": 0.0, "isIskMiktar": 0.0, "hatAciklama": "TALASLI IMALAT", "basZamanTS": "26.08.2025 17:30:14", "maxAyrilmaDk": 5.22611}
        lcd.writeLineIfReady(f"{urunKod}", 0, 0)
        lcd.writeLineIfReady(f"{perKod}", 1, 0)
        lcd.writeLineIfReady(f"U:{onceUretMiktar}+{aktifUretMiktar} | S:{isSaymaInd}/{isSaymaSayisi}", 2, 0)
        lcd.writeLineIfReady(f"D:{durumKod} | E:{emirMiktar}", 3, 0)
    return True
def renderAppTitle():
    # from config import app
    # lcd.writeLineIfReady(f'v{version2Str(app.version)}  ', 0, 0)
    shared._appTitleRendered = True

async def wsCheckStatusIfNeed():
    if not ws.isConnected(): return False
    if not statusShouldBeChecked(): return False
    try:
        rec = await ws.wsTalk(api='tezgahBilgi', timeout=.5)
        if rec:
            rec = rec[0] if isinstance(rec, list) else rec
            shared.curStatus = rec
            shared.lastTime.statusCheck = monotonic()
            ledDurum = rec.get('ledDurum') if isinstance(rec, dict) else None
            durumKod = rec.get('durumKod') if isinstance(rec, dict) else None
            _exec = rec.get('_exec') if isinstance(rec, dict) else None
            print(f'[DEBUG]  durumKod = [{durumKod}] | ledDurum = [{ledDurum}]')
            print(f'[DEBUG]  _exec = [{_exec}] | ledDurum = [{ledDurum}]')
            if ledDurum: led.write(ledDurum)
            elif durumKod is not None: await updateDurumLED(durumKod)
            if _exec:
                _exec = json.loads(_exec) if isinstance(_exec, str) else _exec
                actions = _exec if _exec and isinstance(_exec, dict) and not bool(_exec.get('isError')) else None
                if actions:
                    print(f'actionsCheck interrupt: {json.dumps(_exec)}')
                    if isinstance(actions, list):
                        actions = { 'actions': _exec }
                    localIP = ip2Str(local.ip); targetIP = actions.get('ip')
                    actions = actions.get('actions')
                    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
                        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
                        actions = None
                if actions:
                    await actionsExec(actions)
                
            return True
    except Exception as ex:
        print("[ERROR] wsStatus:", ex)
        print_exception(ex)
    return False
async def actionsCheckAndExec():
    # print('actionsCheckAndExec')
    actions = await actionsCheck()
    await actionsExec(actions)
async def actionsCheck():
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
    try:
        resp = await ws.wsTalk('readTemp', args={ 'key': 'mes-py', 'stream': True }, timeout=.02)
    except (OSError, RuntimeError) as ex:
        resp = None
    except Exception as ex:
        print('[ERROR]', 'APP wsRecv:', ex)
        print_exception(ex)
    if not resp or (isinstance(resp, dict) and bool(resp.get('isError'))):
        return None
    print(f'actionsCheck interrupt: {json.dumps(resp)}')
    if isinstance(resp, list): resp = { 'actions': resp }
    targetIP = resp.get('ip'); _actions = resp.get('actions')
    if _actions:
        actions = _actions
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
            busy()
            result = handler(*args)                                                                                     # ← [js]  handler.call(this, ...args) karşılığı
            if callable(result):
                result = result(*args)
            try: result = await result
            except: pass
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            # await ws.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True
async def processQueues():
    queue = shared.queues.key
    if not queue:
        return
    recs = []; count = 0
    while queue:
        # key, rfid, duration, ts, tsDiff, released
        rec = queue.pop()
        key, rfid, duration, ts, _, released = rec
        if not (key and ts):
            continue
        tsDiff = round(ticks_diff(ticks_ms(), ts))
        recs.append( (key, rfid, duration, ts, tsDiff, released) )
        count += 1
    if not count:
        return
    print(f'[DEBUG]  {count} keys ready to process')
    for rec in recs:
        # key, rfid, duration, ts, tsDiff, released
        _, _, _, _, _,released = rec
        func = getattr(shared, '_onKeyReleased' if released else '_onKeyPressed')
        async def _clear():
            await asleep(.5)
            lcd.writeIfReady('        ', lcd.getRows() - 1, lcd.getCols() - 8)
        async_task(_clear)
        try:
            result = func(rec)
            if hasattr(result, '__await__'):
                result = await result
        except Exception as ex:
            print_exception(ex)
def keyQueue_push(item):
    queue = shared.queues.key
    if not queue:
        queue = shared.queues.key = RingBuffer()
    queue.push(item)
def keyQueue_pop(take=None):
    queue = shared.queues.key
    if not queue:
        return None
    take = taken = take or 1
    last = None
    while queue and taken > 0:
        last = queue.pop()
        taken -= 1
    return last
def keyQueue_clear():
    queue = shared.queues.key
    if queue:
        queue.clear()

async def updateDurumLED(durumKod):
    durumKod2Renk = {
        '': 'SIYAH',
        'DV': 'YESIL', 'DR': 'SARI',
        'BK': 'BEYAZ', 'AT': 'MAVI',
        'MK': 'MAVI'
    }
    renk = durumKod2Renk.get(durumKod)
    if renk:
        led.write(renk)
async def onKeyPressed(rec):
    key,_,_,_,_,_ = rec
    part = activePart()
    return part.onKeyReleased(key, None) if part else await onKeyPressed_defaultAction(rec)
    # return part.onKeyPressed(key) if part else await onKeyPressed_defaultAction(key)
async def onKeyReleased(rec):
    await onKeyReleased_defaultAction(rec)
    # part = activePart()
    # return part.onKeyReleased(key, duration) if part else await onKeyReleased_defaultAction(key, duration)

async def onKeyPressed_defaultAction(rec):
    key, rfid, duration, ts, tsDiff, _ = rec
    print(f'{key} press')
    key = key.lower(); lastTime = shared.lastTime._keyPress
    shared.lastTime._keyPress = monotonic()
    if lastTime and ticks_diff(ticks_ms(), lastTime) < 100:
        return False
    # delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcd.writeIfReady(f'[{key}]', lcd.getRows() - 1, lcd.getCols() - 8)
    shared.lastTime._keySend = monotonic()
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
            # if not await ws.wsTalk('fnIslemi', args={ 'id': _id, 'delayMS': duration }, timeout=1):
            args = { 'id': _id, 'duration': None, 'ts': ts, 'tsDiff': tsDiff, 'released': False }
            if not await ws.wsTalk('fnIslemi', args=args):
                raise RuntimeError()
            await buzzer.beep(3000, .2)
            # lcd.writeLineIfReady(f'* [{key}] GITTI', 2, 0)
        except Exception as ex:
            # lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)
            print_exception(ex)
            # lcd.writeLineIfReady(f'[{key}] KUYRUGA', 2, 1)
            # keyQueue_push({  'ts': monotonic(), 'id': _id, 'delayMS': duration })
            item = (
                # key, rfid, duration, ts, tsDiff, released
                _id, rfid, duration, ticks_ms(), None, False
            )
            keyQueue_push(item)
            await buzzer.beep(500, 1)
        finally:
            await wsCheckStatusIfNeed()
    return True
async def onKeyReleased_defaultAction(rec):
    key, _, duration = rec
    print(f'{key} released | duration = {duration}')
    key = key.lower(); lastTime = shared.lastTime._keyRelease
    shared.lastTime._keyRelease = monotonic()
    if lastTime and ticks_diff(ticks_ms(), lastTime) < 50:
        return False
    if key == 'esc' and duration >= 2:
        from app import reboot
        reboot()
    return True
