from common import *
from config import local, server as srv
from part import *

class AppHandlers:
    def __init__(self):
        dev = self.dev = shared.dev
    
    ## Handler API Interface
    async def exec(self, code):
        result = exec(code, globals())
        if callable(result):
            result = result()
        try: result = await result
        except: pass
        return result
    def reboot(self):
        import app
        app.reboot()
        return self
    async def updateSelf(self):
        import app
        await app.updateFiles()
        return self
    def ethIsConnected(self):
        return self.dev.eth.isConnected()
    def wsIsConnected(self):
        return self.dev.ws.isConnected()
    async def wsOpen(self, statusCheckMessage=None):
        await self.dev.ws.open()
        return self
    async def wsSend(self, data):
        await self.dev.ws.send(data)
        return self
    async def wsRecv(self, timeout=None):
        return await self.dev.ws.recv(timeout)
    async def wsTalk(self, data, timeout=None):
        return await self.dev.ws.talk(data, timeout)
    async def wsSendJSON(self, data):
        await self.dev.ws.sendJSON(data)
        return self
    async def wsRecvJSON(self, timeout=None):
        return await self.dev.ws.recvJSON(timeout)
    async def wsTalkJSON(self, data, timeout=None):
        return await self.dev.ws.talkJSON(data, timeout)
    async def wsClose(self):
        await self.ws.close()
        return self
    async def wsSend(self, api, args = None, data = None, wsPath = None):
        await self.dev.ws.wsSend(api, args, data, wsPath)
        return self
    async def wsRecv(self, timeout=None):
        return await self.dev.ws.wsRecv(timeout)
    async def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return await self.dev.ws.wsTalk(api, args, data, wsPath, timeout)
    async def wsHeartbeat(self, timeout=None):
        return await self.dev.ws.wsHeartbeat(timeout)
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
    async def rfidRead(self):
        return await self.dev.rfid.read()
    async def beep(self, freq, duration):
        return await self.dev.buzzer.beep(freq, duration)
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
