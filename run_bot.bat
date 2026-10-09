@echo off
cd /d "%~dp0telegram_bot"
start "" pythonw.exe tray_runner.py
exit
