import logging
import paho.mqtt.client as mqtt
from pydantic import TypeAdapter
from QbusMqttModels.QbusControllerState import QbusControllerState
from Subscribers.Subscriber import Subscriber


class QbusControllerStateSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)
    _requested: bool = False
    

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/+/state"
        self._type_adapter = TypeAdapter(QbusControllerState)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return

        state = self._type_adapter.validate_json(msg.payload)

        if self._requested == False and state.properties and state.properties.connectable == False:
            self._logger.info(f"Requesting controller firmware update.")
            self._requested = True
            payload = '{"id": "' + state.id + '", "type": "action", "action": "activate", "properties": { "authKey": "ubielite" } }'
            client.publish(f"cloudapp/QBUSMQTTGW/{state.id}/setState", payload)
