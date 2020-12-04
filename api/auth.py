import asyncio
import os
import orjson
import typing as t
import aiohttp
import router
import logging
import urllib.parse

from fastapi import responses, FastAPI
from gateway import Gateway, gateway_connect
from models import User
from redis import redis
from utils import create_session_id


CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

REDIRECT_URL = "https://spooderfy.com/api/login"

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_OAUTH2_AUTH = "/oauth2/authorize"
DISCORD_OAUTH2_USER = "/users/@me"
DISCORD_OAUTH2_TOKEN = "/users/token"


def make_redirect_url() -> str:
    return (
            DISCORD_BASE_URL +
            DISCORD_OAUTH2_AUTH +
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URL, safe='')}"
            "&response_type=code"
            "&scope=identify"
    )


class Authorization(router.Blueprint):
    def __init__(self, app: FastAPI):
        self.app = app

    @router.endpoint(
        "/api/login",
        endpoint_name="Discord Login",
        description="Login via discord.",
        methods=["GET"],
    )
    async def login(self, redirect_to: t.Optional[str] = None, code: t.Optional[str] = None):
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

        if code is None and redirect_to is not None:
            url = make_redirect_url()
            resp = responses.RedirectResponse(url)
            resp.set_cookie("redirect_to", redirect_to)
            return resp

        if code is not None:
            user = await self.get_user(code)

    async def get_user(self, code) -> User:
        pass


def setup(app):
    app.add_blueprint()
