# lcd_line1_simple.py — MicroPython (Pico / Pico W / Pico 2 W)
import machine
import time

from machine import I2C, Pin
from pico_i2c_lcd import I2cLcd

I2C_ADDR     = 0x27
I2C_NUM_ROWS = 4
I2C_NUM_COLS = 20

# I2C1: SCL=GP27, SDA=GP26 (senin örneğinle aynı)
i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

lcd.clear()
time.sleep(1)
lcd.move_to(0, 0)  # 1. satır, 0. sütun
text = ' ' * I2C_NUM_COLS
lcd.putstr(text[:I2C_NUM_COLS])  # 1. satıra sığan kadar yaz

lcd.move_to(0, 0)  # 1. satır, 0. sütun
text = "Bu çok uzun bir metin"
lcd.putstr(text[:I2C_NUM_COLS])  # 1. satıra sığan kadar yaz

