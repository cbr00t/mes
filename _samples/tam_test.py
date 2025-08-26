import time
import board
import busio
import digitalio
from digitalio import DigitalInOut
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from adafruit_matrixkeypad import Matrix_Keypad

# === LCD AYARLARI ===
sda, scl = board.GP0, board.GP1
i2c = busio.I2C(scl, sda)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)

def lcd_write(msg, row=0, col=0):
    lcd.set_cursor_pos(row, col)
    lcd.print(msg)

def lcd_clear():
    lcd.clear()

# === BUTON TESTİ ===
def test_keypad():
    lcd_clear()
    lcd_write("Keypad testi...", 0)
    rows = [board.GP12, board.GP13, board.GP14, board.GP15]
    cols = [board.GP7, board.GP8, board.GP9, board.GP10, board.GP11]
    keys = [
        ["F1", "1", "2", "3", "X"],
        ["F2", "4", "5", "6", "^"],
        ["F3", "7", "8", "9", "V"],
        ["F4", "ESC", "0", "ENTER", None]
    ]
    keypad = Matrix_Keypad(rows, cols, keys)

    start_time = time.monotonic()
    while time.monotonic() - start_time < 10:
        pressed = keypad.pressed_keys
        if pressed:
            lcd_clear()
            lcd_write("Tus:", 0, 0)
            lcd_write(",".join(pressed), 1, 0)
        time.sleep(0.1)

# === EKRAN TESTİ ===
def test_lcd():
    lcd_clear()
    lcd_write("LCD testi...", 0, 0)
    time.sleep(1)
    lcd.set_cursor_pos(1, 3)
    lcd.print("Hello YouTube!")
    time.sleep(1)
    lcd.set_cursor_pos(2, 0)
    lcd.print("Demo text")
    time.sleep(1)
    lcd.clear()
    lcd_write("LCD tamam", 0)
    time.sleep(1)

# === ETHERNET TESTİ ===
def test_ethernet():
    lcd_clear()
    lcd_write("Ethernet baglaniyor", 0)
    try:
        import adafruit_connection_manager
        import adafruit_requests
        from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

        cs = DigitalInOut(board.GP17)
        reset = DigitalInOut(board.GP20)
        spi = busio.SPI(board.GP18, board.GP19, board.GP16)

        eth = WIZNET5K(spi, cs, reset, is_dhcp=True)

        pool = adafruit_connection_manager.get_radio_socketpool(eth)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
        requests = adafruit_requests.Session(pool, ssl_context)

        r = requests.get("http://httpbin.org/json")
        lcd_clear()
        lcd_write("IP OK:", 0)
        lcd_write(eth.pretty_ip(eth.ip_address), 1)
        time.sleep(3)
        r.close()
    except Exception as e:
        lcd_clear()
        lcd_write("ETH HATA", 0)
        lcd_write(str(e)[:20], 1)
        time.sleep(3)

# === ANA TEST AKIŞI ===
lcd.set_backlight(True)
lcd_clear()
lcd_write("TEST BASLIYOR...", 0)
time.sleep(2)

test_lcd()
test_keypad()
test_ethernet()

lcd_clear()
lcd_write("TESTLER TAMAMLANDI", 0)
