import os
import pandas as pd
import chardet
import re
from tqdm import tqdm
import logging

# Konfigurasi logging untuk mencatat kesalahan
logging.basicConfig(filename='processing_errors.log', level=logging.ERROR)

def sanitize_club_name(club):
    """Membersihkan nama klub untuk digunakan dalam nama file."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', club.lower())

def extract_top_players(data, sort_column, output_columns):
    """
    Ekstrak top 100 pemain berdasarkan kolom tertentu.
    Tambahkan kolom 'rank' berdasarkan urutan hasil sorting.
    """
    # Validasi output_columns
    missing_columns = [col for col in output_columns if col not in data.columns]
    if missing_columns:
        raise KeyError(f"Missing columns in DataFrame: {missing_columns}")

    # Ekstrak top 100 pemain
    top_players = data[output_columns].sort_values(by=sort_column, ascending=False).head(100)

    # Tambahkan kolom 'rank' berdasarkan urutan hasil sorting
    top_players.insert(0, 'rank', range(1, len(top_players) + 1))

    return top_players

def process_csv_files(dataset_folder, output_folder):
    """Proses semua file CSV di folder dataset dan hasilkan file output per klub."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Daftar kolom yang akan diekspor ke file output (termasuk kolom 'rank')
    output_columns = [
        'name', 'full_name', 'appearances', 'goals', 'assists', 
        'minutes_played', 'period', 'jersey_name', 'jersey_number',
        'yellow_cards', 'red_cards', 'club', 'position', 'height',
        'nation', 'nation_code', 'profile_url', 'image_url',
        'club_logo_url', 'date_of_birth', 'place_of_birth', 'status'
    ]

    for file in tqdm(os.listdir(dataset_folder), desc="Processing files"):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(dataset_folder, file)
        try:
            # Deteksi encoding file
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read())
            encoding_detected = result['encoding'] if result['encoding'] else 'utf-8'

            # Baca file CSV
            df = pd.read_csv(file_path, encoding=encoding_detected)
        except UnicodeDecodeError:
            logging.error(f"Skipping file {file}, encoding issue.")
            print(f"Skipping file {file}, encoding issue.")
            continue

        # Bersihkan nama kolom dari Byte Order Mark (BOM)
        df.columns = df.columns.str.replace(r'ï»¿', '', regex=True)

        # Tambahkan kolom default
        df['period'] = "N/A"
        df['club_logo_url'] = "N/A"

        # Validasi kolom yang diperlukan
        required_columns = {'name', 'club', 'goals', 'assists', 'minutes_played'}
        if not required_columns.issubset(df.columns):
            logging.error(f"Skipping file {file}, missing required columns.")
            print(f"Skipping file {file}, missing required columns.")
            continue

        # Format kolom minutes_played
        df['minutes_played'] = df['minutes_played'].astype(float).map(lambda x: f"{x:.3f}")

        # Kelompokkan data berdasarkan klub
        grouped = df.groupby('club')

        for club, data in grouped:
            # Ekstrak top goalscorers dan assist providers
            top_goals = extract_top_players(data, 'goals', output_columns)
            top_assists = extract_top_players(data, 'assists', output_columns)

            # Sanitize nama klub untuk nama file
            sanitized_club = sanitize_club_name(club)
            goals_filename = f"{sanitized_club}_top_goals.csv"
            assists_filename = f"{sanitized_club}_top_assists.csv"

            # Simpan hasil ke file CSV
            goals_filepath = os.path.join(output_folder, goals_filename)
            assists_filepath = os.path.join(output_folder, assists_filename)

            top_goals.to_csv(goals_filepath, index=False)
            top_assists.to_csv(assists_filepath, index=False)

            print(f"Files created: {goals_filepath}, {assists_filepath}")

# Jalankan fungsi utama
dataset_folder = "dataset"
output_folder = "input"
process_csv_files(dataset_folder, output_folder)