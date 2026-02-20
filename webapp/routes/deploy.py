import asyncio
import logging
import json

from dataclasses import asdict

from pydantic import ValidationError

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.requests import Request

from models import RouteData, RouteRequest
from core import k8s_client


_LOGGER = logging.getLogger(__name__)


async def deploy_route(request: Request):
    """
    Handles the deployment of an integration route.

    The endpoint accepts a PUT request with a JSON payload containing the XML of multiple Integration Routes.
    It creates Kubernetes resources for the route using the provided XML configuration.

    Args:
        request (Request): The incoming HTTP request.
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
        HTTPException: If an unexpected error occurs during processing.
    """
    _LOGGER.info("Received deployment request")
    try:
        body = await request.json()
        route_request = RouteRequest(**body)

        async def _deploy_single_route(route):
            route_data = RouteData(
                route_name=route.name,
                route_xml=route.xml,
                namespace=route.namespace,
            )
            _LOGGER.info("Creating resources for route: %s", route_data.route_name)
            return await asyncio.to_thread(
                k8s_client.create_route_resources, route_data
            )

        results = await asyncio.gather(
            *[_deploy_single_route(route) for route in route_request.routes]
        )
        created_resources = [r for result in results for r in result]
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
