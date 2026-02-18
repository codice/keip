from typing import Tuple
from kubernetes import config, client
from kubernetes.client.rest import ApiException
import logging
import os

from models import RouteData, Resource, Status

ROUTE_API_GROUP = "keip.codice.org"
ROUTE_API_VERSION = "v1alpha2"
ROUTE_PLURAL = "integrationroutes"
WEBHOOK_CONTROLLER_PREFIX = "integrationroute-webhook"


_LOGGER = logging.getLogger(__name__)

_configured = False
v1 = None
routeApi = None


def _ensure_configured():
    global _configured, v1, routeApi
    if _configured:
        return
    try:
        (
            config.load_kube_config(os.getenv("KUBECONFIG"))
            if os.getenv("KUBECONFIG")
            else config.load_incluster_config()
        )
    except config.ConfigException:
        _LOGGER.error(
            msg="Failed to configure the k8s_client. keip will be unable to deploy integration routes.",
        )
    v1 = client.CoreV1Api()
    routeApi = client.CustomObjectsApi()
    _configured = True


def _check_cluster_reachable() -> bool:
    """
    Checks if the Kubernetes cluster is reachable by attempting to retrieve API resources.

    This function attempts to call the Kubernetes API to list available API resources.
    If the call succeeds, it confirms that the cluster is reachable and returns True.
    If the call fails or raises an exception, it indicates that the cluster is unreachable
    and returns False.

    Returns:
        bool: True if the cluster is reachable, False otherwise.
    """
    _ensure_configured()
    try:
        v1.get_api_resources()
        return True
    except ApiException:
        return False


def _create_integration_route(route_data: RouteData, configmap_name: str) -> Resource:
    """Create or update a new Integration Route with the provided configmap"""
    if not _check_cluster_reachable():
        raise ApiException(
            status=500,
            reason="Kubernetes cluster not reachable. Verify the cluster is running",
        )

    existing_route = routeApi.list_namespaced_custom_object(
        group=ROUTE_API_GROUP,
        version=ROUTE_API_VERSION,
        namespace=route_data.namespace,
        plural=ROUTE_PLURAL,
        field_selector=f"metadata.name={route_data.route_name}",
    )

    body = {
        "apiVersion": "keip.codice.org/v1alpha2",
        "kind": "IntegrationRoute",
        "metadata": {
            "name": route_data.route_name,
            "labels": {"app.kubernetes.io/created-by": "keip"},
        },
        "spec": {"routeConfigMap": configmap_name},
    }

    status = Status.CREATED

    if existing_route["items"]:
        # Delete existing route
        routeApi.delete_namespaced_custom_object(
            group=ROUTE_API_GROUP,
            version=ROUTE_API_VERSION,
            namespace=route_data.namespace,
            plural=ROUTE_PLURAL,
            name=existing_route["items"][0]["metadata"]["name"],
        )
        status = Status.RECREATED

    # Create new route
    routeApi.create_namespaced_custom_object(
        group=ROUTE_API_GROUP,
        version=ROUTE_API_VERSION,
        namespace=route_data.namespace,
        plural=ROUTE_PLURAL,
        body=body,
    )

    return Resource(status=status, name=route_data.route_name)


def _create_route_configmap(route_data: RouteData) -> Resource:
    """
    Creates or updates a ConfigMap containing an XML route payload for an integration route.

    This function generates a ConfigMap with the provided route configuration and creates or updates
    it in the specified namespace.

    Args:
        route_data (RouteData): The route data containing the route name, namespace, and XML route file.

    Returns:
        Resource: A Resource object indicating the status (CREATED or UPDATED) and name of the created/updated ConfigMap.

    Raises:
        ApiException: If the Kubernetes cluster is unreachable or if there is an error during the API call.
        Exception: If an unexpected error occurs during processing.
    """
    if not _check_cluster_reachable():
        raise ApiException(
            status=500,
            reason="Kubernetes cluster not reachable. Verify the cluster is running",
        )

    configmap_name = f"{route_data.route_name}-cm"
    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=configmap_name,
            namespace=route_data.namespace,
            labels={"app.kubernetes.io/created-by": "keip"},
        ),
        data={"integrationRoute.xml": route_data.route_xml},
    )

    result = v1.list_namespaced_config_map(
        namespace=route_data.namespace, field_selector=f"metadata.name={configmap_name}"
    )

    updated = False

    if len(result.items) > 0:
        # Update if exists
        _LOGGER.info(
            "Route ConfigMap '%s' already exists and will be updated", configmap_name
        )

        v1.replace_namespaced_config_map(
            name=configmap_name, namespace=route_data.namespace, body=configmap
        )
        updated = True
    else:
        # Create if doesn't exist
        _LOGGER.info(
            "Route ConfigMap '%s' does not exist and will be created", configmap_name
        )
        v1.create_namespaced_config_map(
            namespace=route_data.namespace, body=configmap
        )

    status = Status.UPDATED if updated else Status.CREATED
    return Resource(status=status, name=configmap_name)


def create_route_resources(route_data: RouteData) -> Tuple[Resource, Resource]:
    """
    Creates both a ConfigMap and an Integration Route resource for the specified route configuration.

    This function orchestrates the creation of two Kubernetes resources:
    1. A ConfigMap containing the XML route payload for the integration route
    2. An Integration Route resource that routes traffic based on the provided configuration

    The function first creates the ConfigMap using the provided route data, then creates the Integration Route
    using the ConfigMap name as the routeConfigMap reference. If a ConfigMap with the same name already exists,
    it is updated rather than recreated. The Integration Route is created or updated based on the existing state.

    Args:
        route_data (RouteData): The route data containing the route name, namespace, and XML route file.
            Must include all required fields to properly configure the integration route.

    Returns:
        Tuple[Resource]: A list containing two Resource objects:
            - The created/updated ConfigMap resource
            - The created/updated Integration Route resource
        The resources are returned in the order: [ConfigMap, Integration Route]

    Raises:
        ApiException: If the Kubernetes cluster is unreachable or if there is an error during API calls.
        Exception: If an unexpected error occurs during processing or resource creation.
    """
    route_cm = _create_route_configmap(route_data=route_data)
    route = _create_integration_route(
        route_data=route_data, configmap_name=route_cm.name
    )
    return route_cm, route
