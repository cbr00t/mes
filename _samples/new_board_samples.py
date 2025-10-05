# === TUM SISTEM TESTI (Pico W, Wi-Fi kapali) ===
import time
import board
import busio
import neopixel
import pwmio
import math
from digitalio import DigitalInOut
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from adafruit_matrixkeypad import Matrix_Keypad
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_connection_manager
import adafruit_requests
from mfrc522 import MFRC522

# ---------------- LCD AYARLARI ----------------
i2c = busio.I2C(board.GP27, board.GP26)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)
def lcd_clear(): lcd.clear()
def lcd_write(msg, row=0, col=0):
    lcd.set_cursor_pos(row, col)
    lcd.print(str(msg))
lcd.set_backlight(True)

# ---------------- LED ----------------
PIXEL_PIN = board.GP22
pixels = neopixel.NeoPixel(PIXEL_PIN, 1, brightness=0.3, auto_write=False)
def solid(color): pixels.fill(color); pixels.show()

# ---------------- BUZZER ----------------
buzzer = pwmio.PWMOut(board.GP21, duty_cycle=0, frequency=440, variable_frequency=True)
def beep(freq=1000, dur=0.1):
    buzzer.frequency = int(freq)
    buzzer.duty_cycle = 32768
    time.sleep(dur)
    buzzer.duty_cycle = 0

# ---------------- SPI1 BUS (ORTAK) ----------------
spi1 = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)

# ---------------- TESTLER ----------------
def test_lcd():
    lcd_clear(); lcd_write("LCD testi...", 0)
    time.sleep(0.5)
    lcd_write("Hello YouTube!", 1)
    time.sleep(0.7)
    lcd_clear(); lcd_write("LCD OK", 0)
    time.sleep(0.8)

def test_keypad():
    lcd_clear(); lcd_write("Keypad testi...", 0)
    rows = [board.GP12, board.GP13, board.GP14, board.GP15]
    cols = [board.GP7, board.GP8, board.GP9, board.GP10, board.GP11]
    keys = [
        ["F1", "1", "2", "3", "X"],
        ["F2", "4", "5", "6", "^"],
        ["F3", "7", "8", "9", "V"],
        ["F4", "ESC", "0", "ENTER", None]
    ]
    keypad = Matrix_Keypad(rows, cols, keys)
    start = time.monotonic()
    while time.monotonic() - start < 8:
        pressed = keypad.pressed_keys
        if pressed:
            lcd_clear(); lcd_write("Tus:", 0)
            lcd_write(",".join(pressed), 1)
            beep(800, 0.05)
        time.sleep(0.08)
    lcd_clear(); lcd_write("Keypad OK", 0)
    time.sleep(0.8)

def test_led():
    lcd_clear(); lcd_write("LED testi...", 0)
    for c in [(255,0,0), (0,255,0), (0,0,255)]:
        solid(c); time.sleep(0.4)
    solid((0,0,0))
    lcd_clear(); lcd_write("LED OK", 0)
    time.sleep(0.8)

def test_buzzer():
    lcd_clear(); lcd_write("Buzzer testi...", 0)
    for f in (440,660,880,1320):
        beep(f,0.15); time.sleep(0.05)
    lcd_clear(); lcd_write("Buzzer OK", 0)
    time.sleep(0.8)

def test_ethernet():
    lcd_clear(); lcd_write("Ethernet baglaniyor", 0)
    try:
        cs = DigitalInOut(board.GP17)
        reset = DigitalInOut(board.GP20)
        eth = WIZNET5K(spi1, cs, reset, is_dhcp=True)
        pool = adafruit_connection_manager.get_radio_socketpool(eth)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
        requests = adafruit_requests.Session(pool, ssl_context)
        lcd_clear(); lcd_write("ETH IP OK:", 0)
        lcd_write(eth.pretty_ip(eth.ip_address), 1)
        beep(1200,0.1)
        time.sleep(2)
    except Exception as e:
        lcd_clear(); lcd_write("ETH HATA", 0)
        lcd_write(str(e)[:18], 1)
        solid((255,0,0))
        time.sleep(2)
    solid((0,0,0))

def test_rfid():
    lcd_clear(); lcd_write("RFID testi...", 0)
    rdr = MFRC522(
        sck=board.GP2,   # SCK
        mosi=board.GP3,  # MOSI
        miso=board.GP4,  # MISO
        rst=board.GP0,   # RST
        cs=board.GP1     # SDA/CS
    )
    lcd_write("Kart bekleniyor...", 1)
    start = time.monotonic(); found = False
    while time.monotonic() - start < 10:
        stat, bits = rdr.request(rdr.REQIDL)
        if stat == rdr.OK:
            stat, uid = rdr.anticoll()
            if stat == rdr.OK and len(uid) >= 4:
                uid_str = ":".join(f"{b:02X}" for b in uid[:4])
                lcd_clear(); lcd_write("Kart OK", 0); lcd_write(uid_str, 1)
                beep(1000, 0.1); solid((0,255,0))
                found = True; time.sleep(1); break
        time.sleep(0.05)
    lcd_clear()
    lcd_write("RFID OK" if found else "RFID YOK", 0)
    solid((0,0,0))
    time.sleep(1)

# ---------------- ANA AKIÞ ----------------
lcd_clear(); lcd_write("TESTLER BASLIYOR", 0)
solid((0,0,255)); time.sleep(1)

test_lcd()
test_keypad()
test_led()
test_buzzer()
test_ethernet()
test_rfid()

lcd_clear(); lcd_write("TUM TESTLER TAMAM", 0)
beep(1000,0.1); time.sleep(0.05)
beep(1400,0.1); time.sleep(0.05)
beep(1800,0.15)
solid((0,255,0))
