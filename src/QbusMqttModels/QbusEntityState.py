from pydantic import BaseModel


class QbusEntityState(BaseModel):
    id: str = None
    type: str = None
    properties: dict = {}
