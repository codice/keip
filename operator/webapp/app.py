import logging.config

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.types import ASGIApp

import config as cfg
from routes import webhook
from routes.deploy import deploy_route
from logconf import LOG_CONF


_LOGGER = logging.getLogger(__name__)


def create_app() -> ASGIApp:
    logging.config.dictConfig(LOG_CONF)

    if cfg.DEBUG:
        _LOGGER.warning("Running server with debug mode. NOT SUITABLE FOR PRODUCTION!")

    routes = [
        Route("/route", deploy_route, methods=["PUT"])
    ]
    starlette_app = Starlette(debug=cfg.DEBUG, routes=routes)
    starlette_app.mount("/webhook", webhook.router)

    return starlette_app


app = create_app()
