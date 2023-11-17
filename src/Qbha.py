import logging
import paho.mqtt.client as mqtt
from Settings import Settings
from Subscribers.Subscriber import Subscriber


class Qbha:
    _QBHA_AVAILABILITY_TOPIC = "qbha/availability"
    _logger = logging.getLogger("qbha." + __name__)
    _settings = Settings()


    def __init__(self, client: mqtt.Client, subscribers: list[Subscriber]) -> None:
        self.mqtt_client = client
        self.subscribers = subscribers


    def start(self) -> None:
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect

        self.mqtt_client.will_set(self._QBHA_AVAILABILITY_TOPIC, "offline")
        self.mqtt_client.username_pw_set(self._settings.MqttUser, self._settings.MqttPassword)

        self._logger.info(f"MQTT client connecting to {self._settings.MqttHost}:{self._settings.MqttPort} with user '{self._settings.MqttUser}'.")
        self.mqtt_client.connect(self._settings.MqttHost, self._settings.MqttPort, 60)
        self.mqtt_client.loop_forever()


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
                self._logger.debug(f"Processing {msg.topic} with {type(subscriber).__name__}.")
                subscriber.process(client, msg)


    def _on_disconnect(self, client: mqtt.Client, userdata, rc) -> None:
        self._logger.debug(f"MQTT client disconnected ({str(rc)}).")
        client.publish(self._QBHA_AVAILABILITY_TOPIC, "offline")
