from time import sleep, monotonic
import json
from common import *
from config import local, server as srv
import core

class AppHandlers:
    def __init__(self, dev = None):
        self.dev = dev
        self._lcdStatus_lastTime = self._ledStatus_lastTime = None
        self._keypad_lastTime = self._lastHeartbeatTime = None
        # sock = dev.sock; req = dev.req
        # lcd = dev.lcd; keypad = dev.keypad
        keypad = dev.keypad
        if keypad is not None:
            keypad.set_onPress(self.keypad_onPressed)
            keypad.set_onRelease(self.keypad_onReleased)
    
    ## Handler API Interface
    def exec(self, code):
        result = exec(code, globals())
        return result
    def reboot(self):
        import microcontroller
        print('rebooting...')
        microcontroller.reset()
        return self
    def sockIsConnected(self):
        return self.dev.sock.isConnected()
    def sockOpen(self, statusCheckMessage=None):
        sock = self.dev.sock
        if (not sock.isConnected()):
            sock.open()
            payload = statusCheckMessage or self.getWSData('getSessionInfo')
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)
            sock.talk(payload)
        return self
    def sockSend(self, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        self.sockOpen(); sock = self.dev.sock
        if data is not None and isinstance(data, (dict, list)):
            data = json.dumps(data)
        sock.write(data)
        return self
    def sockRecv(self, timeout=None):
        self.sockOpen(); sock = self.dev.sock
        result = sock.read() if timeout is None else sock.read(timeout)
        if result:
            print('[sockRecv]  data:', result)
            self._lastHeartbeatTime = monotonic()                                  # basarili bir veri alimi olduysa baglanti gecerlidir, sonra kontrol et
        return result
    def sockTalk(self, data, timeout=None):
        self.sockSend(data).sockRecv(data)
    def sockClose(self):
        self.sock.close()
        return self
    def wsSend(self, api, args = None, data = None, wsPath = None):
        return self.sockSend(self.getWSData(api, args, data, wsPath))
    def wsRecv(self, timeout=None):
        result = self.sockRecv(timeout)
        if not (result is None or isinstance(result, (dict, list))):
            if result and isinstance(result, str):
                for check in [('{', '}'), ('[', ']')]:
                    if not result.startswith(check[0]) and result.endswith(check[1]):
                        result = check[0] + result
                    elif result.startswith(check[0]) and not result.endswith(check[1]):
                        result += check[1]
            result = json.loads(result)
        return result
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return self.wsSend(api, args, data, wsPath).wsRecv(timeout)
    def wsHeartbeat(self, timeout=None):
        try:
            if (self._lastHeartbeatTime or False) <= 0:                   # no check at startup
                return True
            result = self.wsTalk('ping')
            print('[wsHeartbeat] ', result)
            if not result:
                raise RuntimeError('empty data')
            return True
        except Exception:
            self.sockClose()
            self.sockOpen()
            return False
        finally:
            self._lastHeartbeatTime = monotonic()
    def getWSData(self, api, args = None, data = None, wsPath = None):
        if data is not None and isinstance(data, (dict, list)):
            data = json.dumps(data)
        return {
            'ws': wsPath or srv.wsPath, 'api': api, 'args': args,
            'data': { 'data': data }
        }
    def sockClose(self):
        return self.dev.sock.close()
    def req(self, data, timeout=None):
        return self.dev.req.send(data, timeout)
    def textReq(self, data, timeout=None):
        return self.dev.req.sendText(data, timeout)
    def jsonReq(self, data, timeout=None):
        return self.dev.req.sendJSON(data, timeout)
    def lcdWrite(self, text, row=0, col=0):
        self._lcdStatus_lastTime = monotonic()
        self.dev.lcd.write(text, row, col)
        return self
    def lcdClear(self):
        self.dev.lcd.clear()
        return self
    def ledWrite(self, rgb, col=0):
        self.dev.led.write(rgb, col)
        self._ledStatus_lastTime = monotonic()
        return self
    def ledClear(self):
        self.dev.led.clear()
        return self
    def keypadUpdate(self):
        self.dev.keypad.update()
        return self
    def rfidRead(self):
        return self.dev.rfid.read()
    def checkStatus(self):
        return self
    def updateStatus(self, result):
        if result is not None:
            print(json.dumps(result))

    ## Event Handlers
    def keypad_onPressed(self, key):
        self._keypad_lastTime = monotonic()
        print(f'key_press: [{key}]')
    def keypad_onReleased(self, key, duration):
        print(f'key_release: [{key}:{duration}]')
        key = key.lower()
        _id = 'primary' if key == '0' or key == 'enter' else key
        delayMS = int((monotonic() - self._keypad_lastTime) * 1000) if self._keypad_lastTime else 0
        busy()
        self.lcdWrite(' ' * 20, 2, 0); self.lcdWrite(f'TUS GONDER: [{key}]...', 2, 1)
        result = self.wsTalk('fnIslemi', { 'id': _id, 'delayMS': delayMS })
        self.lcdWrite(' ' * 20, 2, 0); self.lcdWrite(f'* [{key}] GITTI', 2, 0)
        return None


