from common import *
from config import app, local, server as srv, hw
from part import *
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
    cpuHaltTime = 0.2 if isIdle() else 0.01; sleep(cpuHaltTime)
    if not shared._appTitleRendered: renderAppTitle()
    if lcd._lastWriteTime: lcd.clearLineIfReady(2)
    # gc.collect()
    keypad.update()
    sock.wsHeartbeatIfNeed()
    if connectToServerIfNot():
        if not shared._updateCheckPerformed:
            updateFiles()
            lcd.clearIfReady(); renderAppTitle()
    actionsCheckAndExec()
    keypad.update()


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
def ethCheck():
    if eth.isConnected(): return True
    lcd.clearLineIfReady(1); lcd.writeIfReady('Ethernet bekleniyor...', 1, 1)
    return False
def ethWait():
    while not checkEth():
        sleep(0.05)
def connectToServerIfNot():
    if sock.isConnected(): return True
    if not ethCheck(): return False
    shared._inActionsCheck = False
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
    lcd.clearLineIfReady(0)
    lcd.writeIfReady(f'{app.name} v{version2Str(app.version)}', 0, 0)
    shared._appTitleRendered = True

def actionsCheckAndExec():
    actions = actionsCheck()
    return actionsExec(actions) if actions else False
def actionsCheck():
    # print(f'    connected = {connected} | shared._inActionsCheck = {shared._inActionsCheck}')
    if not sock.isConnected():
        shared._inActionsCheck = False
        if not lcdIsBusy(): lcd.clearLine(1)
        return None
    if not shared._inActionsCheck:
        if not lcdIsBusy(): lcd.clearLine(range(1, 3));
        lcd.writeIfReady('KOMUT BEKLENIYOR', 1, 2); print('awaiting remote command')
        shared._inActionsCheck = True
    resp = targetIP = actions = None
    timeout = 0.5 if shared.lastTime._keySend and monotonic() - shared.lastTime._keySend < 1 else 0.05
    try: resp = sock.wsRecv(timeout)
    except (OSError, RuntimeError) as ex: resp = None
    except Exception as ex: print('[ERROR]', 'APP sockRecv:', ex); print_exception(ex)
    if not resp: return None
    print(f'rawSocket interrupt: {json.dumps(resp)}')
    if isinstance(resp, list): resp = { 'actions': resp }
    targetIP = resp.get('ip'); actions = resp.get('actions')
    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
        actions = None
    return actions
def actionsExec(actions):
    if not actions: return False
    print('  actions=', actions)
    for item in actions:
        busy(); action = item.get('action') or item.get('cmd')
        print('<< action:', action)
        if not action: continue 
        handler = getattr(shared.handlers, action, None)
        if handler is None:
            print('[ERROR]  no matching handler', action)
            continue
        args = []
        if 'args' in item: args = item['args']                                                                 # Eğer args bir listeyse direkt ekle, değilse tek öğe olarak al
        else: args.append(_args)
        print('<<     action args:', args)
        try:
            sleep(0.05); busy()
            handler(*args)                                                                                     # ← [js]  handler.call(this, ...args) karşılığı
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            # sock.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True 

def onKeyPressed_defaultAction(key):
    return True
def onKeyReleased_defaultAction(key, duration):
    lastTime = shared.lastTime._keySend
    if lastTime and monotonic() - lastTime <= 0.8: return False
    key = key.lower();
    _id = 'primary' if key == '0' or key == 'enter' else key
    lastTime = keypad._lastKeyPressTime
    delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcdRows = range(2, 3)
    if not lcdIsBusy():
        lcd.clearLine(lcdRows); lcd.write(f'TUS: [{key}]', 2, 1)
        lcd.write('...', 3, 1)
    shared.lastTime._keySend = monotonic()
    if sock.wsTalk('fnIslemi', { 'id': _id, 'delayMS': delayMS }):
        if not lcdIsBusy():
            lcd.clearLine(lcdRows); lcd.writeIfReady(f'* [{key}] GITTI', 2, 0)
    else:
        if not lcdIsBusy():
            lcd.clearLine(lcdRows); lcd.writeIfReady(f'* WS ILETISIM SORUNU', 2, 0)
    return True

def onKeyPressed(key):
    part = activePart()
    if part:
        result = part.onKeyPressed(key, duration)
        if result: return result
    return onKeyPressed_defaultAction(key)
def onKeyReleased(key, duration):
    part = activePart()
    if part:
        result = part.onKeyReleased(key, duration)
        if result: return result    
    return onKeyReleased_defaultAction(key, duration)


def updateFiles():
    from os import rename, remove
    shared._updateCheckPerformed = True
    autoUpdate = srv.autoUpdate; urls = getUpdateUrls()
    if autoUpdate is None: autoUpdate = shared.updateCheck != False
    if autoUpdate is None: autoUpdate = False
    if not (autoUpdate and urls):
        return False
    
    lcd.clearLineIfReady(1)
    lcd.writeIfReady('UPDATE CHECK', 1, 1)
    url = None; lastError = None
    for _url in urls:
        if not _url: continue
        try:
            resp = sock.wsTalk('webRequest', None, { 'url': f'{_url}/files.txt' }); print(f'<< resp', resp)
            resp = resp['data']['string'] if isinstance(resp, dict) else None
            # Update List yok ise: oto-update iptal
            if not resp or 'not found' in resp.lower():
                print('[INFO]', "'files.txt' not found, skipping...")
                continue
            url = _url; lastError = None
            break
        except Exception as ex:
            lastError = ex; print(f'[ERROR]', ex)
            continue
    if lastError:
        print('[ERROR]', lastError); print_exception(lastError)
    if lastError or not url:
        return False
    for name in resp.split('\n'):
        name = name.strip()
        if not name: continue
        try:
            busy(); fileUrl = f'{url}/{name}'
            lcd.clearIfReady(); lcd.write('UPDATING:', 0, 0)
            lcd.writeIfReady(name, 1, 2)
            # Uzak Dosyayı indir
            fileContent = sock.wsTalk('webRequest', None, { 'url': fileUrl })
            fileContent = fileContent['data']['string'] if isinstance(fileContent, dict) else None
            # fileContent = textReq(fileUrl)
            # Yanıt boş veya yok ise sonrakine geç
            if not fileContent or 'Not found' in fileContent:
                print('  ... NOT FOUND')
                continue
            if fileContent and splitext(name)[1] == '.py':
                fileContent = fileContent.rstrip() + '\n'
            print(f'<< [{fileUrl}]')
            localFile = name; localBackupFile = f'{name}.bak'
            # Eğer önceki yedek varsa sil
            if exists(localBackupFile):
                remove(localBackupFile)
            # Önceki dosya varsa yedeğini oluştur
            if exists(localFile):
                rename(localFile, localBackupFile)
            # Yeni içerikle dosyayı yaz
            with open(localFile, 'w') as f:
                f.write(fileContent)
            print('  ... UPDATED')
        except Exception as ex:
            print('[ERROR]', ex); print_exception(ex)
            continue
    return True

def test():
    h.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    h.sockClose()

