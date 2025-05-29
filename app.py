from time import sleep
import json
from common import *
from config import local
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
    recv = handlers.sockRecv; send = handlers.sockSend
    if not handlers.sockIsConnected():
        handlers.sockOpen()
        handlers.lcdWrite('KOMUT BEKLENIYOR', 1, 2)
        print('awaiting remote command')
    resp = recv(); actions = None
    if resp:
        if isinstance(resp, str):
            resp = json.loads(resp)
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
                send(json.dumps({
                    'isError': True, 'rc': 'invalidAction',
                    'errorText': f'{action} action gecersizdir'
                }))
                continue
            args = []
            if 'args' in item:
                _args = item['args']
                # Eğer args bir listeyse direkt ekle, değilse tek öğe olarak al
                if isinstance(_args, list): args.extend(_args)
                else: args.append(_args)
            try:
                handler(*args)   # ← JavaScript’teki handler.call(this, ...args) karşılığı budur
            except Exception as ex:
                print(f'[ERROR]  handler execution failed: {ex}')
                send(json.dumps({
                    'isError': True,
                    'rc': 'handlerExecError',
                    'errorText': f'{action} action calistirilamadi: {ex}'
                }))
    handlers.keypadUpdate()
    sleep(0.1)

def test():
    handlers.talk(json.dumps({
        'ws':   'ws/skyMES/makineDurum',
        'api':  'fnIslemi',
        'qs': { 'id': 2, 'ip': local.ip }
    }))
    handlers.sockClose()
