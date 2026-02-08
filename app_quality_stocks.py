from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

quality_stocks_bp = Blueprint("quality_stocks_bp", __name__)

@quality_stocks_bp.route("/quality-stocks")
def quality_stocks():
    sql = "SELECT * FROM `vw_quality_stocks`;"
    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        rows = [dict(r) for r in result]
    return render_template("quality_stocks.html", rows=rows)