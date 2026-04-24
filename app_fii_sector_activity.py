from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB
import os
import files_data_cleanup as fclean
import commonfunctions as cf
from collections import defaultdict
from datetime import datetime


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
    fclean.denormalize_sector_activity(in_FII_SECTOR_ACTIVITY, out_FII_SECTOR_ACTIVITY)
    cf.load_files_to_mysql_upsert(out_FII_SECTOR_ACTIVITY, "fii_sector_activity")

    sql = "SELECT Sectors, DATE, TRANS_VAL FROM vw_fii_sector_activity where Sectors<>'Sovereign' ORDER BY DATE ASC"

    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()

        # 1. Organize data and track months
        pivoted_data = defaultdict(dict)
        months_seen = []
        fortnightly_dates = sorted(list(set(row['DATE'].strftime('%Y-%m-%d') for row in result)))

        # Initialize monthly totals AND grand totals
        monthly_sums = defaultdict(lambda: defaultdict(float))
        grand_totals = defaultdict(float)  # <--- New: Track overall total per sector

        for row in result:
            sec = row['Sectors']
            dt_obj = row['DATE']
            dt_str = dt_obj.strftime('%Y-%m-%d')
            month_key = dt_obj.strftime('%Y-%m')
            val = float(row['TRANS_VAL']) if row['TRANS_VAL'] else 0.0

            pivoted_data[sec][dt_str] = val
            monthly_sums[sec][month_key] += val
            grand_totals[sec] += val  # <--- New: Add to grand total

            if month_key not in months_seen:
                months_seen.append(month_key)

        # 2. Build the final Ordered Column List
        final_columns = []
        months_processed = sorted(months_seen)

        for m in months_processed:
            month_fortnights = [d for d in fortnightly_dates if d.startswith(m)]
            final_columns.extend(month_fortnights)

            dt_obj = datetime.strptime(m, '%Y-%m')
            month_name = dt_obj.strftime('%b').upper()
            total_label = f"{month_name}-TOTAL"
            final_columns.append(total_label)

            for sec in pivoted_data:
                pivoted_data[sec][total_label] = monthly_sums[sec].get(m, 0.0)

        # 3. Add the Grand Total Column <--- New Section
        overall_label = "OVERALL TOTAL"
        final_columns.append(overall_label)

        for sec in pivoted_data:
            pivoted_data[sec][overall_label] = grand_totals[sec]

        return render_template("fii_sector_activity.html",
                               pivoted_data=dict(pivoted_data),
                               unique_dates=final_columns)