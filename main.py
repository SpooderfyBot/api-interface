import logging
import uvicorn
import typing as t
import router

from fastapi import FastAPI

from database import create_engine
from redis import create_cache

create_engine()

APP_FILES = [
    "api.synchronise",
    "api.auth",
]

CACHE_COLLECTIONS = [
    "sessions",
    "room_sessions"
]


def import_callback(app_: FastAPI, endpoint: t.Union[router.Endpoint, router.Websocket]):
    if isinstance(endpoint, router.Endpoint):
        app_.add_api_route(
            endpoint.route,
            endpoint.callback,
            name=endpoint.name,
            methods=endpoint.methods,
            **endpoint.extra)
    else:
        raise NotImplementedError


app = FastAPI(
    title="Spooderfy API",
    description="The Discord bot for all your movie needs.",
    docs_url=None,
    redoc_url="/api/docs",
)


@app.on_event("startup")
async def init():
    await create_cache(CACHE_COLLECTIONS)


router = router.Router(app, APP_FILES, import_callback)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("main:app", host="0.0.0.0", port=5052, log_level="info")
