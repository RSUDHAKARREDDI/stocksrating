from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

# New Blueprint name
yr_new_high_low_bp = Blueprint("yr_new_high_low_bp", __name__)


@yr_new_high_low_bp.route("/yr-new-high-low")
def yr_new_high_low():
    # Adjusted query to include DATE1 and price points
    sql = """
    SELECT 
        `SYMBOL`,
        `SERIES`,
        `DATE1`,
        `LAST_PRICE`,
        `Adjusted_52_Week_High`,
        `Adjusted_52_Week_Low`
    FROM `vw_bhav_copy` 
    WHERE (52_week_high_date = date1 
       OR 52_week_low_dt = date1)
    ORDER BY DATE1 DESC;
    """

    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()

        rows = []
        for row in result:
            d = dict(row)

            # Handle Date formatting
            if d.get('DATE1') and hasattr(d['DATE1'], 'isoformat'):
                d['DATE1_STR'] = d['DATE1'].strftime('%d/%m/%Y')

            # Calculations
            last_price = float(d.get('LAST_PRICE') or 0)
            high_52 = float(d.get('Adjusted_52_Week_High') or 0)
            low_52 = float(d.get('Adjusted_52_Week_Low') or 0)

            # % Distance from 52 Week High
            if high_52 > 0:
                d['pct_from_high'] = round(((last_price - high_52) / high_52) * 100, 2)
            else:
                d['pct_from_high'] = 0

            # % Distance from 52 Week Low
            if low_52 > 0:
                d['pct_from_low'] = round(((last_price - low_52) / low_52) * 100, 2)
            else:
                d['pct_from_low'] = 0

            rows.append(d)

    return render_template("yr_new_high_low.html", rows=rows)