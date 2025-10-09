# örnek kullanım
from common.utils import RingBuffer

queue = RingBuffer(size=32)

# core1 (thread)
def core1_loop():
    import time
    while True:
        key = scan_keypad_once()
        if key:
            if not queue.push(key):
                print("queue full, drop", key)
        time.sleep(0.01)

# core0 (async)
async def ws_loop(ws):
    while True:
        key = queue.pop()
        if key:
            await ws.wsTalk('fnIslemi', args={'id': key})
        await asyncio.sleep(0.02)
