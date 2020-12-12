import aiohttp
import asyncio


async def main():
    session = aiohttp.ClientSession()
    await session.ws_connect("ws://spooderfy.com/gateway?")


asyncio.run(main())
