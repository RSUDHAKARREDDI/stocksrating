import os
import shutil
import os
from sqlalchemy import create_engine, text
import logging
import pandas as pd
from db_config import DB_CONFIG


connection_url = (f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"f"{DB_CONFIG['host']}:3306/{DB_CONFIG['database']}")


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
    """
    if target_dir is None:
        if not file_list_config:
            raise ValueError("target_dir is None and file_list_config not provided.")
        dest_map = _build_dest_map(file_list_config)

    results = {"moved": [], "not_found": [], "skipped_no_target": [], "errors": []}

    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            results["not_found"].append(file_path)
            continue

        # Determine destination directory
        dest_dir = target_dir
        if dest_dir is None:
            key = os.path.basename(file_path)
            dest_dir = dest_map.get(key)

        if not dest_dir:
            print(f"No target mapping for {file_path}; skipped.")
            results["skipped_no_target"].append(file_path)
            continue

        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(file_path, dest_dir)
            print(f"Moved: {file_path} -> {dest_dir}")
            results["moved"].append((file_path, dest_dir))
        except Exception as e:
            print(f"Error moving {file_path}: {e}")
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
    Returns a result dict with counts and errors; raises if nothing inserted.
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

                # Add source column, normalize NaNs→NULL
                df["screener"] = os.path.splitext(filename)[0]
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

