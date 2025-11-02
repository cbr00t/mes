### devBase.py (Ortak Modül)
from common import *
# from config import hw
if isMicroPy():
    from mfrc522 import MFRC522

class BaseRFID:
    def __init__(self):
        self.state = NS(
            # card, ts
            last = [0, None]
        )
        self._defaultKey = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        # self._defaultKey = int.from_bytes(bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]), byteorder)
    def reset(self):
        self.state.last[0] = 0
        return self
    def update(self):
        try:
            rfid = self.read()
            if not rfid:
                return False
            ts = ticks_ms()
            l = self.state.last
            l[0] = rfid
            l[1] = ts
            print(f'[DEBUG]  rfid: {rfid} | last: {l}')
            rec = (
                # key, rfid, duration, ts, tsDiff, released
                'kart', rfid, None, ts, None, None
            )
            shared.queues.key.push(rec)
            buzzer = shared.dev.buzzer
            if buzzer:
                buzzer.beep(2500, .2)
            return True
        except MemoryError as ex:
            print(f"[ERROR]  RFID tarama hatası:", ex)
        except Exception as ex:
            print(f"[ERROR]  RFID tarama hatası:", ex)
            print_exception(ex)
        return False 
    def read(self):
        return None
