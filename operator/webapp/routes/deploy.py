import logging
import re
from pathlib import Path

from dataclasses import asdict

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route, Router

from models import RouteData
from core import k8s_client
from logconf import LOG_CONF


logging.config.dictConfig(LOG_CONF)
_LOGGER = logging.getLogger(__name__)


async def deploy_route(request: Request):
    """
    Handles the deployment of an integration route via an XML file upload.

    The endpoint accepts a PUT request with an XML file uploaded via form data.
    It validates the file content type, extracts the route name from the filename,
    and creates Kubernetes resources for the route using the provided XML configuration.

    Args:
        request (Request): The incoming HTTP request containing the form data.

    Returns:
        JSONResponse: A 201 status code response with the created resources in JSON format.

    Raises:
        HTTPException: If the upload file is missing or has an invalid content type.
        UnicodeDecodeError: If the XML file cannot be decoded properly.
        HTTPException: If an unexpected error occurs during processing.
    """
    _LOGGER.info("Received deployment request")
    try:
        async with request.form() as form:
            if "upload_file" not in form:
                raise HTTPException(
                    status_code=400, detail="Missing request parameter: upload_file"
                )

            filename = Path(form["upload_file"].filename).stem
            route_file = await form["upload_file"].read()
            content_type = form["upload_file"].content_type

        if content_type is None or content_type.lower() != "application/xml":
            _LOGGER.warning("Invalid content type: %s", content_type)
            raise HTTPException(
                status_code=400,
                detail="No Integration Route XML file found in form data",
            )

        route_data = RouteData(
            route_name=_generate_route_name(filename),
            route_file=route_file.decode("utf-8"),
        )

        _LOGGER.info("Creating resources for route: %s", route_data.route_name)
        created_resources = k8s_client.create_route_resources(route_data)

        _LOGGER.debug("Created new resources: %s", created_resources)
        return JSONResponse(
            [asdict(resource) for resource in created_resources], status_code=201
        )

    except HTTPException:
        raise
    except UnicodeDecodeError:
        _LOGGER.warning("Invalid XML file encoding")
        raise HTTPException(status_code=400, detail="Invalid XML file encoding")
    except Exception as e:
        _LOGGER.error("An unexpected error occurred: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _generate_route_name(filename: str) -> str:
    """
    Generates a valid route name from a filename by replacing underscores with hyphens
    and removing invalid characters, ensuring it adheres to Kubernetes naming conventions.

    Args:
        filename (str): The original filename from which to generate the route name.

    Returns:
        str: A cleaned, valid route name in lowercase with only alphanumeric characters and hyphens.

    Example:
        Input: "my-route_with_invalid_chars.txt"
        Output: "my-route-with-invalid-chars"
    """
    filename = filename.replace("_", "-")
    filename = re.sub(r"[^a-z0-9-]", "", filename.lower())
    filename = filename.strip("-")
    return filename


router = Router([Route("/", endpoint=deploy_route, methods=["PUT"])])
