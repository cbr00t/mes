### devBase.py (Ortak Modül)
from common import *
from config import hw

class BaseKeypad:
    def __init__(self):
        c = hw.keypad
        s = self.state = NS(
            labels = c.keys,
            debounce_ms = c.debounce_ms,
            last = [
                # key, ts, lastTS, released
                None, None, None, False
            ],
            pin = (
                # row, col
                [Pin(p, Pin.OUT, value=1) for p in c.rows],              # PASIF HIGH
                [Pin(p, Pin.IN, Pin.PULL_UP) for p in c.cols]
            )
        )
        s.ln = (
            # row, col  (lengths)
            len(s.pin[0]), len(s.pin[1])
        )
        s.rng = (
            # row, col   (ranges)
            range(s.ln[0]), range(s.ln[1])
        )
        pass
    def update(self):
        s = self.state
        try:
            l = self.scanKeyState()
            key = l[0]; _ts = l[1]
            _tsDiff = l[2]; released = l[3]
            if not (key and _ts):
                return False
            rec = (
                # key, rfid, duration, ts, tsDiff, released
                key, None, None, _ts, _tsDiff, released
            )
            shared.queues.key.push(rec)
            return True
        except Exception as ex:
            print("Keypad tarama hatası:", ex)
            print_exception(ex)
        return self
    def scanKeyState(self):
        return None
