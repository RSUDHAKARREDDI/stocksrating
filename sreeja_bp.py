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
    `vw_quality_stocks`.`Margin`
FROM `vw_quality_stocks`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("quality_stocks.html", rows=rows)


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
    `vw_quality_stocks`.`Margin`
FROM `vw_quality_stocks`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("latest_results.html", rows=rows)