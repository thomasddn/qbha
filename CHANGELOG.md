# Changelog

## [0.8.0] - 2024-09-29

### Added

- Add support for ventilation CO2 sensor (#9)
- Make boot order with qbusmqtt irrelevant


## [0.7.3] - 2024-08-30

### Fixed

- Unsupported variant value type in Qbus configuration (#6)


## [0.7.2] - 2024-06-28

### Added

- Support for volume storage (#7 by @mathiasbl)


## [0.7.1] - 2024-06-08

### Fixed

- Unsupported variant value type in Qbus configuration (#6)


## [0.7.0] - 2024-06-07

### Added

- Added support for Luqas and gauges of variant Power, Energy, Current, Voltage. Gauges with unit 'kWh' are considered to be totals. (#5 by @mathiasbl)


## [0.6.0] - 2024-01-12

### Added

- Support for multiple controllers


## [0.5.0] - 2023-12-13

### Added

- Option to create binary sensors for certain switch entities (#3)
- Informational attributes


## [0.4.0] - 2023-11-21

### Added

- Option to create sensors for climate entities (#2)
- Option to define which climate presets to make available in HA

### Changed

- Make use of the `addon_configs` folder when running as HA add-on


## [0.3.0] - 2023-11-10

### Added

- Throttle thermostat updates

### Changed

- Add hostname as part of the MQTT client id

### Fixed

- Error when qbusconfig.json doesn't exist (#4)


## [0.2.0] - 2023-10-28

### Added

- Log version on startup
- Keep a changelog

### Fixed

- Fix permission issue

### Changed

- Upgrade python to v3.12


## [0.1.0] - 2023-10-20

### Added

- Initial version



[Unreleased]: https://github.com/thomasddn/qbha/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/thomasddn/qbha/compare/v0.7.3...v0.8.0
[0.7.3]: https://github.com/thomasddn/qbha/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/thomasddn/qbha/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/thomasddn/qbha/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/thomasddn/qbha/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/thomasddn/qbha/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/thomasddn/qbha/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/thomasddn/qbha/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/thomasddn/qbha/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/thomasddn/qbha/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/thomasddn/qbha/releases/tag/v0.1.0
