from common import *
from config import local, server as srv, hw
import core
from appHandlers import AppHandlers
from time import sleep, monotonic
import json
import traceback

def init():
    global handlers, localIP
    localIP = ip2Str(local.ip)
    handlers = AppHandlers(core.getDevice())

def run():
    handlers.lcdClear(); handlers.lcdWrite('Sky MES', 0, 0)
    print('app started')
    if handlers.sockIsConnected():
        handlers.sockClose()
    while True:
        try:
            loop()
        except Exception as ex:
            print('[ERROR]', 'APP LOOP:', ex)
            traceback.print_exception(ex)

def loop():
    wsRecv = handlers.wsRecv; wsSend = handlers.wsSend;
    wsTalk = handlers.wsTalk; lcdWrite = handlers.lcdWrite; lcdClear = handlers.lcdClear
    lcdCfg = hw.lcd
    if handlers._lcdStatus_lastTime and (monotonic() - handlers._lcdStatus_lastTime) > 5:
        lcdWrite(' ' * lcdCfg.cols, 2, 0)
        handlers._lcdStatus_lastTime = None
    hearbeatInterval = getHeartbeatInterval()
    if (hearbeatInterval or 0) <= 0:
        hearbeatInterval = None
    connected = handlers.sockIsConnected()
    if hearbeatInterval and monotonic() - (handlers._lastHeartbeatTime or 0) > hearbeatInterval:
        handlers.wsHeartbeat()
        connected = handlers.sockIsConnected()
    # print('sock isConnected:', connected)
    if not connected:
        ip = ip2Str(srv.ip); port = srv.rawPort
        if handlers._lcdStatus_lastTime and (monotonic() - handlers._lcdStatus_lastTime) > 5:
            for i in range(1, 3):
                lcdWrite(' ' * lcdCfg.cols, i, 0)
            handlers._lcdStatus_lastTime = None
        lcdWrite('SUNUCUYA BAGLAN:', 1, 0)
        lcdWrite(f'{ip}:{port}', 2, 1)
        try:
            handlers.sockOpen(); connected = True
            for i in range(1, 3):
                lcdWrite(' ' * lcdCfg.cols, i, 0)
            lcdWrite('KOMUT BEKLENIYOR', 1, 2)
            print('awaiting remote command')
        except Exception as ex:
            connected = False
            print('[ERROR]', ex)
    resp = targetIP = actions = None
    if connected and not isBusy():
        try:
            resp = wsRecv(0.05)
        except (OSError, RuntimeError) as ex:
            resp = None
        except Exception as ex:
            print('[ERROR]', 'APP sockRecv:', ex)
            traceback.print_exception(ex)
    if resp:
        print(f'rawSocket interrupt: {json.dumps(resp)}')
        if isinstance(resp, list):
            resp = { 'actions': resp }
    if resp:
        targetIP = resp.get('ip'); actions = resp.get('actions')
    if targetIP and targetIP != localIP:                                          # broadcast message match to local ip
        print(f'[IGNORE] broadcast message => targetIP: [{targetIP} | localIP: [{localIP}]')
        actions = None
    if actions:
        for item in actions:
            busy()
            action = item.get('action') or item.get('cmd')
            if not action:
                continue     # bozuk veri
            handler = getattr(handlers, action, None)
            if handler is None:
                print('[ERROR]  no matching handler', action)
                # wsSend('errorCallback', { 'data': f'{action} action gecersizdir' })
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
                # wsSend('errorCallback', { 'data': f'{action} action calistirilamadi: {ex}' })
    handlers.keypadUpdate()
    cpuHaltTime = 0.5 if isIdle() else 0.02
    sleep(cpuHaltTime)

def test():
    handlers.wsTalk('fnIslemi', { 'id': 2, 'ip': local.ip })
    handlers.sockClose()
