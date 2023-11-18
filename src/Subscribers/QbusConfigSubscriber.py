import json
import logging
import re
import time
import paho.mqtt.client as mqtt
from pydantic import TypeAdapter
from HomeAssistantModels.HomeAssistantDevice import HomeAssistantDevice
from HomeAssistantModels.HomeAssistantMessage import HomeAssistantMessage
from HomeAssistantModels.HomeAssistantPayload import HomeAssistantPayload
from QbusConfigService import QbusConfigService
from QbusMqttModels.QbusConfig import QbusConfig
from QbusMqttModels.QbusConfigDevice import QbusConfigDevice
from QbusMqttModels.QbusConfigEntity import QbusConfigEntity
from Settings import Settings
from Subscribers.Subscriber import Subscriber


class QbusConfigSubscriber(Subscriber):
    _REFID_REGEX = r"^\d+\/(\d+(?:\/\d+)?)$"
    _HA_TYPE_MAP = { "analog": "light", "onoff": "switch", "scene": "scene", "shutter": "cover", "thermo": "climate" }

    _logger = logging.getLogger("qbha." + __name__)
    _settings = Settings()

    def __init__(self) -> None:
        super().__init__()
        self.topic = "cloudapp/QBUSMQTTGW/config"
        self._type_adapter = TypeAdapter(QbusConfig)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        if len(msg.payload) <= 0:
            return
        
        config = self._type_adapter.validate_json(msg.payload)
        totalEntities = 0
        
        # Assure entity
        for controller in config.devices:
            totalEntities += len(controller.functionBlocks)

        if totalEntities <= 0:
            return

        self._logger.info(f"New Qbus config, updating Home Assistant entities.")

        # Save qbus configuration in file
        QbusConfigService.save(msg.payload, config)
        
        # Create HA entities
        entityIds, messages = self._create_homeassistant_messages()

        # Request entity states from Qbus
        self._logger.debug("Requesting states from Qbus.")
        if len(entityIds) > 0:
            client.publish("cloudapp/QBUSMQTTGW/getState", json.dumps(entityIds))
            time.sleep(10)

        # Publish HA entities to MQTT
        self._logger.debug("Publishing Home Assistant MQTT messages.")
        for m in messages:
            payload = None if m.payload is None else m.payload.model_dump_json()
            client.publish(m.topic, payload, m.qos, m.retain)


    def _create_homeassistant_messages(self) -> tuple[list[str], list[HomeAssistantMessage]]:
        entityIds: list[str] = []
        messages: list[HomeAssistantMessage] = []

        for (entity, controller) in QbusConfigService.get_entities_with_controller():
            message = self._create_generic_message(entity, controller)

            if message:
                self._logger.debug(f"Adding entity {message.payload.unique_id}.")
                entityIds.append(entity.id)
                messages.append(message)

            if entity.type.lower() == "thermo":
                message = self._create_climate_sensor_message(entity, controller)

                if self._settings.ClimateSensors:
                    self._logger.debug(f"Adding climate sensor {message.payload.unique_id}.")
                else:
                    # This will remove previously created climate sensors.
                    self._logger.debug(f"Climate sensor {message.payload.unique_id} marked for removal.")
                    message.payload = None

                messages.append(message)

        return entityIds, messages


    def _create_generic_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage | None:
        entityType = entity.type.lower()

        if not self._HA_TYPE_MAP.get(entityType):
            self._logger.warn(f"Entity type '{entityType}' not (yet) supported.")
            return None
        
        message = self._create_base_message(entity, controller)

        match entityType:
            case "analog":
                self._configure_analog_payload(message.payload, entity)
            case "onoff":
                self._configure_onoff_payload(message.payload, entity)
            case "scene":
                self._configure_scene_payload(message.payload, entity)
            case "shutter":
                self._configure_shutter_payload(message.payload, entity)
            case "thermo":
                self._configure_thermo_payload(message.payload, entity)
    
        return message


    def _create_climate_sensor_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor", "_temperature")
        message.payload.device_class = "temperature"
        message.payload.unit_of_measurement = "°C"
        message.payload.state_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"
        message.payload.value_template = "{%- if value_json.properties.currTemp is defined -%} {{ value_json.properties.currTemp }} {%- endif -%}"
    
        return message


    def _create_base_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice, domain: str = None, id_suffix: str = "") -> HomeAssistantMessage:
        refId = self._parseRefId(entity.refId)
        uniqueId = f"qbus_{controller.id}_{refId}{id_suffix}"
        
        if domain is None or domain == "":
            domain = self._HA_TYPE_MAP[entity.type]

        device = HomeAssistantDevice()
        device.name = "Qbus"
        device.manufacturer = "Qbus"
        device.identifiers = controller.serialNr
        device.model = controller.serialNr
        device.sw_version = controller.version

        payload = HomeAssistantPayload()
        payload.name = entity.name
        payload.unique_id = uniqueId
        payload.object_id = uniqueId
        payload.device = device

        if domain != "sensor":
            payload.command_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/setState"
            payload.state_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"

        message = HomeAssistantMessage()
        message.topic = f"homeassistant/{domain}/{uniqueId}/config"
        message.retain = True
        message.qos = 2
        message.payload = payload

        return message


    def _parseRefId(self, refId: str) -> str | None:
        matches = re.findall(self._REFID_REGEX, refId)

        if len(matches) > 0:
            refId = matches[0]

            if refId:
                return refId.replace("/", "-")
            
        return None
    

    def _configure_analog_payload(self, payload: HomeAssistantPayload, entity: QbusConfigEntity) -> None:
        payload.schema = "template"
        payload.brightness_template = "{{ value_json.properties.value | float | multiply(2.55) | round(0) }}"
        payload.command_off_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": 0}}'
        payload.command_on_template = '{%- if brightness is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":{{brightness | float | multiply(0.39215686) | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":100}} {%- endif -%} }'
        payload.state_template = '{% if value_json.properties.value > 0 %} on {% else %} off {% endif %}'
    

    def _configure_onoff_payload(self, payload: HomeAssistantPayload, entity: QbusConfigEntity) -> None:
        payload.payload_on = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": true}}'
        payload.payload_off = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": false}}'
        payload.value_template = "{{ value_json['properties']['value'] }}"
        payload.state_on = True
        payload.state_off = False
        payload.force_update = True
    

    def _configure_scene_payload(self, payload: HomeAssistantPayload, entity: QbusConfigEntity) -> None:
        payload.payload_on = '{"id":"' + entity.id + '", "type": "action", "action": "active"}'
    

    def _configure_shutter_payload(self, payload: HomeAssistantPayload, entity: QbusConfigEntity) -> None:
        if (entity.properties.get("state") != None):
            payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "down"}}'
            payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "up"}}'
            payload.payload_stop = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "stop"}}'
            payload.state_closing = "down"
            payload.state_opening = "up"
            payload.state_stopped = "stop"
            payload.value_template = "{{ value_json['properties']['state'] }}"
            #payload.optimistic = true
        else:
            payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 0}}'
            payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 100}}'
            payload.payload_stop = None
            payload.state_closing = "down"
            payload.state_opening = "up"
            payload.state_stopped = "stop"
            payload.value_template = "{{ value_json['properties']['shutterPosition'] }}"
            #payload.optimistic = true
            payload.position_closed = 0
            payload.position_open = 100
            payload.position_template = "{{ value_json['properties']['shutterPosition'] }}"
            payload.position_topic = payload.state_topic
            payload.set_position_template = '{%- if position is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":{{position| float | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":100}} {%- endif -%} }'
            payload.set_position_topic = payload.command_topic
    

    def _configure_thermo_payload(self, payload: HomeAssistantPayload, entity: QbusConfigEntity) -> None:
        payload.temperature_unit = "C"
        payload.precision = 0.1
        payload.temp_step = 0.5
        payload.force_update = True

        payload.current_temperature_topic = payload.state_topic
        payload.current_temperature_template = "{%- if value_json.properties.currTemp is defined -%} {{ value_json.properties.currTemp }} {%- endif -%}"

        payload.modes = ["heat", "off"]
        payload.mode_state_topic = payload.state_topic
        payload.mode_state_template = "{%- if value_json.properties.setTemp is defined and value_json.properties.currTemp is defined -%} {%- if value_json.properties.setTemp > value_json.properties.currTemp -%} heat {%- else -%} off {%- endif -%} {%- else -%} off {%- endif -%}"

        payload.preset_modes = self._settings.ClimatePresets
        payload.preset_mode_command_topic = payload.command_topic
        payload.preset_mode_command_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"currRegime": "{{ value }}" }}'
        payload.preset_mode_state_topic = payload.state_topic
        payload.preset_mode_value_template = "{%- if value_json.properties.currRegime is defined -%} {{ value_json.properties.currRegime }} {%- endif -%}"

        payload.temperature_command_topic = payload.command_topic
        payload.temperature_command_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"setTemp": {{ value }}}}'
        payload.temperature_state_topic = payload.state_topic
        payload.temperature_state_template = "{%- if value_json.properties.setTemp is defined -%} {{ value_json.properties.setTemp }} {%- endif -%}"

        #payload.swing_modes = []