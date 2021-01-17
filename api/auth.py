import os
import typing as t
import aiohttp
import router
import urllib.parse

from fastapi import responses, FastAPI, Request
from models import User
from utils import create_session_id, session_valid

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

ADD_SESSION = "http://spooderfy_gateway:8000/api/sessions/add"
REDIRECT_URI = "https://spooderfy.com/login"

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_OAUTH2_AUTH = "/oauth2/authorize"
DISCORD_OAUTH2_USER = "/users/@me"
DISCORD_OAUTH2_TOKEN = "/oauth2/token"

DISCORD_AVATAR = "https://images.discordapp.net/avatars/" \
                 "{user_id}/{avatar}.png?size=512"


def make_redirect_url() -> str:
    return (
            DISCORD_BASE_URL +
            DISCORD_OAUTH2_AUTH +
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
            "&response_type=code"
            "&scope=identify"
            f"&state={create_session_id()}"
    )


class Authorization(router.Blueprint):
    def __init__(self, app: FastAPI):
        self.app = app

        self.app.on_event("startup")(self.init_session)
        self.app.on_event("shutdown")(self.close)

        self.session: t.Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session is not None:
            await self.session.close()

    @router.endpoint(
        "/login",
        endpoint_name="Discord Login",
        description="Login via discord.",
        methods=["GET"],
    )
    async def login(
            self,
            request: Request,
            redirect_to: str = "/home",
            code: t.Optional[str] = None
    ):
        """
        The login api for discord, both logins and redirects are used on this
        endpoint, if code is None it means it is a standard login not  a
        redirect from discord, if it is just being spoofed then good job but
        its a invalid token.

        If the code is None the system redirects the user to the Oauth2 endpoint
        for discord's login, with a redirect_to cookie set for when the response
        comes back allowing us to seamlessly login and redirect users.

        Otherwise the code is extracted from the parameters and a POST request
        is made to discord to get the relevant data, a session id is produced
        and saved.
        """

        if code is None:
            if not session_valid(request=request):
                print("valid???")
                return responses.RedirectResponse(redirect_to)

            print("invalid")
            url = make_redirect_url()
            print(url)
            resp = responses.RedirectResponse(url)
            resp.set_cookie("redirect_to", redirect_to)
            print(resp)
            return resp
        else:
            user = await self.get_user(code)
            if user is None:
                return responses.ORJSONResponse({
                    "status": 500,
                    "message": "discord did not respond correctly",
                })

            session_id = create_session_id()
            data = {
                "session_id": session_id,
                "user": {
                    "id": user.id,
                    "name": user.username,
                    "avatar_url": DISCORD_AVATAR.format(user_id=user.id, avatar=user.avatar)
                }
            }
            resp = await self.session.post(ADD_SESSION, json=data)
            if resp.status >= 400:
                return responses.ORJSONResponse({
                    "status": 500,
                    "message": "gateway did not accept request",
                })

            redirect_to = request.cookies.pop("redirect_to", "/home")
            resp = responses.RedirectResponse(redirect_to)
            resp.delete_cookie("redirect_to")
            resp.set_cookie("session", session_id, secure=True, samesite="strict")

            return resp

    async def get_user(self, code) -> t.Optional[User]:
        data = {
            'client_id': int(CLIENT_ID),
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': 'identify'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with self.session.post(
            DISCORD_BASE_URL + DISCORD_OAUTH2_TOKEN,
            data=data,
            headers=headers,
        ) as resp:

            if resp.status >= 400:
                return None

            data = await resp.json()

        async with self.session.get(
            DISCORD_BASE_URL + DISCORD_OAUTH2_USER,
            headers={"Authorization": f"Bearer {data['access_token']}"}
        ) as resp:

            if resp.status >= 400:
                return None

            data = await resp.json()

            return User(**data)


def setup(app):
    app.add_blueprint(Authorization(app))
