import json
import logging
import queue
import threading
import paho.mqtt.client as mqtt
from pydantic import TypeAdapter
from QbusConfigService import QbusConfigService
from QbusMqttModels.QbusEntityState import QbusEntityState
from Subscribers.Subscriber import Subscriber


class QbusEntityStateSubscriber(Subscriber):
    _WAIT_TIME = 3
    _logger = logging.getLogger("qbha." + __name__)


    def __init__(self, client: mqtt.Client) -> None:
        super().__init__()

        self.mqtt_client = client

        self.topic = "cloudapp/QBUSMQTTGW/+/+/state"
        self._type_adapter = TypeAdapter(QbusEntityState)

        self._items = queue.SimpleQueue()
        self._kill = threading.Event()
        self._throttle = threading.Thread(target=self._process_queue)
        self._throttle.start()


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
        
        # Add to queue
        self._items.put(entity.id)


    def close(self) -> None:
        self._kill.set()
    

    def _process_queue(self) -> None:
        self._kill.wait(self._WAIT_TIME)

        while True:
            size = self._items.qsize()
            entity_ids = []

            try:
                for _ in range(size):
                    item = self._items.get()

                    if item not in entity_ids:
                        entity_ids.append(item)
            except queue.Empty:
                pass

            # Publish to MQTT
            if len(entity_ids) > 0:
                self._logger.debug(f"Updating state for thermostat {entity_ids}.")
                self.mqtt_client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(entity_ids))
            
            # If no kill signal is set, sleep for the interval.
            # If kill signal comes in while sleeping, immediately wake up and handle.
            is_killed = self._kill.wait(self._WAIT_TIME)

            if is_killed:
                break

        self._logger.debug(f"Killing thread.")