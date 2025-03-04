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
        matches = re.findall(r"saison_id=(\d{4})", url)
        if matches:
            years.update(map(int, matches))
    if years:
        return f"Tabel_Liga_{min(years)}-{max(years)}.csv"
    return "tabel_liga_data.csv"

# ✅ Ekstrak tahun dari URL
def extract_year_from_url(url: str) -> str:
    match = re.search(r"saison_id=(\d{4})", url)
    return match.group(1) if match else "Unknown"

# ✅ Fungsi utama scraping
async def scrape_transfermarkt(url: str) -> List[Dict[str, str]]:
    year = extract_year_from_url(url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        current_url = url
        clubs_list = []
        seen_clubs = set()
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
            if not rows:
                print(f"⚠️ No rows found on page {page_number}")
            for row in rows:
                rank_element = await row.query_selector("td.rechts.hauptlink")
                rank = await rank_element.evaluate("el => el.textContent.trim()") if rank_element else "Unknown"
                print(f"🔍 Rank: {rank}")

                club_element = await row.query_selector("td.no-border-links.hauptlink a")
                club = await club_element.evaluate("el => el.textContent.trim()") if club_element else "Unknown"
                print(f"🔍 Club: {club}")

                matches_element = await row.query_selector("td.zentriert:nth-child(4)")
                matches = await matches_element.evaluate("el => el.textContent.trim()") if matches_element else "0"
                print(f"🔍 Matches: {matches}")

                wins_element = await row.query_selector("td.zentriert:nth-child(5)")
                wins = await wins_element.evaluate("el => el.textContent.trim()") if wins_element else "0"
                print(f"🔍 Wins: {wins}")

                draws_element = await row.query_selector("td.zentriert:nth-child(6)")
                draws = await draws_element.evaluate("el => el.textContent.trim()") if draws_element else "0"
                print(f"🔍 Draws: {draws}")

                losses_element = await row.query_selector("td.zentriert:nth-child(7)")
                losses = await losses_element.evaluate("el => el.textContent.trim()") if losses_element else "0"
                print(f"🔍 Losses: {losses}")

                goals_element = await row.query_selector("td.zentriert:nth-child(8)")
                goals = await goals_element.evaluate("el => el.textContent.trim()") if goals_element else "0"
                print(f"🔍 Goals: {goals}")

                goal_difference_element = await row.query_selector("td.zentriert:nth-child(9)")
                goal_difference = await goal_difference_element.evaluate("el => el.textContent.trim()") if goal_difference_element else "0"
                print(f"🔍 Goal Difference: {goal_difference}")

                points_element = await row.query_selector("td.zentriert:nth-child(10)")
                points = await points_element.evaluate("el => el.textContent.trim()") if points_element else "0"
                print(f"🔍 Points: {points}")

                club_data = {
                    "rank": rank,
                    "club": club,
                    "matches": matches,
                    "wins": wins,
                    "draws": draws,
                    "losses": losses,
                    "goals": goals,
                    "goal_difference": goal_difference,
                    "points": points,
                    "year": year
                }

                key = (club_data['rank'], club_data['club'])
                if key not in seen_clubs:
                    seen_clubs.add(key)
                    clubs_list.append(club_data)

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
        return clubs_list

# ✅ Scrape semua URL dari file TXT
async def scrape_multiple_urls(file_path: str) -> Tuple[List[Dict[str, str]], str]:
    with open(file_path, "r") as file:
        urls = [line.strip() for line in file.readlines() if line.strip()]

    all_clubs = []
    for url in urls:
        print(f"\n🚀 Scraping dari URL: {url}")
        clubs = await scrape_transfermarkt(url)
        all_clubs.extend(clubs)

    return all_clubs, extract_years_from_urls(urls)

# ✅ Simpan hasil scraping ke CSV berdasarkan tahun
def save_to_csv_by_year(data: List[Dict[str, str]]) -> None:
    # Create the dataset directory if it doesn't exist
    os.makedirs("dataset", exist_ok=True)
    
    # Group data by year
    data_by_year = {}
    for club in data:
        year = club["year"]
        if year not in data_by_year:
            data_by_year[year] = []
        data_by_year[year].append(club)
    
    # Save each year's data to a separate CSV file
    for year, clubs in data_by_year.items():
        filename = f"Tabel_Liga_{year}.csv"
        filepath = os.path.join("dataset", filename)
        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Rank", 
                "Club", 
                "Matches", 
                "Wins", 
                "Draws", 
                "Losses", 
                "Goals", 
                "Goal Difference", 
                "Points", 
                "Year"])
            for club in clubs:
                writer.writerow([
                    club["rank"], 
                    club["club"], 
                    club["matches"], 
                    club["wins"], 
                    club["draws"], 
                    club["losses"], 
                    club["goals"], 
                    club["goal_difference"], 
                    club["points"], 
                    club["year"]])

if __name__ == "__main__":
    # ✅ Scrape Data hanya dari file txt
    urls_file = "urls.txt"
    clubs, _ = asyncio.run(scrape_multiple_urls(urls_file))
    
    # ✅ Simpan Data ke CSV berdasarkan tahun
    save_to_csv_by_year(clubs)
    print(f"🎉 Data berhasil disimpan ke folder dataset! Total klub unik: {len(clubs)}")
