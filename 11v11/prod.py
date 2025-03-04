import csv
import os
import pickle
import random
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Direktori untuk cache
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Fungsi untuk memeriksa cache
def check_cache(url, cache_dir=CACHE_DIR):
    cache_file = os.path.join(cache_dir, f"{url.replace('/', '_').replace(':', '')}.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None

# Fungsi untuk menyimpan cache
def save_cache(url, data, cache_dir=CACHE_DIR):
    cache_file = os.path.join(cache_dir, f"{url.replace('/', '_').replace(':', '')}.pkl")
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)

# Fungsi untuk scraping satu URL
def scrape_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Buka halaman web
            page.goto(url, wait_until="networkidle", timeout=20000)

            # Tangani modal pop-up cookie jika ada
            try:
                page.wait_for_selector("div.qc-cmp2-summary-buttons", timeout=10000)
                page.click("button.css-47sehv")  # Klik tombol "AGREE"
            except Exception:
                pass  # Jika tidak ada pop-up, lanjutkan

            # Ambil konten HTML
            html_content = page.content()
        except Exception as e:
            print(f"Error saat scraping {url}: {e}")
            html_content = None
        finally:
            browser.close()

        return html_content

# Fungsi untuk parsing tabel
def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Cari heading <h2>
    heading = soup.find('h2')
    heading_text = heading.text.strip() if heading else "No_Heading"

    # Cari tabel
    table = soup.find('table')
    if not table:
        print("Tabel tidak ditemukan.")
        return None, heading_text

    # Ekstrak header tabel
    headers = [header.text.strip() for header in table.find_all('th')]

    # Ekstrak baris tabel
    rows = table.find_all('tr')[1:]  # Lewati baris header
    data = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        cols = [col.text.strip() for col in cols]
        data.append(cols)

    return {
        'headers': headers,
        'data': data
    }, heading_text

# Fungsi untuk menyimpan data ke CSV
def save_to_csv(data, output_folder, filename):
    if not data:
        print("Tidak ada data untuk disimpan.")
        return

    # Pastikan direktori output ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Simpan data ke file CSV
    filepath = os.path.join(output_folder, f"{filename}.csv")
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(data['headers'])  # Tulis header
        writer.writerows(data['data'])   # Tulis data

    print(f"Data disimpan ke {filepath}")

# Fungsi utama untuk scraping multi URL
def scrape_multiple_urls(csv_file):
    # Baca URL dari file CSV
    urls = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append(row['urls'])  # Header kolom sekarang adalah "urls"

    # Buat folder output berdasarkan nama file CSV
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_folder = os.path.join("output", base_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Proses setiap URL
    for url in urls:
        print(f"Memproses URL: {url}")

        # Periksa cache
        cached_data = check_cache(url)
        if cached_data:
            print(f"URL {url} sudah di-scrape. Melewati...")
            continue

        # Tambahkan jeda acak
        random_delay = random.uniform(1, 5)
        print(f"Menunggu selama {random_delay:.2f} detik...")
        time.sleep(random_delay)

        # Lakukan scraping
        html_content = scrape_with_playwright(url)
        if not html_content:
            print(f"Gagal mengambil data dari {url}. Melewati...")
            continue

        # Parsing HTML
        result, heading_text = parse_html(html_content)
        if not result:
            print(f"Tidak ada data untuk disimpan dari {url}. Melewati...")
            continue

        # Simpan ke cache
        save_cache(url, result)

        # Simpan data ke CSV
        save_to_csv(result, output_folder, heading_text)

# Contoh penggunaan
if __name__ == "__main__":
    csv_file = "liverpool-history.csv"  # Ganti dengan path file CSV Anda
    scrape_multiple_urls(csv_file)