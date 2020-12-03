import asyncio

import orjson
import typing as t
import aiohttp
import router
import logging

from fastapi import responses, FastAPI

ALTER_ROOM_URL = "http://127.0.0.1:8888/alter?op={}&room_id={}"
WS_EMITTER_URL = "ws://127.0.0.1:8888/emitters"


CREATE = "create"
DELETE = "delete"
ADD_SESSION = "add_session"
REMOVE_SESSION = "remove_session"

OP_PLAY = 0
OP_PAUSE = 1
OP_SEEK = 2
OP_NEXT = 3
OP_PREV = 4
OP_MESSAGE = 5


gatekeeper = logging.getLogger("api-gatekeeper")


class PlayerEndpoints(router.Blueprint):
    def __init__(self, app: FastAPI):
        self.app = app

        # Startup - Shutdown
        self.app.on_event("startup")(self.start_up)
        self.app.on_event("shutdown")(self.shutdown)

        self.ws: t.Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: t.Optional[aiohttp.ClientSession] = None

    async def start_up(self):
        """
        Called when the first is first started and loads,
        this allows us to start our connection to the gateway as an
        emitter and also create a session that we can use later on.
        """

        self.session = aiohttp.ClientSession()
        await self.connect()

    async def connect(self):
        session = aiohttp.ClientSession()
        while True:
            try:
                self.ws = await session.ws_connect(WS_EMITTER_URL)
                return
            except (ConnectionResetError, ConnectionRefusedError):
                print("Couldn't connect to the WS, retry in:")
                print("3")
                await asyncio.sleep(1)
                print("2")
                await asyncio.sleep(1)
                print("1")
                await asyncio.sleep(1)

    async def shutdown(self):
        """
        Called when the server begins to shutdown which closes the ws connection
        and the aiohttp session correctly making everything nice :=)
        """

        await self.ws.close()
        await self.session.close()

    async def send_data(self, data: dict):
        data = orjson.dumps(data)
        try:
            await self.ws.send_bytes(data)
            return
        except ConnectionResetError:
            await self.connect()
        await self.ws.send_bytes(data)

    @router.endpoint(
        "/api/player/{room_id:str}/play",
        endpoint_name="Play Player",
        description="Used to play a set player",
        methods=["PUT"],
    )
    async def play_player(self, room_id: str):
        """
        Begins the play the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        await self.send_data({
            "room_id": room_id,
            "message": {
                "op": OP_PLAY,
            }
        })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{room_id:str}/pause",
        endpoint_name="Pause the player",
        description="Used to pause a set player",
        methods=["PUT"],
    )
    async def pause_player(self, room_id: str):
        """
        Pauses the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        await self.send_data({
            "room_id": room_id,
            "message": {
                "op": OP_PAUSE,
            }
        })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{room_id:str}/seek",
        endpoint_name="Seek the player",
        description="Used to start a seek to a specific player",
        methods=["PUT"],
    )
    async def seek_player(self, room_id: str, position: int):
        """
        Seeks to a set position of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        await self.send_data({
            "room_id": room_id,
            "message": {
                "op": OP_SEEK,
                "position": position,
            }
        })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{room_id:str}/next",
        endpoint_name="Next Video",
        description="Cycles to the next item in a playlist",
        methods=["PUT"],
    )
    async def next_item(self, room_id: str):
        """
        Switches to the next track of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        await self.send_data({
            "room_id": room_id,
            "message": {
                "op": OP_NEXT,
                "track": {  # todo add track fetching
                    "title": "xyz",
                    "reference_url": "xyz.com",
                },
            }
        })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{room_id:str}/prev",
        endpoint_name="Previous Video",
        description="Cycles to the previous item in a playlist",
        methods=["PUT"],
    )
    async def previous_item(self, room_id: str):
        """
        Switches to the previous track of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        await self.send_data({
            "room_id": room_id,
            "message": {
                "op": OP_PREV,
                "track": {  # todo add track fetching
                    "title": "xyz",
                    "reference_url": "xyz.com",
                },
            }
        })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


class MessageChat(router.Blueprint):
    def __init__(self, app):
        self.app = app

    @router.endpoint(
        "/api/room/{room_id:str}/message",
        endpoint_name="Send Message",
        description="Send a message to the set chat room.",
        methods=["PUT"],
    )
    async def pause_player(self, room_id: str):
        print(room_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


class GateKeeping(router.Blueprint):
    def __init__(self, app: FastAPI):
        self.app = app

        # Startup - Shutdown
        self.app.on_event("startup")(self.start_up)
        self.app.on_event("shutdown")(self.shutdown)

        self.ws: t.Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: t.Optional[aiohttp.ClientSession] = None

    async def start_up(self):
        """
        Called when the first is first started and loads,
        this allows us to start our connection to the gateway as an
        emitter and also create a session that we can use later on.
        """

        self.session = aiohttp.ClientSession()
        await self.connect()

    async def connect(self):
        session = aiohttp.ClientSession()
        while True:
            try:
                self.ws = await session.ws_connect(WS_EMITTER_URL)
                return
            except (ConnectionResetError, ConnectionRefusedError):
                print("Couldn't connect to the WS, retry in:")
                print("3")
                await asyncio.sleep(1)
                print("2")
                await asyncio.sleep(1)
                print("1")
                await asyncio.sleep(1)

    async def shutdown(self):
        """
        Called when the server begins to shutdown which closes the ws connection
        and the aiohttp session correctly making everything nice :=)
        """

        await self.ws.close()
        await self.session.close()

    async def send_data(self, data: dict):
        data = orjson.dumps(data)
        try:
            await self.ws.send_bytes(data)
        except ConnectionResetError:
            await self.connect()
        await self.ws.send_bytes(data)

    @router.endpoint(
        "/api/room/{room_id:str}/add/user",
        endpoint_name="Add user(s)",
        description="Add one or several users to the room.",
        methods=["POST"],
    )
    async def add_user(self, room_id: str, user_ids: t.List[str]):
        # Its a hack i know but i dont really want to make an entire system
        # on the gateway just for adding sessions instead of the existing
        # alter endpoint.
        for id_ in user_ids:
            url = (ALTER_ROOM_URL + "&session_id={}").format(ADD_SESSION, room_id, id_)
            async with self.session.post(url) as resp:
                if resp.status >= 400:
                    gatekeeper.log(
                        level=logging.FATAL,
                        msg=f"Error handling session status: {resp.status}",
                    )
                    return responses.ORJSONResponse({
                        "status": 500,
                        "message": "Error handling session with gateway."
                    })
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


def setup(app):
    app.add_blueprint(PlayerEndpoints(app))
    app.add_blueprint(MessageChat(app))
    app.add_blueprint(GateKeeping(app))
