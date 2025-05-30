# ---------- dev_rasppico.py (Güncellenmiş) ----------
from common import *
import core
import config as cfg
from time import sleep, monotonic
from devBase import *
import board
import digitalio
import busio
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from adafruit_matrixkeypad import Matrix_Keypad
import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K


# ---------- Ethernet Class ----------
class Eth:
    def __init__(self):
        self._cs = digitalio.DigitalInOut(board.GP17)
        self._spi = busio.SPI(board.GP18, board.GP19, board.GP16)
    def init(self):
        local = cfg.local; is_dhcp = not local.ip
        eth = self.eth = WIZNET5K(self._spi, self._cs, is_dhcp=is_dhcp)
        if not is_dhcp:
            eth.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
        while not eth.link_status:
            print("eth init...")
            sleep(1)
        return eth

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def __init__(self):
        pool = self._pool = adafruit_connection_manager.get_radio_socketpool(dev.eth)
        self.session = adafruit_requests.Session(pool, None)
    def send(self, url):
        print(f'get request: {url}')
        result = self.session.get(url)
        print(f'... result: [{result}]')
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    def __init__(self):
        super().__init__()
        self._pool = adafruit_connection_manager.get_radio_socketpool(dev.eth)
    def open(self):
        srv = self.server
        sock = self.sock = self._pool.socket()
        ep = (ip2Str(srv.ip), srv.rawPort)
        try:
            sock.connect(ep)
            print(f'! sock_open', '{ep[0]}:{ep[1]}')
        except Exception:
            sock = self.sock = None
            raise
        return self

# ---------- LCD Control Class ----------
class LCDCtl:
    def __init__(self):
        i2c = busio.I2C(board.GP1, board.GP0)
        interface = I2CPCF8574Interface(i2c, 0x27)
        lcd = self.lcd = LCD(interface, num_rows=4, num_cols=20)
        lcd.set_backlight(True)
    def clear(self):
        self.lcd.clear()
        print('lcdClear')
        return self
    def write(self, data, row=0, col=0):
        lcd = self.lcd
        lcd.set_cursor_pos(row, col)
        lcd.print(data)
        print('lcdWrite', data)
        return self

# ---------- Keypad Control Class ----------
class Keypad(BaseKeypad):
    def __init__(self, onPressed = None, onRelease = None):
        super().__init__()
        self.onPressed = onPressed
        self.onRelease = onRelease
        rows = [getattr(board, pin) for pin in hw.rows]
        cols = [getattr(board, pin) for pin in hw.cols]
        keys = hw.keys
        self.keypad = Matrix_Keypad(rows, cols, keys)
        self._pressed = {}
        # Performans için ek değişkenler
        self._last_scan_time = monotonic()
        self._min_scan_interval = 0.0002  # 2ms - optimal tarama sıklığı
    def update(self):
        super().update()
        now = monotonic()
        # Daha sık tarama için, her çağrıda değil, minimum aralıktan sonra tara
        elapsed = now - self._last_scan_time
        if elapsed < self._min_scan_interval:
            # Çok fazla CPU kullanmamak için küçük bir bekleme
            # time.sleep(0.0001)  # 0.1ms bekleme - isteğe bağlı
            return
        # Zamanı güncelle
        self._last_scan_time = now
        try:
            # Ana tarama kodunu hata yakalama içine al
            current_keys = set(self.keypad.pressed_keys)
            # Basılan yeni tuşları algıla
            for key in current_keys:
                if key not in self._pressed:
                    self._pressed[key] = now
                    if self.onPress:
                        self.onPress(key)
            
            # Bırakılan tuşları kontrol et
            released_keys = [key for key in self._pressed if key not in current_keys]
            for key in released_keys:
                pressed_time = self._pressed.pop(key)
                duration = now - pressed_time
                # Tüm tuş bırakma olaylarını işle
                if self.onRelease:
                    # 3 ondalık basamak hassasiyet (milisaniye)
                    self.onRelease(key, duration)
        except Exception as ex:
            # Herhangi bir hata olursa sessizce devam et
            print(f"Keypad tarama hatası: {ex}")
        return self


hw = NS(
    rows = ['GP12', 'GP13', 'GP14', 'GP15'],
    cols = ['GP7', 'GP8', 'GP9', 'GP10', 'GP11'],
    keys = [
        ['F1', '1', '2', '3', 'X'],
        ['F2', '4', '5', '6', '^'],
        ['F3', '7', '8', '9', 'V'],
        ['F4', 'ESC', '0', 'ENTER', None]
    ]
)

# ---------- Device Initialization ----------
dev = core.dev = core.Device()
updateCheck = True
def setup_eth(): dev.eth = Eth().init()
def setup_req(): dev.req = WebReq()
def setup_sock(): dev.sock = RawSocket()
def setup_lcd(): dev.lcd = LCDCtl()
def setup_keypad(): dev.keypad = Keypad()
steps = [setup_eth, setup_req, setup_sock, setup_lcd, setup_keypad]
for step in steps:
    step()
