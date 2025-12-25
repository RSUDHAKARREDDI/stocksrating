# sravani_bp.py
from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

sravani_bp = Blueprint("sravani_bp", __name__)

@sravani_bp.route("/screeners")
def screeners():
    sql = """
SELECT `vw_screeners`.`Name`,
    `vw_screeners`.`BSE Code`,
    `vw_screeners`.`NSE Code`,
    `vw_screeners`.`Industry`,
    `vw_screeners`.`Current Price`,
    `vw_screeners`.`Market Capitalization`,
    `vw_screeners`.`Market Cap`,
    `vw_screeners`.`Promoter holding`,
    `vw_screeners`.`Price to Earning`,
    `vw_screeners`.`Industry PE`,
    `vw_screeners`.`PEG Ratio`,
    `vw_screeners`.`Return over 1week`,
    `vw_screeners`.`Return over 1month`,
    `vw_screeners`.`Return over 3months`,
    `vw_screeners`.`Return over 6months`,
    `vw_screeners`.`EPS latest quarter`,
    `vw_screeners`.`EPS preceding quarter`,
    `vw_screeners`.`EPS preceding year quarter`,
    `vw_screeners`.`Debt`,
    `vw_screeners`.`Debt to equity`,
    `vw_screeners`.`OPM latest quarter`,
    `vw_screeners`.`OPM preceding quarter`,
    `vw_screeners`.`Return on equity`,
    `vw_screeners`.`Return on capital employed`,
    `vw_screeners`.`Price to book value`,
    `vw_screeners`.`FII holding`,
    `vw_screeners`.`DII holding`,
    `vw_screeners`.`Public holding`,
    `vw_screeners`.`screener`,
    `vw_screeners`.`mc essentials`,
    `vw_screeners`.`mc technicals`,
    `vw_screeners`.`margin` ,
     `vw_screeners`.`Total Score`,
     `vw_screeners`.`DELIV_PER`,
    `vw_screeners`.`SERIES` ,
    `vw_screeners`.`52_Week_High`,
    `vw_screeners`.`52_Week_Low`   
FROM `vw_screeners`;
"""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return render_template("screeners.html", rows=rows)
