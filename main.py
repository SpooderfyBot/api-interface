import logging
import uvicorn
import typing as t
import router

from fastapi import FastAPI

from database import create_engine

create_engine()

app_files = [
    "api.synchronise",
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


router = router.Router(app, app_files, import_callback)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")
