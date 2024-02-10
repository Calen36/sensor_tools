@title = Update
@echo on
call "venv/Scripts/activate.bat"
git pull
"venv/Scripts/Python.exe" -m pip install -r requirements.txt
@echo off
pause
