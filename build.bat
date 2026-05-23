@echo off
echo Building Daily Task Log .exe...
echo NOTE: If the app is running, quit it from the tray icon first (right-click ^> Quit).
echo.
venv\Scripts\pip install --upgrade pyinstaller >nul 2>&1
venv\Scripts\pyinstaller ^
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
