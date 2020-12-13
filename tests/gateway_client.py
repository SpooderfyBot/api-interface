import aiohttp
import asyncio


async def read(ws: aiohttp.ClientWebSocketResponse, fut: asyncio.Future):
    while not ws.closed:
        print(await ws.receive())

    fut.set_result(None)


async def write(ws: aiohttp.ClientWebSocketResponse, fut: asyncio.Future):
    pass


async def main():
    loop = asyncio.get_running_loop()

    session = aiohttp.ClientSession()
    ws: aiohttp.ClientWebSocketResponse = await session.ws_connect(
        "wss://spooderfy.com/gateway"
        "?id=63URK"
    )
    print("connected")

    fut = loop.create_future()
    loop.create_task(read(ws, fut))

    await write(ws, fut)

    await fut

    await ws.close()
    await session.close()


asyncio.run(main())
