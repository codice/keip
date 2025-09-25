import pytest
import copy
import json
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from unittest.mock import patch

from routes.deploy import deploy_route
from models import Resource, Status


@pytest.fixture
def mock_k8s_client(mocker):
    return mocker.patch("routes.deploy.k8s_client")


@pytest.fixture
def mock_k8s_config():
    """We need to mock the kubeconfig to prevent the local dev's from being used."""
    with patch("kubernetes.config.load_kube_config"):
        yield


@pytest.fixture(scope="module")
def test_client():
    app = Starlette(routes=[Route("/route", deploy_route, methods=["PUT"])])
    return TestClient(app)


resources = [Resource(name="my-route", status=Status.CREATED)]
with open("./routes/test/json/deploy_request_body.json", "r") as f:
    body = json.load(f)


def test_deploy_route(mock_k8s_client, test_client):
    mock_k8s_client.create_route_resources.return_value = resources

    res = test_client.put("/route", json=body)

    assert res.status_code == 201
    result = res.json()
    assert len(result) == 1
    assert result[0]["name"] == "my-route"
    assert result[0]["status"] == Status.CREATED


@pytest.mark.parametrize(
    "name",
    [
        "-starts-with-hyphen",
        "contains_invalid_char#",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd.commmm",
    ],
)
def test_deploy_route_invalid_names(mock_k8s_client, test_client, name):
    request_body = copy.deepcopy(body)
    request_body["routes"][0]["name"] = name

    res = test_client.put("/route", json=request_body)

    assert res.status_code == 422
    result = res.json()
    assert result["status"] == "error"


def test_deploy_malformed_json(mock_k8s_client, test_client):
    request_body = copy.deepcopy(body)
    del request_body["routes"][0]["name"]

    res = test_client.put("/route", json=request_body)

    assert res.status_code == 422
    result = res.json()
    assert result["status"] == "error"


@pytest.mark.parametrize("content_type", ["application/xml", ""])
def test_deploy_route_invalid_content_type(mock_k8s_client, test_client, content_type):
    res = test_client.put("/route", headers={"content-type": content_type}, json=body)

    assert res.status_code == 400
    assert "No Integration Route XML file found in form data" in res.text


def test_deploy_route_missing_body(mock_k8s_client, test_client):
    res = test_client.put("/route", json={})

    assert res.status_code == 422
    result = res.json()
    assert result["status"] == "error"


def test_deploy_missing_route(mock_k8s_client, test_client):
    request_body = copy.deepcopy(body)
    del request_body["routes"][0]

    res = test_client.put("/route", json=request_body)

    assert res.status_code == 422
    result = res.json()
    assert result["status"] == "error"


def test_deploy_route_generic_exception(mock_k8s_client, test_client):
    mock_k8s_client.create_route_resources.side_effect = Exception(
        "Something went wrong"
    )

    res = test_client.put("/route", json=body)

    assert res.status_code == 500
    assert "Internal server error" in res.text
