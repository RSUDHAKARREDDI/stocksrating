from flask import Blueprint, render_template,request,jsonify
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB


engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

stock_reaction_bp = Blueprint("stock_reaction_bp", __name__)

@stock_reaction_bp.route("/stock-reaction")
def stock_reaction():
    sql = "SELECT * FROM `company_list`;"
    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()
        rows = [dict(r) for r in result]
    return render_template("stock_reaction.html", rows=rows)


@stock_reaction_bp.route("/update-reaction", methods=["POST"])
def update_reaction():
    data = request.json
    company_id = data.get("company_id")
    reaction = data.get("reaction")

    sql = text("UPDATE `company_list` SET stock_reaction = :reaction WHERE Company_ID = :id")

    with engine.connect() as conn:
        conn.execute(sql, {"reaction": reaction, "id": company_id})
        conn.commit()  # Important for persistent updates

    return jsonify({"status": "success", "message": f"Updated ID {company_id}"})