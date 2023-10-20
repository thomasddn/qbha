import logging
from Subscribers.Subscriber import Subscriber
import paho.mqtt.client as mqtt


class QbusCaptureSubscriber(Subscriber):
    _logger = logging.getLogger("qbha." + __name__)

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/#"
        

    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        self._logger.debug(f"{msg.topic} {msg.payload.decode().strip()}")
