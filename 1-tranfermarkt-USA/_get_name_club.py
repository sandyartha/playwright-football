import os
import pandas as pd
import json

# Folder dataset
dataset_folder = "dataset"

# Dictionary untuk menyimpan klub
club_mapping = {}

# Loop semua file CSV dalam folder dataset
for filename in os.listdir(dataset_folder):
    if filename.endswith(".csv"):
        filepath = os.path.join(dataset_folder, filename)

        # Membaca file CSV
        df = pd.read_csv(filepath)

        # Pastikan kolom 'club' ada di dalam file
        if "club" in df.columns:
            # Ambil semua nama klub yang unik dalam satu file
            unique_clubs = df["club"].dropna().unique()

            # Tambahkan ke dictionary dengan daftar kosong, ubah ke huruf kecil
            for club in unique_clubs:
                club_mapping[club.lower()] = []

# Simpan ke file JSON
output_file = "club_list.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(club_mapping, f, indent=2, ensure_ascii=False)

print(f"\n✅ Club list saved to {output_file}")