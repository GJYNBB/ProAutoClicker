<p align="center">
  <img src="assets/app_icon.png" width="120" alt="專業連點器 Pro 圖示">
</p>

<h1 align="center">專業連點器 Pro</h1>

<p align="center">
  一個專注、輕量、適合 Windows 的滑鼠與鍵盤自動連發工具。
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

## 專案簡介

專業連點器 Pro 以 Python 和 PySide6 打造，面向 Windows 桌面使用情境，適合處理日常重複點擊、按鍵連發與輕量自動化操作。這個專案的重點不是堆疊大量功能，而是在常見流程中提供更直接、更穩定的操作體驗。

目前專案已支援完整的簡體中文、繁體中文與 English 多語介面，並會記住你上次真正使用的設定，包括動作模式與介面語言，重新開啟後就能延續上次狀態。

## 主要特色

- 滑鼠模式支援左鍵、右鍵、中鍵連點
- 滑鼠目標支援「啟動後延時記錄目前位置」與「固定座標」兩種方式
- 鍵盤模式支援單鍵與組合鍵連發
- 會依照目前模式自動隱藏不相關參數，介面更乾淨
- 會自動恢復上次使用的實際設定與語言
- 支援全域熱鍵與僅應用內熱鍵
- 支援預設儲存，以及 JSON 匯入匯出
- 支援系統匣執行

## 環境需求

- Windows
- Python 3.14 或更新版本

## 快速開始

安裝相依套件：

```powershell
python -m pip install -r requirements.txt
```

啟動開發版：

```powershell
python auto_clicker.py
```

## 本地打包

```powershell
.\build.ps1
```

打包完成後，可執行檔位於 `dist/ProAutoClicker/ProAutoClicker.exe`。

## 發布流程

儲存庫已內建 `.github/workflows/build-release.yml`。

- 推送到 `main` 分支時會自動建置 Windows Artifact
- 推送 `v1.0.0` 這類標籤時會自動建置並建立 GitHub Release
- 也支援手動觸發 `workflow_dispatch`

維護者發布步驟可參考 [RELEASING.md](./RELEASING.md)。

## 多語支援

- 應用內支援：`简体中文`、`繁體中文`、`English`
- 目前語言會寫入 `settings.json`
- 驗證錯誤、系統匣選單、使用說明、執行狀態文案都會跟著介面語言切換

## 專案結構

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

## 授權

本專案採用 [MIT License](./LICENSE)。
