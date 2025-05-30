# ---------- dev_local.py ----------
from time import sleep
import json
import socket
import requests
from common import *
import config as cfg
import core
from devBase import *

# ---------- Ethernet Class (Mock) ----------
class Eth:
    def __init__(self):
        local = cfg.local
        self.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
    def init(self):
        print("[LocalEth] initialized with:", self.ifconfig)
        return self

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def __init__(self):
        self.eth = dev.eth.eth
    def send(self, url, timeout=None):
        if timeout is None:
            timeout = 8
        print(f'get request: {url}')
        result = requests.get(url, timeout)
        print(f'... result: [{result}]')
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    def open(self):
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

# ---------- LCD Class (Mock) ----------
class LCDCtl:
    def __init__(self):
        print("[LCD] (mock) initialized.")
    def clear(self):
        print("[LCD] cleared.")
        return self
    def write(self, data, row=0, col=0):
        print(f"[LCD] write @({row},{col}):", data)
        return self

# ---------- Keypad Class (Mock) ----------
class Keypad(BaseKeypad):
    def __init__(self, onPress = None, onRelease = None):
        print("[Keypad] (mock) initialized.")
    def update(self):
        super().update()
        # print("[Keypad] updated.")
        return self



# ---------- Device Initialization ----------
updateCheck = False
dev = core.dev = core.Device()
@withErrCheck
def setup_eth(): dev.eth = Eth().init()
@withErrCheck
def setup_req(): dev.req = WebReq()
@withErrCheck
def setup_sock(): dev.sock = RawSocket()
@withErrCheck
def setup_lcd(): dev.lcd = LCDCtl()
@withErrCheck
def setup_keypad(): dev.keypad = Keypad()
steps = [setup_eth, setup_req, setup_sock, setup_lcd, setup_keypad]
for step in steps:
    step()
