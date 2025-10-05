### devBase.py (Ortak Modül)

from common import *
from config import hw
from machine import Pin, PWM

class BaseBuzzer:
    def __init__(self):
        c = hw.buzzer
        self.buzzer = PWM(Pin(c.pin))
    def beep(self, freq=None, duration=None, pause=None):
        c = hw.buzzer
        if freq is None: freq = c.freq
        if duration is None: duration = c.duration
        if pause is None: pause = c.pause
        buzz = self.buzzer
        buzz.freq(freq)           # frekans Hz
        buzz.duty_u16(32768)      # %50 duty cycle
        sleep(duration)           # bu frekansta çal
        buzz.duty_u16(0)          # kapat
        sleep(pause)              # bekle
        return self
