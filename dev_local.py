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
        simulation_interval_ms = hw.keypad.simulation_interval_ms
        if not simulation_interval_ms:
            return False
        return super().update()
    def scanKeyState(self):
        """ (released, key) or None """
        super().scanKeyState()
        s = self.state; l = s.last
        # last = [key, time, tsDiff, released]
        l[0] = 'enter'
        l[1] = ticks_ms()
        l[2] = None
        l[3] = False
        return l

# ---------- LCD Class (Mock) ----------
class LCD(BaseLCD):
    def __init__(self):
        super().__init__()
        print('! lcd init')
    def write(self, data, row=0, col=0, _internal=False):
        # cur = self._buffer[row]
        rcs = self._rc_status
        old = ''.join(self._buffer[row][col : col + len(data)])
        result = super().write(data, row, col)
        new = ''.join(self._buffer[row][col : col + len(data)])
        if not (_internal or new == old or (row, col) == rcs):
        # if not (_internal or new == old):
            self._printBuffer()
        return result
    def _writeChar(self, ch, row=None, col=None):
        pass
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

class LED(BaseLED):
    def __init__(self):
        super().__init__()
        c = hw.led
        self.brightness(c.brightness)
        print('! led init')
    def _write(self, value):
        super()._write(value)
        l = self.state.last
        print('[LED] ', value, join(' | ', l))
    def brightness(self, value):
        super().brightness(value)
        l = self.state.last
        print('[LED] ', value, join(' | ', l))

class RFID(BaseRFID):
    def __init__(self):
        super().__init__()
        print('! rfid init')
    def update(self):
        simulation_interval_ms = hw.rfid.simulation_interval_ms
        if not simulation_interval_ms:
            return False
        return super().update()
    def read(self):
        super().read()
        s = self.state; l = s.last
        uid = int.from_bytes(bytes([0x0C, 0x0B, 0x03, 0x00]), byteorder)
        # rfid, ts
        l[0] = uid
        l[1] = ticks_ms()
        return uid2Str(uid)


# ---------- Device Initialization ----------
shared.updateCheck = False                                     # if config.autoUpdate is None
dev = shared.dev = Device()
def setup_wifi():   dev.wifi   = BaseWiFi()
def setup_req():    dev.req    = WebReq()
# def setup_sock():   dev.sock   = RawSocket()
def setup_ws():     dev.ws     = WebSocket()
def setup_keypad(): dev.keypad = Keypad()
def setup_lcd():    dev.lcd    = LCD()
def setup_led():    dev.led    = LED()
def setup_rfid():   dev.rfid   = RFID()
def setup_buzzer(): dev.buzzer = BaseBuzzer()
steps = [
    setup_wifi, setup_req, setup_ws, setup_keypad,
    setup_lcd, setup_led, setup_rfid, setup_buzzer
]
for step in steps:
    step()
