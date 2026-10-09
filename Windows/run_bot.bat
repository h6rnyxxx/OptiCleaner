@echo off
if exist "%~dp0telegram_bot\tray_runner.py" (
    cd /d "%~dp0telegram_bot"
) else (
    cd /d "%~dp0..\telegram_bot"
)
start "" pythonw.exe tray_runner.py
exit
