import time
from adafruit_matrixkeypad import Matrix_Keypad

class KeypadHandler:
    def __init__(self, row_pins, col_pins, keys, on_press, on_release):
        self.keypad = Matrix_Keypad(row_pins, col_pins, keys)
        self.on_press = on_press
        self.on_release = on_release
        self._pressed = {}

    def update(self):
        now = time.monotonic()
        current_keys = set(self.keypad.pressed_keys)

        # Basılan yeni tuşları algıla
        for key in current_keys:
            if key not in self._pressed:
                self._pressed[key] = now
                if self.on_press:
                    self.on_press(key)

        # Bırakılan tuşları kontrol et
        released_keys = [key for key in self._pressed if key not in current_keys]
        for key in released_keys:
            pressed_time = self._pressed.pop(key)
            duration = now - pressed_time
            if self.on_release:
                self.on_release(key, duration)
