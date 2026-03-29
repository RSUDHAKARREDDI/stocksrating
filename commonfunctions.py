import pandas as pd
import glob
import os, shutil, time,csv
from sqlalchemy import create_engine, text,inspect
from sqlalchemy.dialects.mysql import insert
import uuid # For unique temp files
import logging
import pandas as pd
from config_db import HOST, PORT, USER, PASSWORD, DB
from datetime import datetime
import numpy as np


connection_url = (f"mysql+mysqldb://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")


def _build_dest_map(file_list_config: dict) -> dict:
    """Map filename -> target_directory from the provided config."""
    dest_map = {}
    for section, cfg in file_list_config.items():
        tdir = cfg.get('target_directory', '')
        for fname in cfg.get('file_list', []):
            dest_map[fname] = tdir
    return dest_map


def move_files(file_list, target_dir=None, file_list_config=None):
    """
    Move files to a directory.
    - If target_dir is provided, move all files there.
    - If target_dir is None, look up each file's destination from file_list_config
      by matching its basename to the config's file_list.
    Overwrite behavior: if a file with the same name exists at the destination,
    it will be replaced (atomically where possible).
    """
    # 🔒 Always resolve relative paths against this script's directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    def _abs(p):
        if not p:
            return p
        return p if os.path.isabs(p) else os.path.abspath(os.path.join(BASE_DIR, p))

    # Normalize target_dir (if provided)
    if target_dir is not None:
        target_dir = _abs(target_dir)

    # Prepare destination map
    if target_dir is None:
        if not file_list_config:
            raise ValueError("target_dir is None and file_list_config not provided.")
        dest_map = _build_dest_map(file_list_config)  # your existing helper
        # Normalize all mapped destination directories to absolute under BASE_DIR
        for k, v in list(dest_map.items()):
            dest_map[k] = _abs(v)

    results = {"moved": [], "not_found": [], "skipped_no_target": [], "errors": []}

    for file_path in file_list:
        # Normalize incoming file path (in case it is relative)
        src_path = file_path if os.path.isabs(file_path) else _abs(file_path)

        if not os.path.exists(src_path):
            print(f"File not found: {file_path}")
            results["not_found"].append(file_path)
            continue

        # Determine destination directory
        dest_dir = target_dir
        if dest_dir is None:
            key = os.path.basename(file_path)  # match on the original basename
            dest_dir = dest_map.get(key)

        if not dest_dir:
            print(f"No target mapping for {file_path}; skipped.")
            results["skipped_no_target"].append(file_path)
            continue

        try:
            os.makedirs(dest_dir, exist_ok=True)

            fname = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, fname)

            # If src and dest are same path, skip
            if os.path.abspath(src_path) == os.path.abspath(dest_path):
                print(f"Already in place: {src_path}")
                results["moved"].append((file_path, dest_dir))
                continue

            # --- Overwrite-safe move ---
            # Fast path: same filesystem -> atomic replace
            try:
                os.replace(src_path, dest_path)  # overwrites if exists
            except OSError:
                # Cross-device move: copy to a temp, then atomic replace
                tmp_path = f"{dest_path}.tmp__{int(time.time()*1000)}"
                shutil.copy2(src_path, tmp_path)
                os.replace(tmp_path, dest_path)
                # remove source only after successful replace
                try:
                    os.unlink(src_path)
                except FileNotFoundError:
                    pass

            print(f"Moved (overwrote if existed): {src_path} -> {dest_path}")
            results["moved"].append((file_path, dest_dir))

        except Exception as e:
            print(f"Error moving {src_path}: {e}")
            results["errors"].append((file_path, dest_dir, str(e)))

    return results


