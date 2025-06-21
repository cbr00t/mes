from common import *
from config import local
from time import sleep, monotonic
import json
from traceback import print_exception

def keyQueue_add(item):
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    keyQueue.append(item)
    return item
def keyQueue_pop(item):
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    keyQueue.pop(0)
    return item
def keyQueue_clear():
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    if keyQueue: keyQueue.clear()
def processQueues():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock
    queues = shared.queues; keyQueue = queues.key = queues.key or []
    lcdRows = range(2, 3)
    if keyQueue:
        for item in keyQueue:
            ts = item.get('ts')
            if ts:
                item['tsDiff'] = round((monotonic() - ts) * 1000)
                item.pop('ts', None)
        result = sock.wsTalk('fnIslemi', None, keyQueue)
        debug_result = json.dumps(result) if result else '*empty*'
        print(f'    [processQueue] - [fnIslemi] - result: {debug_result})')
        if isinstance(result, dict) and bool(result.get('isError')) == False:
            sentCount = len(keyQueue)
            if not lcdIsBusy(): lcd.clearLine(lcdRows); lcd.writeIfReady(f'* [{sentCount}] GITTI', 2, 0)
            keyQueue_clear()
        else:
            if not lcdIsBusy(): lcd.clearLine(lcdRows); lcd.writeIfReady(f'* WS ILETISIM SORUNU', 2, 0)


def updateMainScreen():
    rec = shared.curStatus
    if not rec or lcdIsBusy(): return False
    text = json.dumps(rec)
    print(f'\nstatus_check:  \n  {text}\n')
    return True



