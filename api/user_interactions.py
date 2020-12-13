import orjson

import router

from fastapi import responses, Request
from models import UserInfoResponse, User
from redis import redis
from utils import login_required


class UserAPI(router.Blueprint):
    def __init__(self, app):
        self.app = app

    @router.endpoint(
        "/api/users/@me",
        endpoint_name="Get your current user data",
        description="Returns the data (currently room session only)",
        response_model=UserInfoResponse,
        methods=["GET"],
    )
    @login_required
    async def get_myself(self, request: Request):
        """ Gets the user session from redis pending authentication """

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

        room_session = await redis['room_sessions'].get(str(user.id))
        if room_session is None:
            return UserInfoResponse(exists=False)

        room_session = orjson.loads(room_session.decode())
        return UserInfoResponse(exists=True, **room_session)


def setup(app):
    app.add_blueprint(UserAPI(app))