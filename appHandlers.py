from time import sleep
import json
from common import *
from config import local
import core

class AppHandlers:
    def __init__(self, dev = None):
        self.dev = dev
        # sock = dev.sock; req = dev.req
        # lcd = dev.lcd; keypad = dev.keypad
        keypad = dev.keypad
        if keypad is not None:
            keypad.set_onPress(self.keypad_onPressed)
            keypad.set_onRelease(self.keypad_onReleased)
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
            sock.write(statusCheckMessage or { 'ws': 'ws/genel', 'api': 'getSessionInfo' })
        return self
    def sockSend(self, data):
        self.sockOpen()
        self.dev.sock.write(data)
        return self
    def sockRecv(self, timeout=None):
        sock = self.dev.sock
        return sock.read() if timeout is None else sock.read(timeout)
    def talk(self, data):
        self.dev.sock.talk(data)
        return self
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
    def keypad_onPressed(self, key):
        print(f'key_press: [{key}]')
    def keypad_onReleased(self, key, duration):
        print(f'key_release: [{key}:{duration}]')
        pass
