import time
import board
import busio
import digitalio
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from keypad_handler import KeypadHandler
from hardware_config import HARDWARE_CONFIG

# === LCD AYARLARI ===
sda, scl = board.GP0, board.GP1
i2c = busio.I2C(scl, sda)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)

def lcd_write(msg, row=0, col=0):
    lcd.set_cursor_pos(row, col)
    lcd.print(msg)

def lcd_clear():
    lcd.clear()

# === TUŞ OLAYLARINI İŞLEYEN FONKSİYONLAR ===
def on_key_pressed(key):
    lcd_clear()
    lcd_write("BASILDI:", 0, 0)
    lcd_write(str(key), 1, 0)

def on_key_released(key, duration):
    lcd_clear()
    lcd_write("BIRAKILDI:", 0, 0)
    lcd_write(str(key), 1, 0)
    lcd_write(f"Sure: {duration:.2f}s", 2, 0)

# === KEYPAD AYARLARI ===
rows = [getattr(board, pin) for pin in HARDWARE_CONFIG["rows"]]
cols = [getattr(board, pin) for pin in HARDWARE_CONFIG["cols"]]
keys = HARDWARE_CONFIG["keys"]

lcd.set_backlight(True)
lcd_clear()
lcd_write("DHCP baglaniyor...", 0)

# === ETHERNET BAĞLANTISI ===
try:
    import adafruit_connection_manager
    import adafruit_requests
    from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

    cs = digitalio.DigitalInOut(board.GP17)
    reset = digitalio.DigitalInOut(board.GP20)
    spi = busio.SPI(board.GP18, board.GP19, board.GP16)

    eth = WIZNET5K(spi, cs, reset, is_dhcp=True)
    while not eth.link_status:
        lcd_write("Baglanti bekleniyor...", 1)
        time.sleep(0.5)

    lcd_clear()
    lcd_write("IP ALINDI:", 0)
    lcd_write(eth.pretty_ip(eth.ip_address), 1)
    time.sleep(2000)

    # Ping yerine HTTP isteği ile test
    lcd_clear()
    lcd_write("Ping: 192.168.1.1", 0)
    start = time.monotonic()
    try:
        pool = adafruit_connection_manager.get_radio_socketpool(eth)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
        requests = adafruit_requests.Session(pool, ssl_context)
        response = requests.get("http://192.168.1.1")
        duration = time.monotonic() - start
        lcd_write(f"Ping OK: {duration:.2f}s", 1)
        response.close()
    except Exception as e:
        duration = time.monotonic() - start
        print("Ping FAIL:", str(e))
        print(f"Süre: {duration:.2f}s")

    time.sleep(2)

except Exception as e:
    print("ETH HATA:", str(e))
    time.sleep(3)

# === KEYPAD AKTİFLEŞTİRME ===
lcd_clear()
lcd_write("Keypad ekran modu", 0)

keypad_handler = KeypadHandler(rows, cols, keys, on_key_pressed, on_key_released)

while True:
    keypad_handler.update()
    time.sleep(0.05)

