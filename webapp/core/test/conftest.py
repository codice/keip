import copy
import os
from typing import Mapping

import pytest

from conftest import load_json_as_dict


@pytest.fixture()
def full_route(full_route_load: dict):
    return copy.deepcopy(full_route_load)


@pytest.fixture(scope="module")
def full_route_load() -> Mapping:
    cwd = os.path.dirname(os.path.abspath(__file__))
    return load_json_as_dict(f"{cwd}/json/full-integration-route-request.json")
