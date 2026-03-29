from flask import Blueprint, render_template, request, flash
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB
from collections import defaultdict

daily_trade_stats_bp = Blueprint("daily_trade_stats_bp", __name__)

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)


@daily_trade_stats_bp.route("/daily-trade-stats")
def index_returns():
    # 1. Fetch the last 15 unique trading dates first
    date_query = "SELECT DISTINCT DATE1 FROM bhav_copy WHERE DATE1 IS NOT NULL ORDER BY DATE1 DESC LIMIT 15"

    # 2. Build the main query for those dates
    # We use a subquery or IN clause to ensure we only get the last 15 days
    query = """
        SELECT 
            cl.Industry_Group,
            bc.DATE1,
            SUM(bc.NO_OF_TRADES) as total_trades,
            (SUM(bc.TURNOVER_LACS) / 100) as total_turnover_cr,
            AVG(bc.DELIV_PER) as avg_delivery_per
        FROM company_list cl 
        JOIN bhav_copy bc ON cl.NSE_Code = bc.SYMBOL 
        WHERE bc.DATE1 IN (SELECT * FROM ({}) as recent_dates)
        GROUP BY cl.Industry_Group, bc.DATE1
        ORDER BY cl.Industry_Group ASC, bc.DATE1 DESC
    """.format(date_query)

    try:
        with engine.connect() as conn:
            # Get the unique dates for the table headers
            date_result = conn.execute(text(date_query)).fetchall()
            all_dates = [str(r[0]) for r in date_result]  # Sorted newest to oldest

            # Get the main data
            result = conn.execute(text(query)).mappings().all()

            # Pivot the data: industry_data[industry][date] = stats
            pivot_data = defaultdict(dict)
            for row in result:
                pivot_data[row['Industry_Group']][str(row['DATE1'])] = {
                    'trades': row['total_trades'],
                    'turnover': row['total_turnover_cr'],
                    'delivery': row['avg_delivery_per']
                }

    except Exception as e:
        print(f"Error: {e}")
        pivot_data = {}
        all_dates = []
        flash("Error loading trade stats.", "danger")

    return render_template("daily_trade_stats.html",
                           pivot_data=pivot_data,
                           all_dates=all_dates)