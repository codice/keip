import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from routes import deploy
from models import Resource, Status


@pytest.fixture
def mock_k8s_client(mocker):
    return mocker.patch("routes.deploy.k8s_client")


@pytest.fixture(scope="module")
def client():
    app = Starlette()
    app.mount("/deploy", deploy.router)
    return TestClient(app)


resources = [Resource(name="my-route", status=Status.CREATED)]


def test_deploy_route(mock_k8s_client, client):
    mock_k8s_client.create_route_resources.return_value = resources

    res = client.post(
        "/deploy/",
        files={
            "upload_file": (
                "my-route.xml",
                b"<?xml version='1.0'?><route>...</route>",
                "application/xml",
            )
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert len(result) == 1
    assert result[0]["name"] == "my-route"
    assert result[0]["status"] == Status.CREATED


@pytest.mark.parametrize("content_type", ["application/json", ""])
def test_deploy_route_invalid_content_type(client, content_type):
    res = client.post(
        "/deploy/",
        files={
            "upload_file": (
                "my-route.xml",
                b"<?xml version='1.0'?><route>...</route>",
                content_type,
            )
        },
    )

    assert res.status_code == 400
    assert "No Integration Route XML file found in form data" in res.text


def test_deploy_route_missing_upload_file(mock_k8s_client, client):
    res = client.post("/deploy/", files={})

    assert res.status_code == 400
    assert "Missing request parameter: upload_file" in res.text


def test_deploy_route_unsupported_file_encoding(mock_k8s_client, client):
    res = client.post(
        "/deploy/",
        files={
            "upload_file": (
                "my-route.xml",
                "<?xml version='1.0'?><route>...</route>".encode("utf-16"),
                "application/xml",
            )
        },
    )

    assert res.status_code == 400
    assert "Invalid XML file encoding" in res.text


def test_cluster_health(mock_k8s_client, client):
    mock_k8s_client.is_cluster_ready.return_value = True

    response = client.get("/deploy/cluster-health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_cluster_health_cluster_down(mock_k8s_client, client):
    mock_k8s_client.is_cluster_ready.return_value = False

    response = client.get("/deploy/cluster-health")

    assert response.status_code == 200
    assert response.json() == {"status": "DOWN"}


def test_deploy_route_generic_exception(mock_k8s_client, client):
    mock_k8s_client.create_route_resources.side_effect = Exception(
        "Something went wrong"
    )

    res = client.post(
        "/deploy/",
        files={
            "upload_file": (
                "my-route.xml",
                b"<?xml version='1.0'?><route>...</route>",
                "application/xml",
            )
        },
    )

    assert res.status_code == 500
    assert "Internal server error" in res.text
