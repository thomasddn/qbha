from pydantic import BaseModel

from QbusMqttModels.QbusConfigEntity import QbusConfigEntity

class QbusConfigDevice(BaseModel):
    id: str = None
    ip: str = None
    mac: str = None
    name: str = None
    serialNr: str = None
    type: str = None
    version: str = None
    properties: dict = {}
    functionBlocks: list[QbusConfigEntity] = []
