import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles", "uploads")

# Define paths
essentials_file = os.path.join(UPLOAD_DIR, "latest-results.csv")
technicals_file = os.path.join(UPLOAD_DIR, "mc_technicals.csv")
output_file = os.path.join(UPLOAD_DIR, "score_refactor.csv")

def process_and_score_stocks(essentials_path=essentials_file, technicals_path=technicals_file, output_path=output_file):
    """
    Processes stock data and applies scoring logic.
    Returns the final sorted DataFrame and saves it to output_path.
    """
    # 1. Load data
    essentials_df = pd.read_csv(essentials_path)
    technicals_df = pd.read_csv(technicals_path)

    # 2. Clean column names and data
    essentials_df.columns = essentials_df.columns.str.strip()
    technicals_df.columns = technicals_df.columns.str.strip()

    for df in [essentials_df, technicals_df]:
        for col in ["BSE Code", "NSE Code"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', ''], pd.NA)

    # 3. Select columns from technicals and Merge
    tech_cols = [c for c in ["BSE Code", "NSE Code", "mc essentials", "mc technicals"] if c in technicals_df.columns]
    technical_subset = technicals_df[tech_cols].copy()

    merged_df = pd.merge(
        essentials_df,
        technical_subset,
        how='left',
        on=["BSE Code", "NSE Code"]
    )

    # --- Internal Scoring Functions (to encapsulate logic) ---
    def score_public_holding(row):
        try:
            val = row["Public holding"]
            if val < 10: return 20
            if 10 <= val < 15: return 10
            if 15 <= val < 25: return 5
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
            if roe > 20 and roce > 20: return 20
            if roe > 15 and roce > 15: return 10
            return 5
        except:
            return 0

    def score_opm(row):
        try:
            opm = row["OPM latest quarter"]
            if opm > 20: return 20
            if opm > 10: return 10
            return 5
        except:
            return 0

    def score_pe(row):
        try:
            if row["Price to Earning"] < row["Industry PE"]: return 10
        except:
            pass
        return 0

    def score_mc(row):
        try:
            if pd.isna(row["mc essentials"]): return 0
            essentials = float(row["mc essentials"])
            technicals = str(row["mc technicals"]).strip().lower()
            if essentials > 80 and technicals in ["bullish", "very bullish"]: return 20
            if essentials > 70 and technicals in ["bullish", "very bullish"]: return 10
        except:
            pass
        return 0

    def classify_market_cap(row):
        try:
            cap = row["Market Capitalization"]
            if cap < 1000: return "MICRO CAP"
            if cap < 5000: return "SMALL CAP"
            if cap < 20000: return "MID CAP"
            return "LARGE CAP"
        except:
            return "UNKNOWN"

    # 4. Apply Logic
    merged_df["Public Holding Score"] = merged_df.apply(score_public_holding, axis=1)
    merged_df["EPS Score"] = merged_df.apply(score_eps, axis=1)
    merged_df["ROE_ROCE Score"] = merged_df.apply(score_roe_roce, axis=1)
    merged_df["OPM Score"] = merged_df.apply(score_opm, axis=1)
    merged_df["PE Score"] = merged_df.apply(score_pe, axis=1)
    merged_df["MC Score"] = merged_df.apply(score_mc, axis=1)

    merged_df["Total Score"] = (
            merged_df["Public Holding Score"] + merged_df["EPS Score"] +
            merged_df["ROE_ROCE Score"] + merged_df["OPM Score"] +
            merged_df["PE Score"] + merged_df["MC Score"]
    )

    merged_df["Market Cap Category"] = merged_df.apply(classify_market_cap, axis=1)

    # 5. Sort and Save
    df_sorted = merged_df.sort_values(by="Total Score", ascending=False)
    df_sorted.to_csv(output_path, index=False)

    return df_sorted


# --- Execution ---
if __name__ == "__main__":
    process_and_score_stocks(essentials_file, technicals_file, output_file)
    print(f"✅ Refactored scoring saved to: {output_file}")