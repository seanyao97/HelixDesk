@echo off
echo HelixDesk 打包工具
echo.
echo 需要先安装 PyInstaller: pip install PyInstaller
echo.
pip install PyInstaller
python build_exe.py
echo.
echo 打包完成！exe 文件在 dist\HelixDesk.exe
pause
