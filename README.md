# QBHA
QBHA stands for Qbus Bridge for Home Assistant and can be pronounced as "cuba". QBHA will create MQTT topics for Home Assistant based on your Qbus configuration, making all supported entities available in Home Assistant.

This project was inspired by https://github.com/QbusKoen/qbusMqtt and https://github.com/wk275/qbTools-v2. While both these projects install an entire ecosystem, this project focuses on keeping it as slim as possible.

## Setup

### Prerequisites
- Qbus home automation system (hardware)
- Qbus MQTT gateway
  - Docker version: [Docker Hub](https://hub.docker.com/r/thomasddn/qbusmqtt) | [source](https://github.com/thomasddn/qbusmqtt) .
  - Bare metal: https://github.com/QbusKoen/qbusMqtt. Be sure to only install the gateway (qbusMqttGw) and optionally Mosquitto. You can also use an [installer script](https://github.com/QbusKoen/QbusMqtt-installer).
- MQTT broker (e.g. https://hub.docker.com/_/eclipse-mosquitto)

### Installation

1. Create docker-compose.yaml
1. Adjust [environment variables](#configuration) as needed
1. Start the container:  `docker compose up -d`

Example docker-compose.yaml:

```yaml
version: '3.4'

services:
  qbha:
    image: qbha:latest
    container_name: qbha
    restart: unless-stopped
    volumes:
      - ./data:/data            # Optional
    environment:
      MQTT_HOST: 192.168.0.123
      TZ: Europe/Brussels
```

### Configuration

| Key | Required | Default value | Description |
| --- | --- | --- | --- |
| MQTT_HOST | Y | \<empty> | The IP or host name of the MQTT broker. |
| MQTT_PORT | N | 1883 | The port of the MQTT broker. |
| MQTT_USER | N | \<empty> | The username to connect to the MQTT broker. |
| MQTT_PWD | N | \<empty> | The password to connect to the MQTT broker. |
| LOG_LEVEL | N | INFO | The log level to use. Can be one of the following: CRITICAL, ERROR, WARNING, INFO, DEBUG. |
| QBUS_CAPTURE | N | False | Log all Qbus topic messages to a file, regardless of LOG_LEVEL. Used for debugging purposes. |

### Data folder

Optionally, you can mount the `/data` folder. It will contain log files and Qbus configuration files.

## Supported entities

| Qbus | Home Assistant |
| --- | --- |
| Analog | Light |
| On/Off | Switch |
| Scene | Scene |
| Shutter | Cover |
| Thermo | Climate (heating only) |

## Remarks
:warning: This is **not** officially supported by Qbus.
