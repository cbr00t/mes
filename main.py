from common import *

async def main():
    import app
    await app.init()
    await app.run()
    # await test3()






















# async def wsTest():
#     ws = shared.dev.ws
#     await ws.open()
#     print(await ws.recv())
#     print(await ws.recv(2))
#     sleep(1)
#     print(await ws.wsTalk(api='ping'))
#     sleep(1)
#     print(await ws.wsTalk(api='getSessionInfo'))
#     print(await ws.wsTalk(api='getSessionInfo'))
#     print(await ws.wsTalk(api='getSessionInfo'))
#     await ws.close()
# 
# async def wsTest2():
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
    # keypad = shared.dev.keypad
    # keypad.set_onPressed(app.onKeyPressed)
    # while True:
    #     await keypad.update()
    #     await asleep(.05)

async def test3():
    def core1():
        queue = shared.queue.keypad
        i = 0
        while True:
            i = i + 1
            queue.push(i)
            sleep(.005)
    async def core0():
        queue = shared.queue.keypad
        while True:
            i = queue.pop()
            if i is not None:
                print(i)
            await asleep(.001)
    thread(core1)
    await core0()


async_run(main)
