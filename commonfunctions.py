import os
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



def load_csvs_to_mysql(
    directory: str,
    table_name: str,
    connection_url=connection_url,
) -> dict:
    """
    Load ALL CSV files from a directory into a MySQL table.
    Deletes existing rows, then appends rows from each CSV.
    - Derives "Market Cap" ONLY if the table already has a "Market Cap" column
      AND the CSV has "Market Capitalization".
    - Adds "screener" ONLY if the table already has a "screener" column.
    - DataFrame is trimmed to existing table columns before insert.
    """
    result = {
        "directory": directory,
        "table": table_name,
        "processed_files": 0,
        "inserted_rows": 0,
        "skipped_files": [],
        "errors": [],
    }

    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = [f for f in os.listdir(directory) if f.lower().endswith(".csv")]
    if not files:
        raise RuntimeError(f"No CSV files found in: {directory}")

    engine = create_engine(connection_url, pool_pre_ping=True)
    insp = inspect(engine)

    if not insp.has_table(table_name):
        raise RuntimeError(f'Table "{table_name}" does not exist. Create it first.')

    # Reflect existing columns from the target table
    existing_cols = {c["name"] for c in insp.get_columns(table_name)}
    has_market_cap_col = "Market Cap" in existing_cols
    has_screener_col   = "screener" in existing_cols

    try:
        with engine.begin() as conn:
            # Empty the table first
            conn.execute(text(f"DELETE FROM {table_name}"))

            for filename in files:
                path = os.path.join(directory, filename)
                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except Exception as e:
                    msg = f"Read failed: {filename}: {e}"
                    logging.error(msg)
                    result["errors"].append(msg)
                    result["skipped_files"].append(filename)
                    continue

                # Conditionally add screener only if column exists in table
                if has_screener_col:
                    df["screener"] = os.path.splitext(filename)[0]

                # Conditionally derive Market Cap ONLY if table has that column
                if has_market_cap_col and ("Market Capitalization" in df.columns):
                    cap_raw = (
                        df["Market Capitalization"]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.strip()
                    )
                    cap_num = pd.to_numeric(cap_raw, errors="coerce")

                    def _cap_bucket(x):
                        if pd.isna(x):
                            return None
                        if x < 1000:
                            return "MICRO CAP"
                        elif x < 5000:
                            return "SMALL CAP"
                        elif x < 20000:
                            return "MID CAP"
                        else:
                            return "LARGE CAP"

                    df["Market Cap"] = [ _cap_bucket(v) for v in cap_num ]
                # Else: do NOT create/append "Market Cap" column at all

                # Keep only columns that already exist in the table
                # (missing columns in df will default to NULL on insert)
                cols_to_use = [c for c in df.columns if c in existing_cols]
                df = df[cols_to_use]

                # Normalize NaNs→NULL for SQL
                df = df.where(pd.notnull(df), None)

                try:
                    df.to_sql(
                        name=table_name,
                        con=conn,
                        if_exists="append",
                        index=False,
                        chunksize=1000,
                        method="multi",
                    )
                    result["processed_files"] += 1
                    result["inserted_rows"] += len(df)
                except Exception as e:
                    msg = f"Insert failed: {filename}: {e}"
                    logging.error(msg)
                    result["errors"].append(msg)
                    result["skipped_files"].append(filename)

        if result["inserted_rows"] == 0:
            raise RuntimeError(
                "No rows inserted. (Files empty? Schema mismatch? Check logs for details.)"
            )

        return result

    finally:
        try:
            engine.dispose()
        except Exception:
            pass

