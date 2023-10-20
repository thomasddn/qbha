from pydantic import BaseModel

class QbusConfigEntity(BaseModel):
    id: str = None
    location: str = None
    locationId: int = None
    name: str = None
    originalName: str = None
    refId: str = None
    type: str = None
    actions: dict = {}
    properties: dict = {}
