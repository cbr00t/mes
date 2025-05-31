# ---------- dev_local.py ----------
from time import sleep
import json
import socket
import requests
from common import *
from config import local, server as srv
import core
from devBase import *

# ---------- Ethernet Class (Mock) ----------
class Eth(BaseEth):
    def __init__(self):
        super().__init__()
        eth = self.eth = self
        eth.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
    def init(self):
        super().init(); eth = self.eth
        print("[LocalEth] initialized with:", eth.ifconfig)
        return self

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def send(self, url, timeout=None):
        super().send(url, timeout)
        if timeout is None:
            timeout = 8
        print(f'get request: {url}')
        result = requests.get(url, timeout)
        print(f'... result: [{result}]')
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    def open(self):
        super().open()
        srv = self.server
        sock = self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ep = (ip2Str(srv.ip), srv.rawPort)
        try:
            sock.connect(ep)
            print(f'! sock_open', f'{ep[0]}:{ep[1]}')
        except Exception:
            sock = self.sock = None
            raise
        return self

# ---------- Keypad Class (Mock) ----------
class Keypad(BaseKeypad):
    def __init__(self, onPress = None, onRelease = None):
        super().__init__(onPress, onRelease)
        print("[Keypad] (mock) initialized.")
    def update(self):
        super().update()
        # print("[Keypad] updated.")
        return self

# ---------- LCD Class (Mock) ----------
class LCDCtl(BaseLCD):
    def __init__(self):
        super().__init__()
        print("[LCD] (mock) initialized.")
    def clear(self):
        super().clear()
        print("[LCD] cleared.")
        return self
    def write(self, data, row=0, col=0):
        super().write(data, row, col)
        print(f"[LCD] write @({row},{col}):", data)
        return self
    def on():
        super().on()
        print("[LCD] on")
        return self
    def off():
        super().off()
        print("[LCD] off")
        return self

class LEDCtl(BaseLED):
    def __init__(self):
        super().__init__()
        print("[LED] (mock) initialized.")
    def write(self, rgb, col):
        super().write(rgb, col)
        print(f"[LED] write: [{rgb}: {col}]")
        return self

class RFIDCtl(BaseRFID):
    pass


# ---------- Device Initialization ----------
updateCheck = False
dev = core.dev = core.Device()
def setup_eth(): dev.eth = Eth().init()
def setup_req(): dev.req = WebReq()
def setup_sock(): dev.sock = RawSocket()
def setup_keypad(): dev.keypad = Keypad()
def setup_lcd(): dev.lcd = LCDCtl()
def setup_led(): dev.led = LEDCtl()
def setup_rfid(): dev.rfid = RFIDCtl()
steps = [setup_eth, setup_req, setup_sock, setup_keypad, setup_lcd, setup_led, setup_rfid]
for step in steps:
    step()
