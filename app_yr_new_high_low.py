from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB
import pandas as pd, os



# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(DATAFILES_DIR,"uploads")
SCORE_REFACTOR=os.path.join(UPLOAD_DIR, "score_refactor.csv")

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

# New Blueprint name
yr_new_high_low_bp = Blueprint("yr_new_high_low_bp", __name__)


@yr_new_high_low_bp.route("/yr-new-high-low")
def yr_new_high_low():
    # Load and clean score data
    score_df = pd.read_csv(SCORE_REFACTOR).drop_duplicates(subset=['NSE Code'], keep='last')
    score_lookup = score_df.set_index('NSE Code').to_dict('index')

    sql = "SELECT * FROM `vw_bhav_copy` WHERE (52_week_high_date = date1 OR 52_week_low_dt = date1) ORDER BY DATE1 DESC;"

    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        rows = []
        for row in result:
            d = dict(row)
            symbol = d.get('SYMBOL')

            # Use .get() to avoid KeyErrors on column names
            last_price = float(d.get('LAST_PRICE') or 0)
            high_52 = float(d.get('Adjusted_52_Week_High') or d.get('ADJUSTED_52_WEEK_HIGH') or 0)
            low_52 = float(d.get('Adjusted_52_Week_Low') or d.get('ADJUSTED_52_WEEK_LOW') or 0)

            # Series for filtering
            d['series_val'] = d.get('SERIES', 'EQ')

            # Slider Calculation (0 to 100 range)
            if (high_52 - low_52) > 0:
                d['range_pos'] = round(((last_price - low_52) / (high_52 - low_52)) * 100, 2)
            else:
                d['range_pos'] = 50

            # Score data mapping
            extra = score_lookup.get(symbol, {})
            d['total_score'] = extra.get('Total Score', 0)
            d['mc_essentials'] = extra.get('mc essentials', 'N/A')
            d['mc_technicals'] = extra.get('mc technicals', 'N/A')
            d['market_cap_cat'] = extra.get('Market Cap Category', 'UNKNOWN')

            # Distance calculations
            d['pct_from_high'] = round(((last_price - high_52) / high_52) * 100, 2) if high_52 > 0 else 0
            d['pct_from_low'] = round(((last_price - low_52) / low_52) * 100, 2) if low_52 > 0 else 0

            rows.append(d)

    return render_template("yr_new_high_low.html", rows=rows)