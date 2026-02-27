# sravani_bp.py
from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

screeners_bp = Blueprint("screeners_bp", __name__)

@screeners_bp.route("/screeners")
def screeners():
    sql = "SELECT * FROM `vw_screeners`;"
    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        rows = [dict(r) for r in result]
    return render_template("screeners.html", rows=rows)