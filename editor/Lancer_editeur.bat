@echo off
cd /d "%~dp0"
py -3 -c "import PIL" >nul 2>&1
if errorlevel 1 (
  echo Installez les dependances avec : py -3 -m pip install -r requirements.txt
  pause
  exit /b 1
)
if exist prelude_tournoi.json (
  py -3 app.py --project prelude_tournoi.json
) else (
  py -3 app.py
)
if errorlevel 1 pause
