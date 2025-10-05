# matrix_keypad_micropython.py
# Raspberry Pi Pico / Pico 2 W + MicroPython için
from machine import Pin
import time

class MatrixKeypad:
    """
    rows:  OUTPUT pin numaraları (ör. [12,13,14,15])
    cols:  INPUT_PULLUP pin numaraları (ör. [7,8,9,10,11])
    labels:  row x col string etiket matrisi (None geçersiz tuş)
    """
    def __init__(self, row_pins, col_pins, labels, debounce_ms=30, multi=True):
        self._rows = [Pin(p, Pin.OUT, value=1) for p in row_pins]   # pasif HIGH
        self._cols = [Pin(p, Pin.IN, Pin.PULL_UP) for p in col_pins]
        self._labels = labels
        self._rlen = len(self._rows)
        self._clen = len(self._cols)
        self._debounce = debounce_ms
        self._multi = multi

        # Debounce durumları
        self._stable = [[False]*self._clen for _ in range(self._rlen)]
        self._last_read = [[False]*self._clen for _ in range(self._rlen)]
        self._last_change = [[0]*self._clen for _ in range(self._rlen)]

    def _now(self):
        return time.ticks_ms()

    def _scan_raw(self):
        """True=basılı, False=serbest"""
        state = [[False]*self._clen for _ in range(self._rlen)]
        for r, rpin in enumerate(self._rows):
            rpin.value(0)                  # o satırı aktif et (LOW)
            time.sleep_us(50)              # kısa stabilizasyon
            for c, cpin in enumerate(self._cols):
                # Pull-up var; LOW -> tuş basılı
                state[r][c] = (cpin.value() == 0)
            rpin.value(1)                  # pasif (HIGH)
        return state
    def _debounced(self):
        raw = self._scan_raw()
        now = self._now()
        for r in range(self._rlen):
            for c in range(self._clen):
                if raw[r][c] != self._last_read[r][c]:
                    self._last_read[r][c] = raw[r][c]
                    self._last_change[r][c] = now
                else:
                    if time.ticks_diff(now, self._last_change[r][c]) >= self._debounce:
                        self._stable[r][c] = self._last_read[r][c]
        return self._stable
    @property
    def pressed_keys(self):
        """Basılı tuş etiketlerini liste olarak döndürür."""
        st = self._debounced()
        out = []
        for r in range(self._rlen):
            for c in range(self._clen):
                if st[r][c]:
                    lab = self._labels[r][c]
                    if lab:
                        out.append(lab)
                        if not self._multi:
                            return [lab]
        return out


# ====== SENİN PIN/ETİKET DİZİLİMİN ======
ROWS = [12, 13, 14, 15]            # board.GP12..GP15
COLS = [7, 8, 9, 10, 11]           # board.GP7..GP11
KEYS = [
    ["F1", "1", "2", "3", "X"],
    ["F2", "4", "5", "6", "^"],
    ["F3", "7", "8", "9", "V"],
    ["F4", "ESC", "0", "ENTER", None],
]

# ====== DEMO KULLANIM ======
def main(duration_s=10):
    kp = MatrixKeypad(ROWS, COLS, KEYS, debounce_ms=30, multi=True)
    print("Matrix keypad dinleniyor... ({} sn)".format(duration_s))
    t0 = time.ticks_ms()
    last = set()
    while time.ticks_diff(time.ticks_ms(), t0) < duration_s*1000:
        pressed = set(kp.pressed_keys)
        # değişiklik varsa yazdır
        if pressed != last:
            if pressed:
                print("Basılı:", ",".join(sorted(pressed)))
            else:
                print("Serbest")
            last = pressed
        time.sleep_ms(20)

if __name__ == "__main__":
    main(999999)   # sürekli dinle (Ctrl+C ile çık)
