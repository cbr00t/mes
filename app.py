from common import *
from config import local, server, hw as srv
from update import *
from menu import SubMenu, MenuItem
from app_infoPart import *
from app_menus import *

async def init():
    global aborted, localIP, srvIP, srvPort, dev, wifi, ws
    global lcd, led, keypad, rfid, buzzer, h
    localIP = ip2Str(local.ip); srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawwset: [{srvIP}:{srvPort}]')
    aborted = False
    dev = initDevice(); h = initHandlers()
    wifi = dev.wifi; lcd = dev.lcd; led = dev.led;
    ws = dev.ws; keypad = dev.keypad;
    rfid = dev.rfid; buzzer = dev.buzzer
    shared._onKeyPressed = onKeyPressed
    shared._onKeyReleased = onKeyReleased
    
async def run():
    global aborted
    lcd.off().on(); lcd.clearIfReady()
    
    led.write('SIYAH')
    for i in range(0, 2):
        led.clear()
        buzzer.beep(4000, .08)
        led.write('MOR')
        sleep(.01);
    buzzer.beep(4000, .3)
    # sleep(.02); led.clear()
    print('app started')
    
    if ws.isConnected():
        ws.close()
    
    async def init_core1():
        await asleep(10)
        gc.collect()
        thread(threadProc)
        led.write('CYAN')
    
    async_task(init_core1)
    while not aborted:
        try:
            await loop()
        except KeyboardInterrupt as ex:
            aborted = True
            print("\n[core0] stopped by user (KeyboardInterrupt)")
            sleep(.5)
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)
    led.write('TURUNCU')
    lcd.clear(); lcd.write('SHUTDOWN', 1,1)
    await ws.close()

def threadProc():
    global aborted
    global_wait = local.threadLoop_globalWait_ms
    wait_keypad = hw.keypad.scan_interval_ms
    wait_rfid = hw.rfid.scan_interval_ms
    if isLocalPy():
        if wait_keypad:
            wait_keypad += hw.keypad.simulation_interval_ms
        if wait_rfid:
            wait_rfid += hw.rfid.simulation_interval_ms
    _now = ticks_ms(); lastTS_keypad = _now; lastTS_rfid = _now
    gc.collect()
    while not aborted:
        katsayi = 5 if isIdle() else 1
        sleep_ms(global_wait * katsayi)
        try:
            if keypad is not None and wait_keypad and \
                    ticks_diff(ticks_ms(), lastTS_keypad) >= (wait_keypad * katsayi):
                try: keypad.update()
                finally: lastTS_keypad = ticks_ms()
            # print(f'[core1]  keypad_trigger_diff: [{ticks_diff(ticks_ms(), lastTS_keypad)}]')
            if rfid is not None and wait_rfid and \
                    ticks_diff(ticks_ms(), lastTS_rfid) >= (wait_rfid * katsayi):
                try: rfid.update()
                finally: lastTS_rfid = ticks_ms()
        except KeyboardInterrupt as ex:
            aborted = True
            print("\n[core1] stopped by user (KeyboardInterrupt)")
            return
        except Exception as ex:
            print('[ERROR]', ex)
            print_exception(ex)
    print("\n[core1] stopped by abort signal")

async def loop():
    waitMS = 200
    if isIdle():
        waitMS *= 5
    await asleep_ms(waitMS)
    await processQueues()
    if not (await wifiCheck() and await connectToServerIfNot()):
        return
    if not shared._updateCheckPerformed:
        await updateFiles()
    # rfid.update(); keypad.update()
    await wsCheckStatusIfNeed()
    await processQueues()
    # lcd.writeStatus('z' if isIdle() else ' ', 1)
    if not lcdIsBusy():
        await updateMainScreen()
        # rfid.update(); keypad.update()
    if not lcdIsBusy():
        await processQueues()

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
    lcd.write('GUNCELLENIYOR...   ', 3, 2)
    await asleep_ms(50); srv.autoUpdate = True
    await updateFiles()
    reboot()
