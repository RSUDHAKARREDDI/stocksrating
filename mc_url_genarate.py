import pandas as pd
import json
from urllib.parse import urlparse
import os

def generate_urls_from_csv(csv_path, output_json_path):
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    urls_to_download = {}

    for _, row in df.iterrows():
        name = row["NSE Code"] if pd.notna(row["NSE Code"]) else str(int(row["BSE Code"]))
        essentials_url = row["url"]

        # Extract last 2 segments from the path
        parsed = urlparse(essentials_url)
        segments = parsed.path.strip("/").split("/")
        last_two = "/".join(segments[-2:])

        technicals_url = f"https://www.moneycontrol.com/technical-analysis/{last_two}/daily"

        urls_to_download[name] = {
            "essentials": essentials_url,
            "technicals": technicals_url
        }

    # ✅ Sort dictionary by name (key)
    sorted_urls = dict(sorted(urls_to_download.items()))

    with open(output_json_path, "w") as f:
        json.dump(sorted_urls, f, indent=4)

    print(f"✅ JSON saved to {output_json_path}")

# === USAGE ===
if __name__ == "__main__":
    input_csv = "datafiles/uploads/matched_url_company_list.csv"               # Change this if needed
    output_json = "datafiles/uploads/urls_to_download.json"
    generate_urls_from_csv(input_csv, output_json)
