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
        sock.write(data)
        return self
    def sockRecv(self, timeout=None):
        self.sockOpen(); sock = self.dev.sock
        result = sock.read() if timeout is None else sock.read(timeout)
        if result and not isinstance(result, (dict, list)):
            result = json.loads(result)
        return result
    def sockTalk(self, data):
        self.sockOpen(); sock = self.dev.sock
        sock.talk(data)
        return self
    def wsSend(self, api, args = None, data = None, wsPath = None):
        return self.sockSend(self.getWSData(api, args, data, wsPath))
    def wsRecv(self, timeout=None):
        return self.sockRecv(timeout)
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return self.sockTalk(self.getWSData(api, args, data, wsPath))
    def getWSData(self, api, args = None, data = None, wsPath = None):
        return {
            'ws': wsPath or srv.wsPath, 'api': api, 'args': args,
            'data': { 'base64': False, 'data': data }
        }
    def sockClose(self):
        return self.sock.close()
    def req(self, data):
        self.dev.req.send(data)
    def textReq(self, data):
        self.dev.req.sendText(data)
        return self
    def jsonReq(self, data):
        self.dev.req.sendJSON(data)
        return self
    def keypadUpdate(self):
        self.dev.keypad.update()
        return self
    def checkStatus(self):
        pass
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


