import time
import board
import busio
import pwmio  # <-- Pasif buzzer (PWM) için
# Aktif buzzer kullanacaksan şunları aç:
# from digitalio import DigitalInOut, Direction

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

# === BUZZER (GP26) ===
# Pasif buzzer (PWM):
buzzer = pwmio.PWMOut(board.GP26, duty_cycle=0, frequency=1000, variable_frequency=True)

def beep(freq=1200, ms=60, duty=32768):
    buzzer.frequency = freq
    buzzer.duty_cycle = duty  # ~%50
    time.sleep(ms/1000)
    buzzer.duty_cycle = 0

# Aktif buzzer (yalnızca ON/OFF) kullanıyorsan:
# buzzer = DigitalInOut(board.GP26)
# buzzer.direction = Direction.OUTPUT
# def beep(freq=0, ms=60, duty=0):
#     buzzer.value = True
#     time.sleep(ms/1000)
#     buzzer.value = False

# === TUŞ OLAYLARINI İŞLEYEN FONKSİYONLAR ===
def on_key_pressed(key):
    lcd_clear()
    lcd_write("BASILDI:", 0, 0)
    lcd_write(str(key), 1, 0)
    # Tuş sesi (isteğe göre frekansı tuşa göre çeşitlendirebilirsin)
    try:
        k = int(str(key))  # sayıysa farklı ton
        beep(800 + 80*k, 50)
    except:
        beep(1000, 50)

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
lcd_write("Keypad ekran modu", 0)

keypad_handler = KeypadHandler(rows, cols, keys, on_key_pressed, on_key_released)

while True:
    keypad_handler.update()
    time.sleep(0.05)
