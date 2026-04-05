import os
import json
import time
import random
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# -------- Paths --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles", "uploads")
WEB_PAGES_DIR = os.path.join(BASE_DIR, "datafiles", "webpages")


def safe_get(driver, url, retries=3, base_delay=5):
    """Retries page loading with exponential backoff."""
    for attempt in range(retries):
        try:
            driver.get(url)
            # Check for common block indicators immediately after loading
            if "Access Denied" in driver.page_source:
                print(f"⚠️ Access Denied on attempt {attempt + 1} for {url}")
                time.sleep(base_delay * (attempt + 1))
                continue
            return True
        except (TimeoutException, WebDriverException) as e:
            print(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(base_delay * (2 ** attempt) + random.uniform(1, 3))

    print(f"❌ Failed to load URL after {retries} attempts: {url}")
    return False


def load_cookies_from_file(driver, filepath='cookies.txt'):
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return False

    driver.get("https://www.moneycontrol.com")
    time.sleep(3)

    cookies_loaded = 0
    with open(filepath, 'r') as file:
        for line in file:
            if not line.strip().startswith('#') and '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) == 7 and "moneycontrol.com" in parts[0]:
                    cookie = {
                        'domain': '.moneycontrol.com',
                        'name': parts[5],
                        'value': parts[6],
                        'path': parts[2],
                        'secure': parts[3].lower() == 'true'
                    }
                    try:
                        driver.add_cookie(cookie)
                        cookies_loaded += 1
                    except:
                        continue
    print(f"✅ Loaded {cookies_loaded} cookies.")
    return True


def download_authenticated_data():
    os.makedirs(WEB_PAGES_DIR, exist_ok=True)

    try:
        with open(os.path.join(UPLOAD_DIR, "urls_to_download.json"), "r") as f:
            urls_to_download = json.load(f)
    except Exception as e:
        print(f"❌ Could not load JSON: {e}")
        return

    options = uc.ChromeOptions()
    # options.add_argument('--headless')
    driver = uc.Chrome(options=options, version_main=146)

    try:
        if not load_cookies_from_file(driver):
            return

        for name, urls in urls_to_download.items():
            for cat in ['technicals', 'essentials']:
                try:
                    url = urls.get(cat)
                    if not url: continue

                    suffix = "daily_technicals" if cat == 'technicals' else "essentials"
                    filename = os.path.join(WEB_PAGES_DIR, f"{name}_{suffix}.html")

                    if os.path.exists(filename):
                        print(f"⏭️ {name} {cat} exists.")
                        continue

                    print(f"🔍 [ {datetime.now().strftime('%H:%M:%S')} ] Downloading {name} {cat}...")

                    # Use the robust safe_get here
                    if not safe_get(driver, url):
                        print(f"⏭️ Skipping {name} {cat} due to repeated load failures.")
                        continue

                    # Wait for dynamic content
                    time.sleep(random.uniform(4, 7))

                    # Final check for session loss
                    if "Login" in driver.title:
                        print(f"🔄 Session lost. Attempting to reload cookies...")
                        load_cookies_from_file(driver)
                        driver.get(url)  # Retry once after cookie refresh

                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)

                    print(f"💾 Saved {name} {cat}")
                    time.sleep(random.uniform(2, 5))  # Cooldown between requests

                except Exception as inner_e:
                    print(f"💥 Error processing {name} {cat}: {inner_e}")
                    continue  # Ensure we move to the next URL/Stock

    finally:
        print("🏁 Scraper finished or interrupted. Closing driver.")
        driver.quit()


if __name__ == "__main__":
    # Optional: Keep the whole script alive if the driver crashes entirely
    while True:
        try:
            download_authenticated_data()
            print("✅ Work cycle complete.")
            break
        except Exception as e:
            print(f"🔥 Critical Driver Failure: {e}")
            print("🔁 Restarting entire browser session in 20 seconds...")

            time.sleep(20)