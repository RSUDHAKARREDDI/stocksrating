import os
import pandas as pd
from bs4 import BeautifulSoup
import re
import json
from datetime import date

# === File paths ===
folder = "datafiles/webpages"
score_refactor_file = 'datafiles/uploads/matched_url_company_list.csv'
output_file = "datafiles/uploads/mc_technicals.csv"
mc_technical_file="datafiles/uploads/mc_technicals.csv"

# === Load JSON mapping ===
with open("datafiles/uploads/urls_to_download.json", "r") as f:
    urls_to_download = json.load(f)

# === Extraction functions ===

def extract_mc_essentials(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        score_tag = soup.find("div", class_=lambda x: x and "esbx" in x)
        if score_tag:
            text = score_tag.get_text(strip=True)
            integer_part = ''.join(filter(str.isdigit, text.split('%')[0]))
            return int(integer_part)
    except Exception as e:
        return f"❌ Error: {e}"
    return "❌ Not Found"

def extract_mc_technicals(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")
        tech_div = soup.find("div", id="techAnalysisD")
        if tech_div:
            raw_html = str(tech_div)
            match = re.search(r'</svg>\s*([^<]+)(?:</div>|</a>)', raw_html)
            if match:
                return match.group(1).strip()
    except Exception as e:
        return f"❌ Error: {e}"
    return "❌ Not Found"

# === Load latest stock data ===
latest_df = pd.read_csv(score_refactor_file)
mc_technical_df=pd.read_csv(mc_technical_file)

# Prepare 'code' column by preferring NSE Code, falling back to BSE Code
latest_df['code'] = latest_df.apply(lambda row: str(row['NSE Code']) if pd.notna(row['NSE Code']) else str(int(row['BSE Code'])),axis=1)
mc_technical_df['code']= mc_technical_df.apply(lambda row: str(row['NSE Code']) if pd.notna(row['NSE Code']) else str(int(row['BSE Code'])),axis=1)
# === Loop and collect mc essentials and technicals ===
final_data_rows = []  # Collect rows with full final output

# Get set of already existing codes in mc_technical_df
existing_codes = set(mc_technical_df['code'].astype(str))

for symbol in urls_to_download.keys():
    symbol_str = str(symbol)

    # Skip if already exists
    if symbol_str in existing_codes:
        print(f"⏩ Skipping existing symbol: {symbol_str}")
        continue

    essential_file_path = os.path.join(folder, f"{symbol}_essentials.html")
    technical_file_path = os.path.join(folder, f"{symbol}_daily_technicals.html")

    mc_essential = extract_mc_essentials(essential_file_path)
    mc_technical = extract_mc_technicals(technical_file_path)

    print(f'🔍 code: {symbol}, mc essentials: {mc_essential}, mc technicals: {mc_technical}')

    # Match with score_refactor.csv
    match_row = latest_df[latest_df['code'] == symbol_str]

    if not match_row.empty:
        row = match_row.iloc[0].copy()
        row["mc essentials"] = mc_essential
        row["mc technicals"] = mc_technical

        final_data_rows.append({
            "Name": row["Name"],
            "BSE Code": int(row["BSE Code"]) if pd.notna(row["BSE Code"]) else "",
            "NSE Code": row["NSE Code"],
            "mc essentials": row["mc essentials"],
            "mc technicals": row["mc technicals"],
            "updated_date": date.today().strftime("%Y-%m-%d")  # only date
        })

        print(f"✅ Match found: {row['Name']} (code: {symbol})")
    else:
        print(f"❌ No match found for code: {symbol}")

# === Append only if there are new rows ===
if final_data_rows:
    new_df = pd.DataFrame(final_data_rows)

    # Load existing CSV
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    # Save to same output file
    combined_df.to_csv(output_file, index=False)
    print(f"\n✅ Appended new entries to: {output_file}")
else:
    print("\n📭 No new unmatched symbols found to append.")