import typing as t
import aiohttp
import orjson

import router
import logging

from fastapi import responses, FastAPI, Request
from gateway import Gateway, gateway_connect, GatewayException, RoomUnknown
from models import Message, User
from redis import redis
from utils import (
    create_room_id,
    session_valid,
)


ALTER_ROOM_URL = "http://spooderfy_gateway:5051/alter?op={}&room_id={}"
WS_EMITTER_URL = "ws://spooderfy_gateway:5051/emitters"

DISCORD_AVATAR = "https://images.discordapp.net/avatars/" \
                 "{user_id}/{avatar}.png?size=512"

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


class BaseGatewayEnabled:
    def __init__(self, app: FastAPI):
        self.app = app

        # Startup - Shutdown
        self.app.on_event("startup")(self.start_up)
        self.app.on_event("shutdown")(self.shutdown)

        self.ws: t.Optional[Gateway] = None
        self.session: t.Optional[aiohttp.ClientSession] = None

    async def start_up(self):
        """
        Called when the first is first started and loads,
        this allows us to start our connection to the gateway as an
        emitter and also create a session that we can use later on.
        """

        self.session = aiohttp.ClientSession()
        self.ws = await gateway_connect(WS_EMITTER_URL)
        print("[ GATEWAY ] CONNECTED")

    async def shutdown(self):
        """
        Called when the server begins to shutdown which closes the ws connection
        and the aiohttp session correctly making everything nice :=)
        """

        await self.ws.shutdown()
        await self.session.close()


class PlayerEndpoints(BaseGatewayEnabled, router.Blueprint):

    @router.endpoint(
        "/api/player/{room_id:str}/play",
        endpoint_name="Play Player",
        description="Used to play a set player",
        methods=["PUT"],
    )
    async def play_player(self, request: Request, room_id: str):
        """
        Begins the play the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        if not (await session_valid(request)):
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        await self.ws.send({
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
    async def pause_player(self, request: Request, room_id: str):
        """
        Pauses the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        if not (await session_valid(request)):
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        await self.ws.send({
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
    async def seek_player(self, request: Request, room_id: str, position: int):
        """
        Seeks to a set position of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        if not (await session_valid(request)):
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        await self.ws.send({
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
    async def next_item(self, request: Request, room_id: str):
        """
        Switches to the next track of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        if not (await session_valid(request)):
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        await self.ws.send({
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
    async def previous_item(self, request: Request, room_id: str):
        """
        Switches to the previous track of the player of a specific room.

        Authorization is required in order to invoke this endpoint
        otherwise it wont emit to the gateway.
        """

        if not (await session_valid(request)):
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        await self.ws.send({
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


class MessageChat(BaseGatewayEnabled, router.Blueprint):
    @router.endpoint(
        "/api/room/{room_id:str}/message",
        endpoint_name="Send Message",
        description="Send a message to the set chat room.",
        methods=["PUT"],
    )
    async def send_message(self, request: Request, room_id: str, msg: Message):
        """
        Sends a message to the give room, this is limited to 2 messages / sec
        instead of Discord's limit due to the global limit of the webhooks
        and load on our servers.
        """

        session_id = request.cookies.get("session")
        if session_id is None:
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        session = await redis['sessions'].get(session_id)
        if session is None:
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        session = orjson.loads(session.decode())
        user = User(**session)

        await self.ws.send({
            "room_id": room_id,
            "message": {
                "op": OP_MESSAGE,
                "content": msg.content,
                "user_id": user.id,
                "username": user.username,
                "avatar": DISCORD_AVATAR.format(user_id=user.id, avatar=user.avatar),
            }
        })

        return responses.ORJSONResponse({"status": 200, "message": "OK"})


class GateKeeping(BaseGatewayEnabled, router.Blueprint):
    @router.endpoint(
        "/api/create/room",
        endpoint_name="Create Room",
        description="Creates a room given the required data",
        methods=["POST"],
    )
    async def create_room(self):
        """
        Creates a room given that the relevant data is given by the POST
        body of the request. A responding payload will be sent back giving
        the room info like Id.
        """

        room_id = create_room_id()

        try:
            await self.alter_gateway(room_id, CREATE)
            await redis['rooms'].set(room_id, "")
        except GatewayException:
            return responses.ORJSONResponse({
                "status": 500,
                "message": "Gateway responded with 4xx or 5xx code."
            })

        return responses.ORJSONResponse({
            "status": 200,
            "message": "Room Created!",
            "room_id": room_id
        })

    @router.endpoint(
        "/api/room/{room_id:str}/delete",
        endpoint_name="Delete Room",
        description="Deletes and terminates the room session, any existing"
                    "connections to the gateway will be terminated and closed.",
        methods=["DELETE"],
    )
    async def delete_room(self, room_id: str):
        """
        Deletes and terminates the room session, any existing
        connections to the gateway will be terminated and closed.
        """

        try:
            await self.alter_gateway(room_id, DELETE)
            await redis['rooms'].delete(room_id, "")
        except RoomUnknown:
            return responses.ORJSONResponse({
                "status": 404,
                "message": "This room does not exist."
            })
        except GatewayException:
            return responses.ORJSONResponse({
                "status": 500,
                "message": "Gateway responded with 4xx or 5xx code."
            })

        return responses.ORJSONResponse({
            "status": 200,
            "message": "Room deleted",
        })

    async def alter_gateway(self, room_id: str, op: str):
        """
        Exposes the alter endpoint of the gateway HTTP endpoint, this
        ignores the session query however so use alter_session for session
        based systems.
        """

        url = ALTER_ROOM_URL.format(op, room_id)
        await self._post(url)

    async def _post(self, url):
        async with self.session.post(url) as resp:
            if resp.status == 404:
                raise RoomUnknown()
            elif resp.status >= 400:
                gatekeeper.log(
                    level=logging.FATAL,
                    msg=f"Error handling session status: {resp.status}",
                )
                raise GatewayException("Status Invalid")


def setup(app):
    app.add_blueprint(PlayerEndpoints(app))
    app.add_blueprint(MessageChat(app))
    app.add_blueprint(GateKeeping(app))
