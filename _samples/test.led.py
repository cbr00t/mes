from neopixel_pio import Neopixel2
import time

numpix = 10
# SM0, pin=GP1, renk sırası GRB
strip = Neopixel2(numpix, 0, 22, "GRB")
strip.brightness(42)

color = (255, 0, 0)

while True:
    strip.fill(color)
    strip.show()
    time.sleep(0.1)
