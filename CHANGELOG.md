# Changelog

## [Unreleased]

### Added

- Option to create binary sensors for certain switch entities (#3)

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



[Unreleased]: https://github.com/thomasddn/qbha/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/thomasddn/qbha/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/thomasddn/qbha/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/thomasddn/qbha/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/thomasddn/qbha/releases/tag/v0.1.0
