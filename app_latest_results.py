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
    # Selecting all columns to ensure nothing is missed
    sql = "SELECT * FROM `vw_latest_results`;"
    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        rows = [dict(r) for r in result]
    return render_template("latest_results.html", rows=rows)