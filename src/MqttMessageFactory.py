import logging
import re

from HomeAssistantModels.HomeAssistantDevice import HomeAssistantDevice
from HomeAssistantModels.HomeAssistantMessage import HomeAssistantMessage
from HomeAssistantModels.HomeAssistantPayload import HomeAssistantPayload
from QbusMqttModels.QbusConfigDevice import QbusConfigDevice
from QbusMqttModels.QbusConfigEntity import QbusConfigEntity
from Settings import Settings


class MqttMessageFactory:

    _REFID_REGEX = r"^\d+\/(\d+(?:\/\d+)?)$"
    _SUPPORTED_OUTPUTS = [
        "analog",
        "gauge",
        "onoff",
        "scene",
        "shutter",
        "thermo",
    ]
    _SUPPORTED_GAUGE_VARIANTS = {
        "Current": "current",
        "Energy": "energy",
        "Power": "power",
        "Temperature": "temperature",
        "Voltage": "voltage",
        "Volume": "volume_storage",
        "Water": "water",
    }

    _logger = logging.getLogger("qbha." + __name__)
    _settings = Settings()

    def create_homeassistant_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage | list[HomeAssistantMessage] | None:
        entityType = entity.type.lower()

        if entityType not in self._SUPPORTED_OUTPUTS:
            self._logger.warning(f"Entity type '{entityType}' not (yet) supported.")
            return None

        match entityType:
            case "analog":
                return self._create_light_message(entity, controller)
            case "gauge":
                if isinstance(entity.variant, (list, tuple)) or not self._SUPPORTED_GAUGE_VARIANTS.get(entity.variant):
                    self._logger.warning(f"Gauge with variant '{entity.variant}' not (yet) supported.")
                    return None

                return self._create_sensor_message(entity, controller)
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


    def _create_base_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice, domain: str, id_suffix: str = "") -> HomeAssistantMessage:
        refId = self._parseRefId(entity.refId)
        uniqueId = f"qbus_{controller.id}_{refId}{id_suffix}"

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

        if not domain.endswith("sensor"):
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
        message = self._create_base_message(entity, controller, "light")
        message.payload.schema = "template"
        message.payload.brightness_template = "{{ value_json.properties.value | float | multiply(2.55) | round(0) }}"
        message.payload.command_off_template = '{"id": "' + entity.id + '", "type": "state", "properties": {"value": 0}}'
        message.payload.command_on_template = '{%- if brightness is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":{{brightness | float | multiply(0.39215686) | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"value":100}} {%- endif -%} }'
        message.payload.state_template = '{% if value_json.properties.value > 0 %} on {% else %} off {% endif %}'

        return message


    def _create_switch_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "switch")
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
        message = self._create_base_message(entity, controller, "scene")
        message.payload.payload_on = '{"id":"' + entity.id + '", "type": "action", "action": "active"}'

        return message


    def _create_cover_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "cover")

        if (entity.properties.get("state") is not None):
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "down"}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "up"}}'
            message.payload.payload_stop = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "stop"}}'
            message.payload.state_closing = "down"
            message.payload.state_opening = "up"
            message.payload.state_stopped = "stop"
            message.payload.value_template = "{{ value_json['properties']['state'] }}"
            # payload.optimistic = true
        else:
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 0}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 100}}'
            message.payload.payload_stop = None
            message.payload.state_closing = "down"
            message.payload.state_opening = "up"
            message.payload.state_stopped = "stop"
            message.payload.value_template = "{{ value_json['properties']['shutterPosition'] }}"
            # message.payload.optimistic = true
            message.payload.position_closed = 0
            message.payload.position_open = 100
            message.payload.position_template = "{{ value_json['properties']['shutterPosition'] }}"
            message.payload.position_topic = message.payload.state_topic
            message.payload.set_position_template = '{%- if position is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":{{position| float | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":100}} {%- endif -%} }'
            message.payload.set_position_topic = message.payload.command_topic

        return message


    def _create_climate_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "climate")
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

        # message.payload.swing_modes = []

        return message


    def _create_sensor_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor")

        variant = self._SUPPORTED_GAUGE_VARIANTS.get(entity.variant)
        unit = entity.properties.get("currentValue").get("unit")

        if (variant == "water" or variant == "volume_storage") and unit == "l":
            unit = unit.upper()

        message.payload.value_template = "{{ value_json['properties']['currentValue'] }}"
        message.payload.unit_of_measurement = unit
        message.payload.device_class = variant
        message.payload.suggested_display_precision = 2

        match message.payload.unit_of_measurement:
            case "kWh":
                message.payload.state_class = "total"
            case "L":
                message.payload.state_class = "total"
            case _:
                message.payload.state_class = "measurement"

        return message


    def _onoff_as_binarysensor(self, entity: QbusConfigEntity) -> bool:
        for bs in self._settings.BinarySensors:
            bs = bs.upper()

            if (bs == entity.id or
                bs == entity.name.upper() or
                bs == entity.refId or
                bs == self._parseRefId(entity.refId)):  # noqa: E129
                return True

        return False
