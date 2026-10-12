@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -m pip install -r requirements.txt
    py -m PyInstaller --noconfirm --onefile --windowed --name BDFR_VirtualCam app.py
) else (
    python -m pip install -r requirements.txt
    python -m PyInstaller --noconfirm --onefile --windowed --name BDFR_VirtualCam app.py
)
pause
