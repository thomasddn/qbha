import logging
import os
from pathlib import Path


class Settings:
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

        # MQTT settings
        self._mqtt_host = os.environ.get("MQTT_HOST")
        self._mqtt_user = os.environ.get("MQTT_USER")

        self._mqtt_port: int = 1883
        config_port = os.environ.get("MQTT_PORT")

        if config_port and isinstance(config_port, int):
            port = int(config_port)

            if port > 0:
                self._mqtt_port = port

        # Log level
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        self._log_level: int = getattr(logging, log_level.upper(), logging.INFO)

        # Qbus capture
        self._qbus_capture: bool = os.environ.get("QBUS_CAPTURE", "False").lower() in ("true", "1")


    @property
    def MqttHost(self) -> str:
        return self._mqtt_host


    @property
    def MqttPort(self) -> int:
        return self._mqtt_port


    @property
    def MqttUser(self) -> str:
        return self._mqtt_user
    

    @property
    def MqttPassword(self) -> str:
        return os.environ.get("MQTT_PWD")
    

    @property
    def LogLevel(self) -> int:
        return self._log_level


    @property
    def QbusCapture(self) -> bool:
        return self._qbus_capture


    @property
    def DataFolder(self) -> str:
        return self._data_folder
