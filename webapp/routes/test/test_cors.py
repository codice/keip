import pytest
from starlette.testclient import TestClient

from app import app, _with_cors

ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"


@pytest.mark.parametrize(
    "input_origins, request_origin, allowed_origin_header",
    [
        ("http://localhost:8000", "http://localhost:8000", "http://localhost:8000"),
        (
            "https://www.example.com,http://localhost:8000",
            "http://localhost:8000",
            "http://localhost:8000",
        ),
        (
            "  https://www.example.com ,  http://localhost:8000  ",
            "https://www.example.com",
            "https://www.example.com",
        ),
    ],
)
def test_status_endpoint_with_cors_success(
    input_origins, request_origin, allowed_origin_header
):
    test_client = TestClient(_with_cors(app, input_origins))
    response = test_client.get("/status", headers={"Origin": request_origin})

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}

    assert response.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == allowed_origin_header


@pytest.mark.parametrize(
    "input_origins, request_origin",
    [
        ("", "http://localhost:8000"),
        ("http://localhost:8000", "http://localhost:3000"),
        (",,,", "http://localhost:8000"),
    ],
)
def test_status_endpoint_with_cors_not_enabled_on_bad_input(
    input_origins, request_origin
):
    test_client = TestClient(_with_cors(app, input_origins))
    response = test_client.get("/status", headers={"Origin": request_origin})

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}

    assert ACCESS_CONTROL_ALLOW_ORIGIN not in response.headers
