import uvicorn
import typing as t
import router
import asyncio
import multiprocessing as mp

from fastapi import FastAPI

from database import create_engine

APP_FILES = [
    "api.auth",
]


if __name__ != '__main__':
    # Children only aka workers
    create_engine()


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
    openapi_url="/api/openapi.json"
)


router = router.Router(app, APP_FILES, import_callback)

if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5050,
        log_level="info",
        # workers=mp.cpu_count()
    )
