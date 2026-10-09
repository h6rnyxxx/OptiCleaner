@echo off
chcp 65001 >nul
title OptiCleaner Local Web Server
cd /d "%~dp0"
echo Starting OptiCleaner Local Server...
start "" "http://localhost:5000"
python server.py
pause
