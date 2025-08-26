from common import *
def run():
    dev = shared.dev; lcd = dev.lcd
    i = 0; lcd.on()
    interval = 5;
    while True:
        i += 1; delay = 1; text = '   EAT ME!'
        if i == interval:
            i = 0; delay = 3; text = 'DONT EAT ME'
        lcd.writeLine(text, 2, 4)
        sleep(1);
