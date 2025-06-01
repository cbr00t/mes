from common import *
from config import app, local, server as srv, hw
from time import sleep, monotonic
import json
from traceback import print_exception
import gc

def init():
    global localIP, srvIP, srvPort
    localIP = ip2Str(local.ip)
    srvIP = ip2Str(srv.ip); srvPort = srv.rawPort
    print(f'localIP: [{localIP}] | server rawSocket: [{srvIP}:{srvPort}]')

def run():
    dev = shared.dev; sock = dev.sock; lcd = dev.lcd
    if not lcdIsBusy():
        lcd.clear(); lcd.write(f'{app.name} v{version2Str(app.version)}', 0, 0)
    print('app started')
    if sock.isConnected():
        sock.close()
    while True:
        try:
            loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            print_exception(ex)

def loop():
    cpuHaltTime = 0.3 if isIdle() else 0.01
    sleep(cpuHaltTime)
    
    dev = shared.dev; eth = dev.eth; sock = dev.sock
    lcd = dev.lcd; keypad = dev.keypad
    gc.collect()
    if lcdCanBeCleared():
        lcd.clearLine(2)
    connected = sock.isConnected()
    # print('sock isConnected:', connected)
    if not connected:
        if lcdCanBeCleared():
            lcd.clearLine(range(1, 3))
        if not lcdIsBusy():
            lcd.write('SUNUCUYA BAGLAN:', 1, 0)
            lcd.write(f'{srvIP}:{srvPort}', 2, 1)
            print(f'connect to: [{srvIP}:{srvPort}]')
        try:
            sock.wsTalk('ping'); connected = sock.isConnected()
            if connected and not lcdIsBusy():
                lcd.clearLine(range(1, 3))
                lcd.write('KOMUT BEKLENIYOR', 1, 2)
            print('awaiting remote command')
        except Exception as ex:
            connected = False
            print('[ERROR]', ex); print_exception(ex)
    resp = targetIP = actions = None
    if connected and not isBusy():
        try:
            resp = sock.wsRecv(.1)
        except (OSError, RuntimeError) as ex:
            resp = None
            # print('[LOOP SockRecv]', ex)
        except Exception as ex:
            print('[ERROR]', 'APP sockRecv:', ex); print_exception(ex)
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
    if actions:
        for item in actions:
            busy()
            action = item.get('action') or item.get('cmd')
            if not action:
                continue                                                                                        # bozuk veri
            handler = getattr(shared.handlers, action, None)
            if handler is None:
                print('[ERROR]  no matching handler', action)
                # sock.wsSend('errorCallback', { 'data': f'{action} action gecersizdir' })
                continue
            args = []
            if 'args' in item:
                _args = item['args']    # Eğer args bir listeyse direkt ekle, değilse tek öğe olarak al
                if isinstance(_args, list): args.extend(_args)
                else: args.append(_args)
            try:
                handler(*args)                                                                                 # ← [js]  handler.call(this, ...args) karşılığı
            except Exception as ex:
                print(f'[ERROR]  handler execution failed: {ex}')
                # sock.wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    keypad.update()
    if heartbeatShouldBeChecked():
        sock.wsHeartbeat()

def test():
    h = shared.handlers
    h.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    h.sockClose()



