<p align="center">
  <img src="assets/app_icon.png" width="120" alt="专业连点器 Pro 图标">
</p>

<h1 align="center">专业连点器 Pro</h1>

<p align="center">
  一个专注、轻量、适合 Windows 的鼠标与键盘自动连发工具。
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
  <a href="https://github.com/GJYNBB/ProAutoClicker/releases/tag/v1.2.0">查看 v1.2.0 Release</a> |
  <a href="https://github.com/GJYNBB/ProAutoClicker/releases/download/v1.2.0/ProAutoClicker-windows.zip">下载 Windows 安装包</a>
</p>

## 下载

- 当前稳定版本：[v1.2.0](https://github.com/GJYNBB/ProAutoClicker/releases/tag/v1.2.0)
- Windows 直接下载：[ProAutoClicker-windows.zip](https://github.com/GJYNBB/ProAutoClicker/releases/download/v1.2.0/ProAutoClicker-windows.zip)

## 项目简介

专业连点器 Pro 基于 Python 和 PySide6 构建，面向 Windows 桌面场景，适合处理日常重复点击、按键连发和轻量自动化操作。项目的目标不是堆叠复杂功能，而是在常见使用场景下提供更直接、更稳定的操作体验。

现在项目已经支持完整的简体中文、繁体中文和 English 多语言界面，并且会记住你上次真正使用的配置，包括动作模式和界面语言，重新打开即可继续上次的工作状态。

## 主要特性

- 鼠标动作支持左键、右键、中键、单击、双击、三连击和长按
- 鼠标目标支持“启动后延时记录当前位置”和“固定坐标”两种方式
- 键盘动作支持单键和组合键连发
- 高级动作序列支持新增、编辑、复制、批量删除、按钮移动和直接拖拽排序
- 每个动作单元可独立设置随机间隔、随机按住时长、坐标抖动、执行次数、运行时长和完成后等待
- 会自动恢复上次使用的实际配置和语言
- 支持全局热键与仅应用内热键
- 支持预设保存，以及 JSON 导入导出
- 支持系统托盘运行、HUD 悬浮窗、HUD 内容排序和透明度调节
- 支持紧急停止热键、启动前确认、安全倒计时、检查更新和反馈入口

## 安全防护

- 紧急停止热键固定为 `Ctrl+Alt+End`，会尽量保持全局监听；触发后会立即停止控制器并退出应用。
- “启动前确认”默认关闭。启用后，每次开始自动化前都会弹出确认提示，适合固定坐标或高频动作。
- “执行前安全倒计时”默认关闭。设置为大于 `0` 的秒数后，每次动作执行前都会倒计时，期间可以使用退出热键或紧急停止热键取消。
- HUD 可选显示“最近动作”，方便观察最近一次执行时间和累计次数。

## 更新与反馈

- 菜单栏 `帮助 -> 检查更新` 会访问 GitHub Releases API，比较当前 `APP_VERSION` 与最新 release 标签。
- “启动时检查更新”默认关闭，可在界面设置中启用；检查过程异步执行，不会阻塞窗口操作。
- 菜单栏 `帮助 -> 提交反馈 / 报告问题` 会打开项目 Issues 页面。

## 跨平台计划

当前稳定输入后端仍然只支持 Windows，因为底层输入事件依赖 Win32 API：`SendInput`、`RegisterHotKey`、`GetCursorPos` 等。项目现在已经新增 `InputBackend` 抽象层，并将控制器改为后端注入模式：

- Windows 默认使用 `Win32InputBackend`。
- 非 Windows 平台会使用 `UnsupportedInputBackend`，给出明确的不支持提示，而不是在导入时崩溃。
- 后续可以新增基于 `pynput` 或 `pyautogui` 的后端，用于 macOS/Linux 的鼠标、键盘事件发送和热键注册。

## 环境要求

- Windows
- Python 3.14 或更高版本

## 快速开始

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

启动开发版：

```powershell
python auto_clicker.py
```

## 本地打包

```powershell
.\build.ps1
```

打包完成后，可执行文件位于 `dist/ProAutoClicker/ProAutoClicker.exe`。

## 发布流程

仓库已经包含 `.github/workflows/build-release.yml`。

- 推送到 `main` 分支时会自动构建 Windows Artifact
- 推送 `v1.2.0` 这类标签时会自动构建并创建 GitHub Release
- 也支持手动触发 `workflow_dispatch`

维护者发布步骤可参考 [RELEASING.md](./RELEASING.md)。

## 多语言支持

- 应用内支持：`简体中文`、`繁體中文`、`English`
- 当前语言会写入 `settings.json`
- 校验错误、托盘菜单、帮助说明、运行状态文案都会随界面语言一起切换

## 项目结构

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

## 许可证

本项目使用 [MIT License](./LICENSE)。