def load_files_to_mysql(
        file_paths: list,
        table_name: str,
        mode: str,
        connection_url: str = connection_url,
) -> dict:
    result = {
        "files_received": len(file_paths),
        "table": table_name,
        "processed_files": 0,
        "inserted_rows": 0,
        "skipped_files": [],
        "errors": [],
    }

    # 1. REMOVE the SET SESSION command.
    # Use allow_local_infile in connect_args instead.
    engine = create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=280,  # CRITICAL: PythonAnywhere kills connections after 300s
        connect_args={
            "local_infile": 1  # Standard for mysqlclient/mysqldb
        }
    )

    try:
        insp = inspect(engine)
        if not insp.has_table(table_name):
            raise RuntimeError(f'Table "{table_name}" does not exist.')

        existing_cols = [c["name"] for c in insp.get_columns(table_name)]
        has_market_cap_col = "Market Cap" in existing_cols
        has_screener_col = "screener" in existing_cols

        with engine.connect().execution_options(isolation_level="READ COMMITTED") as conn:
            conn.execute(text("SET autocommit=1"))

            if mode == "replace":
                conn.execute(text(f"TRUNCATE TABLE `{table_name}`"))

            for path in file_paths:
                filename = os.path.basename(path)
                if not os.path.exists(path):
                    result["errors"].append(f"Missing: {filename}")
                    continue

                try:
                    df = pd.read_csv(path, encoding="utf-8")

                    # Metadata processing
                    if has_screener_col:
                        df["screener"] = os.path.splitext(filename)[0]

                    if has_market_cap_col and ("Market Capitalization" in df.columns):
                        cap_raw = pd.to_numeric(
                            df["Market Capitalization"].astype(str).str.replace(",", ""),
                            errors="coerce"
                        )
                        df["Market Cap"] = cap_raw.apply(
                            lambda x: "MICRO CAP" if x < 1000 else
                            "SMALL CAP" if x < 5000 else
                            "MID CAP" if x < 20000 else "LARGE CAP" if pd.notna(x) else None
                        )

                    cols_to_use = [c for c in existing_cols if c in df.columns]

                    df = df[cols_to_use]

                    # 2. Fix the "Half-Records" issue (4308 -> 2154)
                    # We force Unix line endings (\n) to avoid CRLF confusion
                    temp_csv_path = f"/tmp/bulk_upload_{uuid.uuid4().hex}_{filename}"
                    df.to_csv(
                        temp_csv_path,
                        index=False,
                        header=False,
                        na_rep='\\N',
                        sep=',',
                        quoting=csv.QUOTE_MINIMAL,  # Minimal quoting is more stable
                        escapechar='\\',  # Add this to match MySQL ESCAPED BY
                        lineterminator='\n'  # Explicitly set \n
                    )

                    # 3. Execute LOAD DATA with matching line endings
                    columns_sql = ", ".join([f"`{c}`" for c in cols_to_use])
                    load_query = text(f"""
                                        LOAD DATA LOCAL INFILE '{temp_csv_path}'
                                        INTO TABLE `{table_name}`
                                        FIELDS TERMINATED BY ','
                                        OPTIONALLY ENCLOSED BY '"'
                                        ESCAPED BY '\\\\'
                                        LINES TERMINATED BY '\\n'
                                        ({columns_sql})
                                    """)

                    conn.execute(load_query)

                    if os.path.exists(temp_csv_path):
                        os.remove(temp_csv_path)

                    result["processed_files"] += 1
                    result["inserted_rows"] += len(df)

                except Exception as e:
                    logging.error(f"Failed {filename}: {str(e)}")
                    result["errors"].append(f"{filename}: {str(e)}")
                    result["skipped_files"].append(filename)

        return result
    finally:
        engine.dispose()


def merge_csv_files(directory="datafiles/temp", output_name="merged_output.csv"):
    # Create the search pattern for all csv files in the dir
    search_path = os.path.join(directory, "*.csv")
    files = glob.glob(search_path)

    # Exclude the output file if it already exists to avoid infinite loops
    files = [f for f in files if os.path.basename(f) != output_name]

    if not files:
        print("No CSV files found to merge.")
        return

    print(f"Merging {len(files)} files...")

    # List comprehension to read all CSVs into a list of DataFrames
    df_list = [pd.read_csv(f) for f in files]

    # Concatenate all DataFrames in the list
    merged_df = pd.concat(df_list, ignore_index=True)

    # Save the merged DataFrame back to the same directory
    output_path = os.path.join(directory, output_name)
    merged_df.to_csv(output_path, index=False)

    print(f"Success! Merged file saved at: {output_path}")


def load_files_to_mysql_upsert(
        file_paths,
        table_name: str,
        mode: str = "upsert",  # Changed default to upsert
        connection_url: str = connection_url,
) -> dict:
    result = {
        "files_received": 0,
        "table": table_name,
        "processed_files": 0,
        "inserted_rows": 0,
        "skipped_files": [],
        "errors": []
    }

    if isinstance(file_paths, str):
        file_paths = [file_paths]

    result["files_received"] = len(file_paths)

    engine = create_engine(connection_url, pool_pre_ping=True, pool_recycle=280)

    try:
        insp = inspect(engine)
        if not insp.has_table(table_name):
            raise RuntimeError(f'Table "{table_name}" does not exist.')

        existing_cols = [c["name"] for c in insp.get_columns(table_name)]

        for path in file_paths:
            filename = os.path.basename(path)
            try:
                df = pd.read_csv(path, encoding="utf-8")
                df.columns = [c.replace('.', '_') for c in df.columns]

                cols_to_use = [c for c in existing_cols if c in df.columns]
                df_to_load = df[cols_to_use].astype(object).replace({np.nan: None})  # Handle NaNs for SQL

                # --- UPSERT LOGIC START ---
                with engine.begin() as conn:
                    # 1. Reflect the table structure
                    from sqlalchemy import MetaData, Table
                    meta = MetaData()
                    table = Table(table_name, meta, autoload_with=engine)

                    # 2. Convert DataFrame to list of dictionaries
                    records = df_to_load.to_dict(orient='records')

                    # 3. Build the Upsert Statement
                    stmt = insert(table).values(records)

                    # Define which columns to update if the key (name, Trend, date) exists
                    # We update everything EXCEPT the primary key columns
                    update_cols = {
                        c.name: c for c in stmt.inserted
                        if c.name not in ['name', 'Trend', 'date']
                    }

                    upsert_stmt = stmt.on_duplicate_key_update(**update_cols)

                    # 4. Execute
                    conn.execute(upsert_stmt)
                # --- UPSERT LOGIC END ---

                result["processed_files"] += 1
                result["inserted_rows"] += len(df_to_load)
                print(f"✅ Upserted {len(df_to_load)} rows from {filename}")

            except Exception as e:
                logging.error(f"Failed {filename}: {str(e)}")
                result["errors"].append(f"{filename}: {str(e)}")
                result["skipped_files"].append(filename)

        return result
    finally:
        engine.dispose()


# Run the function
if __name__ == "__main__":
    merge_csv_files()