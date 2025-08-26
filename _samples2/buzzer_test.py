import time
import board
import pwmio

# GP26 pinini çıkış olarak ayarla (PWM için)
buzzer = pwmio.PWMOut(board.GP26, duty_cycle=0, frequency=440, variable_frequency=True)

def beep(frequency, duration):
    buzzer.frequency = frequency
    buzzer.duty_cycle = 32768  # %50 duty cycle (orta seviye ses)
    time.sleep(duration)
    buzzer.duty_cycle = 0      # sesi kapat

while True:
    beep(1000, 0.5)  # 1000 Hz frekansta 0.5 saniye ses
    time.sleep(0.5)  # 0.5 saniye sessizlik