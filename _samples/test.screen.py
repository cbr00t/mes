# lcd_quick_hello.py — MicroPython, I2C1 @ GP27(SCL)/GP26(SDA), addr=0x27
from machine import I2C, Pin
import time

# PCF8574 pin dizilimi: D7 D6 D5 D4 BL EN RW RS (yaygın backpack)
RS=0x01; RW=0x02; EN=0x04; BL=0x08

i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
ADDR = 0x27

def w(b): i2c.writeto(ADDR, bytes([b]))

def pulse(b):
    w(b | EN); time.sleep_us(500)
    w(b & ~EN); time.sleep_us(100)

def write4(nib, mode=0):
    d = (nib & 0xF0) | mode | BL  # BL açık
    pulse(d)

def send(byte, mode=0):
    write4(byte & 0xF0, mode)
    write4((byte << 4) & 0xF0, mode)

def cmd(c):  send(c, 0)
def putc(ch): send(ch, RS)

def init():
    time.sleep_ms(50)
    # 4-bit init
    write4(0x30); time.sleep_ms(5)
    write4(0x30); time.sleep_us(150)
    write4(0x30); time.sleep_us(150)
    write4(0x20); time.sleep_us(150)
    # Function set: 4-bit, 2-line, 5x8
    cmd(0x28)
    # Display off
    cmd(0x08)
    # Clear
    cmd(0x01); time.sleep_ms(2)
    # Entry mode: increment
    cmd(0x06)
    # Display on
    cmd(0x0C)

def move(col, row):
    # 20x4 adres haritası
    base = [0x00, 0x40, 0x14, 0x54]
    cmd(0x80 | (base[row] + col))

# ---- Çalıştır ----
init()
move(0,0)
for ch in "LCD Hello":
    putc(ord(ch))
move(0,1)
for ch in "Addr 0x27 OK":
    putc(ord(ch))
