from time import sleep
import json
from common import *
from config import local, server as srv
import core
from appHandlers import AppHandlers

def init():
    global handlers
    handlers = AppHandlers(core.getDevice())

def run():
    handlers.lcdWrite('Sky MES', 0, 0)
    print('app started')
    while True:
        loop()

def loop():
    wsRecv = handlers.wsRecv; wsSend = handlers.wsSend; wsTalk = handlers.wsTalk
    connected = handlers.sockIsConnected()
    if not connected:
        ip = ip2Str(srv.ip); port = srv.rawPort
        handlers.lcdClear()
        handlers.lcdWrite('SUNUCUYA BAGLAN:', 0, 1)
        handlers.lcdWrite(f'{ip}:{port}', 1, 2)
        try:
            handlers.sockOpen(); connected = True
            handlers.lcdClear(); handlers.lcdWrite('KOMUT BEKLENIYOR', 1, 2)
            print('awaiting remote command')
        except Exception as ex:
            connected = False
            print('[ERROR]', ex)
    resp = actions = None
    if connected:
        resp = wsRecv()
    if resp:
        print(f'rawSocket interrupt: {json.dumps(resp)}')
        actions = [resp] if isinstance(resp, dict) else resp
    if actions:
        for item in actions:
            action = item.get('action') or item.get('cmd')
            if not action:
                continue     # bozuk veri
            handler = getattr(handlers, action, None)
            if handler is None:
                print('[ERROR]  no matching handler', action)
                wsSend({ 'isError': True, 'rc': 'invalidAction', 'errorText': f'{action} action gecersizdir' })
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
                wsSend({ 'isError': True, 'rc': 'handlerExecError', 'errorText': f'{action} action calistirilamadi: {ex}' })
    handlers.keypadUpdate()
    sleep(0.1)

def test():
    handlers.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    handlers.sockClose()
