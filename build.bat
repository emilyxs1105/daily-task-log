@echo off
echo Building Daily Task Log .exe...
pip install pyinstaller >nul 2>&1
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "DailyTaskLog" ^
  --icon "assets\icon.ico" ^
  --add-data "assets;assets" ^
  main.py
echo.
echo Done! Your .exe is in the dist\ folder.
pause
