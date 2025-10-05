from common import *
import app

async def main():
    await app.init()
    await app.run()

asyncio.run(main())
