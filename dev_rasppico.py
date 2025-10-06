# ---------- dev_rasppico.py (MicroPython sürümü) ----------
from common import *
from config import local, server as srv, hw
from devBase import *
import urequests
import socket
from machine import Pin, I2C, PWM
from network import WLAN, STA_IF
import rp2
from pico_i2c_lcd import I2cLcd
# from lcd_api import LcdApi
from neopixel_pio import Neopixel2
from mpy_websocket import client as _ws_client

# # Birkaç farklı paket ismi olabildiği için esnek import:
# _ws_client = None
# try:
#     from uwebsockets import client
#     _ws_client = client
# except:
#     for modname in ("uwebsockets.client", "websockets.client", "uwebsocket.client", "uwebsockets"):
#         try:
#             _ws_client = __import__(modname, None, None, ("connect",))
#             break
#         except Exception:
#             pass

# ---------- BaseWiFi Class ----------
class WiFi(BaseWiFi):
    def __init__(self):
        super().__init__()
        wlan = self.wlan = WLAN(STA_IF)
        wlan.active(True)
        try:
            import rp2
            rp2.country('TR')   # ülke seçimi (varsa)
        except Exception:
            pass
    def isConnected(self):
        super().isConnected()
        wlan = self.wlan
        return wlan.isconnected()

# ---------- Web Requests Class ----------
class WebReq(BaseWebReq):
    def send(self, url, timeout=5):
        super().send(url, timeout)
        print(f"HTTP GET: {url}")
        try:
            result = urequests.get(url, timeout=timeout)
            print(f"→ status: {result.status_code}")
            return result
        except Exception as ex:
            print("HTTP error:", ex)
            return None

# ---------- Raw TCP Socket Class ----------
class RawSocket(BaseRawSocket):
    async def _open(self):
        if not await super()._open():
            return self
        srv = self.server
        ep = (ip2Str(srv.ip), srv.rawPort)
        try:
            s = socket.socket()
            s.setblocking(True)
            s.connect(ep)
            self.sock = s
            print("! sock_open", f"{ep[0]}:{ep[1]}")
        except Exception as ex:
            self.sock = None
            print("! [ERROR]", "sock_open", ex)
            raise
        return self.isConnected()

class WebSocket(BaseWebSocket):
    async def _open(self):
        if not _ws_client:
            raise ImportError("uwebsockets/websockets client module not found")
        url = self.url
        # Bağlantı (awaitable ya da sync olabilir → her iki yolu da dene)
        conn = _ws_client.connect(url)
        if hasattr(conn, "__await__"):
            ws = await conn
        else:
            ws = conn
        # bazı portlarda send/recv async değil; wrapper gerekmez, üst sınıf zaten ikisini de destekliyor
        self.ws = ws
        return self.isConnected()

# ---------- Keypad Control Class ----------
class Keypad(BaseKeypad):
    @property
    def pressed_keys(self):
        """Basılı tuş etiketlerini liste olarak döndürür."""
        st = self._debounced()
        out = []
        for r in range(self._rlen):
            for c in range(self._clen):
                if not st[r][c]: continue
                lab = self._labels[r][c]
                if not lab: continue 
                out.append(lab)
                if not self._multi: return [lab]
        return out
    
    """
    rows:  OUTPUT pin numaraları (ör. [12,13,14,15])
    cols:  INPUT_PULLUP pin numaraları (ör. [7,8,9,10,11])
    labels:  row x col string etiket matrisi (None geçersiz tuş)
    """
    def __init__(self, onPressed = None, onReleased = None):
        super().__init__(onPressed, onReleased)
        c = hw.keypad
        self._aborted = False
        self._last = []
        _rows = self._rows = [Pin(p, Pin.OUT, value=1) for p in c.rows]              # PASIF HIGH
        _cols = self._cols = [Pin(p, Pin.IN, Pin.PULL_UP) for p in c.cols]
        self._rlen = len(_rows)
        self._clen = len(_cols)
        self._labels = c.keys
        self._debounce = c.debounce_ms
        self._multi = c.multi

        # Debounce durumları
        self._stable = [[False] * self._clen for _ in range(self._rlen)]
        self._last_read = [[False] * self._clen for _ in range(self._rlen)]
        self._last_change = [[0] * self._clen for _ in range(self._rlen)]
    def abort(self):
        self._aborted = True
        return self
    async def loop(self):
        await super().loop()
        # t0 = time.ticks_ms()
        # while time.ticks_diff(time.ticks_ms(), t0) < duration * 1000:
        while not self._aborted:
            self.update()
            await asleep(.05)
        self._aborted = False
        return self
    async def update(self):
        await super().update()
        last = self._last
        try:
            pressed = self.pressed_keys                                     # Liste (sıralı)
            if pressed:
                # --- yeni basılanlar (sırayla, tekrar etmeden)
                lastTime = monotonic()
                for key in pressed:
                    if key in last: continue
                    if self.onPressed: await self.onPressed(key)
                self._lastKeyPressTime = lastTime
            if last:
                # --- bırakılanlar (önceden vardı ama şimdi yok)
                lastTime = monotonic()
                for key in last:
                    if key in pressed: continue
                    duration = monotonic() - self._lastKeyPressTime
                    if self.onReleased: await self.onReleased(key, duration)
                self._lastKeyReleaseTime = lastTime
            last = self._last = pressed  # mevcut durumu kaydet
        except Exception as ex:
            print("Keypad tarama hatası:", ex)
            print_exception(ex)
    def _scan_raw(self):
        """True=basılı, False=serbest"""
        state = [[False]*self._clen for _ in range(self._rlen)]
        for r, rpin in enumerate(self._rows):
            rpin.value(0)      # o satırı aktif et (LOW)
            sleep_us(10)       # kısa stabilizasyon
            for c, cpin in enumerate(self._cols):
                # Pull-up var; LOW -> tuş basılı
                state[r][c] = (cpin.value() == 0)
            rpin.value(1)      # pasif (HIGH)
        return state
    def _debounced(self):
        raw = self._scan_raw()
        now = ticks_ms()
        for r in range(self._rlen):
            for c in range(self._clen):
                if raw[r][c] != self._last_read[r][c]:
                    self._last_read[r][c] = raw[r][c]
                    self._last_change[r][c] = now
                elif time.ticks_diff(now, self._last_change[r][c]) >= self._debounce:
                    self._stable[r][c] = self._last_read[r][c]
        return self._stable

