from common import *
import app

async def main():
    await app.init()
    await app.run()
    # thread(wsTest2)
    # while True:
    #     await asleep(.1)







async def wsTest():
    ws = shared.dev.ws
    await ws.open()
    print(await ws.recv())
    print(await ws.recv(2))
    sleep(1)
    print(await ws.wsTalk(api='ping'))
    sleep(1)
    print(await ws.wsTalk(api='getSessionInfo'))
    print(await ws.wsTalk(api='getSessionInfo'))
    print(await ws.wsTalk(api='getSessionInfo'))
    await ws.close()

async def wsTest2():
    # led = shared.dev.led
    # led.write('TURKUAZ')
    # buzzer = shared.dev.buzzer
    # await buzzer.beep(freq=500, duration=1)
    # await buzzer.beep(freq=200, duration=1)
#     rfid = shared.dev.rfid
#     while True:
#         _id = await rfid.read()
#         if _id: print(_id)
#         await asleep(0.1)
    keypad = shared.dev.keypad
    keypad.set_onPressed(app.onKeyPressed)
    while True:
        await keypad.update()
        await asleep(.05)



async_run(main)
