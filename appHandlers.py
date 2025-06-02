from common import *
from config import local, server as srv
from time import sleep, monotonic
import json
from traceback import print_exception

class AppHandlers:
    def __init__(self):
        dev = self.dev = shared.dev
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
    def ethIsConnected(self):
        return self.dev.eth.isConnected()
    def sockIsConnected(self):
        return self.dev.sock.isConnected()
    def sockOpen(self, statusCheckMessage=None):
        self.dev.sock.open()
        return self
    def sockSend(self, data):
        self.dev.sock.send(data)
        return self
    def sockRecv(self, timeout=None):
        return self.dev.sock.recv(timeout)
    def sockTalk(self, data, timeout=None):
        return self.dev.sock.talk(data, timeout)
    def sockSendJSON(self, data):
        self.dev.sock.sendJSON(data)
        return self
    def sockRecvJSON(self, timeout=None):
        return self.dev.sock.recvJSON(timeout)
    def sockTalkJSON(self, data, timeout=None):
        return self.dev.sock.talkJSON(data, timeout)
    def sockClose(self):
        self.sock.close()
        return self
    def wsSend(self, api, args = None, data = None, wsPath = None):
        self.dev.sock.wsSend(api, args, data, wsPath)
        return self
    def wsRecv(self, timeout=None):
        return self.dev.sock.wsRecv(timeout)
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return self.dev.sock.wsTalk(api, args, data, wsPath, timeout)
    def wsHeartbeat(self, timeout=None):
        return self.dev.sock.wsHeartbeat(timeout)
    def getWSData(self, api, args = None, data = None, wsPath = None):
        return getWSData(api, args, data, wsPath)
    def sockClose(self):
        return self.dev.sock.close()
    def req(self, data, timeout=None):
        return self.dev.req.send(data, timeout)
    def textReq(self, data, timeout=None):
        return self.dev.req.sendText(data, timeout)
    def jsonReq(self, data, timeout=None):
        return self.dev.req.sendJSON(data, timeout)
    def lcdWrite(self, text, row=0, col=0):
        self.dev.lcd.write(text, row, col)
        return self
    def lcdClearLine(self, row):
        lcd = self.dev.lcd
        if isinstance(row, (list, range)):
            for _row in row:
                lcd.clearLine(_row)
        else:
            lcd.clearLine(row)
        return self
    def lcdClear(self):
        self.dev.lcd.clear()
        return self
    def ledWrite(self, rgb, col=0):
        self.dev.led.write(rgb, col)
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
    
    # status checks
    def lcdIsBusy(self):
        return lcdIsBusy()
    def lcdCanBeCleared(self):
        return lcdCanBeCleared()
    def heartbeatShouldBeChecked():
        return heartbeatShouldBeChecked()
    
    ## Event Handlers
    def keypad_onPressed(self, key):
        print(f'key_press: [{key}]')
        handler = shared._onKeyPressed
        if handler is not None: handler(key)
    def keypad_onReleased(self, key, duration):
        print(f'key_release: [{key}:{duration}]')
        handler = shared._onKeyReleased
        if handler is not None: handler(key)

