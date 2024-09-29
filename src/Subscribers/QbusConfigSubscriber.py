import json
import logging
import time

import paho.mqtt.client as mqtt
from pydantic import TypeAdapter

from HomeAssistantModels.HomeAssistantMessage import HomeAssistantMessage
from MqttMessageFactory import MqttMessageFactory
from QbusConfigService import QbusConfigService
from QbusMqttModels.QbusConfig import QbusConfig
from Subscribers.Subscriber import Subscriber


class QbusConfigSubscriber(Subscriber):

    _logger = logging.getLogger("qbha." + __name__)
    _message_factory = MqttMessageFactory()

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/config"
        self._type_adapter = TypeAdapter(QbusConfig)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return

        config = self._type_adapter.validate_json(msg.payload)
        device_ids: list[str] = []
        total_entities = 0

        # Assure entity
        for controller in config.devices:
            device_ids.append(controller.id)
            total_entities += len(controller.functionBlocks)

        # Request device states from Qbus
        if len(device_ids) > 0:
            self._logger.debug("Requesting controller states from Qbus.")
            client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(device_ids))
            time.sleep(10)

        if total_entities <= 0:
            return

        self._logger.info("New Qbus config, updating Home Assistant entities.")

        # Save qbus configuration in file
        QbusConfigService.save(msg.payload, config)

        # Create HA entities
        entity_ids, messages = self._create_homeassistant_messages()

        # Request entity states from Qbus
        if len(entity_ids) > 0:
            self._logger.debug("Requesting entity states from Qbus.")
            client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(entity_ids))
            time.sleep(10)

        # Publish HA entities to MQTT
        self._logger.debug("Publishing Home Assistant MQTT messages.")
        for m in messages:
            payload = None if m.payload is None else m.payload.model_dump_json()
            client.publish(m.topic, payload, m.qos, m.retain)


    def _create_homeassistant_messages(self) -> tuple[list[str], list[HomeAssistantMessage]]:
        entity_ids: list[str] = []
        messages: list[HomeAssistantMessage] = []

        for (entity, controller) in QbusConfigService.get_entities_with_controller():
            message = self._message_factory.create_homeassistant_message(entity, controller)

            if isinstance(message, list):
                entity_ids.append(entity.id)

                for m in message:
                    if m.payload:
                        self._logger.debug(f"Adding entity {m.topic}.")
                    else:
                        self._logger.debug(f"Removing entity {m.topic}.")

                    messages.append(m)
            elif message is not None:
                if message.payload:
                    self._logger.debug(f"Adding entity {message.topic}.")
                else:
                    self._logger.debug(f"Removing entity {message.topic}.")

                entity_ids.append(entity.id)
                messages.append(message)

        return entity_ids, messages
