# bp_basket.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# ====== DB engine (reuse your existing config_db) ======
try:
    from config_db import HOST, PORT, USER, PASSWORD, DB
    connection_url = f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4"
except Exception:
    # Fallback envs (edit if needed)
    import os
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "3306"))
    USER = os.getenv("DB_USER", "root")
    PASSWORD = os.getenv("DB_PASS", "")
    DB = os.getenv("DB_NAME", "stocksrating")
    connection_url = f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4"

engine = create_engine(connection_url, pool_pre_ping=True)

baskets_bp = Blueprint("baskets_bp", __name__, template_folder="templates")

# Utility: tiny cleaner (kept inline, no helpers elsewhere)
def _strip(x):
    return (x or "").strip()

# ====== Routes ======

@baskets_bp.route("/basket/")
def basket_list():
    sql = text("""
        SELECT basket_id, basket_name, description
        FROM basket
        ORDER BY basket_id DESC
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return render_template("basket/basket_list.html", rows=rows)

@baskets_bp.route("/basket/<int:basket_id>")
def basket_view(basket_id: int):
    sql = text("""
        SELECT basket_id, basket_name, description
        FROM basket
        WHERE basket_id = :bid
        LIMIT 1
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"bid": basket_id}).mappings().first()
    if not row:
        flash("Basket not found.", "warning")
        return redirect(url_for("my_holdings_bp.basket_list"))
    return render_template("basket/basket_view.html", row=row)

@baskets_bp.route("/basket/create", methods=["GET", "POST"])
def basket_create():
    if request.method == "POST":
        basket_name = _strip(request.form.get("basket_name"))
        description = _strip(request.form.get("description"))

        if not basket_name:
            flash("Basket name is required.", "danger")
            return render_template("basket/basket_form.html", mode="create", form={"basket_name": basket_name, "description": description})

        sql = text("""
            INSERT INTO basket (basket_name, description)
            VALUES (:name, :desc)
        """)
        with engine.begin() as conn:
            conn.execute(sql, {"name": basket_name, "desc": description})
        flash("Basket created successfully.", "success")
        return redirect(url_for("my_holdings_bp.basket_list"))

    return render_template("basket/basket_form.html", mode="create", form={"basket_name": "", "description": ""})

@baskets_bp.route("/basket/<int:basket_id>/edit", methods=["GET", "POST"])
def basket_edit(basket_id: int):
    if request.method == "POST":
        basket_name = _strip(request.form.get("basket_name"))
        description = _strip(request.form.get("description"))

        if not basket_name:
            flash("Basket name is required.", "danger")
            return render_template("basket/basket_form.html", mode="edit", basket_id=basket_id,
                                   form={"basket_name": basket_name, "description": description})

        sql = text("""
            UPDATE basket
            SET basket_name = :name, description = :desc
            WHERE basket_id = :bid
        """)
        with engine.begin() as conn:
            conn.execute(sql, {"name": basket_name, "desc": description, "bid": basket_id})
        flash("Basket updated successfully.", "success")
        return redirect(url_for("baskets_bp.basket_view", basket_id=basket_id))

    # GET -> load current row
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT basket_id, basket_name, description FROM basket WHERE basket_id = :bid LIMIT 1"),
            {"bid": basket_id}
        ).mappings().first()
    if not row:
        flash("Basket not found.", "warning")
        return redirect(url_for("baskets_bp.basket_list"))

    return render_template("basket/basket_form.html", mode="edit", basket_id=basket_id,
                           form={"basket_name": row["basket_name"], "description": row["description"]})

@baskets_bp.route("/basket/<int:basket_id>/delete", methods=["POST"])
def basket_delete(basket_id: int):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM basket WHERE basket_id = :bid"), {"bid": basket_id})
    flash("Basket deleted.", "info")
    return redirect(url_for("baskets_bp.basket_list"))
