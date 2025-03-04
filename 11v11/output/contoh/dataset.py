import pandas as pd
import os

# Tentukan folder input dan output
folder_input = 'input'  # Folder tempat file CSV berada
folder_output = 'output'  # Folder untuk menyimpan file H2H

# Pastikan folder output ada
if not os.path.exists(folder_output):
    os.makedirs(folder_output)

# Mapping nama klub untuk normalisasi
nama_klub_mapping = {
    "Manchester United": "Man Utd",
    "Manchester City": "Man City",
    "Liverpool FC": "Liverpool",
    "Arsenal FC": "Arsenal",
    "Newcastle United": "Newcastle",
    "Tottenham Hotspur": "Tottenham"
}

# Fungsi untuk memproses satu file CSV
def proses_file_csv(file_path):
    # Membaca file CSV
    df = pd.read_csv(file_path)

    # Memisahkan kolom "Match" menjadi dua kolom: "Tim 1" dan "Tim 2"
    df[['Tim 1', 'Tim 2']] = df['Match'].str.split(' v ', expand=True)

    # Memisahkan kolom "Score" menjadi dua kolom: "Skor Tim 1" dan "Skor Tim 2"
    def pisahkan_score(score):
        # Ambil hanya bagian sebelum "Agg:" jika ada
        if isinstance(score, str) and "Agg:" in score:
            score = score.split("Agg:")[0].strip()
        # Pisahkan skor menjadi dua bagian
        if isinstance(score, str) and "-" in score:
            skor_tim_1, skor_tim_2 = score.split("-")
            return int(skor_tim_1), int(skor_tim_2)
        return None, None

    df['Skor Tim 1'], df['Skor Tim 2'] = zip(*df['Score'].apply(pisahkan_score))

    # Normalisasi nama klub di kolom "Tim 1" dan "Tim 2"
    df['Tim 1'] = df['Tim 1'].apply(lambda x: nama_klub_mapping.get(x, x))
    df['Tim 2'] = df['Tim 2'].apply(lambda x: nama_klub_mapping.get(x, x))

    # Filter pertandingan Liverpool
    liverpool_matches = df[(df['Tim 1'] == 'Liverpool') | (df['Tim 2'] == 'Liverpool')].copy()

    # Ekstrak daftar klub unik yang pernah bertanding melawan Liverpool
    klub_unik = pd.concat([liverpool_matches['Tim 1'], liverpool_matches['Tim 2']]).unique()
    klub_unik = [klub for klub in klub_unik if klub != 'Liverpool']

    # Proses setiap klub
    for klub in klub_unik:
        # Filter pertandingan antara Liverpool dan klub tertentu
        klub_matches = liverpool_matches[
            ((liverpool_matches['Tim 1'] == 'Liverpool') & (liverpool_matches['Tim 2'] == klub)) |
            ((liverpool_matches['Tim 2'] == 'Liverpool') & (liverpool_matches['Tim 1'] == klub))
        ].copy()

        # List untuk menyimpan hasil H2H
        h2h_data = []
        poin_liverpool = 0
        poin_club_lain = 0
        total_draw = 0

        for index, row in klub_matches.iterrows():
            # Tentukan hasil pertandingan
            if row['Tim 1'] == 'Liverpool':
                lawan = row['Tim 2']
                hasil_liverpool = 'Win' if row['Skor Tim 1'] > row['Skor Tim 2'] else 'Draw' if row['Skor Tim 1'] == row['Skor Tim 2'] else 'Lost'
            elif row['Tim 2'] == 'Liverpool':
                lawan = row['Tim 1']
                hasil_liverpool = 'Win' if row['Skor Tim 2'] > row['Skor Tim 1'] else 'Draw' if row['Skor Tim 2'] == row['Skor Tim 1'] else 'Lost'

            # Hitung poin Liverpool
            if hasil_liverpool == 'Win':
                poin_liverpool += 1

            # Hitung poin klub lawan
            if hasil_liverpool == 'Lost':  # Hanya hitung kemenangan klub lawan
                poin_club_lain += 1

            # Hitung jumlah seri
            if hasil_liverpool == 'Draw':
                total_draw += 1

            # Simpan hasil
            h2h_data.append({
                'Date': row['Date'],
                'Liverpool': poin_liverpool,  # Poin akumulasi Liverpool
                klub: poin_club_lain,         # Poin akumulasi klub lawan
                'Draw': total_draw            # Total jumlah seri
            })

        # Buat DataFrame dari hasil H2H
        h2h_df = pd.DataFrame(h2h_data)

        if not h2h_df.empty:
            # Simpan hasil ke file CSV
            nama_file_h2h = os.path.join(folder_output, f'h2h_{klub.lower().replace(" ", "_")}.csv')
            h2h_df.to_csv(nama_file_h2h, index=False)
            print(f"Data H2H Liverpool vs {klub} berhasil disimpan ke {nama_file_h2h}")
        else:
            print(f"Tidak ada data H2H Liverpool vs {klub}.")

# Iterasi semua file CSV di folder input
for file_name in os.listdir(folder_input):
    if file_name.endswith('.csv'):
        file_path = os.path.join(folder_input, file_name)
        print(f"\nMemproses file: {file_path}")
        proses_file_csv(file_path)

print("\nPemrosesan selesai!")