def reboot():
    if isMicroPy(): import machine
    print('rebooting...')
    lcd.write('REBOOTING...    ', 3, 2)
    sleep_ms(50)
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
    if not lcdIsBusy() and (not lastTime.wifiCheckMsg or ticks_diff(ticks_ms(), lastTime.wifiCheckMsg) >= 5_000):
        # lcd.clearLineIfReady(range(1, 3))
        lcd.writeLineIfReady('WiFi bekleniyor...', 1, 0)
        lastTime.wifiCheckMsg = ticks_ms()
    return False
async def connectToServerIfNot():
    lastTime = shared.lastTime
    if ws.isConnected():
        shared._appReady = True 
        lastTime.srvConnectMsg = None
        return True
    shared._appTitleRendered = False
    lastTime.updateMainScreen = shared._updateMainScreen_lastDebugText = None
    if not await wifiCheck():
        shared._appReady = False
        lcd.writeStatus('x', -1)
        return False
    shared._inActionsCheck = False; lastTime = shared.lastTime
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    if not lcdIsBusy() and (not lastTime.srvConnectMsg or ticks_diff(ticks_ms(), lastTime.srvConnectMsg) >= 5_000):
        lcd.writeLineIfReady('SUNUCUYA BAGLAN:', 1, 0)
        lcd.writeLineIfReady(f'{srvIP}:{srvPort}', 2, 1)
        lastTime.srvConnectMsg = ticks_ms()
    try:
        result = await ws.open()
        await ws.recv(timeout=.1)
        await ws.wsTalk('ping')
        shared._appReady = True
        led.write('MAVI')
        return result
    except Exception as ex:
        print('[ERROR]', ex); print_exception(ex)
        shared._appReady = False
        return False

async def updateMainScreen():
    # if True: return False
    if lcdIsBusy():
        return False
    lastTime = shared.lastTime
    if lastTime.updateMainScreen and ticks_diff(ticks_ms(), lastTime.updateMainScreen) < 200:
        return False
    renderAppTitle()
    # if lcdCanBeCleared(): lcd.clearLineIfReady(range(1, lcd.getRows() - 1))
    rec = shared.curStatus
    rec = rec and rec[0] if isinstance(rec, list) else rec if isinstance(rec, dict) else {}
    _rec = {k: v for k, v in rec.items() if 'Sure' not in k}
    def str_val(key):
        return rec.get(key) or ''
    def int_val(key):
        value = rec.get(key) or 0
        return int(value) if isinstance(value, (str, int, float)) else 0
    # text = json.dumps(_rec)
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
    ) if lastTime else None
    if hashStr != shared._updateMainScreen_lastHashStr:
        print(f'status_check cur  hash:  [{hashStr}]')
        print(f'status_check prev hash:  [{shared._updateMainScreen_lastHashStr}]')
        shared._updateMainScreen_lastHashStr = hashStr
        # shared._updateMainScreen_lastDebugText = text
        #  {"isNetMiktar": 15.0, "operNo": 8, "isFireMiktar": 0.0, "siradakiIsSayi": 0, "emirNox": "1688", "sonDurTS": "26.08.2025 17:35:28", "duraksamaKritik": false, "hatID": "030", "aktifCevrimSayisi": 0, "atananIsSayi": 1, "sonIslemTS": "26.08.2025 17:30:27", "sabitDuraksamami": 0, "operAciklama": "CNC DİK TORNA", "emirMiktar": 2.0, "operatorCagrimTS": null, "ip": "192.168.2.50", "onceUretMiktar": 15.0, "durumKod": "DR", "isSaymaSayisi": 1, "oemID": 9762, "urunAciklama": "9-11 KAMPANA İŞLEME", "urunKod": "KAMP01-9-11-6B", "perKod": "AR-GE01", "isSaymaInd": 0, "durNedenKod": "06", "sinyalKritik": true, "emirTarih": "25.06.2025 00:00:00", "sonAyrilmaDk": 5.22611, "perIsim": "ENES VURAL", "oemgerceklesen": 35.0, "onceCevrimSayisi": 15, "isID": 3, "aciklama": "CNC1", "ekBilgi": "", "seq": 1, "oemistenen": 2.0, "id": "CNC01", "durNedenAdi": "AYRILMA", "aktifUretMiktar": 0.0, "isIskMiktar": 0.0, "hatAciklama": "TALASLI IMALAT", "basZamanTS": "26.08.2025 17:30:14", "maxAyrilmaDk": 5.22611}
        if not (lastTime and shared._updateMainScreen_lastUrunKod == urunKod):
            lcd.writeLineIfReady(f"{urunKod}", 0, 0)
        if not (lastTime and shared._updateMainScreen_lastPerKod == perKod):
            lcd.writeLineIfReady(f"{perKod}", 1, 0)
        lcd.writeLineIfReady(f"U:{onceUretMiktar}+{aktifUretMiktar} | S:{isSaymaInd}/{isSaymaSayisi}", 2, 0)
        lcd.writeLineIfReady(f"D:{durumKod} | E:{emirMiktar}", 3, 0)
        lastTime.updateMainScreen = ticks_ms()
        shared._updateMainScreen_lastUrunKod = urunKod
        shared._updateMainScreen_lastPerKod = perKod
    return True
