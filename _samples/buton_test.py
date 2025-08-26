import time
import board
from digitalio import DigitalInOut
from adafruit_matrixkeypad import Matrix_Keypad

# 📌 4 SATIR ve 5 SÜTUN pinleri (sen kendi pinlerini yazabilirsin)
rows = [board.GP12, board.GP13, board.GP14, board.GP15]  # 4 adet satır pini
cols = [board.GP7, board.GP8, board.GP9, board.GP10, board.GP11]  # 5 adet sütun pini

# 🧮 Tuş dizilimi (4 satır x 5 sütun)
keys = [
    ["F1", "1", "2", "3", "X"],
    ["F2", "4", "5", "6", "^"],
    ["F3", "7", "8", "9", "V"],
    ["F4", "ESC", "0", "ENTER", None]
]

# ⌨️ Keypad nesnesini oluştur
keypad = Matrix_Keypad(rows, cols, keys)

print("Keypad aktif, tuşlara basın...")

# 🔄 Sürekli kontrol döngüsü
while True:
    pressed = keypad.pressed_keys
    if pressed:
        print("Basılan tuşlar:", pressed)
    time.sleep(0.1)