# ---------- LCD Control Class ----------
class LCD(BaseLCD):
    def __init__(self):
        super().__init__()
        c = hw.lcd;
        addr = self.addr = c.addr
        print(f'SCL = {Pin(c.scl)}')
        print(f'SDA = {Pin(c.sda)}')
        print(f'freq = {c.freq}')
        print(f'addr = {addr}')
        print(f'c.rows = {c.rows}')
        print(f'c.cols = {c.cols}')
        i2c = self.i2c = I2C(c._id, scl=Pin(c.scl), sda=Pin(c.sda), freq=c.freq)
        lcd = self.lcd = I2cLcd(i2c, addr, c.rows, c.cols)
        self.unblink()
        self.showCursor()
        self.clear()
        # lcd.hal_write_command(lcd.LCD_ENTRY_MODE)
    def clear(self):
        super().clear()
        self.lcd.clear()
        print("lcdClear")
        return self
    def write(self, data, row=0, col=0, _internal=False):
        super().write(data, row, col, _internal)
        self.move(row, col)
        self.lcd.putstr(data)
        print("lcdWrite:", data)
        return self
    def move(self, row=0, col=0):
        super().move(row, col)
        self.lcd.move_to(col, row)
        return self
    def on(self):
        super().on()
        self.lcd.backlight_on()
        return self
    def off(self):
        super().off()
        self.lcd.backlight_off()
        return self
    def blink(self):
        super().blink()
        self.lcd.blink_cursor_on()
        return self
    def unblink(self):
        super().unblink()
        self.lcd.blink_cursor_off()
        return self
    def showCursor(self):
        super().showCursor()
        self.lcd.show_cursor()
        return self
    def hideCursor(self):
        super().hideCursor()
        self.lcd.hide_cursor()
        return self

class LED(BaseLED):
    def __init__(self):
        super().__init__()
        c = hw.led
        # SM0, pin=GP1, renk sırası GRB
        strip = self.strip = Neopixel2(c.count, 0, c.pin, "GRB")
        self.brightness(c.brightness)
        pass
    def _write(self, color):
        super()._write(color)
        strip = self.strip
        strip.fill(color)
        strip.show()
        return self
    def clear(self):
        super().clear()
        self.strip.clear()
        return self
    def brightness(self, value):
        super().brightness(value)
        self.strip.brightness(value)
        return self

class RFID(BaseRFID):
    def __init__(self):
        super().__init__()

class Buzzer(BaseBuzzer):
    def __init__(self):
        super().__init__()
        c = hw.buzzer
        self.buzzer = PWM(Pin(c.pin))

# ---------- Device Initialization ----------
shared.updateCheck = True
dev = shared.dev = Device()

def setup_wifi():   dev.wifi   = WiFi()
def setup_req():    dev.req    = WebReq()
# def setup_sock():   dev.sock   = RawSocket()
def setup_ws():     dev.ws     = WebSocket()
def setup_keypad(): dev.keypad = Keypad()
def setup_lcd():    dev.lcd    = LCD()
def setup_led():    dev.led    = LED()
def setup_rfid():   dev.rfid   = RFID()
def setup_buzzer(): dev.buzzer = Buzzer()

for step in [
    setup_wifi, setup_req, setup_ws, setup_keypad,
    setup_lcd, setup_led, setup_rfid, setup_buzzer
]:
    step()
