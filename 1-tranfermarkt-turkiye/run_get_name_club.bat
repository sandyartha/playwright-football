@echo off
cd /d "F:\PlayWright"
call venv\Scripts\activate.bat
cd /d "F:\PlayWright\1-tranfermarkt-turkiye"
python _get_name_club.py
pause
