from time import sleep
import json
from common import *
from config import local
import core

def init():
    global dev
    dev = core.getDevice()

def run():
    test()
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
    sleep(0.2)
    sock = dev.sock
    if not sock.isConnected():
        sock.open()
        sock.write({ 'ws': 'ws/genel', 'api': 'getSessionInfo' })
    resp = sock.read()
    if resp:
        print(f'rawSocket interrupt: [{json.dumps(resp)}]')
        sleep(1000)
