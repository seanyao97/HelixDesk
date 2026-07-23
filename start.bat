@echo off
cd /d "%~dp0"
echo HelixDesk 启动中...
python main.py
if errorlevel 1 (
    echo.
    echo 启动失败！请确认已安装 PySide6：
    echo pip install PySide6
    pause
)