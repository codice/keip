from typing import List
from kubernetes import config, client
from kubernetes.client.rest import ApiException
import logging

from models import RouteData, Resource, Status

ROUTE_API_GROUP = "keip.codice.org"
ROUTE_API_VERSION = "v1alpha1"
ROUTE_PLURAL = "integrationroutes"
WEBHOOK_CONTROLLER_PREFIX = "integrationroute-webhook"


_LOGGER = logging.getLogger(__name__)


try:
    # Try in-cluster config first
    config.load_incluster_config()
    _LOGGER.info("Using in-cluster Kubernetes config")
except config.ConfigException:
    # Fall back to local kubeconfig
    _LOGGER.info(
        msg="Detected not running inside a cluster. Falling back to local kubeconfig."
    )
    config.load_kube_config()


v1 = client.CoreV1Api()
routeApi = client.CustomObjectsApi()


def _check_cluster_reachable():
    try:
        v1.get_api_resources()
        return True
    except Exception:
        return False


def create_integration_route(route_data: RouteData, configmap_name: str) -> Resource:
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
        "apiVersion": "keip.codice.org/v1alpha1",
        "kind": "IntegrationRoute",
        "metadata": {
            "name": route_data.route_name,
            "labels": {"app.kubernetes.io/created-by": "keip"}
        },
        "spec": {"routeConfigMap": configmap_name},
    }

    status = Status.CREATED

    if existing_route["items"]:
        # Recreate route
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


def create_route_configmap(route_data: RouteData) -> Resource:
    """Create or update a ConfigMap with an XML route payload"""
    if not _check_cluster_reachable():
        raise ApiException(
            status=500,
            reason="Kubernetes cluster not reachable. Verify the cluster is running",
        )

    configmap_name = f"{route_data.route_name}-cm"
    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=configmap_name, namespace=route_data.namespace,
            labels={"app.kubernetes.io/created-by": "keip"}
        ),
        data={"integrationRoute.xml": route_data.route_file},
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
        configmap = v1.create_namespaced_config_map(
            namespace=route_data.namespace, body=configmap
        )

    status = Status.UPDATED if updated else Status.CREATED
    return Resource(status=status, name=configmap_name)


def create_route_resources(route_data: RouteData) -> List[Resource]:
    route_cm = create_route_configmap(route_data=route_data)
    route = create_integration_route(
        route_data=route_data, configmap_name=route_cm.name
    )
    return [route_cm, route]
