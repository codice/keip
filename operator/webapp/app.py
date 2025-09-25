import logging.config

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

import config as cfg
from routes import webhook
from routes.deploy import deploy_route
from logconf import LOG_CONF


_LOGGER = logging.getLogger(__name__)


async def status(request):
    return JSONResponse({"status": "UP"})


def create_app() -> ASGIApp:
    logging.config.dictConfig(LOG_CONF)

    if cfg.DEBUG:
        _LOGGER.warning("Running server with debug mode. NOT SUITABLE FOR PRODUCTION!")

    routes = [
        Route("/route", deploy_route, methods=["PUT"]),
        Route("/status", status, methods=["GET"]),
        Mount(path="/webhook", routes=webhook.routes),
    ]
    starlette_app = Starlette(debug=cfg.DEBUG, routes=routes)

    return starlette_app


app = create_app()
