import aiohttp
import asyncio
import orjson
import typing as t


async def gateway_connect(url: str) -> "Gateway":
    session = aiohttp.ClientSession()
    gw = Gateway(session, url)
    await gw.connect()
    return gw


class Gateway:
    """
    The Gateway is a general class that manages the connection to the
    gateway server, Upon disconnects it will attempt to reconnect a
    maximum of 3 times before raising an error.

    The WS is monitored by a internal task.
    """

    def __init__(self, session: aiohttp.ClientSession, url: str):
        self.url = url
        self.loop = asyncio.get_event_loop()
        self.session = session
        self.ws: t.Optional[aiohttp.ClientWebSocketResponse] = None

    async def connect(self):
        for _ in range(3):
            try:
                self.ws = await self.session.ws_connect(self.url)
                self.loop.create_task(self._watcher())
                return
            except ConnectionError:
                await asyncio.sleep(3)
        raise ConnectionRefusedError("Could not connect to the socket")

    async def _watcher(self):
        while self.ws is not None and not self.ws.closed:
            await asyncio.sleep(1)
        await self.connect()

    async def shutdown(self):
        if self.ws is not None:
            await self.ws.close()
        await self.session.close()

    async def send(self, data: t.Union[dict, list]):
        if self.ws is None:
            raise TypeError("Ws was None at time of sending")

        try:
            await self.ws.send_bytes(orjson.dumps(data))
        except ConnectionError:
            await self.connect()

            # Try send it again
            await self.ws.send_bytes(orjson.dumps(data))