./venv/Scripts/activate

# Panduan Menggunakan Playwright dengan Virtual Environment dan requirements.txt

## 1. Persiapan Awal

Pastikan Anda sudah menginstal Python (disarankan versi 3.8 atau lebih baru). Cek dengan perintah:

```sh
python --version
```

atau

```sh
python3 --version
```

## 2. Membuat Virtual Environment

Buat direktori proyek dan masuk ke dalamnya:

```sh
mkdir playwright_project
cd playwright_project
```

Buat virtual environment:

```sh
python -m venv venv
```

Aktifkan virtual environment:

- **Windows**:
  ```sh
  venv\Scripts\activate
  ```
- **Mac/Linux**:
  ```sh
  source venv/bin/activate
  ```

## 3. Instalasi Playwright

Setelah virtual environment aktif, instal Playwright dan dependensinya:

```sh
pip install playwright
```

Untuk mengunduh browser yang diperlukan oleh Playwright:

```sh
playwright install
```

## 4. Membuat `requirements.txt`

Untuk menyimpan daftar dependensi proyek, gunakan perintah:

```sh
pip freeze > requirements.txt
```

File `requirements.txt` akan berisi semua paket yang telah diinstal dalam virtual environment.

## 5. Menjalankan Skrip Playwright

Buat file `test.py` dengan isi contoh berikut:

```python
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com")
        print(page.title())
        browser.close()

if __name__ == "__main__":
    run()
```

Jalankan skrip dengan perintah:

```sh
python test.py
```

## 6. Menggunakan `requirements.txt` di Komputer Lain

Untuk menginstal semua dependensi pada komputer lain, aktifkan virtual environment dan jalankan:

```sh
pip install -r requirements.txt
```

## 7. Menonaktifkan Virtual Environment

Jika ingin keluar dari virtual environment, gunakan perintah:

```sh
deactivate
```

Dengan mengikuti langkah-langkah di atas, Anda dapat mengelola proyek Playwright dengan baik menggunakan virtual environment dan `requirements.txt`. Selamat mencoba!
