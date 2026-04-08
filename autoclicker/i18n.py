from __future__ import annotations

import locale
import os
from collections.abc import Iterable

SUPPORTED_LANGUAGES = ("zh-CN", "zh-TW", "en")
LANGUAGE_NATIVE_NAMES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "en": "English",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh-CN": {
        "app.display_name": "专业连点器 Pro",
        "app.hero_subtitle": "默认记住上次实际使用的配置，鼠标与键盘模式按需展示参数。",
        "preset.default_name": "默认",
        "group.action": "动作设置",
        "group.mouse": "鼠标参数",
        "group.timing": "通用参数",
        "group.hotkey": "热键",
        "group.options": "选项",
        "group.controls": "操作",
        "group.status": "运行状态",
        "group.help": "使用说明",
        "group.presets": "预设",
        "field.action_mode": "动作类型",
        "field.action_key": "键盘按键",
        "field.mouse_button": "鼠标按键",
        "field.target_mode": "目标模式",
        "field.fixed_coordinates": "固定坐标",
        "field.capture_delay": "记录位置延时",
        "field.frequency": "频率",
        "field.language": "界面语言",
        "field.hotkey_scope": "热键范围",
        "field.toggle_hotkey": "开始 / 暂停",
        "field.exit_hotkey": "退出程序",
        "field.current_preset": "当前预设",
        "field.current_state": "当前状态",
        "field.hud_items": "悬浮窗显示项",
        "field.hud_position": "悬浮窗位置",
        "field.actual_frequency": "实际触发频率",
        "field.action_count": "累计点击/按键数",
        "field.target_position": "目标位置",
        "field.current_summary": "当前配置概览",
        "action.mouse": "鼠标",
        "action.keyboard": "键盘",
        "mouse_button.left": "左键",
        "mouse_button.right": "右键",
        "mouse_button.middle": "中键",
        "target.capture": "启动后延时记录当前位置",
        "target.fixed": "固定坐标",
        "hotkey_scope.global": "全局热键",
        "hotkey_scope.application": "仅应用内生效",
        "hud_item.state": "运行状态",
        "hud_item.rate": "实际频率",
        "hud_item.count": "累计次数",
        "hint.action_key": "支持一个主键加可选修饰键，例如 Ctrl+F8。",
        "hint.hotkey_scope": "全局热键在切到别的程序后仍然生效；仅应用内热键只在本窗口处于焦点时生效。",
        "hint.hotkey_input": "点击这里后按下快捷键",
        "hint.hud_items": "至少选择 1 项，最多可同时显示 3 项；位置使用屏幕坐标。",
        "option.minimize_to_tray": "关闭窗口时最小化到系统托盘，而不是直接退出",
        "option.hud_enabled": "启用半透明悬浮窗",
        "button.read_cursor": "读取当前鼠标位置",
        "button.start_resume": "开始 / 继续",
        "button.pause": "暂停",
        "button.exit": "退出",
        "button.load": "加载",
        "button.save": "保存",
        "button.save_as": "另存为",
        "button.delete": "删除",
        "button.import_json": "导入 JSON",
        "button.export_json": "导出 JSON",
        "button.ok": "确定",
        "suffix.seconds": " 秒",
        "suffix.per_second": " 次/秒",
        "value.actual_frequency": "{frequency:.1f} 次/秒",
        "menu.file": "文件",
        "menu.file.import_presets": "导入预设",
        "menu.file.export_presets": "导出预设",
        "menu.file.exit": "退出",
        "menu.language": "语言",
        "menu.help": "帮助",
        "menu.help.usage": "使用说明",
        "tray.show_window": "显示窗口",
        "tray.start_pause": "开始 / 暂停",
        "tray.pause": "暂停",
        "tray.exit": "退出",
        "state.idle": "待命",
        "state.countdown": "等待记录位置",
        "state.running": "运行中",
        "state.paused": "已暂停",
        "status.ready": "准备就绪。",
        "status.fix_errors_before_hotkey": "请先修正当前配置中的错误，再使用热键。",
        "status.loaded_preset": "已加载预设：{name}",
        "status.saved_preset": "已保存预设：{name}",
        "status.saved_preset_as": "已另存预设：{name}",
        "status.deleted_preset": "已删除预设：{name}",
        "status.imported_presets": "已导入 {count} 个预设。",
        "status.exported_presets": "预设已导出到：{path}",
        "status.save_config_failed": "保存配置失败：{error}",
        "status.tray_running": "程序仍在系统托盘中运行。",
        "controller.paused": "已暂停。",
        "controller.waiting_capture": "等待记录鼠标位置。",
        "controller.capture_failed": "记录位置失败。",
        "controller.capture_position_failed": "记录鼠标位置失败。",
        "controller.captured_position": "已记录鼠标位置：({x}, {y})。",
        "controller.running": "正在执行：{action}。",
        "controller.execution_error": "因执行错误而暂停。",
        "controller.countdown": "{seconds} 秒后记录当前位置...",
        "summary.target.not_applicable": "不适用",
        "summary.target.capture": "启动后延时 {seconds:.1f} 秒记录当前位置",
        "summary.target.fixed": "固定坐标 ({x}, {y})",
        "summary.action.keyboard": "{action}：{combo}",
        "summary.not_set": "未设置",
        "summary.hotkeys": "开始/暂停 {toggle}，退出 {exit}，{scope}",
        "summary.full": "{action}；频率 {frequency:.1f} 次/秒；目标模式：{target}；热键：{hotkeys}。",
        "target_value.keyboard_mode": "键盘模式不使用鼠标目标。",
        "target_value.fixed": "固定坐标：({x}, {y})",
        "target_value.capture_pending": "将在开始时记录当前位置。",
        "target_value.waiting_capture": "等待记录当前位置。",
        "target_value.captured": "已记录目标位置：({x}, {y})",
        "dialog.help_title": "{app_name} 使用说明",
        "dialog.preset_name": "请输入预设名称：",
        "dialog.delete_preset": "确定删除预设“{name}”吗？",
        "dialog.import_failed": "导入预设失败。\n{error}",
        "dialog.export_failed": "导出预设失败。\n{error}",
        "dialog.cursor_failed": "读取当前鼠标位置失败。",
        "dialog.json_filter": "JSON 文件 (*.json)",
        "dialog.presets_file_name": "presets.json",
        "validation.capture_delay_range": "记录位置延时必须在 0 到 60 秒之间。",
        "validation.frequency_range": "频率必须在每秒 0.1 到 1000 次之间。",
        "validation.toggle_hotkey_required": "必须设置开始 / 暂停热键。",
        "validation.exit_hotkey_required": "必须设置退出热键。",
        "validation.hotkeys_must_differ": "开始 / 暂停热键和退出热键不能相同。",
        "validation.toggle_hotkey_unsupported": "开始 / 暂停热键使用了当前版本不支持的按键。",
        "validation.exit_hotkey_unsupported": "退出热键使用了当前版本不支持的按键。",
        "validation.action_mode_unsupported": "选择了不支持的动作类型。",
        "validation.mouse_button_unsupported": "选择了不支持的鼠标按键。",
        "validation.hotkey_scope_unsupported": "选择了不支持的热键范围。",
        "validation.keyboard_action_required": "键盘动作必须设置一个目标按键。",
        "validation.keyboard_action_unsupported": "键盘动作使用了当前版本不支持的按键。",
        "validation.keyboard_equals_toggle": "键盘动作不能与开始 / 暂停热键完全相同。",
        "validation.keyboard_equals_exit": "键盘动作不能与退出热键完全相同。",
        "validation.target_mode_unsupported": "选择了不支持的目标模式。",
        "validation.fixed_coordinates_invalid": "固定坐标必须是大于等于 0 的整数。",
        "error.invalid_preset_root": "预设文件格式不正确。",
        "error.invalid_preset_presets": "预设文件中的 presets 字段必须是数组。",
        "error.unsupported_keyboard_action": "键盘动作使用了当前版本不支持的按键。",
        "error.unsupported_hotkey": "不支持的热键：{hotkey}",
        "error.register_toggle_failed": "注册开始 / 暂停热键失败：{hotkey}",
        "error.register_exit_failed": "注册退出热键失败：{hotkey}",
        "error.mouse_target_required": "鼠标模式需要有效的目标位置。",
        "help.html": """
<h3>快速开始</h3>
<ol>
  <li>先选择动作类型：鼠标或键盘。</li>
  <li>如果是键盘模式，录入要持续触发的按键或组合键。</li>
  <li>如果是鼠标模式，再设置鼠标按键、目标模式和记录位置延时。</li>
  <li>设置频率、开始 / 暂停热键和退出热键。</li>
  <li>点击 <b>开始 / 继续</b>。如果是“记录当前位置”模式，每次开始都会重新读取鼠标位置。</li>
</ol>
<h3>注意事项</h3>
<ul>
  <li>键盘动作支持一个主键和可选的 Ctrl、Alt、Shift、Win 修饰键。</li>
  <li>开始 / 暂停热键和退出热键不能相同。</li>
  <li>键盘动作不能与开始 / 暂停热键或退出热键完全相同。</li>
  <li>全局热键基于 Windows 实现，本版本优先面向 Windows 使用场景。</li>
  <li>预设放在页面底部，适合在常用配置稳定后再保存和切换。</li>
</ul>
<h3>托盘行为</h3>
<p>如果开启托盘模式，关闭主窗口后程序仍会留在系统托盘中运行，你可以通过托盘菜单继续开始、暂停或退出。</p>
""",
    },
    "zh-TW": {
        "app.display_name": "專業連點器 Pro",
        "app.hero_subtitle": "預設會記住上次實際使用的設定，滑鼠與鍵盤模式會按需顯示參數。",
        "preset.default_name": "預設",
        "group.action": "動作設定",
        "group.mouse": "滑鼠參數",
        "group.timing": "通用參數",
        "group.hotkey": "熱鍵",
        "group.options": "選項",
        "group.controls": "操作",
        "group.status": "執行狀態",
        "group.help": "使用說明",
        "group.presets": "預設",
        "field.action_mode": "動作類型",
        "field.action_key": "鍵盤按鍵",
        "field.mouse_button": "滑鼠按鍵",
        "field.target_mode": "目標模式",
        "field.fixed_coordinates": "固定座標",
        "field.capture_delay": "記錄位置延時",
        "field.frequency": "頻率",
        "field.language": "介面語言",
        "field.hotkey_scope": "熱鍵範圍",
        "field.toggle_hotkey": "開始 / 暫停",
        "field.exit_hotkey": "結束程式",
        "field.current_preset": "目前預設",
        "field.current_state": "目前狀態",
        "field.hud_items": "懸浮窗顯示項目",
        "field.hud_position": "懸浮窗位置",
        "field.actual_frequency": "實際觸發頻率",
        "field.action_count": "累計點擊/按鍵數",
        "field.target_position": "目標位置",
        "field.current_summary": "目前設定概覽",
        "action.mouse": "滑鼠",
        "action.keyboard": "鍵盤",
        "mouse_button.left": "左鍵",
        "mouse_button.right": "右鍵",
        "mouse_button.middle": "中鍵",
        "target.capture": "啟動後延時記錄目前位置",
        "target.fixed": "固定座標",
        "hotkey_scope.global": "全域熱鍵",
        "hotkey_scope.application": "僅應用內生效",
        "hud_item.state": "執行狀態",
        "hud_item.rate": "實際頻率",
        "hud_item.count": "累計次數",
        "hint.action_key": "支援一個主鍵加可選修飾鍵，例如 Ctrl+F8。",
        "hint.hotkey_scope": "全域熱鍵在切到其他程式後仍會生效；僅應用內熱鍵只會在本視窗聚焦時生效。",
        "hint.hotkey_input": "點這裡後按下快捷鍵",
        "hint.hud_items": "至少選擇 1 項，最多可同時顯示 3 項；位置使用螢幕座標。",
        "option.minimize_to_tray": "關閉視窗時最小化到系統匣，而不是直接結束",
        "option.hud_enabled": "啟用半透明懸浮窗",
        "button.read_cursor": "讀取目前滑鼠位置",
        "button.start_resume": "開始 / 繼續",
        "button.pause": "暫停",
        "button.exit": "結束",
        "button.load": "載入",
        "button.save": "儲存",
        "button.save_as": "另存為",
        "button.delete": "刪除",
        "button.import_json": "匯入 JSON",
        "button.export_json": "匯出 JSON",
        "button.ok": "確定",
        "suffix.seconds": " 秒",
        "suffix.per_second": " 次/秒",
        "value.actual_frequency": "{frequency:.1f} 次/秒",
        "menu.file": "檔案",
        "menu.file.import_presets": "匯入預設",
        "menu.file.export_presets": "匯出預設",
        "menu.file.exit": "結束",
        "menu.language": "語言",
        "menu.help": "說明",
        "menu.help.usage": "使用說明",
        "tray.show_window": "顯示視窗",
        "tray.start_pause": "開始 / 暫停",
        "tray.pause": "暫停",
        "tray.exit": "結束",
        "state.idle": "待命",
        "state.countdown": "等待記錄位置",
        "state.running": "執行中",
        "state.paused": "已暫停",
        "status.ready": "準備就緒。",
        "status.fix_errors_before_hotkey": "請先修正目前設定中的錯誤，再使用熱鍵。",
        "status.loaded_preset": "已載入預設：{name}",
        "status.saved_preset": "已儲存預設：{name}",
        "status.saved_preset_as": "已另存預設：{name}",
        "status.deleted_preset": "已刪除預設：{name}",
        "status.imported_presets": "已匯入 {count} 個預設。",
        "status.exported_presets": "預設已匯出到：{path}",
        "status.save_config_failed": "儲存設定失敗：{error}",
        "status.tray_running": "程式仍在系統匣中執行。",
        "controller.paused": "已暫停。",
        "controller.waiting_capture": "等待記錄滑鼠位置。",
        "controller.capture_failed": "記錄位置失敗。",
        "controller.capture_position_failed": "記錄滑鼠位置失敗。",
        "controller.captured_position": "已記錄滑鼠位置：({x}, {y})。",
        "controller.running": "正在執行：{action}。",
        "controller.execution_error": "因執行錯誤而暫停。",
        "controller.countdown": "{seconds} 秒後記錄目前位置...",
        "summary.target.not_applicable": "不適用",
        "summary.target.capture": "啟動後延時 {seconds:.1f} 秒記錄目前位置",
        "summary.target.fixed": "固定座標 ({x}, {y})",
        "summary.action.keyboard": "{action}：{combo}",
        "summary.not_set": "未設定",
        "summary.hotkeys": "開始/暫停 {toggle}，結束 {exit}，{scope}",
        "summary.full": "{action}；頻率 {frequency:.1f} 次/秒；目標模式：{target}；熱鍵：{hotkeys}。",
        "target_value.keyboard_mode": "鍵盤模式不使用滑鼠目標。",
        "target_value.fixed": "固定座標：({x}, {y})",
        "target_value.capture_pending": "將在開始時記錄目前位置。",
        "target_value.waiting_capture": "等待記錄目前位置。",
        "target_value.captured": "已記錄目標位置：({x}, {y})",
        "dialog.help_title": "{app_name} 使用說明",
        "dialog.preset_name": "請輸入預設名稱：",
        "dialog.delete_preset": "確定刪除預設「{name}」嗎？",
        "dialog.import_failed": "匯入預設失敗。\n{error}",
        "dialog.export_failed": "匯出預設失敗。\n{error}",
        "dialog.cursor_failed": "讀取目前滑鼠位置失敗。",
        "dialog.json_filter": "JSON 檔案 (*.json)",
        "dialog.presets_file_name": "presets.json",
        "validation.capture_delay_range": "記錄位置延時必須介於 0 到 60 秒之間。",
        "validation.frequency_range": "頻率必須介於每秒 0.1 到 1000 次之間。",
        "validation.toggle_hotkey_required": "必須設定開始 / 暫停熱鍵。",
        "validation.exit_hotkey_required": "必須設定結束熱鍵。",
        "validation.hotkeys_must_differ": "開始 / 暫停熱鍵和結束熱鍵不能相同。",
        "validation.toggle_hotkey_unsupported": "開始 / 暫停熱鍵使用了目前版本不支援的按鍵。",
        "validation.exit_hotkey_unsupported": "結束熱鍵使用了目前版本不支援的按鍵。",
        "validation.action_mode_unsupported": "選擇了不支援的動作類型。",
        "validation.mouse_button_unsupported": "選擇了不支援的滑鼠按鍵。",
        "validation.hotkey_scope_unsupported": "選擇了不支援的熱鍵範圍。",
        "validation.keyboard_action_required": "鍵盤動作必須設定一個目標按鍵。",
        "validation.keyboard_action_unsupported": "鍵盤動作使用了目前版本不支援的按鍵。",
        "validation.keyboard_equals_toggle": "鍵盤動作不能與開始 / 暫停熱鍵完全相同。",
        "validation.keyboard_equals_exit": "鍵盤動作不能與結束熱鍵完全相同。",
        "validation.target_mode_unsupported": "選擇了不支援的目標模式。",
        "validation.fixed_coordinates_invalid": "固定座標必須是大於等於 0 的整數。",
        "error.invalid_preset_root": "預設檔案格式不正確。",
        "error.invalid_preset_presets": "預設檔案中的 presets 欄位必須是陣列。",
        "error.unsupported_keyboard_action": "鍵盤動作使用了目前版本不支援的按鍵。",
        "error.unsupported_hotkey": "不支援的熱鍵：{hotkey}",
        "error.register_toggle_failed": "註冊開始 / 暫停熱鍵失敗：{hotkey}",
        "error.register_exit_failed": "註冊結束熱鍵失敗：{hotkey}",
        "error.mouse_target_required": "滑鼠模式需要有效的目標位置。",
        "help.html": """
<h3>快速開始</h3>
<ol>
  <li>先選擇動作類型：滑鼠或鍵盤。</li>
  <li>如果是鍵盤模式，輸入要持續觸發的按鍵或組合鍵。</li>
  <li>如果是滑鼠模式，再設定滑鼠按鍵、目標模式和記錄位置延時。</li>
  <li>設定頻率、開始 / 暫停熱鍵和結束熱鍵。</li>
  <li>點擊 <b>開始 / 繼續</b>。如果是「記錄目前位置」模式，每次開始都會重新讀取滑鼠位置。</li>
</ol>
<h3>注意事項</h3>
<ul>
  <li>鍵盤動作支援一個主鍵和可選的 Ctrl、Alt、Shift、Win 修飾鍵。</li>
  <li>開始 / 暫停熱鍵和結束熱鍵不能相同。</li>
  <li>鍵盤動作不能與開始 / 暫停熱鍵或結束熱鍵完全相同。</li>
  <li>全域熱鍵基於 Windows 實作，本版本優先面向 Windows 使用情境。</li>
  <li>預設放在頁面底部，適合在常用設定穩定後再儲存與切換。</li>
</ul>
<h3>系統匣行為</h3>
<p>如果開啟系統匣模式，關閉主視窗後程式仍會留在系統匣中執行，你可以透過系統匣選單繼續開始、暫停或結束。</p>
""",
    },
    "en": {
        "app.display_name": "Pro Auto Clicker",
        "app.hero_subtitle": "Remembers your last real session and only shows the parameters relevant to the current mouse or keyboard mode.",
        "preset.default_name": "Default",
        "group.action": "Action",
        "group.mouse": "Mouse",
        "group.timing": "General",
        "group.hotkey": "Hotkeys",
        "group.options": "Options",
        "group.controls": "Controls",
        "group.status": "Runtime",
        "group.help": "Guide",
        "group.presets": "Presets",
        "field.action_mode": "Action Type",
        "field.action_key": "Keyboard Key",
        "field.mouse_button": "Mouse Button",
        "field.target_mode": "Target Mode",
        "field.fixed_coordinates": "Fixed Coordinates",
        "field.capture_delay": "Capture Delay",
        "field.frequency": "Frequency",
        "field.language": "Language",
        "field.hotkey_scope": "Hotkey Scope",
        "field.toggle_hotkey": "Start / Pause",
        "field.exit_hotkey": "Exit App",
        "field.current_preset": "Current Preset",
        "field.current_state": "Current State",
        "field.hud_items": "HUD Items",
        "field.hud_position": "HUD Position",
        "field.actual_frequency": "Actual Rate",
        "field.action_count": "Cumulative Actions",
        "field.target_position": "Target Position",
        "field.current_summary": "Current Summary",
        "action.mouse": "Mouse",
        "action.keyboard": "Keyboard",
        "mouse_button.left": "Left Button",
        "mouse_button.right": "Right Button",
        "mouse_button.middle": "Middle Button",
        "target.capture": "Capture current cursor after delay on start",
        "target.fixed": "Fixed coordinates",
        "hotkey_scope.global": "Global hotkeys",
        "hotkey_scope.application": "App only",
        "hud_item.state": "State",
        "hud_item.rate": "Rate",
        "hud_item.count": "Count",
        "hint.action_key": "Supports one main key plus optional modifiers, for example Ctrl+F8.",
        "hint.hotkey_scope": "Global hotkeys keep working when you switch to another app; app-only hotkeys work only while this window has focus.",
        "hint.hotkey_input": "Click here and press a shortcut",
        "hint.hud_items": "Choose at least 1 item and up to 3 items. Position uses screen coordinates.",
        "option.minimize_to_tray": "Minimize to the system tray when closing the window instead of exiting immediately",
        "option.hud_enabled": "Enable translucent HUD overlay",
        "button.read_cursor": "Use current cursor position",
        "button.start_resume": "Start / Resume",
        "button.pause": "Pause",
        "button.exit": "Exit",
        "button.load": "Load",
        "button.save": "Save",
        "button.save_as": "Save As",
        "button.delete": "Delete",
        "button.import_json": "Import JSON",
        "button.export_json": "Export JSON",
        "button.ok": "OK",
        "suffix.seconds": " s",
        "suffix.per_second": " / s",
        "value.actual_frequency": "{frequency:.1f} / s",
        "menu.file": "File",
        "menu.file.import_presets": "Import Presets",
        "menu.file.export_presets": "Export Presets",
        "menu.file.exit": "Exit",
        "menu.language": "Language",
        "menu.help": "Help",
        "menu.help.usage": "Usage Guide",
        "tray.show_window": "Show Window",
        "tray.start_pause": "Start / Pause",
        "tray.pause": "Pause",
        "tray.exit": "Exit",
        "state.idle": "Idle",
        "state.countdown": "Waiting to capture position",
        "state.running": "Running",
        "state.paused": "Paused",
        "status.ready": "Ready.",
        "status.fix_errors_before_hotkey": "Please fix the current configuration errors before using the hotkey.",
        "status.loaded_preset": "Loaded preset: {name}",
        "status.saved_preset": "Saved preset: {name}",
        "status.saved_preset_as": "Saved preset as: {name}",
        "status.deleted_preset": "Deleted preset: {name}",
        "status.imported_presets": "Imported {count} presets.",
        "status.exported_presets": "Presets exported to: {path}",
        "status.save_config_failed": "Failed to save settings: {error}",
        "status.tray_running": "The app is still running in the system tray.",
        "controller.paused": "Paused.",
        "controller.waiting_capture": "Waiting to capture the cursor position.",
        "controller.capture_failed": "Failed to capture the target position.",
        "controller.capture_position_failed": "Failed to capture the cursor position.",
        "controller.captured_position": "Captured cursor position: ({x}, {y}).",
        "controller.running": "Running: {action}.",
        "controller.execution_error": "Paused because of an execution error.",
        "controller.countdown": "Capturing the current position in {seconds} seconds...",
        "summary.target.not_applicable": "Not applicable",
        "summary.target.capture": "Capture the current cursor after {seconds:.1f} seconds on start",
        "summary.target.fixed": "Fixed coordinates ({x}, {y})",
        "summary.action.keyboard": "{action}: {combo}",
        "summary.not_set": "Not set",
        "summary.hotkeys": "Toggle {toggle}, exit {exit}, {scope}",
        "summary.full": "{action}; frequency {frequency:.1f}/s; target: {target}; hotkeys: {hotkeys}.",
        "target_value.keyboard_mode": "Keyboard mode does not use a mouse target.",
        "target_value.fixed": "Fixed coordinates: ({x}, {y})",
        "target_value.capture_pending": "The current cursor position will be captured when you start.",
        "target_value.waiting_capture": "Waiting to capture the current cursor position.",
        "target_value.captured": "Captured target position: ({x}, {y})",
        "dialog.help_title": "{app_name} Guide",
        "dialog.preset_name": "Enter a preset name:",
        "dialog.delete_preset": "Delete preset \"{name}\"?",
        "dialog.import_failed": "Failed to import presets.\n{error}",
        "dialog.export_failed": "Failed to export presets.\n{error}",
        "dialog.cursor_failed": "Failed to read the current cursor position.",
        "dialog.json_filter": "JSON Files (*.json)",
        "dialog.presets_file_name": "presets.json",
        "validation.capture_delay_range": "Capture delay must be between 0 and 60 seconds.",
        "validation.frequency_range": "Frequency must be between 0.1 and 1000 actions per second.",
        "validation.toggle_hotkey_required": "A start / pause hotkey is required.",
        "validation.exit_hotkey_required": "An exit hotkey is required.",
        "validation.hotkeys_must_differ": "The start / pause hotkey and exit hotkey must be different.",
        "validation.toggle_hotkey_unsupported": "The start / pause hotkey uses a key that is not supported in this version.",
        "validation.exit_hotkey_unsupported": "The exit hotkey uses a key that is not supported in this version.",
        "validation.action_mode_unsupported": "The selected action type is not supported.",
        "validation.mouse_button_unsupported": "The selected mouse button is not supported.",
        "validation.hotkey_scope_unsupported": "The selected hotkey scope is not supported.",
        "validation.keyboard_action_required": "Keyboard mode requires a target key.",
        "validation.keyboard_action_unsupported": "Keyboard mode uses a key that is not supported in this version.",
        "validation.keyboard_equals_toggle": "The keyboard action cannot be exactly the same as the start / pause hotkey.",
        "validation.keyboard_equals_exit": "The keyboard action cannot be exactly the same as the exit hotkey.",
        "validation.target_mode_unsupported": "The selected target mode is not supported.",
        "validation.fixed_coordinates_invalid": "Fixed coordinates must be integers greater than or equal to 0.",
        "error.invalid_preset_root": "The preset file format is invalid.",
        "error.invalid_preset_presets": "The `presets` field in the preset file must be an array.",
        "error.unsupported_keyboard_action": "The keyboard action uses a key that is not supported in this version.",
        "error.unsupported_hotkey": "Unsupported hotkey: {hotkey}",
        "error.register_toggle_failed": "Failed to register the start / pause hotkey: {hotkey}",
        "error.register_exit_failed": "Failed to register the exit hotkey: {hotkey}",
        "error.mouse_target_required": "Mouse mode requires a valid target position.",
        "help.html": """
<h3>Quick Start</h3>
<ol>
  <li>Choose an action type: mouse or keyboard.</li>
  <li>In keyboard mode, enter the key or key combo you want to repeat.</li>
  <li>In mouse mode, choose the mouse button, target mode, and capture delay.</li>
  <li>Set the frequency, start / pause hotkey, and exit hotkey.</li>
  <li>Click <b>Start / Resume</b>. In capture mode, the app records the current cursor position every time you start.</li>
</ol>
<h3>Notes</h3>
<ul>
  <li>Keyboard actions support one main key plus optional Ctrl, Alt, Shift, and Win modifiers.</li>
  <li>The start / pause hotkey and exit hotkey must be different.</li>
  <li>The keyboard action cannot exactly match the start / pause hotkey or the exit hotkey.</li>
  <li>Global hotkeys use a Windows-specific implementation and this release is optimized for Windows workflows.</li>
  <li>Presets live at the bottom of the page so the main flow stays focused on the active configuration.</li>
</ul>
<h3>System Tray</h3>
<p>If tray mode is enabled, closing the main window keeps the app running in the system tray so you can resume, pause, or exit from the tray menu.</p>
""",
    },
}


