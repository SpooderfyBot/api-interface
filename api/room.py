import orjson

import router

from fastapi import responses, Request
from models import UserInfoResponse, User
from redis import redis
from utils import login_required


with open("./templates/room_v3.html") as file:
    room = file.read()


class RoomServe(router.Blueprint):
    def __init__(self, app):
        self.app = app

    @router.endpoint(
        "/room/{room_id:str}",
        endpoint_name="Room",
        description="Standard HTML room",
        methods=["GET"],
    )
    @login_required
    async def serve_room(self, request: Request, room_id: str):
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

        does_exist = await redis['rooms'].get(room_id)
        if does_exist is None:
            return responses.ORJSONResponse({
                "status": 404,
                "message": "Not Found"
            }, status_code=404)

        return responses.HTMLResponse(room)


def setup(app):
    app.add_blueprint(RoomServe(app))