import re

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from typing import List


class Status(str, Enum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
    RECREATED = "recreated"


class Route(BaseModel):
    name: str = Field(min_length=1, max_length=253)
    namespace: str = "default"
    xml: str

    @field_validator("name", mode="before")
    @classmethod
    def is_valid_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Route name cannot be empty")

        if value != value.lower():
            raise ValueError("Route name must be lowercase")

        if not re.match(r"^[a-z0-9]([-.a-z0-9]*[a-z0-9])?$", value):
            raise ValueError(
                "Route name must start and end with alphanumeric characters and contain only lowercase letters, numbers, hyphens, and periods"
            )

        return value


class RouteRequest(BaseModel):
    routes: List[Route] = Field(min_length=1)


@dataclass
class RouteData:
    route_name: str
    route_xml: str
    namespace: str


@dataclass
class Resource:
    name: str
    status: Status
