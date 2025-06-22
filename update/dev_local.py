# ---------- dev_local.py ----------
from common import *
from config import server as srv, hw
from devBase import *
from time import sleep
import json
import socket
import requests
from sys import stdin
from os import system
import keyboard

# ---------- Ethernet Class (Mock) ----------
class Eth(BaseEth):
    def __init__(self):
        from config import local
        super().__init__()
        eth = self.eth = self
        eth.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
    def init(self):
        super().init(); eth = self.eth
        print('! eth init:', eth.ifconfig)
        return self

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def send(self, url, timeout=None):
        super().send(url, timeout)
        if timeout is None:
            timeout = 8
        result = requests.get(url, timeout)
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    def _open(self):
        if not super()._open(): return self
        srv = self.server; ep = (ip2Str(srv.ip), srv.rawPort)
        sock = self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(ep)
            print('! sock open', f'{ep[0]}:{ep[1]}')
        except Exception:
            sock = self.sock = None
            raise
        return self.isConnected()

# ---------- Keypad Class (Mock) ----------
class Keypad(BaseKeypad):
    def __init__(self, onPressed = None, onReleased = None):
        super().__init__(onPressed, onReleased)
        print('! keypad init')
    def update(self):
        super().update();
        if keyboard.is_pressed('enter'):
            key = input('  > ')
            onPressed = self.onPressed; onReleased = self.onReleased
            self._lastKeyPressTime = monotonic()
            if onPressed: onPressed(key)
            sleep(0.2)                     # kısa bekleme
            lastTime = self._lastKeyReleaseTime = monotonic()
            if onReleased:
                duration = monotonic() - lastTime
                onReleased(key, duration)
        return self

# ---------- LCD Class (Mock) ----------
class LCDCtl(BaseLCD):
    def __init__(self):
        super().__init__()
        print('! lcd init')
    def write(self, data, row=0, col=0, _internal=False):
        cur = self._buffer[row]; old = ''.join(cur[col : col + len(data)])
        result = super().write(data, row, col)
        if not (_internal or data == old):
            self._printBuffer()
        return result
    def clearLine(self, row):
        result = super().clearLine(row)
        # self._printBuffer()
        return result
    def clear(self):
        result = super().clear()
        # self._printBuffer()
        return result
    def on(self):
        super().on()
        print('! lcd on')
        return self
    def off(self):
        super().off()
        print('! lcd off')
        return self
    def _printBuffer(self):
        system('cls'); print('\n')  # print('\033[2J')
        return super()._printBuffer()

class LEDCtl(BaseLED):
    def __init__(self):
        super().__init__()
        print('! led init')
    def write(self, rgb, col):
        return super().write(rgb, col)

class RFIDCtl(BaseRFID):
    def __init__(self):
        super().__init__()
        print('! rfid init')


# ---------- Device Initialization ----------
shared.updateCheck = False                                     # if config.autoUpdate is None
dev = shared.dev = Device()
def setup_eth(): dev.eth = Eth().init()
def setup_req(): dev.req = WebReq();
def setup_sock(): dev.sock = RawSocket()
def setup_keypad(): dev.keypad = Keypad()
def setup_lcd(): dev.lcd = LCDCtl()
def setup_led(): dev.led = LEDCtl()
def setup_rfid(): dev.rfid = RFIDCtl()
steps = [
    setup_eth, setup_req, setup_sock, setup_keypad,
    setup_lcd, setup_led, setup_rfid
]
for step in steps:
    step()
