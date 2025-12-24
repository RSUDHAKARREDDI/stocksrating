import os
import pandas as pd
import numpy as np

# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")

bhav_copy_file = os.path.join(BASE_DIR, "datafiles","uploads","bhav_copy.csv")
wk_high_low=os.path.join(BASE_DIR, "datafiles","uploads","52_wk_High_low.csv")


def process_and_overwrite_bhavcopy(file_path):
    """
    Reads the file, cleans headers, filters specific series,
    and overwrites the original file.
    """
    # 1. Read the file
    df = pd.read_csv(file_path, skipinitialspace=True)

    # 2. Clean Headers (Removes leading spaces like ' SERIES')
    df.columns = [col.strip() for col in df.columns]

    # 3. Clean String Data
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # 4. Apply Series Filter (Exclude E1, GB, GS, IV)
    exclude_series = ['E1', 'GB', 'GS', 'IV']
    if 'SERIES' in df.columns:
        # Keep records NOT IN the exclude list
        df = df[~df['SERIES'].isin(exclude_series)].copy()

    # 5. Handle Numeric Conversions for MySQL compatibility
    cols_to_fix = ['DELIV_QTY', 'DELIV_PER']
    for col in cols_to_fix:
        if col in df.columns:
            # Replace hyphens with NaN then fill with 0
            df[col] = pd.to_numeric(df[col].replace('-', np.nan), errors='coerce').fillna(0)

    # 6. Overwrite the file
    df.to_csv(file_path, index=False)

    # 7. Return the DataFrame for inspection (Prevents AttributeError)
    return df


def clean_and_filter_52wk(file_path):
    # 1. Skip ONLY the first 2 lines (Disclaimer & Effective Date)
    # This keeps the 3rd line ("SYMBOL","SERIES",...) as the header
    df = pd.read_csv(file_path, skiprows=2, skipinitialspace=True)

    # 2. Clean headers (Remove double quotes and spaces)
    df.columns = [col.replace('"', '').strip() for col in df.columns]

    # 3. Clean all string data in the dataframe
    df = df.apply(lambda x: x.str.replace('"', '').str.strip() if x.dtype == "object" else x)

    # 4. Filter out records where ANY of the 52-week columns contain '-'
    # We define exactly what we are looking for in the cleaned columns
    date_cols = ['52_Week_High_Date', '52_Week_Low_DT']
    price_cols = ['Adjusted_52_Week_High', 'Adjusted_52_Week_Low']
    all_target_cols = date_cols + price_cols

    # Remove rows with hyphens
    for col in all_target_cols:
        if col in df.columns:
            df = df[df[col] != '-']
        else:
            # Troubleshooting: Print columns if one is missing to avoid KeyError
            print(f"Warning: Column {col} not found in {df.columns.tolist()}")

    # 5. Convert Dates to MySQL format (YYYY-MM-DD)
    # Handles '12-FEB-2025' -> '2025-02-12'
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

    # 6. Now drop rows where date conversion failed (if any)
    # This won't throw a KeyError now because we checked columns in step 4
    df = df.dropna(subset=[c for c in date_cols if c in df.columns])

    # 7. Overwrite the file for loading
    df.to_csv(file_path, index=False)
    print(f"✅ Success: {file_path} cleaned and saved.")
    return df

# --- Execution ---
process_and_overwrite_bhavcopy(bhav_copy_file)

clean_and_filter_52wk(wk_high_low)



