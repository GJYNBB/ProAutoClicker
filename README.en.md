<p align="center">
  <img src="assets/app_icon.png" width="120" alt="Pro Auto Clicker icon">
</p>

<h1 align="center">Pro Auto Clicker</h1>

<p align="center">
  A focused Windows desktop auto clicker for repeatable mouse and keyboard automation.
</p>

<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README.zh-TW.md">繁體中文</a> |
  <a href="./README.en.md">English</a>
</p>

<p align="center">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows-0A66C2">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.14%2B-3776AB">
  <img alt="GUI" src="https://img.shields.io/badge/GUI-PySide6-41CD52">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-111111">
</p>

<p align="center">
  <a href="https://github.com/GJYNBB/ProAutoClicker/releases/tag/v1.2.0">View v1.2.0 Release</a> |
  <a href="https://github.com/GJYNBB/ProAutoClicker/releases/download/v1.2.0/ProAutoClicker-windows.zip">Download Windows Package</a>
</p>

## Download

- Current stable release: [v1.2.0](https://github.com/GJYNBB/ProAutoClicker/releases/tag/v1.2.0)
- Direct Windows download: [ProAutoClicker-windows.zip](https://github.com/GJYNBB/ProAutoClicker/releases/download/v1.2.0/ProAutoClicker-windows.zip)

## Overview

Pro Auto Clicker is a lightweight Windows automation tool built with Python and PySide6. It is designed for fast, repeatable actions without overloading the interface: choose mouse or keyboard mode, tune the few settings that matter, and start.

The app now includes full multilingual support for Simplified Chinese, Traditional Chinese, and English. It also remembers your last real working state, including the selected action mode and interface language, so reopening the app feels seamless.

## Highlights

- Mouse actions support left, right, middle, single click, double click, triple click, and long press.
- Mouse targeting supports delayed position capture on start or fixed coordinates.
- Keyboard actions support single keys and modifier combinations.
- Advanced action sequences support add, edit, duplicate, batch delete, button-based reordering, and direct drag-and-drop reordering.
- Each action unit can define its own random interval, random hold duration, coordinate jitter, execution count, run duration, and post-step delay.
- Your last-used configuration and language are restored on the next launch.
- Global hotkeys and app-only hotkeys are both supported.
- Presets can be saved locally and imported or exported as JSON.
- System tray support keeps the tool accessible while it runs in the background.
- HUD content ordering, HUD opacity, emergency stop, start confirmation, safety countdown, update checks, and feedback links are supported.

## Safety

- The emergency stop hotkey is fixed to `Ctrl+Alt+End` and is kept globally registered when possible. Triggering it stops the controller and exits the app immediately.
- “Confirm Before Start” is disabled by default. When enabled, the app asks for confirmation before starting automation, which is useful for fixed coordinates or high-frequency actions.
- “Pre-action Safety Countdown” is disabled by default. Set it to a value greater than `0` to count down before each action; during the countdown you can cancel with the exit or emergency hotkey.
- The HUD can optionally show the “Last Action” line so you can see the most recent execution time and cumulative count.

## Updates And Feedback

- `Help -> Check for Updates` calls the GitHub Releases API and compares the latest release tag with the local `APP_VERSION`.
- “Check for updates on startup” is disabled by default. When enabled, the check runs asynchronously and does not block the UI.
- `Help -> Submit Feedback / Report Issue` opens the repository Issues page.

## Cross-platform Plan

The stable input backend is still Windows-only because low-level input events currently depend on Win32 APIs such as `SendInput`, `RegisterHotKey`, and `GetCursorPos`. The project now includes an `InputBackend` abstraction and the controller accepts a backend via dependency injection:

- Windows uses `Win32InputBackend` by default.
- Non-Windows platforms use `UnsupportedInputBackend`, which fails with a clear unsupported-platform message instead of crashing on import.
- A future backend can use `pynput` or `pyautogui` for macOS/Linux mouse, keyboard, and hotkey support.

## Requirements

- Windows
- Python 3.14 or newer

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the development build:

```powershell
python auto_clicker.py
```

## Build a Windows Package

```powershell
.\build.ps1
```

After packaging, the executable is generated at `dist/ProAutoClicker/ProAutoClicker.exe`.

## Release Workflow

The repository already includes `.github/workflows/build-release.yml`.

- Push to `main` to build a Windows artifact automatically.
- Push a tag like `v1.2.0` to build and publish a GitHub Release automatically.
- Trigger `workflow_dispatch` manually when you want a one-off build.

For the maintainer checklist, see [RELEASING.md](./RELEASING.md).

## Localization

- In-app languages: `简体中文`, `繁體中文`, `English`
- The selected language is persisted in `settings.json`
- Validation messages, tray menu text, help content, and runtime status text all switch with the UI language

## Project Structure

```text
auto_clicker.py
autoclicker/
  app.py
  controller.py
  i18n.py
  keymaps.py
  input_backend.py
  models.py
  resources.py
  store.py
  update_checker.py
  win32_backend.py
  ui/
    action_unit_editor.py
    components.py
    hotkey_edit.py
    main_window.py
    status_hud.py
assets/
scripts/
tests/
.github/workflows/
build.ps1
ProAutoClicker.spec
```

## License

This project is released under the [MIT License](./LICENSE).
