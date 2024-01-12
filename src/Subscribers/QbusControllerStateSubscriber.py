import logging
import paho.mqtt.client as mqtt
from pydantic import TypeAdapter
from QbusMqttModels.QbusControllerState import QbusControllerState
from Subscribers.Subscriber import Subscriber


class QbusControllerStateSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)
    _requested: list[str] = []
    

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/+/state"
        self._type_adapter = TypeAdapter(QbusControllerState)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return

        state = self._type_adapter.validate_json(msg.payload)

        if state.properties and state.properties.connectable == False and state.id not in self._requested:
            self._logger.info(f"Activating controller {state.id}.")
            self._requested.append(state.id)
            payload = '{"id": "' + state.id + '", "type": "action", "action": "activate", "properties": { "authKey": "ubielite" } }'
            client.publish(f"cloudapp/QBUSMQTTGW/{state.id}/setState", payload)
