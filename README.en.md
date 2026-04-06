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

## Overview

Pro Auto Clicker is a lightweight Windows automation tool built with Python and PySide6. It is designed for fast, repeatable actions without overloading the interface: choose mouse or keyboard mode, tune the few settings that matter, and start.

The app now includes full multilingual support for Simplified Chinese, Traditional Chinese, and English. It also remembers your last real working state, including the selected action mode and interface language, so reopening the app feels seamless.

## Highlights

- Mouse mode supports left, right, and middle button automation.
- Mouse targeting supports delayed position capture on start or fixed coordinates.
- Keyboard mode supports single keys and modifier combinations.
- The UI automatically hides unrelated controls based on the selected mode.
- Your last-used configuration and language are restored on the next launch.
- Global hotkeys and app-only hotkeys are both supported.
- Presets can be saved locally and imported or exported as JSON.
- System tray support keeps the tool accessible while it runs in the background.

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
- Push a tag like `v1.0.0` to build and publish a GitHub Release automatically.
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
  models.py
  resources.py
  store.py
  win32_backend.py
  ui/
    hotkey_edit.py
    main_window.py
assets/
scripts/
tests/
.github/workflows/
build.ps1
ProAutoClicker.spec
```

## License

This project is released under the [MIT License](./LICENSE).
