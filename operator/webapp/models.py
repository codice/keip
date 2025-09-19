from dataclasses import dataclass


class Status:
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
    RECREATED = "recreated"


@dataclass
class RouteData:

    route_name: str
    route_file: str
    namespace: str = "default"


@dataclass
class Resource:
    name: str
    status: Status
