from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB
import os

index_returns_bp = Blueprint("index_returns_bp", __name__)

# Engine setup
engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)


@index_returns_bp.route("/index-returns")
def index_returns():
    # We query the table loaded by your CSV script
    sql = "SELECT * FROM vw_index_returns"

    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        # Convert SQLAlchemy rows to a list of regular dictionaries
        rows = [dict(row) for row in result]

    return render_template("index_returns.html", rows=rows)