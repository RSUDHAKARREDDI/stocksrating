from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB
import os
import files_data_cleanup as fclean
import commonfunctions as cf


# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")

in_FII_SECTOR_ACTIVITY = os.path.join(BASE_DIR, "datafiles","uploads","FII_SECTOR_ACTIVITY.csv")
out_FII_SECTOR_ACTIVITY=os.path.join(BASE_DIR, "datafiles","uploads","Proccessed_FII_SECTOR_ACTIVITY.csv")



fii_sector_activity_bp = Blueprint("fii_sector_activity_bp", __name__)

# Engine setup
engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)


@fii_sector_activity_bp.route("/fii-sector-activity")
def index_returns():
    # Your standard SQL query
    fclean.denormalize_sector_activity(in_FII_SECTOR_ACTIVITY, out_FII_SECTOR_ACTIVITY)
    cf.load_files_to_mysql_upsert(out_FII_SECTOR_ACTIVITY, "fii_sector_activity")
    sql = "SELECT Sectors, DATE, TRANS_VAL FROM vw_fii_sector_activity where Sectors<>'Sovereign' ORDER BY Sectors ASC"

    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()

    # 1. Extract all unique dates to use as Table Headers
    # We use a sorted list so the timeline is correct (Jan -> Feb -> Mar)
    unique_dates = sorted(list(set(row['DATE'].strftime('%Y-%m-%d') for row in result)))

    # 2. Pivot the data: { 'Automobile': {'2024-01-15': -500, '2024-12-31': -2656}, ... }
    pivoted_data = {}
    for row in result:
        sec = row['Sectors']
        dt = row['DATE'].strftime('%Y-%m-%d')
        val = float(row['TRANS_VAL']) if row['TRANS_VAL'] else 0.0

        if sec not in pivoted_data:
            pivoted_data[sec] = {}
        pivoted_data[sec][dt] = val

    return render_template("fii_sector_activity.html",
                           pivoted_data=pivoted_data,
                           unique_dates=unique_dates)