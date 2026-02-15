import pandas as pd
import glob
import os, shutil, time
from sqlalchemy import create_engine, text,inspect
import logging
import pandas as pd
from config_db import HOST, PORT, USER, PASSWORD, DB


connection_url = (f"mysql+mysqlconnector://{USER}:{PASSWORD}@"f"{HOST}:{PORT}/{DB}")


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
        connection_url=connection_url,
) -> dict:
    """
    Load a SPECIFIC list of CSV files into a MySQL table.
    Fully compatible with Pandas 2.3.x and SQLAlchemy 2.0.
    """
    result = {
        "files_received": len(file_paths),
        "table": table_name,
        "processed_files": 0,
        "inserted_rows": 0,
        "skipped_files": [],
        "errors": [],
    }

    if not file_paths:
        raise ValueError("The list of file paths is empty.")

    engine = create_engine(connection_url, pool_pre_ping=True)

    try:
        # Use inspect to check table and columns before opening a connection block
        insp = inspect(engine)
        if not insp.has_table(table_name):
            raise RuntimeError(f'Table "{table_name}" does not exist. Create it first.')

        existing_cols = {c["name"] for c in insp.get_columns(table_name)}
        has_market_cap_col = "Market Cap" in existing_cols
        has_screener_col = "screener" in existing_cols

        # Open a single connection for the entire operation
        with engine.connect() as conn:
            # 1. Handle "replace" mode using text() for SQLAlchemy 2.0 compatibility
            if mode == "replace":
                conn.execute(text(f"DELETE FROM {table_name}"))
                conn.commit()  # Explicitly commit the deletion
                logging.info(f"Table {table_name} cleared (mode='replace').")
            else:
                logging.info(f"Table {table_name} kept; appending new data.")

            for path in file_paths:
                filename = os.path.basename(path)

                if not os.path.exists(path):
                    msg = f"File not found: {path}"
                    logging.error(msg)
                    result["errors"].append(msg)
                    result["skipped_files"].append(filename)
                    continue

                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except Exception as e:
                    msg = f"Read failed: {filename}: {e}"
                    logging.error(msg)
                    result["errors"].append(msg)
                    result["skipped_files"].append(filename)
                    continue

                # --- Data Processing Logic ---
                if has_screener_col:
                    df["screener"] = os.path.splitext(filename)[0]

                if has_market_cap_col and ("Market Capitalization" in df.columns):
                    cap_raw = df["Market Capitalization"].astype(str).str.replace(",", "", regex=False).str.strip()
                    cap_num = pd.to_numeric(cap_raw, errors="coerce")

                    def _cap_bucket(x):
                        if pd.isna(x): return None
                        if x < 1000:
                            return "MICRO CAP"
                        elif x < 5000:
                            return "SMALL CAP"
                        elif x < 20000:
                            return "MID CAP"
                        else:
                            return "LARGE CAP"

                    df["Market Cap"] = [_cap_bucket(v) for v in cap_num]

                # Align columns and handle NaNs for MySQL NULL compatibility
                cols_to_use = [c for c in df.columns if c in existing_cols]
                df = df[cols_to_use].copy()
                df = df.where(pd.notnull(df), None)

                # --- Database Insertion ---
                try:
                    # Pass the active connection 'conn' instead of 'engine'
                    df.to_sql(
                        name=table_name,
                        con=conn,
                        if_exists="append",
                        index=False,
                        chunksize=1000,
                        method="multi",
                    )
                    # Commit after each file to ensure data is saved
                    conn.commit()

                    result["processed_files"] += 1
                    result["inserted_rows"] += len(df)
                except Exception as e:
                    conn.rollback()  # Rollback if this specific file fails
                    msg = f"Insert failed: {filename}: {str(e)}"
                    logging.error(msg)
                    result["errors"].append(msg)
                    result["skipped_files"].append(filename)

        if result["inserted_rows"] == 0 and result["processed_files"] > 0:
            raise RuntimeError("Files were processed but no rows were inserted.")

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


# Run the function
if __name__ == "__main__":
    merge_csv_files()