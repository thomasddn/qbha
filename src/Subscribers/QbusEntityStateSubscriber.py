import json
import logging
import paho.mqtt.client as mqtt
from pydantic import TypeAdapter
from QbusConfigService import QbusConfigService
from QbusMqttModels.QbusEntityState import QbusEntityState
from Subscribers.Subscriber import Subscriber


class QbusEntityStateSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)


    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/+/+/state"
        self._type_adapter = TypeAdapter(QbusEntityState)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return

        payload = self._type_adapter.validate_json(msg.payload)

        # Skip if not an event
        if payload.type != "event":
            return
        
        # Find entity
        entity = QbusConfigService.find_entity_by_id(payload.id)

        if entity is None or entity.type != "thermo":
            return
        
        # Prepare payload
        entityIds = [ entity.id ]

        # Publish to MQTT
        self._logger.debug(f"Updating state for thermostat {entityIds}.")
        client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(entityIds))

