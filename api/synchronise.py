import asyncio
import orjson
import typing as t
import aiohttp
import router

from fastapi import responses, FastAPI

EMITTER_URL = "http://127.0.0.1:8888/alter"
WS_EMITTER_URL = "ws://127.0.0.1:8888/emitters"


OP_PLAY = 0
OP_PAUSE = 1
OP_SEEK = 2
OP_NEXT = 3
OP_PREV = 4
OP_MESSAGE = 5


class PlayerEndpoints(router.Blueprint):
    def __init__(self, app: FastAPI):
        self.app = app
        self.app.on_event("startup")(self.start_up)
        self.ws: t.Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: t.Optional[aiohttp.ClientSession] = None

    async def start_up(self):
        """
        Called when the first is first started and loads,
        this allows us to start our connection to the gateway as an
        emitter and also create a session that we can use later on.
        """

        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(EMITTER_URL)
        print("Connected to Gateway")

    async def shutdown(self):
        """
        Called when the server begins to shutdown which closes the ws connection
        and the aiohttp session correctly making everything nice :=)
        """

        await self.ws.close()
        await self.session.close()

    async def send_data(self, data: dict):
        data = orjson.dumps(data)
        await self.ws.send_bytes(data)

    @router.endpoint(
        "/api/player/{room_id:int}/play",
        endpoint_name="Play Player",
        description="Used to play a set player",
        methods=["PUT"],
    )
    async def play_player(self, room_id: int):
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
        "/api/player/{room_id:int}/pause",
        endpoint_name="Pause the player",
        description="Used to pause a set player",
        methods=["PUT"],
    )
    async def pause_player(self, room_id: int):
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
        "/api/player/{room_id:int}/seek",
        endpoint_name="Seek the player",
        description="Used to start a seek to a specific player",
        methods=["PUT"],
    )
    async def seek_player(self, room_id: int, position: int):
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
        "/api/player/{room_id:int}/next",
        endpoint_name="Next Video",
        description="Cycles to the next item in a playlist",
        methods=["PUT"],
    )
    async def next_item(self, room_id: int):
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
        "/api/player/{room_id:int}/prev",
        endpoint_name="Previous Video",
        description="Cycles to the previous item in a playlist",
        methods=["PUT"],
    )
    async def previous_item(self, room_id: int):
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
        "/api/room/{room_id:int}/message",
        endpoint_name="Send Message",
        description="Send a message to the set chat room.",
        methods=["PUT"],
    )
    async def pause_player(self, room_id: str):
        print(room_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


def setup(app):
    app.add_blueprint(PlayerEndpoints(app))
    app.add_blueprint(MessageChat(app))
