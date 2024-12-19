import logging
import re

from HomeAssistantModels.HomeAssistantDevice import HomeAssistantDevice
from HomeAssistantModels.HomeAssistantMessage import HomeAssistantMessage
from HomeAssistantModels.HomeAssistantPayload import HomeAssistantPayload
from QbusMqttModels.QbusConfigDevice import QbusConfigDevice
from QbusMqttModels.QbusConfigEntity import QbusConfigEntity
from Settings import Settings

_REF_ID_REGEX = re.compile(r"^\d+\/(\d+(?:\/\d+)?)$")
_TO_SNAKE_CASE_REGEX = re.compile(r"(?<=[a-z0-9])([A-Z])")

_SUPPORTED_OUTPUTS = [
    "analog",
    "gauge",
    "onoff",
    "scene",
    "shutter",
    "thermo",
    "ventilation",
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
_SUPPORTED_GAUGE_PROPERTIES = [
    "consumptionValue",
    "currentValue",
]


def _parse_ref_id(ref_id: str) -> str:
    matches = re.findall(_REF_ID_REGEX, ref_id)

    if len(matches) > 0:
        ref_id = matches[0]

        if ref_id:
            return ref_id.replace("/", "-")

    return ""


def _to_snake_case(key: str) -> str:
    key = _TO_SNAKE_CASE_REGEX.sub(r"_\1", key)
    return key.lower()


class MqttMessageFactory:

    _logger = logging.getLogger("qbha." + __name__)
    _settings = Settings()

    def create_homeassistant_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage | list[HomeAssistantMessage] | None:
        entityType = entity.type.lower()

        if entityType not in _SUPPORTED_OUTPUTS:
            self._logger.warning(f"Entity type '{entityType}' not (yet) supported.")
            return None

        match entityType:
            case "analog":
                return self._create_light_message(entity, controller)

            case "gauge":
                if isinstance(entity.variant, str) and _SUPPORTED_GAUGE_VARIANTS.get(entity.variant):
                    return self._create_sensor_message_for_gauge_with_variant(entity, controller)

                if any(supported in entity.properties for supported in _SUPPORTED_GAUGE_PROPERTIES):
                    return self._create_sensor_message_for_gauge_by_properties(entity, controller)

                self._logger.warning(f"Gauge with variant '{entity.variant}' not (yet) supported.")
                return None

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
                climatesensor_message = self._create_sensor_message_for_climate(entity, controller)

                if not self._settings.ClimateSensors:
                    climatesensor_message.payload = None

                return [thermo_message, climatesensor_message]

            case "ventilation":
                return (
                    self._create_sensor_message_for_ventilation(entity, controller)
                    if entity.properties.get("co2") is not None
                    else None
                )

        return None


    def _create_base_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice, domain: str, *, id_suffix: str = "", suffix_in_name: bool = False) -> HomeAssistantMessage:
        ref_id = _parse_ref_id(entity.refId)
        unique_id = f"qbus_{controller.id}_{ref_id}{id_suffix}"

        device = HomeAssistantDevice()
        device.name = "Qbus"
        device.manufacturer = "Qbus"
        device.identifiers = controller.serialNr
        device.model = controller.serialNr
        device.sw_version = controller.version

        payload = HomeAssistantPayload()

        if suffix_in_name:
            suffix = id_suffix.lstrip("_").replace("_", " ").title()
            payload.name = f"{entity.name} {suffix}"
        else:
            payload.name = entity.name

        payload.unique_id = unique_id
        payload.object_id = unique_id
        payload.device = device
        payload.state_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"
        payload.json_attributes_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/state"
        payload.json_attributes_template = '{ "controller_id": "' + controller.id + '", "entity_id": "{{ value_json.id }}", "ref_id": "' + ref_id + '" }'

        if not domain.endswith("sensor"):
            payload.command_topic = f"cloudapp/QBUSMQTTGW/{controller.id}/{entity.id}/setState"

        message = HomeAssistantMessage()
        message.topic = f"homeassistant/{domain}/{unique_id}/config"
        message.retain = True
        message.qos = 2
        message.payload = payload

        return message


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


    def _create_sensor_message_for_climate(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor", id_suffix="_temperature")
        message.payload.device_class = "temperature"
        message.payload.unit_of_measurement = "°C"
        message.payload.value_template = "{%- if value_json.properties.currTemp is defined -%} {{ value_json.properties.currTemp }} {%- endif -%}"

        return message


    def _create_sensor_message_for_gauge_with_variant(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor")

        variant = _SUPPORTED_GAUGE_VARIANTS.get(entity.variant) if isinstance(entity.variant, str) else None
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

    def _create_sensor_message_for_gauge_by_properties(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> list[HomeAssistantMessage]:
        messages: list[HomeAssistantMessage] = []

        for key, value in entity.properties.items():
            if key not in _SUPPORTED_GAUGE_PROPERTIES:
                self._logger.warning(f"Gauge property '{key}' not (yet) supported.")
                continue

            unit = value.get("unit")

            message = self._create_base_message(entity, controller, "sensor", id_suffix=f"_{_to_snake_case(key)}", suffix_in_name=True)
            message.payload.value_template = "{%- if '" + key + "' in value_json.properties -%}{{ value_json.properties." + key + " }}{%- endif -%}"
            message.payload.unit_of_measurement = unit
            message.payload.suggested_display_precision = 2

            match unit:
                case "kWh":
                    message.payload.device_class = "energy"
                    message.payload.state_class = "total"
                case "L":
                    message.payload.device_class = "volume_storage"
                    message.payload.state_class = "total"
                case _:
                    message.payload.state_class = "measurement"

            messages.append(message)

        return messages

    def _create_sensor_message_for_ventilation(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "sensor")
        message.payload.value_template = "{{ value_json['properties']['co2'] }}"
        message.payload.unit_of_measurement = entity.properties.get("co2").get("unit")
        message.payload.device_class = "carbon_dioxide"
        message.payload.suggested_display_precision = 0
        message.payload.state_class = "measurement"

        return message


    def _create_scene_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "scene")
        message.payload.payload_on = '{"id":"' + entity.id + '", "type": "action", "action": "active"}'

        return message


    def _create_cover_message(self, entity: QbusConfigEntity, controller: QbusConfigDevice) -> HomeAssistantMessage:
        message = self._create_base_message(entity, controller, "cover")
        message.payload.payload_stop = None

        if "state" in entity.properties:
            message.payload.state_closing = "down"
            message.payload.state_opening = "up"
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "down"}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "up"}}'
            message.payload.value_template = "{{ value_json['properties']['state'] }}"
            message.payload.optimistic = True

        if "shutterStop" in entity.actions:
            message.payload.state_stopped = "stop"
            message.payload.payload_stop = '{"id": "' + entity.id + '", "type": "state", "properties": {"state": "stop"}}'

        if "shutterPosition" in entity.properties:
            message.payload.payload_close = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 0}}'
            message.payload.payload_open = '{"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition": 100}}'
            message.payload.value_template = "{{ value_json['properties']['shutterPosition'] }}"
            message.payload.position_closed = 0
            message.payload.position_open = 100
            message.payload.position_template = "{{ value_json['properties']['shutterPosition'] }}"
            message.payload.position_topic = message.payload.state_topic
            message.payload.set_position_template = '{%- if position is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":{{position | float | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"shutterPosition":100}} {%- endif -%} }'
            message.payload.set_position_topic = message.payload.command_topic

        if "slatPosition" in entity.properties:
            message.payload.tilt_closed_value = 0
            message.payload.tilt_opened_value = 100
            message.payload.tilt_status_template = "{{ value_json['properties']['slatPosition'] }}"
            message.payload.tilt_status_topic = message.payload.state_topic
            message.payload.tilt_command_template = '{%- if tilt_position is defined -%} {"id": "' + entity.id + '", "type": "state", "properties": {"slatPosition":{{tilt_position | float | round(0)}}}} {%- else -%} {"id": "' + entity.id + '", "type": "state", "properties": {"slatPosition":100}} {%- endif -%} }'
            message.payload.tilt_command_topic = message.payload.command_topic

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


    def _onoff_as_binarysensor(self, entity: QbusConfigEntity) -> bool:
        for bs in self._settings.BinarySensors:
            bs = bs.upper()

            if (bs == entity.id or
                bs == entity.name.upper() or
                bs == entity.refId or
                bs == _parse_ref_id(entity.refId)):  # noqa: E129
                return True

        return False
