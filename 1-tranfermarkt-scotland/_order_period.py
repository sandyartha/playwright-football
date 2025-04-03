import pandas as pd
from pathlib import Path

# Path folder
period_folder = Path("period")
raw_folder = Path("raw")

# Dapatkan semua file di folder period
for period_file in period_folder.glob("*.csv"):
    club_name = period_file.stem  # Nama klub tanpa ekstensi
    raw_file = raw_folder / f"{club_name}_top_goals.csv"  # Sesuaikan dengan pola nama di raw
    
    if raw_file.exists():
        # Baca data dari folder period
        period_df = pd.read_csv(period_file)
        
        # Baca data dari folder raw
        raw_df = pd.read_csv(raw_file)
        
        # Gabungkan berdasarkan kolom 'name'
        merged_df = raw_df.merge(period_df[['name', 'periods']], on='name', how='left')
        
        # Update kolom 'period' dengan data dari 'periods'
        merged_df['period'] = merged_df['periods']
        
        # Hapus kolom tambahan
        merged_df = merged_df.drop(columns=['periods'])
        
        # Simpan kembali ke folder raw
        merged_df.to_csv(raw_file, index=False)
