import logging.config

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.types import ASGIApp

import config as cfg
from logconf import LOG_CONF
from routes import webhook
from routes.deploy import deploy_route

_LOGGER = logging.getLogger(__name__)


def _with_cors(app: Starlette, origins_env: str):
    origins = [s for part in origins_env.split(",") if (s := part.strip())]
    if not origins:
        _LOGGER.warning(
            "Failed to parse 'CORS_ALLOWED_ORIGINS' env var. CORS headers are disabled."
        )
        return app

    _LOGGER.info("Enable CORS headers. Allowed origins: %s", origins)

    return CORSMiddleware(
        app=app,
        allow_origins=origins,
        allow_methods=["GET", "PUT"],
    )


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

    if cfg.CORS_ALLOWED_ORIGINS:
        starlette_app = _with_cors(starlette_app, cfg.CORS_ALLOWED_ORIGINS)

    return starlette_app


app = create_app()
