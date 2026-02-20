import logging
from json import JSONDecodeError
from typing import Callable, Mapping

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.status import HTTP_400_BAD_REQUEST

from core.sync import sync


_LOGGER = logging.getLogger(__name__)


def _summarize_request(body: dict) -> str:
    """Return a short summary of the sync request without sensitive fields."""
    metadata = body.get("parent", {}).get("metadata", {})
    return f"name={metadata.get('name')}, namespace={metadata.get('namespace')}, generation={metadata.get('generation')}"


def build_webhook(sync_func: Callable[[Mapping], Mapping]):
    async def webhook(request: Request):
        try:
            body = await request.json()
            _LOGGER.debug("Webhook request: %s", _summarize_request(body))
            response = sync_func(body)
        except JSONDecodeError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse request body: {repr(e)}",
            )
        except KeyError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Missing field from request: {repr(e)}",
            )
        except Exception as e:
            _LOGGER.error("Unexpected error processing webhook: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

        _LOGGER.debug("Webhook response: status=%s", response.get("status", {}))
        return JSONResponse(response)

    return webhook


routes = [
    Route("/sync", endpoint=build_webhook(sync), methods=["POST"]),
]
