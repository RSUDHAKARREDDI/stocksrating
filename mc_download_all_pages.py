import os
import json
import time
import random
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")
WEB_PAGES_DIR = os.path.join(BASE_DIR, "datafiles","webpages")


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

def load_cookies_from_file(driver, filepath='cookies.txt'):
    """Correctly parses and injects Netscape cookies into the driver."""
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found! Technicals will likely fail.")
        return False

    # You must visit the domain first to set the cookie scope
    driver.get("https://www.moneycontrol.com")
    time.sleep(3)

    cookies_loaded = 0
    with open(filepath, 'r') as file:
        for line in file:
            if not line.strip().startswith('#') and '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) == 7 and "moneycontrol.com" in parts[0]:
                    cookie = {
                        'domain': '.moneycontrol.com',  # Standardize domain
                        'name': parts[5],
                        'value': parts[6],
                        'path': parts[2],
                        'secure': parts[3].lower() == 'true'
                    }
                    try:
                        driver.add_cookie(cookie)
                        cookies_loaded += 1
                    except Exception as e:
                        continue
    print(f"✅ Loaded {cookies_loaded} cookies. Session active.")
    return True


def download_authenticated_data():

    os.makedirs(WEB_PAGES_DIR, exist_ok=True)

    try:
        with open(f"{UPLOAD_DIR}/urls_to_download.json", "r") as f:
            urls_to_download = json.load(f)
    except Exception as e:
        print(f"❌ Could not load JSON: {e}")
        return

    # Use undetected_chromedriver to bypass Akamai
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Uncomment once you verify it works
    driver = uc.Chrome(options=options)

    try:
        # 1. Handle Authentication First
        if not load_cookies_from_file(driver):
            return

        # 2. Loop through stocks using the SAME driver session
        for name, urls in urls_to_download.items():
            for cat in ['technicals', 'essentials']:
                url = urls.get(cat)
                if not url: continue

                suffix = "daily_technicals" if cat == 'technicals' else "essentials"
                filename = os.path.join(WEB_PAGES_DIR, f"{name}_{suffix}.html")

                if os.path.exists(filename):
                    print(f"⏭️ {name} {cat} exists.")
                    continue

                print(f"🔍 Downloading {name} {cat}...")
                driver.get(url)

                # Human-like wait to allow scripts to execute
                time.sleep(random.uniform(5, 8))

                # Check if we got redirected or blocked
                if "Access Denied" in driver.page_source or "Login" in driver.title:
                    print(f"❌ Session lost or blocked at {name}. Stopping.")
                    return

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

                print(f"💾 Saved {name} {cat}")
                time.sleep(random.uniform(2, 4))  # Gap between requests

    finally:
        driver.quit()


if __name__ == "__main__":
    download_authenticated_data()