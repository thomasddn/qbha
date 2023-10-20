import logging
import paho.mqtt.client as mqtt
from Settings import Settings
from Subscribers.Subscriber import Subscriber


class Qbha:
    _QBHA_AVAILABILITY_TOPIC = "qbha/availability"
    _logger = logging.getLogger("qbha." + __name__)


    def __init__(self, subscribers: list[Subscriber]) -> None:
        self.subscribers = subscribers


    def start(self) -> None:
        settings = Settings()
        
        client = mqtt.Client("qbha")
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        client.will_set(self._QBHA_AVAILABILITY_TOPIC, "offline")
        client.username_pw_set(settings.MqttUser, settings.MqttPassword)

        self._logger.info(f"MQTT client 'qbha' connecting to {settings.MqttHost}:{settings.MqttPort} with user '{settings.MqttUser}'.")
        client.connect(settings.MqttHost, settings.MqttPort, 60)
        client.loop_forever()


    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        self._logger.debug(f"MQTT client connected ({str(rc)}).")
        client.publish(self._QBHA_AVAILABILITY_TOPIC, "online")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topics: list[tuple[str, int]] = []

        for subscriber in self.subscribers:
            self._logger.debug(f"MQTT client subscribing to {subscriber.topic}.")
            topics.append((subscriber.topic, subscriber.qos))

        client.subscribe(topics)


    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        for subscriber in self.subscribers:
            if subscriber.can_process(msg):
                subscriber.process(client, msg)


    def _on_disconnect(self, client: mqtt.Client, userdata, rc) -> None:
        self._logger.debug(f"MQTT client disconnected ({str(rc)}).")
        client.publish(self._QBHA_AVAILABILITY_TOPIC, "offline")
