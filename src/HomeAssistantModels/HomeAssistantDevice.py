from pydantic import BaseModel


class HomeAssistantDevice(BaseModel):
    identifiers: str = None
    name: str = None
    model: str = None
    manufacturer: str = None
    sw_version: str = None