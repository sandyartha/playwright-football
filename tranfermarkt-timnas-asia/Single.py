import asyncio
import csv
import re
import os
import logging
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
import pycountry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_country_code(country_name: str) -> str:
    """Convert country name to country code."""
    try:
        return pycountry.countries.lookup(country_name).alpha_2.lower()
    except LookupError:
        return "unknown"

def extract_table_data(html: str, base_url: str) -> List[Dict[str, str]]:
    """Extract player data from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    players_list = []
    
    # Extract club name from h1
    club_name = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown"
    
    table = soup.find('table', class_='items')
    if not table:
        logging.warning("Table with class 'items' not found.")
        return []
    
    for row in table.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        if len(cols) < 12:
            continue  # Skip invalid rows
        
        # Extract player name, profile URL, and status
        name_container = cols[1].find('table', class_='inline-table')
        if name_container:
            name_element = name_container.find('td', class_='hauptlink').find('a')
            status_element = name_container.find_all('tr')[1].find('td') if len(name_container.find_all('tr')) > 1 else None
            image_element = name_container.find('a').find('img') if name_container.find('a') else None
        else:
            name_element = None
            status_element = None
            image_element = None
        
        name = name_element.text.strip() if name_element else "Unknown"
        status = status_element.text.strip() if status_element else "Unknown"
        raw_profile_url = name_element['href'] if name_element and 'href' in name_element.attrs else ""
        profile_url = urljoin(base_url, raw_profile_url) if raw_profile_url and raw_profile_url != "#" else "Unknown"
        image_url = image_element['src'] if image_element and 'src' in image_element.attrs else "Unknown"
        
        # Extract nation(s)
        nation_images = cols[5].find_all('img')
        nations = nation_images[0]['alt'] if nation_images and 'alt' in nation_images[0].attrs else "Unknown"
        nation_code = get_country_code(nations)
        
        # Extract other statistics with correct column mapping
        player = {
            "name": name,
            "status": status,
            "profile_url": profile_url,
            "image_url": image_url,
            "nation": nations,
            "nation_code": nation_code,
            "club": club_name,

            "dateofbirth": cols[6].text.strip(),
            "appearances": cols[7].text.strip(),
            "goals": cols[8].text.strip(),
            "assists": cols[9].text.strip(),
            "own_goals": cols[10].text.strip(),
            "yellow_cards": cols[11].text.strip(),
            "second_yellow": cols[12].text.strip(),
            "red_cards": cols[13].text.strip(),
            "sub_on": cols[14].text.strip(),
            "sub_off": cols[15].text.strip(),
            "minutes_played": cols[16].text.strip(),
        }
        logging.info(f"Extracted player: {player}")
        players_list.append(player)
    
    return players_list

async def scrape_profile_data(page: Page, profile_url: str) -> Dict[str, str]:
    """Scrape additional data from player's profile page."""
    if profile_url == "Unknown":
        return {"profile_heading": "Unknown", "place_of_birth": "Unknown", "position": "Unknown"}
    
    try:
        await page.goto(profile_url, wait_until="domcontentloaded")
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        heading_element = soup.find('h1')
        heading = heading_element.find('strong').get_text(strip=True) if heading_element and heading_element.find('strong') else "Unknown"
        
        # Extract full name
        full_name_element = soup.find('span', string='Name in home country:')
        full_name = full_name_element.find_next('span', class_='info-table__content--bold').get_text(strip=True) if full_name_element else "Unknown"
        
        # Extract place of birth
        place_of_birth_element = soup.find('span', string='Place of birth:')
        place_of_birth = place_of_birth_element.find_next('span', class_='info-table__content--bold').get_text(strip=True) if place_of_birth_element else "Unknown"
        
        # Extract position
        position_element = soup.find('span', string='Position:')
        position = position_element.find_next('span', class_='info-table__content--bold').get_text(strip=True) if position_element else "Unknown"
        
        # Extract height
        height_element = soup.find('span', string='Height:')
        height = height_element.find_next('span', class_='info-table__content--bold').get_text(strip=True) if height_element else "Unknown"

        # Extract number jersey
        numjersey_element = soup.find('div', class_='national-career__row')
        numjersey = numjersey_element.find_next('div', class_='national-career__cell--red').get_text(strip=True) if numjersey_element else "Unknown"
        
        return {"jersey_name": heading, "full_name": full_name, "place_of_birth": place_of_birth, "position": position, "height": height, "jersey_number": numjersey}
    except Exception as e:
        logging.error(f"Error scraping profile {profile_url}: {e}")
        return {"jersey_name": "Unknown", "full_name": "Unknown", "place_of_birth": "Unknown", "position": "Unknown", "height": "Unknown", "jersey_number": "Unknown"}

async def scrape_page(url: str) -> List[Dict[str, str]]:  # Removed use_pagination parameter
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        current_url = url
        all_data = []

        try:
            await page.goto(current_url, wait_until="domcontentloaded")
            html = await page.content()
            logging.info(f"Scraped URL: {current_url}")
            data = extract_table_data(html, current_url)
            
            # Scrape additional profile data
            for player in data:
                if player["profile_url"] != "Unknown":
                    profile_data = await scrape_profile_data(page, player["profile_url"])
                    player.update(profile_data)
                else:
                    player.update({"jersey_name": "Unknown", "place_of_birth": "Unknown", "position": "Unknown"})
            
            all_data.extend(data)
        except Exception as e:
            logging.error(f"Error scraping {current_url}: {e}")

        await browser.close()
        return all_data

def save_to_csv(data: List[Dict[str, str]], club_name: str):
    os.makedirs("dataset", exist_ok=True)
    filename = f"{club_name.replace(' ', '_').lower()}_players_data.csv"
    filepath = os.path.join("dataset", filename)
    
    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "name", 
            "status", 
            "profile_url", 
            "image_url", 
            "jersey_name", 
            "jersey_number",
            "nation",
            "nation_code",
            "club", 
            "place_of_birth", 
            "full_name",
            "position",
            "height",
            "date_of_birth", 
            "appearances", 
            "goals", 
            "assists", 
            "own_goals", 
            "yellow_cards", 
            "second_yellow", 
            "red_cards", 
            "substituted_on", 
            "substituted_off", 
            "minutes_played"
            ])
        for player in data:
            writer.writerow([
                player["name"], 
                player["status"], 
                player["profile_url"], 
                player["image_url"], 
                player["jersey_name"],
                player["jersey_number"], 
                player["nation"],
                player["nation_code"],
                player["club"], 
                player["place_of_birth"], 
                player["full_name"],
                player["position"],
                player["height"],
                player["dateofbirth"], 
                player["appearances"], 
                player["goals"], 
                player["assists"], 
                player["own_goals"], 
                player["yellow_cards"], 
                player["second_yellow"], 
                player["red_cards"], 
                player["sub_on"], 
                player["sub_off"], 
                player["minutes_played"]
                ])
    
    logging.info(f"Data saved to {filepath}")

async def scrape_multiple_urls(file_path: str):
    with open(file_path, "r") as file:
        urls = [line.strip() for line in file.readlines() if line.strip()]
    
    all_data = []
    for url in urls:
        logging.info(f"Scraping URL: {url}")
        data = await scrape_page(url)
        all_data.extend(data)
    
    if all_data:
        club_name = all_data[0]["club"] if all_data else "unknown_club"
        save_to_csv(all_data, club_name)

if __name__ == "__main__":
    urls_file = "urls.txt"
    asyncio.run(scrape_multiple_urls(urls_file))
