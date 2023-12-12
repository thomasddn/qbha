from pydantic import BaseModel, ConfigDict
from HomeAssistantModels.HomeAssistantDevice import HomeAssistantDevice

class HomeAssistantPayload(BaseModel):
    model_config = ConfigDict(extra='allow')

    name: str = None
    unique_id: str = None
    object_id: str = None
    command_topic: str = None
    state_topic: str = None
    json_attributes_topic: str = None
    json_attributes_template: str = None
    device: HomeAssistantDevice = None