def renderAppTitle():
    # from config import app
    # lcd.writeLineIfReady(f'v{version2Str(app.version)}  ', 0, 0)
    shared._appTitleRendered = True

async def wsCheckStatusIfNeed():
    if not ws.isConnected(): return False
    if not statusShouldBeChecked(): return False
    try:
        await ws.recv(.001)
        rec = None
        try:
            for i in range(0, 5):
                rec = await ws.wsTalk(api='tezgahBilgi', timeout=.5)
                if rec:
                    break
                else:
                    await asleep_ms(10)
        except Exception as ex:
            print(ex)
            print_exception(ex)
        if not rec:
            rec = {
                'urunKod': 'MAKINE TANIMI VEYA', 'perKod': 'BEKLEYEN IS YOK',
                'durumKod': '', 'ledDurum': 'ROSE', '_exec': None
            }
        if rec:
            rec = rec[0] if isinstance(rec, list) else rec
            if rec.get('isError') and bool(rec.get('isError')):
                code = rec.get('code') or rec.get('rc')
                errorText = 'IP-CIHAZ TANIMI YOK' if code == 'invalidMachine' \
                            else rec.get('errorText')
                rec = {
                    'urunKod': errorText, 'perKod': ip2Str(local.ip),
                    'durumKod': '', 'ledDurum': 'ORANGERED', '_exec': None
                }
            shared.curStatus = rec
            ledDurum = rec.get('ledDurum') if isinstance(rec, dict) else None
            durumKod = rec.get('durumKod') if isinstance(rec, dict) else None
            _exec = rec.get('_exec') if isinstance(rec, dict) else None
            print(f'[DEBUG]  urunKod = [{rec.get("urunKod")}] | perKod = [{rec.get("perKod")}]')
            print(f'[DEBUG]  durumKod = [{durumKod}] | ledDurum = [{ledDurum}]')
            print(f'[DEBUG]  _exec = [{_exec}] | ledDurum = [{ledDurum}]')
            if ledDurum:
                led.write(ledDurum or 'SIYAH')
            elif durumKod is not None:
                await updateDurumLED(durumKod)
            shared.lastTime.statusCheck = ticks_ms()            
            if _exec:
                _exec = json.loads(_exec) if isinstance(_exec, str) else _exec
                actions = None
                if not isinstance(_exec, list):
                    actions = _exec if _exec and isinstance(_exec, dict) and not bool(_exec.get('isError')) else None
                if actions:
                    print(f'actionsCheck interrupt: {json.dumps(_exec)}')
                    if isinstance(actions, list):
                        actions = { 'actions': _exec }
                    localIP = ip2Str(local.ip)
                    targetIP = actions.get('ip')
                    actions = actions.get('actions') or actions
                    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
                        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
                        actions = None
                if actions:
                    await actionsExec(actions)
                gc.collect()
            return True
    except Exception as ex:
        print("[ERROR] wsStatus:", ex)
        print_exception(ex)
    return False
