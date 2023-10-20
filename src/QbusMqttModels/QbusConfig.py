from pydantic import BaseModel

from QbusMqttModels.QbusConfigDevice import QbusConfigDevice

class QbusConfig(BaseModel):
    app: str = None
    version: str = None
    devices: list[QbusConfigDevice] = []
