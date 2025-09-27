import os
import csv
import mysql.connector
from db_config import DB_CONFIG

# Folder where app.py saves uploaded files
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_files")

def create_table_if_not_exists():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mstock_margin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        code VARCHAR(100) UNIQUE,
        margin DECIMAL(10,2),
        source_file VARCHAR(255)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    cursor.close()
    conn.close()

def load_csv(filepath):
    """Load one CSV file into mstock_margin table"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    filename = os.path.basename(filepath)

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            name = row.get("NAME") or row.get("Name") or row.get("name")
            code = row.get("CODE") or row.get("Code") or row.get("code")
            margin = row.get("MARGIN") or row.get("Margin") or row.get("margin")
            try:
                margin_val = float(margin) if margin else None
            except:
                margin_val = None
            if not code:
                continue
            rows.append((name, code, margin_val, filename))

    if rows:
        sql = """
        INSERT INTO mstock_margin (name, code, margin, source_file)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            margin = VALUES(margin),
            source_file = VALUES(source_file)
        """
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(rows)} rows from {filename} into MySQL")

def load_all_csvs():
    """Scan data_files folder and load all CSVs into MySQL"""
    create_table_if_not_exists()
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    for fname in files:
        filepath = os.path.join(DATA_FOLDER, fname)
        load_csv(filepath)

if __name__ == "__main__":
    load_all_csvs()
