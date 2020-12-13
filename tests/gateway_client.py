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
        "ws://spooderfy.com/gateway"
        "?id=XGI7X"
        "&session=b95e8c8f4cdf4065ba86ac006d93b57c",
    )
    print("connected")

    fut = loop.create_future()
    loop.create_task(read(ws, fut))

    await write(ws, fut)

    await fut

    await ws.close()
    await session.close()


asyncio.run(main())
