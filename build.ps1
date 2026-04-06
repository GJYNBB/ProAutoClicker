param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

& $Python -m pip install -r requirements.txt
& $Python -m pip install pyinstaller
& $Python .\scripts\generate_icon.py
& $Python -m PyInstaller --noconfirm --clean .\ProAutoClicker.spec
