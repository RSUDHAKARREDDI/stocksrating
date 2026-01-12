import os
import pandas as pd

# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(DATAFILES_DIR, "uploads")

# File paths
latest_results_path = os.path.join(UPLOAD_DIR, "latest-results.csv")
qualified_companies_file = os.path.join(UPLOAD_DIR, "qualified_companies_list.csv")
urls_file = os.path.join(UPLOAD_DIR, "extracted_stock_links.csv")
filtered_urls_file = os.path.join(UPLOAD_DIR, "matched_url_company_list.csv")
unmatched_names_file = os.path.join(UPLOAD_DIR, "unmatched_url_company_list.csv")


# --- Helper Functions ---

def normalize(name):
    return ' '.join(str(name).strip().upper().split())


def progressive_match(name, stock_names_set, min_length=3):
    name = normalize(name)
    for i in range(len(name), min_length - 1, -1):
        partial_name = name[:i]
        if partial_name in stock_names_set:
            return partial_name
    return None


# --- Scoring Logic ---

def score_public_holding(row):
    try:
        val = row["Public holding"]
        if val < 10:
            return 20
        elif 10 <= val < 15:
            return 10
        elif 15 <= val < 25:
            return 5
        return 0
    except:
        return 0


def score_eps(row):
    try:
        if row["EPS latest quarter"] > row["EPS preceding quarter"] and \
                row["EPS latest quarter"] > row["EPS preceding year quarter"]:
            return 20
    except:
        pass
    return 0


def score_roe_roce(row):
    try:
        roe, roce = row["Return on equity"], row["Return on capital employed"]
        if roe > 20 and roce > 20:
            return 20
        elif roe > 15 and roce > 15:
            return 10
        return 5
    except:
        return 0


def score_opm(row):
    try:
        opm = row["OPM latest quarter"]
        if opm > 20:
            return 20
        elif opm > 10:
            return 10
        return 5
    except:
        return 0


def score_pe(row):
    try:
        if row["Price to Earning"] < row["Industry PE"]: return 10
    except:
        pass
    return 0


def classify_market_cap(row):
    try:
        cap = row["Market Capitalization"]
        if cap < 1000:
            return "MICRO CAP"
        elif cap < 5000:
            return "SMALL CAP"
        elif cap < 20000:
            return "MID CAP"
        return "LARGE CAP"
    except:
        return "UNKNOWN"


def filter_scores_with_whitelist(score_file_path):
    """Combines Score Logic with Whitelist Exception"""
    try:
        current_dir = os.path.dirname(score_file_path)
        screener_files = [
            "eps_pe_mscaps.csv", "good_pe_less_roe_roce.csv",
            "good_pe_roe_roce_all_good.csv", "good_pe_roe_roce_altimate.csv",
            "good_pe_roe_roce_lcap.csv", "good_roe_roce_more_pe.csv",
            "less_public_holding.csv", "power_bi_query.csv"
        ]

        whitelisted_names = set()
        for file_name in screener_files:
            file_path = os.path.join(current_dir, file_name)
            if os.path.exists(file_path):
                temp_df = pd.read_csv(file_path)
                if 'Name' in temp_df.columns:
                    names = temp_df['Name'].str.strip().str.upper().unique()
                    whitelisted_names.update(names)

        df_score = pd.read_csv(score_file_path)
        df_score['Name_Clean'] = df_score['Name'].str.strip().str.upper()

        # APPLY LOGIC: (MCap > 1000 AND Score >= 50) OR (Found in Screener Files)
        cond_std = (df_score['Market Capitalization'] > 1000) & (df_score['Total Score'] >= 50)
        cond_white = df_score['Name_Clean'].isin(whitelisted_names)

        df_filtered = df_score[cond_std | cond_white].copy()
        df_filtered['normalized_name'] = df_filtered['Name'].apply(normalize)

        return df_filtered.drop(columns=['Name_Clean'])
    except Exception as e:
        print(f"❌ Filtering Error: {e}")
        return pd.DataFrame()


# --- MAIN EXECUTION FLOW ---

# 1. Load and Score
df = pd.read_csv(latest_results_path)
df.columns = df.columns.str.strip()

score_cols = ["Public Holding Score", "EPS Score", "ROE_ROCE Score", "OPM Score", "PE Score"]
df["Public Holding Score"] = df.apply(score_public_holding, axis=1)
df["EPS Score"] = df.apply(score_eps, axis=1)
df["ROE_ROCE Score"] = df.apply(score_roe_roce, axis=1)
df["OPM Score"] = df.apply(score_opm, axis=1)
df["PE Score"] = df.apply(score_pe, axis=1)

df[score_cols] = df[score_cols].fillna(0)
df["Total Score"] = df[score_cols].sum(axis=1)
df["Market Cap Category"] = df.apply(classify_market_cap, axis=1)

df.sort_values(by="Total Score", ascending=False).to_csv(qualified_companies_file, index=False)
print(f"✅ Scoring Complete: {qualified_companies_file}")

# 2. Filter using the smart function (This handles the whitelist logic)
df_filtered = filter_scores_with_whitelist(qualified_companies_file)

# 3. URL Matching logic
try:
    df_urls = pd.read_csv(urls_file)
    df_urls['normalized_stock_name'] = df_urls['Stock Name'].apply(normalize)
    df_urls_unique = df_urls.groupby('normalized_stock_name').first()
    stock_name_map = df_urls_unique.to_dict('index')
    stock_name_set = set(stock_name_map.keys())

    matched_rows = []
    unmatched = []

    for _, row in df_filtered.iterrows():
        matched_key = progressive_match(row['Name'], stock_name_set)
        if matched_key:
            matched_rows.append({
                'Name': df_urls_unique.loc[matched_key, 'Stock Name'],
                'BSE Code': row['BSE Code'],
                'NSE Code': row['NSE Code'],
                'Total Score': row['Total Score'],
                'url': stock_name_map[matched_key]['URL']
            })
        else:
            unmatched.append({
                'Unmatched Name': row['Name'],
                'BSE Code': row['BSE Code'],
                'Total Score': row['Total Score']
            })

    # Save results
    pd.DataFrame(matched_rows).to_csv(filtered_urls_file, index=False)
    if unmatched:
        pd.DataFrame(unmatched).to_csv(unmatched_names_file, index=False)

    print(f"✅ Matched URLs: {len(matched_rows)} | Unmatched: {len(unmatched)}")

except Exception as e:
    print(f"⚠️ URL Matching Error: {e}")