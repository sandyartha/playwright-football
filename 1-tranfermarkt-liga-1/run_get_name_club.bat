@echo off
cd /d "F:\PlayWright"
call venv\Scripts\activate.bat
cd /d "F:\PlayWright\1-tranfermarkt-liga-1"
python _get_name_club.py
pause
