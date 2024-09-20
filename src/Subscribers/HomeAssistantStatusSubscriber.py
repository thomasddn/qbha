import json
import logging
from QbusConfigService import QbusConfigService
from Subscribers.Subscriber import Subscriber
import paho.mqtt.client as mqtt


class HomeAssistantStatusSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)

    def __init__(self) -> None:
        super().__init__()
        self.topic = "homeassistant/status"


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if msg.payload.decode() != "online":
            return

        self._logger.info("Home Assistant came online, refreshing Qbus states.")

        # Gather IDs to retrieve state for
        states = []

        for entity in QbusConfigService.get_entities():
            states.append(entity.id)

        if len(states) > 0:
            # Publish to MQTT
            client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(states))
