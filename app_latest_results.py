# bp_sreeja.py
from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

latest_results_bp = Blueprint("latest_results_bp", __name__)

@latest_results_bp.route("/latest-results")
def latest_results():
    sql = """
SELECT `vw_latest_results`.`Name`,
    `vw_latest_results`.`BSE Code`,
    `vw_latest_results`.`NSE Code`,
    `vw_latest_results`.`Industry`,
    `vw_latest_results`.`Current Price`,
    `vw_latest_results`.`Market Capitalization`,
    `vw_latest_results`.`Market Cap`,
    `vw_latest_results`.`Promoter holding`,
    `vw_latest_results`.`Price to Earning`,
    `vw_latest_results`.`Industry PE`,
    `vw_latest_results`.`PEG Ratio`,
    `vw_latest_results`.`Return over 1week`,
    `vw_latest_results`.`Return over 1month`,
    `vw_latest_results`.`Return over 3months`,
    `vw_latest_results`.`Return over 6months`,
    `vw_latest_results`.`EPS latest quarter`,
    `vw_latest_results`.`EPS preceding quarter`,
    `vw_latest_results`.`EPS preceding year quarter`,
    `vw_latest_results`.`Debt`,
    `vw_latest_results`.`Debt to equity`,
    `vw_latest_results`.`OPM latest quarter`,
    `vw_latest_results`.`OPM preceding quarter`,
    `vw_latest_results`.`Return on equity`,
    `vw_latest_results`.`Return on capital employed`,
    `vw_latest_results`.`Price to book value`,
    `vw_latest_results`.`FII holding`,
    `vw_latest_results`.`DII holding`,
    `vw_latest_results`.`Public holding`,
    `vw_latest_results`.`Last result date`,
    `vw_latest_results`.`screener`,
    `vw_latest_results`.`mc essentials`,
    `vw_latest_results`.`mc technicals`,
    `vw_latest_results`.`Margin`,
    `vw_latest_results`.`Total Score`,
    `vw_latest_results`.`DELIV_PER`,
    `vw_latest_results`.`SERIES` ,
    `vw_latest_results`.`52_Week_High` ,
    `vw_latest_results`.`52_Week_Low`
FROM `vw_latest_results`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("latest_results.html", rows=rows)