def normalize_language(language: str | None) -> str:
    value = str(language or "").strip()
    if value in SUPPORTED_LANGUAGES:
        return value

    lowered = value.replace("_", "-").lower()
    if not lowered:
        return "zh-CN"
    if lowered in {"zh-cn", "zh-hans", "zh-sg"} or "simplified" in lowered:
        return "zh-CN"
    if lowered in {"zh-tw", "zh-hk", "zh-mo", "zh-hant"} or "traditional" in lowered:
        return "zh-TW"
    if lowered.startswith("en"):
        return "en"
    if lowered.startswith("zh"):
        return "zh-CN"
    return "zh-CN"


def detect_system_language() -> str:
    candidates: list[str | None] = [
        os.environ.get("LC_ALL"),
        os.environ.get("LANGUAGE"),
        os.environ.get("LANG"),
    ]

    try:
        system_locale = locale.getlocale()[0]
    except ValueError:
        system_locale = None
    candidates.append(system_locale)

    for candidate in candidates:
        normalized = normalize_language(candidate)
        if candidate:
            return normalized
    return "zh-CN"


def tr(language: str | None, key: str, **kwargs: object) -> str:
    locale_key = normalize_language(language)
    template = TRANSLATIONS.get(locale_key, {}).get(key)
    if template is None:
        template = TRANSLATIONS["zh-CN"].get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template


def language_items() -> list[tuple[str, str]]:
    return [(code, LANGUAGE_NATIVE_NAMES[code]) for code in SUPPORTED_LANGUAGES]


def choice_labels(language: str | None, prefix: str, values: Iterable[str]) -> dict[str, str]:
    return {value: tr(language, f"{prefix}.{value}") for value in values}


def app_display_name(language: str | None) -> str:
    return tr(language, "app.display_name")


def build_help_html(language: str | None) -> str:
    return tr(language, "help.html")


def default_preset_name(language: str | None = None) -> str:
    return tr(language or detect_system_language(), "preset.default_name")


def default_preset_names() -> set[str]:
    names = {default_preset_name(code) for code in SUPPORTED_LANGUAGES}
    names.add("默认")
    return names
