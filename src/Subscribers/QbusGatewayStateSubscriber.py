import logging

import paho.mqtt.client as mqtt
from pydantic import TypeAdapter

from QbusMqttModels.QbusGatewayState import QbusGatewayState
from Subscribers.Subscriber import Subscriber


class QbusGatewayStateSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/state"
        self._type_adapter = TypeAdapter(QbusGatewayState)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return

        state = self._type_adapter.validate_json(msg.payload)

        if state is not None and state.online is True:
            client.publish("cloudapp/QBUSMQTTGW/getConfig", b"")
