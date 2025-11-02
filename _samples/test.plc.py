# gp28_adc_threshold_transitions.py — MicroPython (Pico / Pico 2 / 2W)
from machine import ADC, Pin
import utime

PIN_NO       = 28        # GP28 = ADC2
VREF         = 3.3       # ADC referansı (tipik 3.3 V)
THRESHOLD_V  = 2.9       # Eşik
PERIOD_MS    = 300       # 0.3 sn'de bir ölç

adc = ADC(Pin(PIN_NO))

def read_volts():
    raw = adc.read_u16()              # 0..65535 (12-bit ADC ölçekli)
    return raw * VREF / 65535.0

# İlk durum
v = read_volts()
state = 1 if v >= THRESHOLD_V else 0
print("Başlatıldı: {:.3f} V -> {}".format(v, state))

last_state = state

while True:
    v = read_volts()
    state = 1 if v >= THRESHOLD_V else 0

    if state != last_state:
        if state == 1:
            print("1 oldu  | {:.3f} V".format(v))
        else:
            print("0 oldu  | {:.3f} V".format(v))
        last_state = state

    utime.sleep_ms(PERIOD_MS)
