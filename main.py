from common import *
import app

async def main():
    await app.init()
    await app.run()
    # await wsTest()

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

async_run(main)
