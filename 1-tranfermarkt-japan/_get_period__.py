import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright
import os
from glob import glob

# Install fuzzywuzzy jika belum ada
try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("Installing fuzzywuzzy...")
    os.system("pip install fuzzywuzzy python-Levenshtein")
    from fuzzywuzzy import fuzz

# Daftar aturan untuk menangani singkatan klub
CLUB_ALIASES = {
  "albirex niigata": ["albirex", "the swans"],
  "avispa fukuoka": ["avispa", "the hornets"],
  "cerezo osaka": ["cerezo", "the cherry blossoms"],
  "fagiano okayama": ["fagiano", "the pheasants"],
  "fc tokyo": ["tokyo", "the gasmen"],
  "gamba osaka": ["gamba", "the black and blues"],
  "kashima antlers": ["antlers", "kashima", "the deer"],
  "kashiwa reysol": ["reysol", "the sun kings"],
  "kawasaki frontale": ["frontale", "the dolphins"],
  "kyoto sanga": ["sanga", "the purple sanga"],
  "machida zelvia": ["zelvia", "the green warriors"],
  "nagoya grampus": ["grampus", "the killer whales"],
  "sanfrecce hiroshima": ["sanfrecce", "the three arrows"],
  "shimizu s-pulse": ["s-pulse", "the orange wave"],
  "shonan bellmare": ["bellmare", "the sea breeze"],
  "tokyo verdy": ["verdy", "the green phoenix"],
  "urawa red diamonds": ["urawa reds", "the reds"],
  "vissel kobe": ["vissel", "the crimson"],
  "yokohama f. marinos": ["marinos", "the tricolore"],
  "yokohama fc": ["yokohama", "the fulie"]
}

def normalize_club_name(club_name):
    return club_name.lower().strip()

def get_canonical_club_name(club_name):
    club_name_normalized = normalize_club_name(club_name)
    for canonical_name, aliases in CLUB_ALIASES.items():
        if club_name_normalized in [normalize_club_name(alias) for alias in aliases]:
            return canonical_name
    return club_name_normalized

def is_club_match(club1, club2, threshold=80):
    club1_canonical = get_canonical_club_name(club1)
    club2_canonical = get_canonical_club_name(club2)
    if club1_canonical == club2_canonical:
        return True
    club1_normalized = normalize_club_name(club1)
    club2_normalized = normalize_club_name(club2)
    similarity = fuzz.ratio(club1_normalized, club2_normalized)
    return similarity >= threshold

def convert_to_transfers_url(profile_url):
    return profile_url.replace('/profil/', '/transfers/')

def get_transfer_history(profile_url):
    transfers_url = convert_to_transfers_url(profile_url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        print(f"Fetching URL with Playwright: {transfers_url}")
        try:
            page.goto(transfers_url)
            page.wait_for_selector('div.tm-player-transfer-history-grid', timeout=15000)
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            transfer_rows = soup.find_all('div', class_='grid tm-player-transfer-history-grid')
            if not transfer_rows:
                return []
            transfers = []
            for row in transfer_rows:
                if 'tm-player-transfer-history-grid--sum' in row.get('class', []) or 'tm-player-transfer-history-grid--heading' in row.get('class', []):
                    continue
                season = row.find('div', class_='tm-player-transfer-history-grid__season')
                date = row.find('div', class_='tm-player-transfer-history-grid__date')
                old_club = row.find('div', class_='tm-player-transfer-history-grid__old-club')
                new_club = row.find('div', class_='tm-player-transfer-history-grid__new-club')
                if season and date and old_club and new_club:
                    season_text = season.text.strip()
                    date_text = date.text.strip()
                    old_club_text = old_club.find('a', class_='tm-player-transfer-history-grid__club-link')
                    old_club_text = old_club_text.text.strip() if old_club_text else old_club.text.strip()
                    new_club_text = new_club.find('a', class_='tm-player-transfer-history-grid__club-link')
                    new_club_text = new_club_text.text.strip() if new_club_text else new_club.text.strip()
                    transfer = {
                        'season': season_text,
                        'date': date_text,
                        'old_club': old_club_text,
                        'new_club': new_club_text
                    }
                    transfers.append(transfer)
            transfers.sort(key=lambda x: parse_date(x['date']) if parse_date(x['date']) else datetime.min)
            return transfers
        except Exception as e:
            print(f"Error fetching {transfers_url}: {e}")
            return []
        finally:
            browser.close()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%b %d, %Y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d %b %Y')
        except ValueError:
            return None

def get_period_in_club(transfers, target_club):
    periods = []
    current_start = None
    target_club_normalized = normalize_club_name(target_club)
    for transfer in transfers:
        date = parse_date(transfer['date'])
        if date is None:
            continue
        old_club = transfer['old_club']
        new_club = transfer['new_club']
        if is_club_match(new_club, target_club):
            if not current_start:
                current_start = date
        elif is_club_match(old_club, target_club) and current_start:
            periods.append((current_start, date))
            current_start = None
    if current_start:
        for transfer in transfers:
            if transfer['new_club'].lower() == 'retired':
                end_date = parse_date(transfer['date'])
                if end_date:
                    periods.append((current_start, end_date))
                    current_start = None
                    break
        if current_start:
            periods.append((current_start, datetime.now()))
    return periods

# Ambil semua file CSV di folder raw
dataset_folder = 'raw'
csv_files = glob(os.path.join(dataset_folder, '*.csv'))

if not csv_files:
    print("No CSV files found in 'raw' folder.")
    exit()

# Buat folder 'period' jika belum ada
output_base_folder = 'period'
os.makedirs(output_base_folder, exist_ok=True)

# Proses setiap file CSV
all_results = []
for csv_file in csv_files:
    print(f"\nProcessing file: {csv_file}")
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except UnicodeDecodeError:
        print("UTF-8 failed, trying latin-1 encoding...")
        df = pd.read_csv(csv_file, encoding='latin-1')

    print("Columns:", df.columns.tolist())
    print("Data:", df.to_dict(orient='records'))

    for index, row in df.iterrows():
        name = row['name']
        club = row['club']
        profile_url = row['profile_url']
        
        print(f"\nProcessing {name} for club {club}...")
        transfers = get_transfer_history(profile_url)
        if not transfers:
            print(f"No transfer history found for {name}")
            continue
        
        periods_list = get_period_in_club(transfers, club)
        if not periods_list:
            print(f"No periods found for {name} in {club}")
            periods_combined = "NO DATA"
        else:
            period_strings = [f"{start.strftime('%Y')}-{end.strftime('%Y')}" for start, end in periods_list]
            periods_combined = ", ".join(period_strings)
        
        period_strings = [f"{start.strftime('%Y')}-{end.strftime('%Y')}" for start, end in periods_list]
        periods_combined = ", ".join(period_strings)
        
        all_results.append({
            'name': name,
            'club': club,
            'periods': periods_combined
        })

# Buat DataFrame dari semua hasil
results_df = pd.DataFrame(all_results)

if results_df.empty:
    print("No results to process.")
    exit()

print("\nAll Results:")
print(results_df)

# Simpan hasil per klub dalam satu file CSV
for club in results_df['club'].unique():
    club_df = results_df[results_df['club'] == club]
    club_filename = normalize_club_name(club).replace(" ", "_") + ".csv"
    output_file = os.path.join(output_base_folder, club_filename)
    
    club_df.to_csv(output_file, index=False)
    print(f"Saved {len(club_df)} records for {club} to {output_file}")