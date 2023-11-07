from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import sys

from Qbha import Qbha
from Settings import Settings
from Subscribers.HomeAssistantStatusSubscriber import HomeAssistantStatusSubscriber
from Subscribers.QbusCaptureSubscriber import QbusCaptureSubscriber
from Subscribers.QbusConfigSubscriber import QbusConfigSubscriber
from Subscribers.QbusControllerStateSubscriber import QbusControllerStateSubscriber
from Subscribers.QbusEntityStateSubscriber import QbusEntityStateSubscriber
from Subscribers.Subscriber import Subscriber


load_dotenv()
settings = Settings()


def configure_logging():
    # class NoErrorFilter(logging.Filter):
    #     def filter(record):
    #         return record.levelno < logging.ERROR

    #logging.basicConfig(level=settings.LogLevel)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s')

    default_handler = logging.StreamHandler(sys.stdout)
    default_handler.setLevel(settings.LogLevel)
    default_handler.setFormatter(formatter)
    #default_handler.addFilter(NoErrorFilter)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(f"{settings.DataFolder}qbha.log", backupCount=3, maxBytes=10485760)
    file_handler.setLevel(settings.LogLevel)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("qbha")
    logger.setLevel(settings.LogLevel)
    logger.addHandler(default_handler)
    logger.addHandler(error_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    # Specific logger for QbusCaptureSubscriber
    capture_handler = RotatingFileHandler(f"{settings.DataFolder}qbuscapture.log", backupCount=1, maxBytes=10485760)
    capture_handler.setLevel(logging.DEBUG)
    capture_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))

    QbusCaptureSubscriber._logger.setLevel(logging.DEBUG)
    QbusCaptureSubscriber._logger.addHandler(capture_handler)
    QbusCaptureSubscriber._logger.propagate = False


if __name__ == '__main__':
    configure_logging()
    logger = logging.getLogger("qbha")
    logger.info(f"Starting qbha {settings.Version}.")

    mqtt_client: mqtt.Client = None
    subscribers: list[Subscriber] = []
    
    try:
        mqtt_client = mqtt.Client(f"qbha-{settings.Hostname}")

        if settings.QbusCapture:
            subscribers.append(QbusCaptureSubscriber())

        subscribers.extend([HomeAssistantStatusSubscriber(),
            QbusConfigSubscriber(),
            QbusControllerStateSubscriber(),
            QbusEntityStateSubscriber(mqtt_client)])

        qbha = Qbha(mqtt_client, subscribers)
        qbha.start()
    except KeyboardInterrupt:
        pass
    except Exception as exception:
        logger.exception(exception)
    finally:
        logger.info("Closing application.")

        for subscriber in subscribers:
            subscriber.close()

        if mqtt_client is not None:
            mqtt_client.disconnect()
