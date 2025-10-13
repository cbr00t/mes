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
    def update(self):
        s = self.state
        dev = shared.dev; buzzer = dev.buzzer
        try:
            l = self.scanKeyState()
            if l is None:
                return False
            
            key, _ts, _tsDiff, released = l
            if not (key and _ts):
                return False
            
            # key, rfid, duration, ts, tsDiff, released
            rec = (key, None, None, _ts, _tsDiff, released)
            shared.queues.key.push(rec)
            busy()
            
            if buzzer:
                buzzer.beep(3500, .1)
            
            # reset sadece press eventlerinde
            if not released:
                # key, ts, lastTS, released
                # lock = allocate_lock()
                # with lock:
                l[0] = l[1] = l[2] = None
                l[3] = False
            return True
        except Exception as ex:
            print("Keypad tarama hatası:", ex)
            print_exception(ex)
            return False

    def scanKeyState(self):
        return None
