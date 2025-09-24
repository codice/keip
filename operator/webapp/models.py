from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import List


class Status(str, Enum):
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
    RECREATED = "recreated"

class Route(BaseModel):
    name: str
    namespace: str = "default"
    xml: str

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
