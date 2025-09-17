import pytest
from kubernetes import client
from core.k8s_client import (
    create_integration_route,
    create_route_configmap,
    is_cluster_ready,
)
from models import RouteData, Resource, Status
from kubernetes.client.rest import ApiException


@pytest.fixture
def route_data():
    return RouteData(
        namespace="default",
        route_name="my-route",
        route_file="<xml>payload</xml>",
    )


@pytest.fixture(autouse=True)
def mock_api(mocker):
    """Patch the global `v1` and `routeApi` objects used by k8s_client."""
    v1 = mocker.patch("core.k8s_client.v1")
    route_api = mocker.patch("core.k8s_client.routeApi")
    return {"v1": v1, "route_api": route_api}


def test_create_route_configmap_creates_new(route_data, mock_api):
    """When no ConfigMap exists the function should call create_namespaced_config_map."""
    cm_list = client.V1ConfigMapList(items=[])
    mock_api["v1"].list_namespaced_config_map.return_value = cm_list

    res: Resource = create_route_configmap(route_data)

    # Verify that the correct name is returned
    assert res.name == f"{route_data.route_name}-cm"
    assert res.status == Status.CREATED


def test_create_route_configmap_updates_existing(mocker, route_data, mock_api):
    """When a ConfigMap already exists the function should replace it."""
    cm_name = f"{route_data.route_name}-cm"
    existing_cm = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=cm_name, namespace="default"),
        data={"integrationRoute.xml": "<old/>"},
    )
    cm_list = client.V1ConfigMapList(items=[existing_cm])
    mock_api["v1"].list_namespaced_config_map.return_value = cm_list

    res: Resource = create_route_configmap(route_data)

    assert res.name == cm_name
    assert res.status == Status.UPDATED


def test_create_integration_route_creates_new(route_data, mock_api):
    """When no IntegrationRoute exists the function should call create."""
    mock_api["route_api"].list_namespaced_custom_object.return_value = {"items": []}

    res: Resource = create_integration_route(route_data, f"{route_data.route_name}-cm")

    assert res.name == route_data.route_name
    assert res.status == Status.CREATED


def test_create_integration_route_updates_existing(route_data, mock_api):
    """When an IntegrationRoute exists the function should recreate it."""
    existing_ir = {"metadata": {"name": "old-ir"}}
    mock_api["route_api"].list_namespaced_custom_object.return_value = {
        "items": [existing_ir]
    }

    res: Resource = create_integration_route(route_data, f"{route_data.route_name}-cm")

    assert res.name == route_data.route_name
    assert res.status == Status.RECREATED


@pytest.mark.parametrize("ready_flag", [True, False])
def test_is_cluster_ready_various(mocker, ready_flag):
    """Verify that the function returns True only when at least one pod is Ready."""
    mock_pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name="integrationroute-webhook-pod", namespace="default"
        ),
        status=client.V1PodStatus(
            phase="Running",
            conditions=[client.V1PodCondition(type="Ready", status=ready_flag)],
        ),
    )
    pod_list = client.V1PodList(items=[mock_pod])

    mock_v1 = mocker.patch("core.k8s_client.v1")
    mock_v1.list_pod_for_all_namespaces.return_value = pod_list

    assert is_cluster_ready() == ready_flag


def test_is_cluster_ready_no_matching_pods(mocker):
    """When there are no pods with the prefix, the function should return False."""
    pod_list = client.V1PodList(items=[])
    mock_v1 = mocker.patch("core.k8s_client.v1")
    mock_v1.list_pod_for_all_namespaces.return_value = pod_list

    assert not is_cluster_ready()


def test_is_cluster_ready_pod_no_conditions(mocker):
    """When a pod has no conditions, the function should return False."""
    mock_pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name="integrationroute-webhook-pod", namespace="default"
        ),
        status=client.V1PodStatus(
            phase="Running",
            conditions=[],
        ),
    )
    pod_list = client.V1PodList(items=[mock_pod])

    mock_v1 = mocker.patch("core.k8s_client.v1")
    mock_v1.list_pod_for_all_namespaces.return_value = pod_list

    assert not is_cluster_ready()


def test_is_cluster_ready_api_exception(mocker):
    """When an ApiException is raised, the function should return False."""
    mock_v1 = mocker.patch("core.k8s_client.v1")
    mock_v1.list_pod_for_all_namespaces.side_effect = ApiException()

    assert not is_cluster_ready()


def test_create_integration_route_cluster_not_reachable(route_data, mocker):
    """When the cluster is not reachable, create_integration_route should raise an ApiException."""
    mocker.patch("core.k8s_client._check_cluster_reachable", return_value=False)
    with pytest.raises(ApiException):
        create_integration_route(route_data, "configmap-name")


def test_create_route_configmap_cluster_not_reachable(route_data, mocker):
    """When the cluster is not reachable, create_route_configmap should raise an ApiException."""
    mocker.patch("core.k8s_client._check_cluster_reachable", return_value=False)
    with pytest.raises(ApiException):
        create_route_configmap(route_data)


def test_is_cluster_ready_pod_no_status(mocker):
    """When a pod has no status, the function should return False."""
    mock_pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name="integrationroute-webhook-pod", namespace="default"
        ),
        status=None,
    )
    pod_list = client.V1PodList(items=[mock_pod])

    mock_v1 = mocker.patch("core.k8s_client.v1")
    mock_v1.list_pod_for_all_namespaces.return_value = pod_list

    assert not is_cluster_ready()
