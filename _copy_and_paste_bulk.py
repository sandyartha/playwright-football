import shutil
import os

# Base path
base_path = "F:\\PlayWright"

# Daftar folder tujuan
dest_folders = [
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
    "1-tranfermarkt-USA"
]

# Path file sumber
source_file = os.path.join(base_path, "1-tranfermarkt-turkiye", "_check_period.py")

# Gabungkan base_path dengan nama folder tujuan
dest_paths = [os.path.join(base_path, folder) for folder in dest_folders]

# Loop untuk menyalin file ke setiap folder
for dest_path in dest_paths:
    try:
        # Buat folder jika belum ada
        os.makedirs(dest_path, exist_ok=True)
        # Path lengkap tujuan
        dest_file_path = os.path.join(dest_path, "_check_period.py")
        # Salin file (skip jika folder tujuan adalah folder sumber)
        if dest_path != os.path.dirname(source_file):
            shutil.copy2(source_file, dest_file_path)
            print(f"Berhasil menyalin ke {dest_path}")
        else:
            print(f"Skip {dest_path} (folder sumber)")
    except Exception as e:
        print(f"Gagal menyalin ke {dest_path}: {str(e)}")