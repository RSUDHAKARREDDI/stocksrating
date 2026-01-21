import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

# -------- Paths & Configuration --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure the datafiles directory exists
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
os.makedirs(DATAFILES_DIR, exist_ok=True)

# SQLAlchemy Engine (Shared by both functions)
encoded_pass = quote_plus(PASSWORD)
DATABASE_URL = f"mysql+mysqlconnector://{USER}:{encoded_pass}@{HOST}:{PORT}/{DB}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def export_table_to_csv(table_name):
    """
    Exports a MySQL table to a CSV file named 'table_name.csv'.
    """
    try:
        output_file = os.path.join(DATAFILES_DIR, f"{table_name}.csv")

        # Using pandas for a cleaner one-liner export
        df = pd.read_sql_table(table_name, con=engine)
        df.to_csv(output_file, index=False, encoding="utf-8")

        print(f"✅ Export Successful: {table_name} -> {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Export Error for {table_name}: {e}")


def import_csv_to_table(table_name, if_exists='append'):
    """
    Imports a CSV file named 'table_name.csv' into the MySQL table.
    if_exists options: 'fail', 'replace', 'append'
    """
    try:
        input_file = os.path.join(DATAFILES_DIR, f"{table_name}.csv")

        if not os.path.exists(input_file):
            print(f"⚠️ File not found: {input_file}")
            return

        df = pd.read_csv(input_file)
        df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)

        print(f"✅ Import Successful: {input_file} -> MySQL table '{table_name}'")
    except Exception as e:
        print(f"❌ Import Error for {table_name}: {e}")


# -------- Examples of Usage --------
if __name__ == "__main__":
    # Example 1: Export 'basket' table
    #export_table_to_csv("basket")
    #export_table_to_csv("my_holdings")

    # Example 2: Import 'basket.csv' back into the database
    import_csv_to_table("basket", if_exists="append")
    import_csv_to_table("my_holdings", if_exists="append")