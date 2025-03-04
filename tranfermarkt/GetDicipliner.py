import asyncio
import csv
import re
import os
from playwright.async_api import async_playwright
from typing import List, Dict, Tuple

# ✅ Ekstrak tahun dari URL untuk nama file CSV
def extract_years_from_urls(urls: List[str]) -> str:
    years = set()
    for url in urls:
        matches = re.findall(r"saison_id/(\d{4})", url)
        if matches:
            years.update(map(int, matches))
    if years:
        return f"Players_Disciplinary_{min(years)}-{max(years)}.csv"
    return "players_data.csv"

# ✅ Ekstrak tahun dari URL
def extract_year_from_url(url: str) -> str:
    match = re.search(r"saison_id/(\d{4})", url)
    return match.group(1) if match else "Unknown"

# ✅ Fungsi utama scraping
async def scrape_transfermarkt(url: str) -> List[Dict[str, str]]:
    year = extract_year_from_url(url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        current_url = url
        players_list = []
        seen_players = set()
        page_number = 1

        while current_url:
            try:
                await page.goto(current_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error loading page {current_url}: {e}")
                break

            print(f"📄 Scraping Halaman {page_number}: {current_url}")

            rows = await page.query_selector_all("table.items tbody tr")
            for row in rows:
                name_element = await row.query_selector("td:nth-child(2) table.inline-table td.hauptlink a")
                name = await name_element.evaluate("el => el.textContent.trim()") if name_element else "Unknown"

                position_element = await row.query_selector("td:nth-child(2) table.inline-table tr:nth-child(2) td")
                position = await position_element.evaluate("el => el.textContent.trim()") if position_element else "Unknown"

                nation_element = await row.query_selector("td.zentriert:nth-child(3) img:nth-of-type(1)")
                nation = await nation_element.evaluate("el => el.title") if nation_element else "Unknown"

                club_element = await row.query_selector("td.zentriert:nth-child(3) img")
                club = await club_element.evaluate("el => el.title") if club_element else "no clubs"

                stats = []
                for i in range(5, 13):
                    stat_element = await row.query_selector(f"td.zentriert:nth-child({i})")
                    stat = await stat_element.evaluate("el => el.textContent.trim()") if stat_element else "0"
                    stats.append(stat)

                player_data = {
                    "name": name,
                    "position": position,
                    "club": club,
                    "nation": nation,
                    "appearances": stats[0],
                    "yellow_suspensions": stats[1],
                    "yellow_cards": stats[2],
                    "second_yellow_cards": stats[3],
                    "red_cards": stats[4],
                    "sending_offs": stats[5],
                    "points": stats[6],
                    "cards_per_match": stats[7],
                    "year": year
                }

                key = (player_data['name'], player_data['position'], player_data['club'], player_data['nation'])
                if key not in seen_players:
                    seen_players.add(key)
                    players_list.append(player_data)

            next_page_url = await page.evaluate('''
                () => {
                    let nextButton = document.querySelector(".tm-pagination__list-item--icon-next-page a");
                    return nextButton ? nextButton.href : null;
                }
            ''')

            if next_page_url:
                current_url = next_page_url
                page_number += 1
            else:
                current_url = None

        await browser.close()
        return players_list

# ✅ Scrape semua URL dari file TXT
async def scrape_multiple_urls(file_path: str) -> Tuple[List[Dict[str, str]], str]:
    with open(file_path, "r") as file:
        urls = [line.strip() for line in file.readlines() if line.strip()]

    all_players = []
    for url in urls:
        print(f"\n🚀 Scraping dari URL: {url}")
        players = await scrape_transfermarkt(url)
        all_players.extend(players)

    return all_players, extract_years_from_urls(urls)

# ✅ Simpan hasil scraping ke CSV
def save_to_csv(data: List[Dict[str, str]], filename: str) -> None:
    # Buat folder 'dataset' jika belum ada
    os.makedirs("dataset", exist_ok=True)
    filepath = os.path.join("dataset", filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Name", 
            "Position", 
            "Club", 
            "Nation", 
            "Appearances", 
            "Yellow Card Suspensions", 
            "Yellow Cards", 
            "Second Yellow Cards", 
            "Red Cards", 
            "Sending Offs", 
            "Points", 
            "Cards Per Match", 
            "Year"])
        for player in data:
            writer.writerow([
                player["name"], 
                player["position"], 
                player["club"], 
                player["nation"], 
                player["appearances"], 
                player["yellow_suspensions"], 
                player["yellow_cards"], 
                player["second_yellow_cards"], 
                player["red_cards"], 
                player["sending_offs"], 
                player["points"], 
                player["cards_per_match"], 
                player["year"]])

if __name__ == "__main__":
    # ✅ Scrape Data hanya dari file txt
    urls_file = "urls.txt"
    players, csv_filename = asyncio.run(scrape_multiple_urls(urls_file))
    
    # ✅ Simpan Data ke CSV dengan nama otomatis
    save_to_csv(players, csv_filename)
    print(f"🎉 Data berhasil disimpan ke dataset/{csv_filename}! Total pemain unik: {len(players)}")
