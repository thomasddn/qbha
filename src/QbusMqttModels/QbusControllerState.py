from QbusMqttModels.QbusControllerStateProperties import QbusControllerStateProperties
from pydantic import BaseModel


class QbusControllerState(BaseModel):
    id: str = None
    properties: QbusControllerStateProperties = None
    type: str = None