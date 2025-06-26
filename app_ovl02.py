from common import *
from config import local
from menu import SubMenu, MenuItem
from app_infoPart import *
from app_menus import *
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
        # lcd.clearLineIfReady(range(1, 3));
        # lcd.writeIfReady('KOMUT BEKLENIYOR', 1, 2)
        print('awaiting remote command')
        shared._inActionsCheck = True
    resp = targetIP = actions = None
    timeout = 0.05 if shared.lastTime._keySend and monotonic() - shared.lastTime._keySend < 3 else 0.2
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
            sleep(0.01); busy()
            handler(*args)                                                                                     # ← [js]  handler.call(this, ...args) karşılığı
        except Exception as ex:
            print(f'[ERROR]  handler execution failed: {ex}')
            # sock.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    return True


def onKeyPressed(key):
    part = activePart()
    return part.onKeyPressed(key) if part else onKeyPressed_defaultAction(key)
def onKeyReleased(key, duration):
    part = activePart()
    return part.onKeyReleased(key, duration) if part else onKeyReleased_defaultAction(key, duration)

def onKeyPressed_defaultAction(key):
    return True
def onKeyReleased_defaultAction(key, duration):
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock; keypad = dev.keypad
    lastTime = shared.lastTime._keySend; key = key.lower()
    if lastTime and monotonic() - lastTime <= 0.8: return False
    lastTime = keypad._lastKeyPressTime; delayMS = int((monotonic() - lastTime) * 1000) if lastTime else 0
    lcdRows = range(2, 3)
    # lcd.clearLineIfReady(lcdRows)
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
            processQueues()
            if not sock.wsTalk('fnIslemi', { 'id': _id, 'delayMS': duration }):
                raise RuntimeError()
            # lcd.writeLineIfReady(f'* [{key}] GITTI', 2, 0)
            sleep(0.1); lcd.clearLineIfReady(lcd.getRows() - 1) 
        except Exception as ex:
            # lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)
            print_exception(ex)
            lcd.writeLineIfReady(f'[{key}] KUYRUGA', 2, 1)
            keyQueue_add({ 'ts': monotonic(), 'id': _id, 'delayMS': duration })
    return True
