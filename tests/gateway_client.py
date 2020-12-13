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
        "ws://127.0.0.1:5051/ws"
        "?id=nvs34"
        "&session=1234",
        heartbeat=5
    )
    print("connected")

    fut = loop.create_future()
    loop.create_task(read(ws, fut))

    await write(ws, fut)

    await fut

    await ws.close()
    await session.close()


asyncio.run(main())
