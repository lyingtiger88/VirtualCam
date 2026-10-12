@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -m pip install -r requirements.txt || pause
    py app.py
) else (
    python -m pip install -r requirements.txt || pause
    python app.py
)
if errorlevel 1 pause
