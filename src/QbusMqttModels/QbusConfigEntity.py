from typing import Any
from pydantic import BaseModel


class QbusConfigEntity(BaseModel):
    id: str | None = None
    location: str | None = None
    locationId: int | None = None
    name: str | None = None
    originalName: str | None = None
    refId: str | None = None
    type: str | None = None,
    variant: str | list[Any] | None = None,
    actions: dict = {}
    properties: dict = {}
