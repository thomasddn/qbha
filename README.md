# QBHA
QBHA stands for Qbus Bridge for Home Assistant and can be pronounced as "cuba". QBHA will create MQTT topics for Home Assistant based on your Qbus configuration, making all supported entities available in Home Assistant.

The application runs as a Docker container. It is also available as a Home Assistant add-on: https://github.com/thomasddn/home-assistant-addons.

[![GitHub release (with filter)][releases-shield]][releases]

![Supports amd64 Architecture][amd64-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports arm64 Architecture][arm64-shield]
![Supports i386 Architecture][i386-shield]

## 🥤 Snack-fueled coding 

You know what goes great with open-source coding? Snacks! If my project helped you out, maybe throw a little something my way so my potato chips and Coca-Cola stash doesn't run out!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/N4N7UZ6KN)

## ✨ Features

### General

- Full interoperability between Qbus and Home Assistant for the supported entities.
- Automatic firmware update of your Qbus controller (if required).
- New Qbus entities are automatically added to Home Assistant.
- Entities get a persistent ID in Home Assistant, even when changing the Qbus entity names in Serial Manager or when Qbus MQTT rebuilds.
- Climate entity in Home Assistant reflects current temperature, requested temperature and preset, regardless of whether you change the temperature by preset or manually.
- Climate entity in Home Assistant automatically sets its mode to either `heat` or `off`.
- When Home Assistant restarts, all Qbus entities will report their current state.
- Supports multiple controllers.
- Supports Luqas P1 meter gauges.

### Customizations

All customizations are optional.

- Automatically create sensors for climate entities so you can show a nice graph on your dashboard.
- Choose which climate presets you want to make available in Home Assistant.
- Define on/off entities that should be created as a binary sensor.

### Supported entities

| Qbus | Home Assistant |
| --- | --- |
| Dimmer | Light |
| Gauge | Sensor |
| On/Off | Switch (or Binary sensor) |
| Scene | Scene |
| Shutter | Cover |
| Thermostat | Climate (heating only) |
| Ventilation | Sensor (CO2) |

## 🛠️ Setup

### Prerequisites
- Qbus home automation system (hardware).
- Qbus MQTT gateway. Choose one of these installation methods:
  - Docker version: thomasddn/qbusmqtt ([Docker Hub](https://hub.docker.com/r/thomasddn/qbusmqtt) | [source](https://github.com/thomasddn/qbusmqtt))
  - Bare metal: https://github.com/QbusKoen/qbusMqtt. Be sure to only install the gateway (qbusMqttGw) and optionally Mosquitto. You can also use an [installer script](https://github.com/QbusKoen/QbusMqtt-installer).
- MQTT broker (e.g. https://hub.docker.com/_/eclipse-mosquitto).
- Home Assistant MQTT integration (https://www.home-assistant.io/integrations/mqtt/)

### Installation

1. Create docker-compose.yaml
1. Adjust [environment variables](#configuration) as needed
1. Start the container:  `docker compose up -d`

Example docker-compose.yaml:

```yaml
version: '3.4'

services:
  qbha:
    image: thomasddn/qbha:latest
    container_name: qbha
    restart: unless-stopped
    volumes:
      - ./data:/data            # Optional
    environment:
      MQTT_HOST: 192.168.0.123
      TZ: Europe/Brussels
```

Check the wiki for more examples.

### Configuration

| Key | Required | Default value | Description |
| --- | --- | --- | --- |
| MQTT_HOST | Y | \<empty> | The IP or host name of the MQTT broker. |
| MQTT_PORT | N | 1883 | The port of the MQTT broker. |
| MQTT_USER | N | \<empty> | The username to connect to the MQTT broker. |
| MQTT_PWD | N | \<empty> | The password to connect to the MQTT broker. |
| BINARY_SENSORS | N | \<empty> | Comma separated list of on/off entities to be created as binary sensors. You can use either the Qbus `entity_id`, `ref_id` or `name` to define an on/off entity. |
| CLIMATE_PRESETS | N | MANUEEL, VORST, NACHT, ECONOMY, COMFORT | Comma separated list of climate presets you want to have available in HA. Also useful if your controller is set to another language. Applies to all climate entities. |
| CLIMATE_SENSORS | N | False | Create sensors for climate entities, having the current temperature as state. |
| QBUS_CAPTURE | N | False | Log all Qbus topic messages to a file, regardless of LOG_LEVEL. Used for debugging purposes. |
| LOG_LEVEL | N | INFO | The log level to use. Can be one of the following: CRITICAL, ERROR, WARNING, INFO, DEBUG. |

### Data folder

Optionally, you can mount the `/data` folder. It will contain log files and Qbus configuration files.

## 💡 Credits

This project was inspired by https://github.com/QbusKoen/qbusMqtt and https://github.com/wk275/qbTools-v2.

## 🗣️ Remarks
:warning: This is **not** officially supported by Qbus.



[releases-shield]: https://img.shields.io/github/v/release/thomasddn/qbha?style=flat-square
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg?style=flat-square
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg?style=flat-square
[arm64-shield]: https://img.shields.io/badge/arm64-yes-green.svg?style=flat-square
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg?style=flat-square
[releases]: https://github.com/thomasddn/qbha/releases
