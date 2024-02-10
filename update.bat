@title = Update
@echo on
call "venv/Scripts/activate.bat"
"venv/Scripts/Python.exe" -m pip install -r requirements.txt
git pull

@echo off
pause
