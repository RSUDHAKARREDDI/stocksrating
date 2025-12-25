# bp_sreeja.py
from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

sreeja_bp = Blueprint("sreeja_bp", __name__)

@sreeja_bp.route("/latest-results")
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
    `vw_latest_results`.`Total Score`
FROM `vw_latest_results`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("latest_results.html", rows=rows)


@sreeja_bp.route("/quality-stocks")
def quality_stocks():
    sql = """
SELECT `vw_quality_stocks`.`Name`,
    `vw_quality_stocks`.`BSE Code`,
    `vw_quality_stocks`.`NSE Code`,
    `vw_quality_stocks`.`Industry`,
    `vw_quality_stocks`.`Current Price`,
    `vw_quality_stocks`.`Market Capitalization`,
    `vw_quality_stocks`.`Market Cap`,
    `vw_quality_stocks`.`Promoter holding`,
    `vw_quality_stocks`.`Price to Earning`,
    `vw_quality_stocks`.`Industry PE`,
    `vw_quality_stocks`.`PEG Ratio`,
    `vw_quality_stocks`.`Return over 1week`,
    `vw_quality_stocks`.`Return over 1month`,
    `vw_quality_stocks`.`Return over 3months`,
    `vw_quality_stocks`.`Return over 6months`,
    `vw_quality_stocks`.`EPS latest quarter`,
    `vw_quality_stocks`.`EPS preceding quarter`,
    `vw_quality_stocks`.`EPS preceding year quarter`,
    `vw_quality_stocks`.`Debt`,
    `vw_quality_stocks`.`Debt to equity`,
    `vw_quality_stocks`.`OPM latest quarter`,
    `vw_quality_stocks`.`OPM preceding quarter`,
    `vw_quality_stocks`.`Return on equity`,
    `vw_quality_stocks`.`Return on capital employed`,
    `vw_quality_stocks`.`Price to book value`,
    `vw_quality_stocks`.`FII holding`,
    `vw_quality_stocks`.`DII holding`,
    `vw_quality_stocks`.`Public holding`,
    `vw_quality_stocks`.`Last result date`,
    `vw_quality_stocks`.`screener`,
    `vw_quality_stocks`.`mc essentials`,
    `vw_quality_stocks`.`mc technicals`,
    `vw_quality_stocks`.`Margin`,
    `vw_quality_stocks`.`Total Score`,
    `vw_quality_stocks`.`DELIV_PER`,
    `vw_quality_stocks`.`SERIES` ,
    `vw_quality_stocks`.`52_Week_High`,
    `vw_quality_stocks`.`52_Week_Low`   
FROM `vw_quality_stocks`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("quality_stocks.html", rows=rows)