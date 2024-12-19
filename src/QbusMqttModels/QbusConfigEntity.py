from typing import Any
from pydantic import BaseModel


class QbusConfigEntity(BaseModel):
    id: str = None
    location: str = None
    locationId: int = None
    name: str = None
    originalName: str = None
    refId: str = None
    type: str = None,
    variant: str | tuple[Any] | list[Any] | None = None,
    actions: dict[str, Any] = {}
    properties: dict[str, Any] = {}
