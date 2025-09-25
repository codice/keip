import logging.config
import json

from dataclasses import asdict

from pydantic import ValidationError

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.requests import Request

from models import RouteData, RouteRequest
from core import k8s_client
from logconf import LOG_CONF


logging.config.dictConfig(LOG_CONF)
_LOGGER = logging.getLogger(__name__)


async def deploy_route(request: Request):
    """
    Handles the deployment of an integration route via an XML file upload.

    The endpoint accepts a PUT request with a JSON payload containing the XML of multiple Integration Routes.
    It validates the file content type, extracts the route name from the filename,
    and creates Kubernetes resources for the route using the provided XML configuration.

    Args:
        request (Request): The incoming HTTP request containing the form data.
        The request body is a JSON payload containing a list of integration routes.
        {
            "routes": [
                {
                    "name": route-name
                    "namespace": "default"
                    "xml": "<xml>...</xml>"
                }
                ...
            ]
        }

    Returns:
        JSONResponse: A 201 status code response with the created resources in JSON format.

    Raises:
        HTTPException: If the upload file is missing or has an invalid content type.
        UnicodeDecodeError: If the XML file cannot be decoded properly.
        HTTPException: If an unexpected error occurs during processing.
    """
    _LOGGER.info("Received deployment request")
    try:
        body = await request.json()
        route_request = RouteRequest(**body)

        content_type = request.headers["content-type"]
        if content_type != "application/json":
            _LOGGER.warning("Invalid content type: '%s'", content_type)
            raise HTTPException(
                status_code=400,
                detail="No Integration Route XML file found in form data",
            )
        created_resources = []
        for route in route_request.routes:
            route_data = RouteData(
                route_name=route.name,
                route_xml=route.xml,
                namespace=route.namespace,
            )

            _LOGGER.info("Creating resources for route: %s", route_data.route_name)
            created_resources = k8s_client.create_route_resources(route_data)

            _LOGGER.debug("Created new resources: %s", created_resources)
        return JSONResponse(
            [asdict(resource) for resource in created_resources], status_code=201
        )

    except HTTPException:
        raise
    except ValidationError as e:
        return JSONResponse(
            {
                "status": "error",
                "message": "Validation failed",
                "errors": json.loads(e.json()),
            },
            status_code=422,
        )
    except Exception as e:
        _LOGGER.error("An unexpected error occurred: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e
