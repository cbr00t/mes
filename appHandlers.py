from common import *
from config import local, server as srv
from part import *

class AppHandlers:
    def __init__(self):
        dev = self.dev = shared.dev
    
    ## Handler API Interface
    def exec(self, code):
        result = exec(code, globals())
        return result
    def reboot(self):
        import app
        app.reboot()
        return self
    def updateSelf(self):
        import app
        app.updateSelf()
        return self
    def ethIsConnected(self):
        return self.dev.eth.isConnected()
    def wsIsConnected(self):
        return self.dev.ws.isConnected()
    def wsOpen(self, statusCheckMessage=None):
        self.dev.ws.open()
        return self
    def wsSend(self, data):
        self.dev.ws.send(data)
        return self
    def wsRecv(self, timeout=None):
        return self.dev.ws.recv(timeout)
    def wsTalk(self, data, timeout=None):
        return self.dev.ws.talk(data, timeout)
    def wsSendJSON(self, data):
        self.dev.ws.sendJSON(data)
        return self
    def wsRecvJSON(self, timeout=None):
        return self.dev.ws.recvJSON(timeout)
    def wsTalkJSON(self, data, timeout=None):
        return self.dev.ws.talkJSON(data, timeout)
    def wsClose(self):
        self.ws.close()
        return self
    def wsSend(self, api, args = None, data = None, wsPath = None):
        self.dev.ws.wsSend(api, args, data, wsPath)
        return self
    def wsRecv(self, timeout=None):
        return self.dev.ws.wsRecv(timeout)
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return self.dev.ws.wsTalk(api, args, data, wsPath, timeout)
    def wsHeartbeat(self, timeout=None):
        return self.dev.ws.wsHeartbeat(timeout)
    def getWSData(self, api, args = None, data = None, wsPath = None):
        return getWSData(api, args, data, wsPath)
    def wsClose(self):
        return self.dev.ws.close()
    def req(self, data, timeout=None):
        return self.dev.req.send(data, timeout)
    def textReq(self, data, timeout=None):
        return self.dev.req.sendText(data, timeout)
    def jsonReq(self, data, timeout=None):
        return self.dev.req.sendJSON(data, timeout)
    def lcdWrite(self, text, row=0, col=0):
        if not lcdIsBusy():
            self.dev.lcd.write(text, row, col, False)
        return self
    def lcdWriteLine(self, text, row=0, col=0):
        if not lcdIsBusy():
            self.dev.lcd.writeLine(text, row, col, False)
        return self
    def lcdClearLine(self, row):
        if not lcdIsBusy():
            self.dev.lcd.clearLine(row)
        return self
    def lcdClear(self):
        if not lcdIsBusy():
            self.dev.lcd.clear()
        return self
    def ledWrite(self, rgb):
        self.dev.led.write(rgb)
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
