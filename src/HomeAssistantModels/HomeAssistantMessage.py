from HomeAssistantModels.HomeAssistantPayload import HomeAssistantPayload


class HomeAssistantMessage:
    topic: str = None
    qos: int = 0
    retain: bool = False
    payload: HomeAssistantPayload = None

