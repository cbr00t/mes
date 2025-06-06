from common import *
from config import local
from menu import SubMenu, MenuItem
from app_ovl03 import *
from time import sleep, monotonic
import json
from traceback import print_exception

def actionsCheckAndExec():
    actions = actionsCheck()
    return actionsExec(actions) if actions else False
def actionsCheck():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock
    localIP = ip2Str(local.ip)
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
    targetIP = resp.get('ip'); _actions = resp.get('actions')
    if _actions: actions = _actions
    if targetIP and targetIP != localIP:                                                                        # broadcast message match to local ip
        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
        actions = None
    return actions
def actionsExec(actions):
    if not actions: return False
    print('  actions=', actions)
    dev = shared.dev; lcd = dev.lcd; h = shared.handlers
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
            sleep(0.05); busy()
            handler(*args)                                                                                     # ← [js]  handler.call(this, ...args) karşılığı
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            # sock.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True 

def onKeyPressed(key):
    part = activePart()
    if part:
        result = part.onKeyPressed(key)
        if result: return result
    return onKeyPressed_defaultAction(key)
def onKeyReleased(key, duration):
    part = activePart()
    if part:
        result = part.onKeyReleased(key, duration)
        if result: return result    
    return onKeyReleased_defaultAction(key, duration)

def onKeyPressed_defaultAction(key):
    return True
def onKeyReleased_defaultAction(key, duration):
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock; keypad = dev.keypad
    lastTime = shared.lastTime._keySend; key = key.lower()
    if lastTime and monotonic() - lastTime <= 0.8: return False
    lastTime = keypad._lastKeyPressTime; delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcdRows = range(2, 3)
    if not lcdIsBusy():
        lcd.clearLine(lcdRows); lcd.write(f'TUS: [{key}]', 2, 1)
        lcd.write('...', 3, 1)
    lastTime = shared.lastTime._keySend = monotonic()
    if key == '0':
        getMenu('main').run()
    elif key == '3':
        mnu = getMenu_duraksamaNedenleri()
        if mnu: mnu.run()
    elif key == 'x':
        from part_input import InputPart
        InputPart(_title = 'Input Test', _val = 'cik').run()
    else:
        _id = 'secondary' if key == 'enter' else key
        if sock.wsTalk('fnIslemi', { 'id': _id, 'delayMS': delayMS }):
            if not lcdIsBusy():
                lcd.clearLine(lcdRows); lcd.writeIfReady(f'* [{key}] GITTI', 2, 0)
        else:
            if not lcdIsBusy():
                lcd.clearLine(lcdRows); lcd.writeIfReady(f'* WS ILETISIM SORUNU', 2, 0)
    return True