async def actionsExec(actions):
    if not actions: return False
    print('  actions=', actions)
    for item in actions:
        busy()
        action = item.get('action') or item.get('cmd')
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
            if iscoroutine(result):
                result = await result
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            print_exception(ex)
            # await ws.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True
async def processQueues():
    queue = shared.queues.key
    if not queue:
        return
    recs = []; count = 0
    while queue:
        # key, rfid, duration, ts, tsDiff, released
        # with queue.lock:
        rec = queue.pop()
        key, rfid, duration, ts, _, released = rec
        if not (key and ts):
            continue
        tsDiff = round(ticks_diff(ticks_ms(), ts))
        recs.append( (key, rfid, duration, ts, tsDiff, released) )
        count += 1
    if not count:
        return
    print('[DEBUG]  ', f'{count} keys ready to process')
    async def _clear():
        await asleep_ms(200)
        lcd.writeIfReady('        ', lcd.getRows() - 1, lcd.getCols() - 8)
    for rec in recs:
        # key, rfid, duration, ts, tsDiff, released
        key, rfid, _, _, _,released = rec
        func = shared._onKeyReleased if released else shared._onKeyPressed
        print('[DEBUG]  ', 'released' if released else 'pressed', f'key: [{key}] | rfid: [{rfid}] | handler: [{func}]')
        async_task(_clear)
        busy()
        try:
            result = func(rec)
            if iscoroutine(result):
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
    key = rec[0]
    part = activePart()
    if part:
        return part.onKeyReleased(key, None)
    return await onKeyPressed_defaultAction(rec)
    # return part.onKeyPressed(key) if part else await onKeyPressed_defaultAction(key)
async def onKeyReleased(rec):
    return await onKeyReleased_defaultAction(rec)
    # part = activePart()
    # return part.onKeyReleased(key, duration) if part else await onKeyReleased_defaultAction(key, duration)

async def onKeyPressed_defaultAction(rec):
    key, rfid, duration, ts, tsDiff, _ = rec
    key = key.lower(); appReady = shared._appReady
    print(f'{key} press', f' [appReady={appReady}]')
    lcd.writeIfReady(f'[{key}]', lcd.getRows() - 1, lcd.getCols() - 8)
    if key == 'f1':
        DeviceInfoPart().run()
    elif appReady and key == 'f2':
        mnu = getMenu_duraksamaNedenleri()
        if mnu: mnu.run()
    # elif key == 'x':
    #    from part_input import InputPart
    #    InputPart(_title = 'Input Test', _val = 'cik').run()
    elif appReady:
        _id = 'secondary' if key == 'enter' else key
        try:
            if not ws.isConnected():
                return False
            args = { 'id': _id, 'duration': None, 'ts': ts, 'tsDiff': tsDiff, 'released': False }
            if not await ws.wsSend('fnIslemi', args=args):
                raise RuntimeError()
            buzzer.beep(4500, .05)
            buzzer.beep(4500, .05)
            # lcd.writeLineIfReady(f'* [{key}] GITTI', 2, 0)
        except Exception as ex:
            # lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)
            print(ex)
            if not isinstance(ex, RuntimeError):
                print_exception(ex)
            # lcd.writeLineIfReady(f'[{key}] KUYRUGA', 2, 1)
            # keyQueue_push({  'ts': monotonic(), 'id': _id, 'delayMS': duration })
            item = (
                # key, rfid, duration, ts, tsDiff, released
                _id, rfid, duration, ticks_ms(), None, False
            )
            keyQueue_push(item)
            buzzer.beep(400, .5)
            buzzer.beep(400, 1)
        finally:
            await wsCheckStatusIfNeed()
    return True
async def onKeyReleased_defaultAction(rec):
    key, _, duration = rec
    print(f'{key} released | duration = {duration}')
    key = key.lower();
    if key == 'esc' and duration >= 2:
        from app import reboot
        reboot()
    return True
