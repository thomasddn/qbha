import logging
import os
from pathlib import Path
import socket


class Settings:
    _VERSION = "v0.4.0"


    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        
        return cls.instance
      

    def __init__(self) -> None:
        # Docker
        cgroup = Path('/proc/self/cgroup')
        self._is_docker = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()

        # Data folder
        if self._is_docker:
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
