import pytest
from kubernetes import client
from core.k8s_client import _create_integration_route, _create_route_configmap, create_route_resources
from models import RouteData, Resource, Status
from kubernetes.client.rest import ApiException


@pytest.fixture
def route_data():
    return RouteData(
        namespace="default",
        route_name="my-route",
        route_xml="<xml>payload</xml>",
    )


@pytest.fixture
def mock_api(mocker):
    """Patch the global `v1` and `routeApi` objects used by k8s_client."""
    mocker.patch("core.k8s_client._ensure_configured")
    v1 = mocker.patch("core.k8s_client.v1")
    route_api = mocker.patch("core.k8s_client.routeApi")
    return {"v1": v1, "route_api": route_api}


def test_create_route_configmap_creates_new(route_data, mock_api):
    """When no ConfigMap exists the function should call create_namespaced_config_map."""
    cm_list = client.V1ConfigMapList(items=[])
    mock_api["v1"].list_namespaced_config_map.return_value = cm_list

    res: Resource = _create_route_configmap(route_data)

    # Verify that the correct name is returned
    assert res.name == f"{route_data.route_name}-cm"
    assert res.status == Status.CREATED


def test_create_route_configmap_updates_existing(route_data, mock_api):
    """When a ConfigMap already exists the function should replace it."""
    cm_name = f"{route_data.route_name}-cm"
    existing_cm = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=cm_name, namespace="default"),
        data={"integrationRoute.xml": "<old/>"},
    )
    cm_list = client.V1ConfigMapList(items=[existing_cm])
    mock_api["v1"].list_namespaced_config_map.return_value = cm_list

    res: Resource = _create_route_configmap(route_data)

    assert res.name == cm_name
    assert res.status == Status.UPDATED


def test_create_integration_route_creates_new(route_data, mock_api):
    """When no IntegrationRoute exists the function should call create."""
    mock_api["route_api"].list_namespaced_custom_object.return_value = {"items": []}

    res: Resource = _create_integration_route(route_data, f"{route_data.route_name}-cm")

    assert res.name == route_data.route_name
    assert res.status == Status.CREATED


def test_create_integration_route_updates_existing(route_data, mock_api):
    """When an IntegrationRoute exists the function should patch it."""
    existing_ir = {"metadata": {"name": route_data.route_name}}
    mock_api["route_api"].list_namespaced_custom_object.return_value = {
        "items": [existing_ir]
    }

    res: Resource = _create_integration_route(route_data, f"{route_data.route_name}-cm")

    assert res.name == route_data.route_name
    assert res.status == Status.UPDATED
    mock_api["route_api"].patch_namespaced_custom_object.assert_called_once()


def test_create_route_resources_cluster_not_reachable(route_data, mocker):
    """When the cluster is not reachable, create_route_resources should raise an ApiException."""
    mocker.patch("core.k8s_client._check_cluster_reachable", return_value=False)
    with pytest.raises(ApiException):
        create_route_resources(route_data)
