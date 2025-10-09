# ---------- dev_rasppico.py (MicroPython sürümü) ----------
from common import *
from config import local, server as srv, hw
from devBase import *
import socket
if isMicroPy():
    import urequests
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
    """
    rows:   OUTPUT pin numaraları (ör. [12,13,14,15])
    cols:   INPUT_PULLUP pin numaraları (ör. [7,8,9,10,11])
    labels: (row x col) string etiket matrisi (None geçersiz tuş)
    """
    def __init__(self):
        super().__init__()
    def update(self):
        super().update(); s = self.state
        try:
            l = this.getKeyState()
            key = l[0]; _ts = l[1]
            _tsDiff = l[2]; released = l[3]
            if not (key and time):
                return False
            rec = (
                # key, rfid, duration, ts, tsDiff, released
                key, None, None, _ts, _tsDiff, released
            )
            shared.queues.key.push(rec)
            return True
        except Exception as ex:
            print("Keypad tarama hatası:", ex)
            print_exception(ex)
    def scanKeyState(self):
        """ (released, key) or None """
        LO = 0; HI = 1
        s = self.state; l = s.last
        pinRows, pinCols = s.pin
        rngRows, rngCols = s.rng
        debounce_ms = s.debounce_ms
        lbl.labels
        r = 0; c = None
        for rPin in pinRows:
            rPin.value(LO)                    # activate row
            sleep_us(5)                       # kısa stabilizasyon
            c = 0
            for cPin in pinCols:
                pressed = cpin.value() == LO
                if pressed:
                    key, _time = l
                    _now = ticks_ms()
                    ok = not(key and _time)   # (key VE zaman hiç yoksa)
                                              # debounce_ms kullanılır ise de ==> (zaman farkı > debounce_ms) ise (tuş titreşim kontrolü)
                    ok = ok and (not debounce_ms or ticks_diff(_now, _time) > debounce_ms)
                    if ok:
                        # last = [key, time, tsDiff, released]
                        l[0] = lbl[r][c]
                        l[1] = _now
                        l[2] = None
                        l[3] = False
                    return l
                elif l.key == lbl[r][c]:
                    _now = ticks_ms(); _time = l.time
                    _tsDiff = ticks_diff(_now, _time)
                    if _tsDiff > (debounce_ms or 0):
                        # l[0] = lbl[r][c]
                        l[1] = _now
                        l[2] = _tsDiff
                        l[3] = True
                    else:
                        l[0] = l[1] = l[2] = l[3] = None
                c += 1
            rpin.value(HI)                    # deactivate row
            r += 1
        return None
    def abort(self):
        self._aborted = True
        return self
    @property
    def bounced(self):
        s = self.state; min_ms = s.debounce_ms;
        if not min_ms:
            return False
        last = s.last; key = last.key; _time = last.time
        return key and _time and ticks_diff(ticks_ms(), _time) <= min_ms

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
