import logging
from logging.handlers import RotatingFileHandler
import sys
from dotenv import load_dotenv

from Qbha import Qbha
from Settings import Settings
from Subscribers.HomeAssistantStatusSubscriber import HomeAssistantStatusSubscriber
from Subscribers.QbusCaptureSubscriber import QbusCaptureSubscriber
from Subscribers.QbusConfigSubscriber import QbusConfigSubscriber
from Subscribers.QbusControllerStateSubscriber import QbusControllerStateSubscriber
from Subscribers.QbusEntityStateSubscriber import QbusEntityStateSubscriber


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
    try:
        configure_logging()
        logger = logging.getLogger("qbha")
        logger.info("Starting qbha.")

        subscribers = []

        if settings.QbusCapture:
            subscribers.append(QbusCaptureSubscriber())

        subscribers.extend([HomeAssistantStatusSubscriber(),
            QbusConfigSubscriber(),
            QbusControllerStateSubscriber(),
            QbusEntityStateSubscriber()])

        qbha = Qbha(subscribers)
        qbha.start()
    except KeyboardInterrupt:
        pass
    except Exception as exception:
        logger.exception(exception)
    finally:
        logger.info("Closing application.")
