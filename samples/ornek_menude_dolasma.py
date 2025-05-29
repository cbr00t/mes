#Bu örneğin denenmesi için enter tuşunu 2sn den fazla süre basılı tutun bu menüyü açacaktır.
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

def lcd_write(msg, row=0, col=0, invert=False):
    lcd.set_cursor_pos(row, col)
    prefix = "> " if invert else "  "
    msg_str = prefix + str(msg)
    msg_str = msg_str[:20]  # Trim if too long
    msg_str += ' ' * (20 - len(msg_str))  # Pad if too short
    lcd.print(msg_str)

def lcd_clear():
    lcd.clear()

# === MENÜ ===
menu_items = [f"menu{i+1}" for i in range(9)] + ["menuden cik"]
menu_index = 0
menu_mode = False

# === TUŞ OLAYLARI ===
def on_key_pressed(key):
    global menu_mode
    if key == "ENTER" and not menu_mode:
        lcd_clear()
        lcd_write("ENTER BASILI", 0)

def on_key_released(key, duration):
    global menu_mode, menu_index
    if key == "ENTER" and duration > 2:
        menu_mode = True
        menu_index = 0
        show_menu()
    elif menu_mode:
        if key == "V":
            menu_index = (menu_index + 1) % len(menu_items)
            show_menu()
        elif key == "^":
            menu_index = (menu_index - 1) % len(menu_items)
            show_menu()
        elif key == "ENTER":
            lcd_clear()
            lcd_write(f"{menu_items[menu_index]}", 0)
            lcd_write("menusu secildi", 1)
            time.sleep(2)
            if menu_items[menu_index] == "menuden cik":
                menu_mode = False
                lcd_clear()
                lcd_write("Keypad ekran modu", 0)
            else:
                show_menu()
    else:
        lcd_clear()
        lcd_write("BIRAKILDI:", 0)
        lcd_write(str(key), 1)
        lcd_write(f"Sure: {duration:.2f}s", 2)

def show_menu():
    lcd_clear()
    start = max(0, menu_index - 3)
    for i in range(start, min(start + 4, len(menu_items))):
        lcd_write(menu_items[i], i - start, invert=(i == menu_index))

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
