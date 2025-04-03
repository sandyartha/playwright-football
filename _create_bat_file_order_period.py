import os

folders = [
    "1-tranfermarkt-argentina",
    "1-tranfermarkt-australia",
    "1-tranfermarkt-austria",
    "1-tranfermarkt-belgia",
    "1-tranfermarkt-brazil",
    "1-tranfermarkt-chinese",
    "1-tranfermarkt-croatian",
    "1-tranfermarkt-czech",
    "1-tranfermarkt-england",
    "1-tranfermarkt-france",
    "1-tranfermarkt-germany",
    "1-tranfermarkt-india",
    "1-tranfermarkt-indonesia-2",
    "1-tranfermarkt-italy",
    "1-tranfermarkt-japan",
    "1-tranfermarkt-liga-1",
    "1-tranfermarkt-mexico",
    "1-tranfermarkt-netherlands",
    "1-tranfermarkt-portugal",
    "1-tranfermarkt-russian",
    "1-tranfermarkt-saudi-arabia",
    "1-tranfermarkt-scotland",
    "1-tranfermarkt-spain",
    "1-tranfermarkt-swiss",
    "1-tranfermarkt-turkiye",
    "1-tranfermarkt-ukraine",
    "1-tranfermarkt-USA",
]

base_path = "F:\\PlayWright"

for folder in folders:
    folder_path = os.path.join(base_path, folder)
    bat_content = f"""@echo off
cd /d "{base_path}"
call venv\\Scripts\\activate.bat
cd /d "{folder_path}"
python _order_period.py
pause
"""
    bat_file_path = os.path.join(folder_path, "run_order_period.bat")

    with open(bat_file_path, "w") as f:
        f.write(bat_content)

print("Semua file .bat sudah dibuat di masing-masing folder!")
