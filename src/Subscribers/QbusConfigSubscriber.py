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
            message = self._create_homeassistant_message(entity, controller)

            if isinstance(message, list):
                entityIds.append(entity.id)

                for m in message:
                    if m.payload:
                        self._logger.debug(f"Adding entity {m.topic}.")
                    else:
                        self._logger.debug(f"Removing entity {m.topic}.")

                    messages.append(m)
            elif message:
                if message.payload:
                    self._logger.debug(f"Adding entity {message.topic}.")
                else:
                    self._logger.debug(f"Removing entity {message.topic}.")

                entityIds.append(entity.id)
                messages.append(message)

        return entityIds, messages


    def _create_homeassistant_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage | list[HomeAssistantMessage] | None:
        entityType = entity.type.lower()

        if not self._HA_TYPE_MAP.get(entityType):
            self._logger.warn(f"Entity type '{entityType}' not (yet) supported.")
            return None

        match entityType:
            case "analog":
                return self._create_light_message(entity, controller)
            case "onoff":
                onoff_message = self._create_switch_message(entity, controller)
                binarysensor_message = self._create_binarysensor_message(entity, controller)

                if self._onoff_as_binarysensor(entity):
                    onoff_message.payload = None
                else:
                    binarysensor_message.payload = None

                return [onoff_message, binarysensor_message]

            case "scene":
                return self._create_scene_message(entity, controller)
            case "shutter":
                return self._create_cover_message(entity, controller)
            case "thermo":
                thermo_message = self._create_climate_message(entity, controller)
                climatesensor_message = self._create_climatesensor_message(entity, controller)

                if not self._settings.ClimateSensors:
                    climatesensor_message.payload = None

                return [thermo_message, climatesensor_message]
    
        return None


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
        payload.state_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"
        payload.json_attributes_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"
        payload.json_attributes_template = '{ "controller_id": "' + controller.id + '", "entity_id": "{{ value_json.id }}", "ref_id": "' + refId + '" }'

        if domain and not domain.endswith("sensor"):
            payload.command_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/setState"

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
    

    def _create_light_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)
        message.payload.schema = "template"
        message.payload.brightness_template = "{{ value_json.properties.value | float | multiply(2.55) | round(0) }}"
        message.payload.command_off_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": 0}}'
        message.payload.command_on_template = '{%- if brightness is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":{{brightness | float | multiply(0.39215686) | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":100}} {%- endif -%} }'
        message.payload.state_template = '{% if value_json.properties.value > 0 %} on {% else %} off {% endif %}'
    
        return message
    

    def _create_switch_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)
        message.payload.payload_on = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": true}}'
        message.payload.payload_off = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": false}}'
        message.payload.value_template = "{{ value_json['properties']['value'] }}"
        message.payload.state_on = True
        message.payload.state_off = False
    
        return message


    def _create_binarysensor_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "binary_sensor")
        message.payload.value_template = "{{ value_json['properties']['value'] }}"
        message.payload.payload_on = True
        message.payload.payload_off = False
        return message


    def _create_climatesensor_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor", "_temperature")
        message.payload.device_class = "temperature"
        message.payload.unit_of_measurement = "°C"
        message.payload.value_template = "{%- if value_json.properties.currTemp is defined -%} {{ value_json.properties.currTemp }} {%- endif -%}"
    
        return message


    def _create_scene_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)
        message.payload.payload_on = '{"id":"' + entity.id + '", "type": "action", "action": "active"}'
    
        return message
    

    def _create_cover_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)

        if (entity.properties.get("state") != None):
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "down"}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "up"}}'
            message.payload.payload_stop = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "stop"}}'
            message.payload.state_closing = "down"
            message.payload.state_opening = "up"
            message.payload.state_stopped = "stop"
            message.payload.value_template = "{{ value_json['properties']['state'] }}"
            #payload.optimistic = true
        else:
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 0}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 100}}'
            message.payload.payload_stop = None
            message.payload.state_closing = "down"
            message.payload.state_opening = "up"
            message.payload.state_stopped = "stop"
            message.payload.value_template = "{{ value_json['properties']['shutterPosition'] }}"
            #message.payload.optimistic = true
            message.payload.position_closed = 0
            message.payload.position_open = 100
            message.payload.position_template = "{{ value_json['properties']['shutterPosition'] }}"
            message.payload.position_topic = message.payload.state_topic
            message.payload.set_position_template = '{%- if position is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":{{position| float | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":100}} {%- endif -%} }'
            message.payload.set_position_topic = message.payload.command_topic
    
        return message
    

    def _create_climate_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)
        message.payload.temperature_unit = "C"
        message.payload.precision = 0.1
        message.payload.temp_step = 0.5

        message.payload.current_temperature_topic = message.payload.state_topic
        message.payload.current_temperature_template = "{%- if value_json.properties.currTemp is defined -%} {{ value_json.properties.currTemp }} {%- endif -%}"

        message.payload.modes = ["heat", "off"]
        message.payload.mode_state_topic = message.payload.state_topic
        message.payload.mode_state_template = "{%- if value_json.properties.setTemp is defined and value_json.properties.currTemp is defined -%} {%- if value_json.properties.setTemp > value_json.properties.currTemp -%} heat {%- else -%} off {%- endif -%} {%- else -%} off {%- endif -%}"

        message.payload.preset_modes = self._settings.ClimatePresets
        message.payload.preset_mode_command_topic = message.payload.command_topic
        message.payload.preset_mode_command_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"currRegime": "{{ value }}" }}'
        message.payload.preset_mode_state_topic = message.payload.state_topic
        message.payload.preset_mode_value_template = "{%- if value_json.properties.currRegime is defined -%} {{ value_json.properties.currRegime }} {%- endif -%}"

        message.payload.temperature_command_topic = message.payload.command_topic
        message.payload.temperature_command_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"setTemp": {{ value }}}}'
        message.payload.temperature_state_topic = message.payload.state_topic
        message.payload.temperature_state_template = "{%- if value_json.properties.setTemp is defined -%} {{ value_json.properties.setTemp }} {%- endif -%}"

        #message.payload.swing_modes = []
    
        return message


    def _create_humidity_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller)
        return message


    def _onoff_as_binarysensor(self, entity: QbusConfigEntity) -> bool:
        for bs in self._settings.BinarySensors:
            bs = bs.upper()

            if (bs == entity.id or 
                bs == entity.name.upper() or 
                bs == entity.refId or 
                bs == self._parseRefId(entity.refId)):
                return True
            
        return False