@echo off
cd /d "F:\PlayWright"
call venv\Scripts\activate.bat
cd /d "F:\PlayWright\1-tranfermarkt-mexico"
python _dataset_to_input.py
pause
