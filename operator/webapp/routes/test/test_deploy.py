import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from routes import deploy
from models import Resource, Status


@pytest.fixture
def mock_k8s_client(mocker):
    return mocker.patch("routes.deploy.k8s_client")


@pytest.fixture(scope="module")
def test_client():
    app = Starlette()
    app.mount("/deploy", deploy.router)
    return TestClient(app)


resources = [Resource(name="my-route", status=Status.CREATED)]


def test_deploy_route(mock_k8s_client, test_client):
    mock_k8s_client.create_route_resources.return_value = resources

    res = test_client.post(
        "/deploy/route",
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
def test_deploy_route_invalid_content_type(test_client, content_type):
    res = test_client.post(
        "/deploy/route",
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


def test_deploy_route_missing_upload_file(test_client):
    res = test_client.post("/deploy/route", files={})

    assert res.status_code == 400
    assert "Missing request parameter: upload_file" in res.text


def test_deploy_route_unsupported_file_encoding(test_client):
    response = test_client.post(
        "/deploy/route",
        files={
            "upload_file": (
                "my-route.xml",
                "<?xml version='1.0'?><route>...</route>".encode("utf-16"),
                "application/xml",
            )
        },
    )

    assert response.status_code == 400
    assert "Invalid XML file encoding" in response.text


def test_deploy_route_generic_exception(mock_k8s_client, test_client):
    mock_k8s_client.create_route_resources.side_effect = Exception(
        "Something went wrong"
    )

    res = test_client.post(
        "/deploy/route",
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
