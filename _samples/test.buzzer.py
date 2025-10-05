import time
from machine import Pin, PWM

# GP21 pinine bağlı pasif buzzer
buzzer = PWM(Pin(21))

def beep(freq=440, duration=0.2, pause=0.05):
    buzzer.freq(freq)           # frekans Hz
    buzzer.duty_u16(32768)      # %50 duty cycle
    time.sleep(duration)        # bu frekansta çal
    buzzer.duty_u16(0)          # kapat
    time.sleep(pause)           # bekle

def test_buzzer_pattern():
    # klasik dört nota dizisi
    for f in (440, 660, 880, 1320):
        beep(f, 0.15, 0.05)

    time.sleep(0.5)

    # melodik tekrar
    for f in (523, 587, 659, 698, 784):   # do, re, mi, fa, sol
        beep(f, 0.2, 0.1)

# çalıştır
test_buzzer_pattern()
