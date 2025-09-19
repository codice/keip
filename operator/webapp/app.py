import logging.config

from starlette.applications import Starlette
from starlette.types import ASGIApp

import config as cfg
from routes import webhook, deploy
from logconf import LOG_CONF


_LOGGER = logging.getLogger(__name__)


def create_app() -> ASGIApp:
    logging.config.dictConfig(LOG_CONF)

    if cfg.DEBUG:
        _LOGGER.warning("Running server with debug mode. NOT SUITABLE FOR PRODUCTION!")

    app = Starlette(debug=cfg.DEBUG)
    app.mount("/webhook", webhook.router)
    app.mount("/route", deploy.router)

    return app


app = create_app()
