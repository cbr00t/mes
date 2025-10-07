### devBase.py (Ortak Modül)

from common import *
from config import hw

class BaseBuzzer:
    def __init__(self):
        self.buzzer = None
    async def beep(self, freq=None, duration=None, pause=None):
        buzz = self.buzzer
        if buzz is None:
            return self
        c = hw.buzzer
        if freq is None: freq = c.freq
        if duration is None: duration = c.duration
        if pause is None: pause = c.pause
        buzz.freq(freq)           # frekans Hz
        buzz.duty_u16(32768)      # %50 duty cycle
        await asleep(duration)    # calarken bekle
        buzz.duty_u16(0)          # kapat
        if pause:
            await asleep(pause)   # bekle
        return self
