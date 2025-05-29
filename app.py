from time import sleep
import json
from common import *
from config import local
import core

def init():
    global dev, req, sock, lcd, keypad
    dev = core.getDevice()
    sock = dev.sock; req = dev.req
    lcd = dev.lcd; keypad = dev.keypad
    keypad.set_onRelease(keypad_onRelease)

def run():
    # test()
    lcd.write('RUNNING', 0, 0)
    while True:
        loop()

def test():
    global dev; sock = dev.sock
    sock.open()
    sock.talk(json.dumps({
        'ws':   'ws/skyMES/makineDurum',
        'api':  'fnIslemi',
        'qs': { 'id': 2, 'ip': local.ip }
    }))
    sock.close()

def loop():
    global dev, sock
    sleep(0.05)
    sock = dev.sock
    if not sock.isConnected():
        sock.open()
        sock.write({ 'ws': 'ws/genel', 'api': 'getSessionInfo' })
    resp = sock.read()
    if resp:
        print(f'rawSocket interrupt: [{json.dumps(resp)}]')
        sleep(0.2)
    keypad.update()

def keypad_onPress(key):
    print(f'key_press: [{key}]')
def keypad_onRelease(key, duration):
    print(f'key_release: [{key}:{duration}]')

