from typing import Iterator
from pydantic import TypeAdapter
from QbusMqttModels.QbusConfig import QbusConfig
from QbusMqttModels.QbusConfigDevice import QbusConfigDevice
from QbusMqttModels.QbusConfigEntity import QbusConfigEntity
from Settings import Settings


class QbusConfigService(object):
    _config: QbusConfig = None
    _settings = Settings()

    @staticmethod
    def save(source: bytes | bytearray, config: QbusConfig) -> None:
        # Save to file
        with open(f"{QbusConfigService._settings.DataFolder}qbusconfig.json", "w") as file:
            file.write(config.model_dump_json())

        with open(f"{QbusConfigService._settings.DataFolder}qbusconfig.source.json", "w") as file:
            file.write(source.decode())

        # Set prop
        QbusConfigService._config = config


    @staticmethod
    def load() -> QbusConfig | None:
        if QbusConfigService._config is None:
            with open(f"{QbusConfigService._settings.DataFolder}qbusconfig.json", "r") as file:
                config = file.read()
                QbusConfigService._config = TypeAdapter(QbusConfig).validate_json(config)
        
        return QbusConfigService._config


    @staticmethod
    def get_entities() -> Iterator[QbusConfigEntity]:
        QbusConfigService.load()

        if QbusConfigService._config is None:
            return []

        for controller in QbusConfigService._config.devices or []:
            for entity in controller.functionBlocks or []:
                yield entity


    @staticmethod
    def get_entities_with_controller() -> Iterator[tuple[QbusConfigEntity, QbusConfigDevice]]:
        QbusConfigService.load()

        if QbusConfigService._config is None:
            return []

        for controller in QbusConfigService._config.devices or []:
            for entity in controller.functionBlocks or []:
                yield (entity, controller)


    @staticmethod
    def find_entity_by_id(id: str) -> QbusConfigEntity | None:
        for entity in QbusConfigService.get_entities():
            if entity.id == id:
                return entity
        
        return None
