from time import sleep, monotonic
import json
from common import *
from config import local, server as srv
import core

class AppHandlers:
    def __init__(self, dev = None):
        self.dev = dev
        self._keypad_lastTime = None
        # sock = dev.sock; req = dev.req
        # lcd = dev.lcd; keypad = dev.keypad
        keypad = dev.keypad
        if keypad is not None:
            keypad.set_onPress(self.keypad_onPressed)
            keypad.set_onRelease(self.keypad_onReleased)
    
    ## Handler API Interface
    def reboot(self):
        import supervisor
        print('rebooting...')
        supervisor.reload()
        return self
    def lcdWrite(self, text, row=0, col=0):
        self.dev.lcd.write(text, row, col)
        return self
    def lcdClear(self):
        self.dev.lcd.clear()
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
        if not (result is None or isinstance(result, (dict, list))):
            result = json.loads(result)
        return result
    def sockTalk(self, data):
        self.sockOpen(); sock = self.dev.sock
        if data is not None and isinstance(data, (dict, list)):
            data = json.dumps(data)
        return sock.talk(data)
    def sockClose(self):
        self.sock.close()
        return self
    def wsSend(self, api, args = None, data = None, wsPath = None):
        return self.sockSend(self.getWSData(api, args, data, wsPath))
    def wsRecv(self, timeout=None):
        return self.sockRecv(timeout)
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        result = self.sockTalk(self.getWSData(api, args, data, wsPath))
        if (isinstance(result, str)):
            result = json.loads(result)
        return result
    def getWSData(self, api, args = None, data = None, wsPath = None):
        if data is not None and isinstance(data, (dict, list)):
            data = json.dumps(data)
        return {
            'ws': wsPath or srv.wsPath, 'api': api, 'args': args,
            'data': { 'base64': False, 'data': data }
        }
    def sockClose(self):
        return self.dev.sock.close()
    def req(self, data, timeout=None):
        return self.dev.req.send(data, timeout)
    def textReq(self, data, timeout=None):
        return self.dev.req.sendText(data, timeout)
    def jsonReq(self, data, timeout=None):
        return self.dev.req.sendJSON(data, timeout)
    def keypadUpdate(self):
        self.dev.keypad.update()
        return self
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
        delayMS = monotonic() - self._keypad_lastTime if self._keypad_lastTime else 0
        self.wsTalk('fnIslemi', { 'id': _id, 'delayMS': delayMS })


