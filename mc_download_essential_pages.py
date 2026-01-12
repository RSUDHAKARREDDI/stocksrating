import os
import json
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException


def safe_get(driver, url, retries=3, base_delay=3):
    for attempt in range(retries):
        try:
            driver.get(url)
            return True
        except (TimeoutException, WebDriverException) as e:
            print(f"⚠️ Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 2))
    print(f"❌ Failed to load URL after {retries} attempts: {url}")
    return False


def load_cookies_from_file(filepath):
    cookies = []
    with open(filepath, 'r') as file:
        for line in file:
            if not line.strip().startswith('#') and '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) == 7 and "moneycontrol.com" in parts[0]:
                    cookies.append({
                        'domain': parts[0],
                        'httpOnly': False,
                        'name': parts[5],
                        'path': parts[2],
                        'secure': False,
                        'value': parts[6]
                    })
    return cookies


def extract_mc_essential(driver, url, stock_name='UNKNOWN', cookies_path='cookies.txt'):
    if not safe_get(driver, "https://www.moneycontrol.com"):
        return

    cookies = load_cookies_from_file(cookies_path)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"⚠️ Skipping cookie {cookie.get('name')} — {e}")

    if not safe_get(driver, url):
        return

    time.sleep(1)
    filename = f"datafiles/webpages/{stock_name}_essentials.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"💾 Saved essential HTML to {filename}")


def download_pages(essential_url,  stock_name, folder="datafiles/webpages/"):
    os.makedirs(folder, exist_ok=True)

    essential_file = os.path.join(folder, f"{stock_name}_essentials.html")


    if os.path.exists(essential_file):
        print(f"⏭️ Skipping {stock_name} — already downloaded today.")
        return

    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)

    try:
        if not safe_get(driver, "https://www.moneycontrol.com"):
            return

        print(f"🌐 Downloading Essentials for {stock_name}")

        extract_mc_essential(driver, essential_url, stock_name=stock_name)

    finally:
        driver.quit()


# === MAIN LOOP WITH AUTO-RESTART ===
while True:
    try:
        with open("datafiles/uploads/urls_to_download.json", "r") as f:
            urls_to_download = json.load(f)

        for name, urls in urls_to_download.items():
            essential_url = urls.get('essentials')

            print(f"🔍 Checking: {name} at {datetime.now().strftime('%H:%M:%S')}")
            download_pages(essential_url, name)

        print("✅ All downloads completed successfully.")
        break  # Exit the loop if everything went fine

    except Exception as e:
        print(f"\n💥 Script failed due to error: {e}")
        print("🔁 Restarting in 15 seconds...\n")
        time.sleep(15)
