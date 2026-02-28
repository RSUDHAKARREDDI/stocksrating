import os
import pandas as pd
import operator as op

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV  = os.path.join(BASE_DIR, "datafiles", "uploads", "latest-results.csv")
OUTPUT_PATH  = os.path.join(BASE_DIR, "datafiles", "uploads")

# ---- Config: column names used in filters ----
NUM_COLS = [
    "EPS latest quarter",
    "EPS preceding quarter",
    "EPS preceding year quarter",
    "Price to Earning",
    "Industry PE",
    "Market Capitalization",
    "Return over 1week",
	"Return over 1month",
    "Return over 3months",
	"Return over 6months",

    "Current Price",
    "PEG Ratio",
    "Debt to equity",
    "OPM latest quarter",
    "OPM preceding quarter",
    "Price to book value",
    "Promoter holding",
	"FII holding",
    "DII holding",
    "Public holding"
]

def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Make sure numeric-like columns become numbers (handles commas, blanks).
    Non-convertible values turn into NaN.
    """
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def eps_pe_mscaps() -> pd.DataFrame:
    """
    Filter rows where:
      EPS latest quarter > EPS preceding quarter
      EPS latest quarter > EPS preceding year quarter
      EPS preceding quarter > 0
      EPS latest quarter > 0
      Price to Earning < Industry PE
      Market Capitalization > 1000
      Return over 1month > 0
      Return over 3months > 5

      Promoter holding > 70
      Market Capitalization < 20000

    Writes filtered rows to OUTPUT_FILE and returns the filtered DataFrame.
    """
    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "eps_pe_mscaps.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions
    cond = (
        (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
        (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
        (df["EPS preceding quarter"] > 0) &
        (df["EPS latest quarter"] > 0) &
        (df["Price to Earning"] < df["Industry PE"]) &
        (df["Market Capitalization"] > 1000) &
        (df["Return over 1month"] > 0) &
        (df["Return over 3months"] > 5) &

        (df["Promoter holding"] > 70) &
        (df["Market Capitalization"] < 20000)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def good_roe_roce_more_pe() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "good_roe_roce_more_pe.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions
    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Price to Earning"] > df["Industry PE"]) &
            (df["Promoter holding"] > 50) &
            (df["EPS latest quarter"] > 2) &
            (df["Market Capitalization"] > 1000) &

            (df["Return on equity"] > 20) &
            (df["Return on capital employed"] > 20)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def good_pe_roe_roce_lcap() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "good_pe_roe_roce_lcap.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions
    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Price to Earning"] < df["Industry PE"]) &
            (df["Promoter holding"] > 50) &
            (df["Debt to equity"] < 1) &
            (df["EPS latest quarter"] > 0) &
            (df["Market Capitalization"] > 20000) &

            (df["Return on equity"] > 15) &
            (df["Return on capital employed"] > 15)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def good_pe_less_roe_roce() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "good_pe_less_roe_roce.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions
    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Promoter holding"] > 70) &
            (df["Price to Earning"] < df["Industry PE"]) &
            (df["EPS latest quarter"] > 2) &
            (df["Market Capitalization"] > 1000) &

            (df["Debt to equity"] < 1) &
            (df["OPM latest quarter"] > 10) &
            (df["Return on equity"] < 15) &
            (df["Return on capital employed"] < 15)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def good_pe_roe_roce_all_good() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "good_pe_roe_roce_all_good.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions
    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Promoter holding"] > 50) &
            (df["Price to Earning"] < df["Industry PE"]) &
            (df["EPS latest quarter"] > 0) &
            (df["Market Capitalization"] < 20000) &
            (df["Market Capitalization"] > 1000) &

            (df["Debt to equity"] < 1) &
            (df["Return on equity"] > 15) &
            (df["Return on capital employed"] > 15)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def good_pe_roe_roce_altimate() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "good_pe_roe_roce_altimate.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions

    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Promoter holding"] > 70) &
            (df["Price to Earning"] < df["Industry PE"]) &
            (df["EPS latest quarter"] > 0) &
            (df["Market Capitalization"] > 1000) &

            (df["Debt to equity"] < 1) &
            (df["Return on equity"] > 20) &
            (df["Return on capital employed"] > 20) &
            (df["Price to book value"] < 10)
    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def less_public_holding() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "less_public_holding.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions

    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Public holding"] < 10) &
            (df["Return on equity"] > 15) &
            (df["Return on capital employed"] > 15) &

            (df["Promoter holding"] > 50)

    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def power_bi_query() -> pd.DataFrame:

    OUTPUT_FILE = os.path.join(OUTPUT_PATH, "power_bi_query.csv")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df = _coerce_numeric(df, NUM_COLS)

    # Build boolean mask with your conditions

    cond = (
            (df["EPS latest quarter"] > df["EPS preceding quarter"]) &
            (df["EPS latest quarter"] > df["EPS preceding year quarter"]) &
            (df["Market Capitalization"] > 1000) &
            (df["Return on equity"] > 15) &
            (df["Return on capital employed"] > 15) &

            (df["Promoter holding"] > 50)

    )

    out = df.loc[cond].copy()

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ Saved {len(out)} rows to: {OUTPUT_FILE}")
    return out

def screeners_load():
    eps_pe_mscaps()
    good_roe_roce_more_pe()
    good_pe_roe_roce_lcap()
    good_pe_less_roe_roce()
    good_pe_roe_roce_all_good()
    good_pe_roe_roce_altimate()
    less_public_holding()
    power_bi_query()

def main():
    return None

if __name__ == "__main__":

    main()
    screeners_load()






