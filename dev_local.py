# ---------- dev_local.py ----------
from common import *
from config import server as srv, hw
from devBase import *
import socket
import requests
# import keyboard

try:
    import websockets
except ImportError:
    websockets = None


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
    async def _open(self):
        if not await super()._open(): return self
        srv = self.server; ep = (ip2Str(srv.ip), srv.rawPort)
        sock = self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(ep)
            print('! sock open', f'{ep[0]}:{ep[1]}')
        except Exception:
            sock = self.sock = None
            raise
        return self.isConnected()

class WebSocket(BaseWebSocket):
    async def _open(self):
        if not websockets:
            raise ImportError("websockets module not found. Install via: pip install websockets")

        url = self.url              # örn: ws://127.0.0.1:8765/path
        try:
            self.ws = await websockets.connect(
                url,
                max_size=64 * 1024,
                ping_interval=2_000
            )
            print("Connected to", url)
            return True
        except Exception as ex:
            print("[ERROR] ws open:", ex);
            print_exception(ex)
            self.ws = None
            return False

# ---------- Keypad Class (Mock) ----------
class Keypad(BaseKeypad):
    def __init__(self):
        super().__init__()
        print('! keypad init')
    def update(self):
        super().update()
        sleep(.2)
        # if keyboard.is_pressed('enter'):
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
        # system('cls')
        print('\n')  # print('\033[2J')
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
def setup_wifi():   dev.wifi   = BaseWiFi()
def setup_req():    dev.req    = WebReq()
# def setup_sock():   dev.sock   = RawSocket()
def setup_ws():     dev.ws     = WebSocket()
def setup_keypad(): dev.keypad = Keypad()
def setup_lcd():    dev.lcd    = BaseLCD()
def setup_led():    dev.led    = BaseLED()
def setup_rfid():   dev.rfid   = BaseRFID()
def setup_buzzer(): dev.buzzer = BaseBuzzer()
steps = [
    setup_wifi, setup_req, setup_ws, setup_keypad,
    setup_lcd, setup_led, setup_rfid, setup_buzzer
]
for step in steps:
    step()
