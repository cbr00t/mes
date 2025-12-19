### devBase.py (Ortak Modül)
from common import *

class BasePLC:
    def __init__(self):
        self.state = NS(
            # isBitti, ts
            last = [False, None]
        )
    def reset(self):
        self.state.last[0] = False
        return self
    def update(self):
        try:
            l = self.state.last
            isBitti = self.read()
            if isBitti != l[0]:
                print(f'[DEBUG]  plc  [ isBitti: {isBitti} | last: {l} ]')
                busy()
                ts = ticks_ms()
                tsDiff = ticks_diff(ts, l[1]) if l[1] else None
                if isBitti:
                    rec = (
                        # key, rfid, duration, ts, tsDiff, released
                        'secondary', 'plc', None, ts, tsDiff, False
                    )
                    shared.queues.key.push(rec)
                    buzzer = shared.dev.buzzer
                    if buzzer:
                        buzzer.beep(1500, .3)
                l[0] = isBitti
                l[1] = ticks_ms()
            return True
        except MemoryError as ex:
            print(f"[ERROR]  RFID tarama hatası:", ex)
        except Exception as ex:
            print(f"[ERROR]  RFID tarama hatası:", ex)
            print_exception(ex)
        return False 
    def read(self):
        return None
