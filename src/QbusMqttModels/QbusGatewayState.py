from pydantic import BaseModel


class QbusGatewayState(BaseModel):
    id: str = None
    online: bool = False
    reason: str = None
