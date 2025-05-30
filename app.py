from time import sleep, monotonic
import json
from common import *
from config import local, server as srv
import core
from appHandlers import AppHandlers

def init():
    global handlers
    handlers = AppHandlers(core.getDevice())

def run():
    handlers.lcdClear(); handlers.lcdWrite('Sky MES', 0, 0)
    print('app started')
    if handlers.sockIsConnected():
        handlers.sockClose()
    while True:
        loop()

def loop():
    wsRecv = handlers.wsRecv; wsSend = handlers.wsSend; wsTalk = handlers.wsTalk
    _lcdStatus_lastTime = handlers._lcdStatus_lastTime
    if _lcdStatus_lastTime and (monotonic() - _lcdStatus_lastTime) > 5:
        handlers.lcdWrite(' ' * 20, 2, 1)
    hearbeatInterval = getHeartbeatInterval()
    if (hearbeatInterval or 0) <= 0:
        hearbeatInterval = None
    connected = handlers.sockIsConnected()
    if connected and hearbeatInterval:
        if monotonic() - (handlers._lastHeartbeatTime or 0) > hearbeatInterval:
            handlers.wsHeartbeat()
            connected = handlers.sockIsConnected()
    # print('sock isConnected:', connected)
    if not connected:
        ip = ip2Str(srv.ip); port = srv.rawPort
        for i in range(1, 3):
            handlers.lcdWrite(' ' * 20, i, 0)
        handlers.lcdWrite('SUNUCUYA BAGLAN:', 1, 0)
        handlers.lcdWrite(f'{ip}:{port}', 2, 1)
        try:
            handlers.sockOpen(); connected = True
            for i in range(1, 3):
                handlers.lcdWrite(' ' * 20, i, 0)
            handlers.lcdWrite('KOMUT BEKLENIYOR', 1, 2)
            print('awaiting remote command')
        except Exception as ex:
            connected = False
            print('[ERROR]', ex)
    resp = actions = None
    if connected:
        try:
            resp = wsRecv(0.1)
        except (OSError, RuntimeError) as ex:
            resp = None
    if resp:
        print(f'rawSocket interrupt: {json.dumps(resp)}')
        actions = [resp] if isinstance(resp, dict) else resp
    if actions:
        for item in actions:
            busy()
            action = item.get('action') or item.get('cmd')
            if not action:
                continue     # bozuk veri
            handler = getattr(handlers, action, None)
            if handler is None:
                print('[ERROR]  no matching handler', action)
                wsSend('errorCallback', { 'data': f'{action} action gecersizdir' })
                continue
            args = []
            if 'args' in item:
                _args = item['args']
                # Eğer args bir listeyse direkt ekle, değilse tek öğe olarak al
                if isinstance(_args, list): args.extend(_args)
                else: args.append(_args)
            try:
                handler(*args)                                                    # ← [js]  handler.call(this, ...args) karşılığı
            except Exception as ex:
                print(f'[ERROR]  handler execution failed: {ex}')
                wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    handlers.keypadUpdate()
    cpuHaltTime = 0.5 if isIdle() else 0.1
    sleep(cpuHaltTime)

def test():
    handlers.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    handlers.sockClose()
