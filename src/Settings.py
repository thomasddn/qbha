import logging
import os
from pathlib import Path
import socket


class Settings:
    _VERSION = "v0.7.1"


    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        
        return cls.instance
      

    def __init__(self) -> None:
        # Docker
        cgroup = Path('/proc/self/cgroup')
        self._is_docker = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()
        self._is_ha_addon: bool = os.environ.get("IS_HA_ADDON", "False").lower() in ("true", "1")

        # Data folder
        if self._is_ha_addon:
            self._data_folder = "/config/"
        elif self._is_docker:
            self._data_folder = "/data/"
        else:
            self._data_folder = "data/"

        # Hostname
        self._hostname = socket.gethostname()

        # MQTT settings
        self._mqtt_port: int = 1883
        config_port = os.environ.get("MQTT_PORT")

        if config_port and isinstance(config_port, int):
            port = int(config_port)

            if port > 0:
                self._mqtt_port = port

        # Log level
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        self._log_level: int = getattr(logging, log_level.upper(), logging.INFO)

        # Other
        self._qbus_capture: bool = os.environ.get("QBUS_CAPTURE", "False").lower() in ("true", "1")
        self._climate_sensors: bool = os.environ.get("CLIMATE_SENSORS", "False").lower() in ("true", "1")

        climate_presets = os.environ.get("CLIMATE_PRESETS", "MANUEEL,VORST,NACHT,ECONOMY,COMFORT").split(",")
        self._climate_presets: list[str] = [x for x in climate_presets if x.strip()]

        binary_sensors = os.environ.get("BINARY_SENSORS", "").split(",")
        self._binary_sensors: list[str] = [x for x in binary_sensors if x.strip()]


    @property
    def BinarySensors(self) -> list[str]:
        return self._binary_sensors


    @property
    def ClimatePresets(self) -> list[str]:
        return self._climate_presets


    @property
    def ClimateSensors(self) -> bool:
        return self._climate_sensors


    @property
    def DataFolder(self) -> str:
        return self._data_folder


    @property
    def Hostname(self) -> str:
        return self._hostname


    @property
    def LogLevel(self) -> int:
        return self._log_level


    @property
    def MqttHost(self) -> str:
        return os.environ.get("MQTT_HOST")


    @property
    def MqttPassword(self) -> str:
        return os.environ.get("MQTT_PWD")


    @property
    def MqttPort(self) -> int:
        return self._mqtt_port


    @property
    def MqttUser(self) -> str:
        return os.environ.get("MQTT_USER")


    @property
    def QbusCapture(self) -> bool:
        return self._qbus_capture


    @property
    def Version(self) -> str:
        return self._VERSION
