from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import pickle
import random
import time
import csv

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

# Fungsi untuk scraping satu URL dengan Playwright
def scrape_with_playwright(url):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Ubah ke headless=False jika ingin melihat browser

        # Create a new browser context with custom options
        context = browser.new_context(
            ignore_https_errors=True,  # Ignore HTTPS errors
            java_script_enabled=False,  # Disable JavaScript
            bypass_csp=True,  # Bypass Content Security Policy
            no_viewport=True,  # Disable viewport
            color_scheme='light'  # Set color scheme
        )

        page = context.new_page()

        try:
            # Blokir permintaan CSS dan gambar untuk mempercepat proses
            def block_css_and_images(route, request):
                if request.resource_type in ["stylesheet", "image"]:
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", block_css_and_images)

            # Hapus semua cookie
            context.clear_cookies()

            # Buka halaman web
            print(f"Membuka URL: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Hapus style inline menggunakan JavaScript
            page.evaluate("""
                const elements = document.querySelectorAll('*');
                elements.forEach(el => el.removeAttribute('style'));
            """)

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
            urls.append(row['urls'])

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
    csv_file = "manchester-united-history.csv"  # Ganti dengan path file CSV Anda
    scrape_multiple_urls(csv_file)