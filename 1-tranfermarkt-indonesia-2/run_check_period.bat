@echo off
cd /d "F:\PlayWright"
call venv\Scripts\activate.bat
cd /d "F:\PlayWright\1-tranfermarkt-indonesia-2"
python _check_period.py
pause
