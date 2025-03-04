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
        return f"Players_Goals_{min(years)}-{max(years)}.csv"
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

                club_element = await row.query_selector("td.zentriert:nth-child(5) a")
                club = await club_element.evaluate("el => el.title") if club_element else "for 2 clubs"
                
                minutes_played_element = await row.query_selector("td.rechts:nth-child(9)")
                minutes_played = await minutes_played_element.evaluate("el => el.textContent.trim()") if minutes_played_element else "0"

                minutes_per_goal_element = await row.query_selector("td.rechts:nth-child(10)")
                minutes_per_goal = await minutes_per_goal_element.evaluate("el => el.textContent.trim()") if minutes_per_goal_element else "0"

                appearances_element = await row.query_selector("td.zentriert:nth-child(6)")
                appearances = await appearances_element.evaluate("el => el.textContent.trim()") if appearances_element else "0"

                assists_element = await row.query_selector("td.zentriert:nth-child(7)")
                assists = await assists_element.evaluate("el => el.textContent.trim()") if assists_element else "0"

                penalty_kick_element = await row.query_selector("td.zentriert:nth-child(8)")
                penalty_kick = await penalty_kick_element.evaluate("el => el.textContent.trim()") if penalty_kick_element else "0"

                goals_per_match_element = await row.query_selector("td.zentriert:nth-child(11)")
                goals_per_match = await goals_per_match_element.evaluate("el => el.textContent.trim()") if goals_per_match_element else "0"

                goals_element = await row.query_selector("td.zentriert:nth-child(12)")
                goals = await goals_element.evaluate("el => el.textContent.trim()") if goals_element else "0"

                player_data = {
                    "name": name,
                    "position": position,
                    "club": club,
                    "nation": nation,
                    "appearances": appearances,
                    "assists": assists,
                    "penalty_kick": penalty_kick,
                    "menitbermain": minutes_played,
                    "menitgoal": minutes_per_goal,
                    "goalpermatch": goals_per_match,
                    "goals": goals,
                    "year": year
                }

                key = (
                    player_data['name'], 
                    player_data['position'], 
                    player_data['club'], 
                    player_data['nation'])
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
    # Create the dataset directory if it doesn't exist
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
            "Assists",
            "Penalty Kick",
            "Menit Bermain",
            "Menit Goal",
            "Goals per match",
            "Goals",
            "Year"])
        for player in data:
            writer.writerow([
                player["name"], 
                player["position"], 
                player["club"], 
                player["nation"], 
                player["appearances"],
                player["assists"],
                player["penalty_kick"], # Penalty Kick
                player["menitbermain"], # Menit Bermain
                player["menitgoal"], # Menit Goal
                player["goalpermatch"], # Goals per match
                player["goals"], # Goals
                player["year"]])
                
if __name__ == "__main__":
    # ✅ Scrape Data hanya dari file txt
    urls_file = "urls.txt"
    players, csv_filename = asyncio.run(scrape_multiple_urls(urls_file))
    
    # ✅ Simpan Data ke CSV dengan nama otomatis
    save_to_csv(players, csv_filename)
    print(f"🎉 Data berhasil disimpan ke dataset/{csv_filename}! Total pemain unik: {len(players)}")
