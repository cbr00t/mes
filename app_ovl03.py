from common import *
from config import local, app
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
            lcd.writeLineIfReady(f'* [{sentCount}] GITTI', 2, 0)
            keyQueue_clear()
        else:
            lcd.writeLineIfReady(f'* WS ILETISIM SORUNU', 2, 0)

def updateMainScreen():
    if lcdIsBusy(): return False
    lastTime = shared.lastTime
    if lastTime.updateMainScreen and monotonic() - lastTime.updateMainScreen <= 0.5: return False
    dev = shared.dev; lcd = dev.lcd;
    renderAppTitle()
    # if lcdCanBeCleared(): lcd.clearLineIfReady(range(1, lcd.getRows() - 1))
    rec = shared.curStatus
    rec = rec and rec[0] if isinstance(rec, list) else rec
    if not rec: return False
    _rec = {k: v for k, v in rec.items() if 'Sure' not in k}
    text = json.dumps(_rec)
    if text != shared._updateMainScreen_lastDebugText:
        print(f'\nstatus_check:  \n  {text}\n')
        shared._updateMainScreen_lastDebugText = text
        lcd.writeLineIfReady(f"U:{int(rec.get('onceUretMiktar'))}+{int(rec.get('aktifUretMiktar'))}  C:{rec.get('onceCevrimSayisi')}+{int(rec.get('aktifCevrimSayisi'))}", 1, 0)
        lcd.writeLineIfReady(f"S:{int(rec.get('isSaymaInd'))}/{int(rec.get('isSaymaSayisi'))}    D:{rec.get('durumKod')}", 2, 0)
        lastTime.updateMainScreen = monotonic()
    return True

def renderAppTitle():
    dev = shared.dev; lcd = dev.lcd; sock = dev.sock
    # lcd.clearLine(0)
    lcd.writeIfReady(f'v{version2Str(app.version)}  ', 0, 0)
    shared._appTitleRendered = True
