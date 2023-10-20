from pydantic import BaseModel


class QbusControllerStateProperties(BaseModel):
    connectable: bool | None = None
    connected: bool | None = None