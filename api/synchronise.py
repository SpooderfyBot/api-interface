import typing as t
import aiohttp
import router
import logging

from fastapi import responses, FastAPI, Request
from gateway import Gateway, gateway_connect
from models import Message, User
from redis import redis
from utils import create_session_id, session_valid


ALTER_ROOM_URL = "http:///spooderfy_gateway:5051/alter?op={}&room_id={}"
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

        session = await redis['session'].get(session_id)
        if session is None:
            return responses.ORJSONResponse({
                "status": 401,
                "message": "Unauthorized"
            }, status_code=401)

        user = User(**session)

        await self.ws.send({
            "room_id": room_id,
            "message": {
                "op": OP_MESSAGE,
                "message": msg.dict(),
                "user_id": user.id,
                "username": user.username,
                "avatar": DISCORD_AVATAR.format(user.id, user.avatar),
            }
        })

        return responses.ORJSONResponse({"status": 200, "message": "OK"})


class GateKeeping(BaseGatewayEnabled, router.Blueprint):

    @router.endpoint(
        "/api/room/{room_id:str}/add/user",
        endpoint_name="Add user(s)",
        description="Add one or several users to the room.",
        methods=["POST"],
    )
    async def add_user(self, room_id: str, user_ids: t.List[str]):
        """
        Add user can take a list of user ids that are then given a
        session id, the session id is a randomly general string that is used
        for the ws connection to avoid people being able to spoof other's
        sessions or WS connections.

        The list of user_ids is taken from the POST body of the request.
        """
        for user_id in user_ids:
            session_id = await redis['room_session'].get(user_id)
            if session_id is None:
                session_id = create_session_id()
                await redis['room_session'].set(user_id, session_id)
            try:
                await self.alter_session(room_id, session_id, ADD_SESSION)
            except ValueError:
                return responses.ORJSONResponse({
                    "status": 500,
                    "message": "Error handling session with gateway."
                })

        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/room/{room_id:str}/remove/user",
        endpoint_name="Remove user(s)",
        description="Remove one or several users to the room.",
        methods=["POST"],
    )
    async def remove_user(self, room_id: str, user_ids: t.List[str]):
        """
        Removes a set of user ids from a room, this will actually just
        remove the session ids linked with the user id, because this is a
        protected endpoint this should be alright.
        """

        for user_id in user_ids:
            session_id = await redis['room_session'].get(user_id)
            if session_id is None:
                continue

            try:
                await self.alter_session(room_id, session_id, REMOVE_SESSION)
            except ValueError:
                return responses.ORJSONResponse({
                    "status": 500,
                    "message": "Error handling session with gateway."
                })

        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    async def alter_session(self, room_id: str, session_id: str, op: str):
        # Its a hack i know but i dont really want to make an entire system
        # on the gateway just for adding sessions instead of the existing
        # alter endpoint.
        url = (ALTER_ROOM_URL + "&session_id={}").format(op, room_id, session_id)
        async with self.session.post(url) as resp:
            if resp.status >= 400:
                gatekeeper.log(
                    level=logging.FATAL,
                    msg=f"Error handling session status: {resp.status}",
                )
                raise ValueError("Status Invalid")


def setup(app):
    app.add_blueprint(PlayerEndpoints(app))
    app.add_blueprint(MessageChat(app))
    app.add_blueprint(GateKeeping(app))
