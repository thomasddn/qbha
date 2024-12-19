from HomeAssistantModels.HomeAssistantPayload import HomeAssistantPayload


class HomeAssistantMessage:
    topic: str | None = None
    qos: int = 0
    retain: bool = False
    payload: HomeAssistantPayload | None = None
