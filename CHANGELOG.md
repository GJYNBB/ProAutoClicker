# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project uses semantic versioning.

## [1.0.0] - 2026-04-06

### Added

- Initial public release of Pro Auto Clicker for Windows.
- Mouse automation with left, right, and middle click support.
- Keyboard automation with single-key and modifier-combination repeat actions.
- Two mouse target modes: delayed capture of the current cursor position and fixed coordinates.
- Local preset save, load, import, and export support with JSON files.
- Global hotkeys, app-only hotkeys, system tray support, and PyInstaller packaging.

### Changed

- Simplified the action model into mouse mode and keyboard mode.
- Simplified the interface by hiding irrelevant settings based on the active mode.
- Moved language switching into the top menu bar next to the main application menus.
- Added full Simplified Chinese, Traditional Chinese, and English localization for the app UI and README.
- Restored the last-used working configuration and interface language when reopening the app.

### Fixed

- Hardened settings parsing and preset import handling for malformed saved data.
- Fixed startup and runtime UI issues caused by incomplete window wiring.
- Added regression coverage for state restore, mode switching, target-row visibility, and localization behavior.
