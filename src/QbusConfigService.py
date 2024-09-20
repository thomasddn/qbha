import logging
import os
from typing import Iterator
from pydantic import TypeAdapter
from QbusMqttModels.QbusConfig import QbusConfig
from QbusMqttModels.QbusConfigDevice import QbusConfigDevice
from QbusMqttModels.QbusConfigEntity import QbusConfigEntity
from Settings import Settings


class QbusConfigService(object):
    _config: QbusConfig = None
    _settings = Settings()
    _logger = logging.getLogger("qbha." + __name__)


    @staticmethod
    def save(source: bytes | bytearray, config: QbusConfig) -> None:
        # Save to file
        with open(f"{__class__._settings.DataFolder}qbusconfig.json", "w") as file:
            file.write(config.model_dump_json())

        with open(f"{__class__._settings.DataFolder}qbusconfig.source.json", "w") as file:
            file.write(source.decode())

        # Set prop
        __class__._config = config


    @staticmethod
    def load() -> QbusConfig | None:
        if __class__._config is None:
            if os.path.isfile(f"{__class__._settings.DataFolder}qbusconfig.json"):
                with open(f"{__class__._settings.DataFolder}qbusconfig.json", "r") as file:
                    config = file.read()
                    __class__._config = TypeAdapter(QbusConfig).validate_json(config)
            else:
                __class__._logger.warning("File 'qbusconfig.json' does not exist. Try to restart the Qbus MQTT service.")

        return __class__._config


    @staticmethod
    def get_entities() -> Iterator[QbusConfigEntity]:
        __class__.load()

        if __class__._config is None:
            return []

        for controller in __class__._config.devices or []:
            for entity in controller.functionBlocks or []:
                yield entity


    @staticmethod
    def get_entities_with_controller() -> Iterator[tuple[QbusConfigEntity, QbusConfigDevice]]:
        __class__.load()

        if __class__._config is None:
            return []

        for controller in __class__._config.devices or []:
            for entity in controller.functionBlocks or []:
                yield (entity, controller)


    @staticmethod
    def find_entity_by_id(id: str) -> QbusConfigEntity | None:
        for entity in __class__.get_entities():
            if entity.id == id:
                return entity

        return None
