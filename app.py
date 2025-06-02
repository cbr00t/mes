from common import *
from config import app, local, server as srv, hw
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
    sock.close()
def loop():
    global cpuHaltTime
    cpuHaltTime = 0.3 if isIdle() else 0.01; sleep(cpuHaltTime)
    if not shared._appTitleRendered: renderAppTitle()
    if lcd._lastWriteTime: lcd.clearLineIfReady(2)
    gc.collect()
    if connectToServerIfNot():
        if not shared._updateCheckPerformed: updateFiles()
        actionsCheckAndExec()
        sock.wsHeartbeatIfNeed()
    keypad.update()

def test():
    h.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    h.sockClose()

# Initialization
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
    lcd.clearLine(range(1, 3))
    lcd.writeIfReady('SUNUCUYA BAGLAN:', 1, 0)
    lcd.writeIfReady(f'{srvIP}:{srvPort}', 2, 1)
    print(f'connect to: [{srvIP}:{srvPort}]')
    try:
        if sock.open():
            lcd.clearLineIfReady(range(1, 3))
            lcd.writeIfReady('KOMUT BEKLENIYOR', 1, 2)
            print('awaiting remote command')
            return True
    except Exception as ex:
        connected = False
        print('[ERROR]', ex); print_exception(ex)
        return False
def renderAppTitle():
    lcd.clearLineIfReady(0)
    lcd.writeIfReady(f'{app.name} v{version2Str(app.version)}', 0, 0)
    shared._appTitleRendered = True

def updateFiles():
    from os import rename, remove
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
    shared._updateCheckPerformed = true
    return True

def actionsCheck():
    resp = targetIP = actions = None
    if not isBusy() and sock.isConnected:
        try: resp = sock.wsRecv(.1)
        except (OSError, RuntimeError) as ex: resp = None
        except Exception as ex: print('[ERROR]', 'APP sockRecv:', ex); print_exception(ex)
    if resp:
        print(f'rawSocket interrupt: {json.dumps(resp)}')
        if isinstance(resp, list):
            resp = { 'actions': resp }
    if resp:
        targetIP = resp.get('ip')
        actions = resp.get('actions')
    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
        actions = None
    return actions

def actionsExec(actions):
    if not actions:
        return False
    for item in actions:
        actionExec(item)
    return True
def actionsCheckAndExec():
    actions = actionsCheck()
    return actionsExec(actions) if actions else False
def actionExec(item):
    action = item.get('action') or item.get('cmd') if item and isinstance(item, dict) else None
    if not action:
        return False
    handler = getattr(shared.handlers, action, None)
    if handler is None:
        print('[ERROR]  no matching handler', action)
        return False
    args = []
    if 'args' in item:
        _args = item['args']                                                                           # Eğer args bir listeyse direkt ekle, değilse tek öğe olarak al
        if isinstance(_args, list): args.extend(_args)
        else: args.append(_args)
    try:
        handler(*args)                                                                                 # ← [js]  handler.call(this, ...args) karşılığı
        return True
    except Exception as ex:
        print(f'[ERROR]  handler execution failed: {ex}')
        # sock.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
        return False

def onKeyPressed_defaultAction(key):
    return True
def onKeyReleased_defaultAction(key, duration):
    key = key.lower();
    _id = 'primary' if key == '0' or key == 'enter' else key
    lastTime = keypad._lastKeyPressTime
    delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    busy(); self.lcdWrite(' ' * 20, 2, 0); self.lcdWrite(f'TUS GONDER: [{key}]...', 2, 1)
    self.wsSend('fnIslemi', { 'id': _id, 'delayMS': delayMS })
    result = self.wsRecv(0)
    self.lcdWrite(' ' * 20, 2, 0); self.lcdWrite(f'* [{key}] GITTI', 2, 0)
    return True

def onKeyPressed(key):
    part = Part.current()
    if part:
        result = part.onKeyPressed(key, duration)
        if result: return result
    return onKeyPressed_defaultAction(key)
def onKeyReleased(key, duration):
    part = Part.current()
    if part:
        result = part.onKeyReleased(key, duration)
        if result: return result    
    return onKeyReleased_defaultAction(key, duration)
