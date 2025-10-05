# ---------- dev_rasppico.py (Güncellenmiş) ----------
from common import *
from config import local, server as srv, hw
from devBase import *
from time import sleep, monotonic
from traceback import print_exception

try:
    import board
    import digitalio
    import busio
    from lcd.lcd import LCD
    from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
    from adafruit_matrixkeypad import Matrix_Keypad
    import adafruit_connection_manager
    import adafruit_requests
    from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except (Exception):
    pass


# ---------- Ethernet Class ----------
class Eth(BaseEth):
    def __init__(self):
        super().__init__()
        self.pool = self._spi = self._cs = self._reset = None
    def init(self):
        ec = hw.eth
        is_dhcp = not local.ip
        spi = self._spi; cs = self._cs;
        reset = self._reset; eth = self.eth
        # getattr(board, pin)
        # if spi is not None: spi.deinit(); spi = None
        if cs is None:
            cs = self._cs = digitalio.DigitalInOut(getattr(board, ec.cs)) \
                if 'digitalio' in globals() else None
        if spi is None:
            spi = self._spi = busio.SPI(\
                    getattr(board, ec.spi[0]), \
                    getattr(board, ec.spi[1]), \
                    getattr(board, ec.spi[2]) \
                ) if 'busio' in globals() else None
        if reset is None:
            reset = self._reset = digitalio.DigitalInOut(getattr(board, ec.reset)) \
                if 'digitalio' in globals() else None
        try:
            eth = self.eth = WIZNET5K(spi, cs, reset, is_dhcp=is_dhcp) if 'WIZNET5K' in globals() else self
            if not is_dhcp: eth.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
        except RuntimeError as e:
            print("Ethernet başlatılamadı:", e)
            eth = self.eth = None
        return self
    def isConnected(self):
        eth = self.eth
        if eth is None: self.init(); eth = self.eth
        return False if eth is None else eth.link_status
    def getPool(self):
        pool = self.pool
        if pool is not None: return pool
        if not ('adafruit_connection_manager' in globals() and self.isConnected()): return None
        pool = self.pool = adafruit_connection_manager.get_radio_socketpool(self.eth)
        return pool

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def send(self, url, timeout=None):
        super().send(url, timeout); session = self.session
        print(f'get request: {url}')
        if timeout is None:
            timeout = 5
        result = session.get(url, timeout=timeout)
        print(f'... result: [{result}]')
        return result
    def _initSession(self):
        eth = shared.dev.eth
        self.session = adafruit_requests.Session(eth.getPool(), None) if 'adafruit_requests' in globals() else None

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    def _open(self):
        if not super()._open(): return self
        srv = self.server; ep = (ip2Str(srv.ip), srv.rawPort)
        eth = shared.dev.eth; pool = eth.getPool()
        sock = self.sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        try:
            sock.connect(ep)
            print('! sock_open', f'{ep[0]}:{ep[1]}')
        except Exception as ex:
            sock = self.sock = None
            print('! [ERROR]', 'sock_open', ex)
            raise
        return self.isConnected()

# ---------- Keypad Control Class ----------
class Keypad(BaseKeypad):
    def __init__(self, onPressed = None, onReleased = None):
        super().__init__(onPressed, onReleased)
        cfg = hw.keypad
        rows = [getattr(board, pin) for pin in cfg.rows] if 'board' in globals() else cfg.rows
        cols = [getattr(board, pin) for pin in cfg.cols] if 'board' in globals() else cfg.cols
        keys = cfg.keys
        self.keypad = Matrix_Keypad(rows, cols, keys) if 'Matrix_Keypad' in globals() else NS()
        self._pressed = {}
        # Performans için ek değişkenler
        self._last_scan_time = monotonic()
        self._min_scan_interval = 0.0002  # 2ms - optimal tarama sıklığı
    def update(self):
        super().update(); _pressed = self._pressed
        onPressed = self.onPressed; onReleased = self.onReleased
        lastTime = shared.lastTime
        # Daha sık tarama için, her çağrıda değil, minimum aralıktan sonra tara
        now = monotonic()
        elapsed = now - self._last_scan_time
        if elapsed < self._min_scan_interval:
            # Çok fazla CPU kullanmamak için küçük bir bekleme
            # time.sleep(0.0001)  # 0.1ms bekleme - isteğe bağlı
            return
        # Zamanı güncelle
        self._last_scan_time = monotonic()
        try:
            # Ana tarama kodunu hata yakalama içine al
            current_keys = set(self.keypad.pressed_keys)
            # Basılan yeni tuşları algıla
            for key in current_keys:
                if key not in _pressed:
                    self._lastKeyPressTime = _pressed[key] = monotonic()
                    if onPressed: onPressed(key)
            
            # Bırakılan tuşları kontrol et
            released_keys = [key for key in _pressed if key not in current_keys]
            for key in released_keys:
                pressed_time = _pressed.pop(key)
                duration = now - pressed_time                                                       # 3 ondalık basamak hassasiyet (milisaniye)
                # Tüm tuş bırakma olaylarını işle
                self._lastKeyReleaseTime = monotonic()
                if onReleased: onReleased(key, duration)
        except Exception as ex:
            # Herhangi bir hata olursa sessizce devam et
            print(f"Keypad tarama hatası: {ex}")
            print_exception(ex)
        return self

# ---------- LCD Control Class ----------
class LCDCtl(BaseLCD):
    def __init__(self):
        super().__init__()
        i2c = busio.I2C(board.GP1, board.GP0) if 'busio' in globals() else None
        interface = I2CPCF8574Interface(i2c, 0x27) if 'I2CPCF8574Interface' in globals() else None
        lcdCfg = hw.lcd
        lcd = self.lcd = LCD(interface, num_rows=lcdCfg.rows, num_cols=lcdCfg.cols) if 'LCD' in globals() else None
        if lcd is not None:
            self.off(); self.clear()
    def clear(self):
        super().clear()
        self.lcd.clear(); print('lcdClear')
        return self
    def write(self, data, row=0, col=0, _internal=False):
        super().write(data, row, col)
        lcd = self.lcd; lcd.set_cursor_pos(row, col)
        lcd.print(data); print('lcdWrite', data)
        # if not data.strip():
        #     raise RuntimeError()
        return self
    def on(self):
        self.lcd.set_backlight(True)
        return self
    def off(self):
        self.lcd.set_backlight(False)
        return self

class LEDCtl(BaseLED):
    pass

class RFIDCtl(BaseRFID):
    pass


# ---------- Device Initialization ----------
shared.updateCheck = True                                    # if config.autoUpdate is None
dev = shared.dev = Device()
def setup_eth(): dev.eth = Eth().init()
def setup_req(): dev.req = WebReq()
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
