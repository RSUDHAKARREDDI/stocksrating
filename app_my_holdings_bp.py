# bp_my_holdings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from api_ninja import build_ticker, get_stock_price
from app_auth_utils import login_required
import os, csv
import sqlite3

# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")
MARKET_DB_PATH=os.path.join(BASE_DIR, "../options_trading/","datafiles","market_data.db")

try:
    from config_db import HOST, PORT, USER, PASSWORD, DB
    connection_url = f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4"
except Exception:
    import os
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "3306"))
    USER = os.getenv("DB_USER", "root")
    PASSWORD = os.getenv("DB_PASS", "")
    DB = os.getenv("DB_NAME", "stocksrating")
    connection_url = f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4"

engine = create_engine(connection_url, pool_pre_ping=True)
my_holdings_bp = Blueprint("my_holdings_bp", __name__, template_folder="templates")

def _strip(x): return (x or "").strip()

def _load_companies():
    with engine.begin() as conn:
        return conn.execute(text("SELECT Name FROM company_list ORDER BY Name")).mappings().all()

@my_holdings_bp.route("/my_holdings/<int:holding_id>/price")
@login_required
def my_holdings_price(holding_id):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM vw_my_holdings WHERE holding_id=:id"),
            {"id": holding_id}
        ).mappings().first()

    if not row:
        return {"error": "not_found", "message": "Holding not found"}, 404

    # Be tolerant to column naming: NSE Code / NSE_Code, BSE Code / BSE_Code
    nse_code = row.get("NSE Code") or row.get("NSE_Code") or row.get("nse_code")
    bse_code = row.get("BSE Code") or row.get("BSE_Code") or row.get("bse_code")

    ticker = build_ticker(nse_code, bse_code)
    if not ticker:
        return {"error": "no_ticker", "message": "No NSE/BSE code on record"}, 400

    data = get_stock_price(ticker)
    # normalize a bit so frontend is easy:
    payload = {"ticker": ticker, **(data if isinstance(data, dict) else {"raw": data})}
    return payload, (200 if "error" not in payload else 502)


@my_holdings_bp.route("/my_holdings/live_feed")
@login_required
def live_feed():
    # 1. Load the mapping from your CSV (Instrument Key -> NSE Code)
    mapping = {}
    try:
        # Update this path to your actual mapping CSV file
        CSV_MAPPING_PATH = os.path.join(BASE_DIR, "../options_trading/","datafiles", "uploads", "matched_holdings.csv")
        with open(CSV_MAPPING_PATH, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Key: NSE_EQ|INE... -> Value: TARIL
                mapping[row['instrument_key']] = row['nse_code']
    except Exception as e:
        print(f"Mapping Load Error: {e}")

    try:
        with sqlite3.connect(MARKET_DB_PATH, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, price FROM stocks")
            rows = cursor.fetchall()

            # 2. Translate keys: instead of "NSE_EQ|...", we send "TARIL"
            translated_data = {}
            for row in rows:
                instrument_key = row['symbol']
                # If the key exists in our mapping, use the short nse_code (TARIL)
                # Otherwise, fallback to the instrument key
                clean_key = mapping.get(instrument_key, instrument_key)
                translated_data[clean_key] = row['price']

            return translated_data
    except Exception as e:
        return {"error": str(e)}, 500

@my_holdings_bp.route("/my_holdings/")
@login_required
def my_holdings_list():
    sql = text("""
        SELECT
            m.holding_id,
            m.Company_Name,
            m.Buy_Qty,
            m.Buy_Price,
            CASE 
                WHEN m.Sell_Qty > 0 THEN m.Buy_Price
                ELSE COALESCE(ROUND(a.total_invested / NULLIF(a.total_buy_qty, 0), 2), m.Buy_Price)                  
            END AS buy_avg_price,
            m.Buy_Date,
            m.Sell_Qty,
            m.Sell_Price,
            m.Sell_Date,
            m.Basket_ID,
            m.NSE_Code,
            m.`Total Score`,
            m.`DELIV_PER`,
            m.`SERIES`,
            m.`52_Week_High`,
            m.`52_Week_Low`
        FROM vw_my_holdings AS m
        LEFT JOIN (
              SELECT
                Company_Name,
                SUM(Buy_Qty) AS total_buy_qty,
                SUM(Buy_Qty * Buy_Price) AS total_invested
              FROM vw_my_holdings
              WHERE Sell_Qty IS NULL
              GROUP BY Company_Name
        ) AS a ON a.Company_Name = m.Company_Name
        ORDER BY m.holding_id DESC
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()

    # --- CSV Generation Logic ---
    try:
        # Ensure the directory exists
        os.makedirs(DATAFILES_DIR, exist_ok=True)
        csv_path = os.path.join(DATAFILES_DIR, "my_holdings.csv")

        with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Writing Header
            writer.writerow(["Company_Name", "NSE_Code"])

            # Writing Data Rows
            for row in rows:
                writer.writerow([row["Company_Name"], row["NSE_Code"]])

    except Exception as e:
        # It's usually good to log this rather than crashing the page
        print(f"Error writing CSV: {e}")

    return render_template("my_holdings/my_holdings_list.html", rows=rows)

@my_holdings_bp.route("/my_holdings/create", methods=["GET", "POST"])
@login_required
def my_holdings_create():
    with engine.begin() as conn:
        baskets = conn.execute(
            text("SELECT basket_id, basket_name FROM basket ORDER BY basket_name")
        ).mappings().all()

    if request.method == "POST":
        data = {
            "Company_Name": (request.form.get("Company_Name") or "").strip(),
            "Buy_Qty": request.form.get("Buy_Qty") or None,
            "Buy_Price": request.form.get("Buy_Price") or None,
            "Buy_Date": request.form.get("Buy_Date") or None,
            "Basket_ID": request.form.get("Basket_ID") or None,  # required
        }
        if not data["Company_Name"]:
            flash("Company name required.", "danger")
            return render_template("my_holdings/my_holdings_form.html",
                                   mode="create", companies=_load_companies(), baskets=baskets, form=data)
        if not data["Basket_ID"]:
            flash("Please select a Basket.", "danger")
            return render_template("my_holdings/my_holdings_form.html",
                                   mode="create", companies=_load_companies(), baskets=baskets, form=data)

        sql = text("""
            INSERT INTO my_holdings
            (Company_Name, Buy_Qty, Buy_Price, Buy_Date, Basket_ID)
            VALUES (:Company_Name, :Buy_Qty, :Buy_Price, :Buy_Date, :Basket_ID)
        """)
        with engine.begin() as conn:
            conn.execute(sql, data)
        flash("Holding created.", "success")
        return redirect(url_for("my_holdings_bp.my_holdings_list"))

    return render_template("my_holdings/my_holdings_form.html",
                           mode="create", companies=_load_companies(), baskets=baskets, form={})




@my_holdings_bp.route("/my_holdings/<int:holding_id>")
@login_required
def my_holdings_view(holding_id):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM vw_my_holdings WHERE holding_id=:id"),
            {"id": holding_id}
        ).mappings().first()

        bname = None
        if row and row.get("Basket_ID"):
            b = conn.execute(
                text("SELECT basket_name FROM basket WHERE basket_id=:bid"),
                {"bid": row["Basket_ID"]}
            ).mappings().first()
            bname = b["basket_name"] if b else None

    if not row:
        flash("Record not found.", "warning")
        return redirect(url_for("my_holdings_bp.my_holdings_list"))

    # Try a direct fetch for the detail page:
    nse_code = row.get("NSE Code") or row.get("NSE_Code") or row.get("nse_code")
    bse_code = row.get("BSE Code") or row.get("BSE_Code") or row.get("bse_code")
    ticker = build_ticker(nse_code, bse_code)
    live_price = get_stock_price(ticker) if ticker else {"error": "no_ticker"}

    return render_template(
        "my_holdings/my_holdings_view.html",
        row=row,
        basket_name=bname,
        ticker=ticker,
        live_price=live_price,
    )


@my_holdings_bp.route("/my_holdings/<int:holding_id>/edit", methods=["GET", "POST"])
@login_required
def my_holdings_edit(holding_id):
    # helper: tolerant getter for keys with different casings/names
    def _g(row, *keys, default=None):
        for k in keys:
            if k in row and row[k] is not None:
                return row[k]
        return default

    # load companies & baskets for the form (both GET and on validation errors)
    with engine.begin() as conn:
        companies = conn.execute(
            text("SELECT Name FROM company_list ORDER BY Name")
        ).mappings().all()
        baskets = conn.execute(
            text("SELECT basket_id, basket_name FROM basket ORDER BY basket_name")
        ).mappings().all()

    if request.method == "POST":
        data = {
            "Company_Name": (request.form.get("Company_Name") or "").strip(),
            "Buy_Qty": request.form.get("Buy_Qty") or None,
            "Buy_Price": request.form.get("Buy_Price") or None,
            "Buy_Date": request.form.get("Buy_Date") or None,
            "Sell_Qty": request.form.get("Sell_Qty") or None,
            "Sell_Price": request.form.get("Sell_Price") or None,
            "Sell_Date": request.form.get("Sell_Date") or None,
            "Basket_ID": request.form.get("Basket_ID") or None,
            "holding_id": holding_id,
        }

        if not data["Company_Name"]:
            flash("Company name required.", "danger")
            return render_template(
                "my_holdings/my_holdings_form.html",
                mode="edit", companies=companies, baskets=baskets,
                form=data, holding_id=holding_id
            )

        if not data["Basket_ID"]:
            flash("Please select a Basket.", "danger")
            return render_template(
                "my_holdings/my_holdings_form.html",
                mode="edit", companies=companies, baskets=baskets,
                form=data, holding_id=holding_id
            )

        sql = text("""
            UPDATE my_holdings
               SET Company_Name=:Company_Name, Buy_Qty=:Buy_Qty, Buy_Price=:Buy_Price,
                   Buy_Date=:Buy_Date, Sell_Qty=:Sell_Qty, Sell_Price=:Sell_Price,
                   Sell_Date=:Sell_Date, Basket_ID=:Basket_ID
             WHERE holding_id=:holding_id
        """)
        with engine.begin() as conn:
            conn.execute(sql, data)
        flash("Holding updated.", "success")
        return redirect(url_for("my_holdings_bp.my_holdings_list"))

    # GET -> load current row from the view
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM vw_my_holdings WHERE holding_id=:id"),
            {"id": holding_id}
        ).mappings().first()

    if not row:
        flash("Record not found.", "warning")
        return redirect(url_for("my_holdings_bp.my_holdings_list"))

    # Try to read Basket_ID from the view; if missing, fetch from base table
    basket_id = _g(row, "Basket_ID", "basket_id", "Basket Id", "basketId")
    if basket_id is None:
        with engine.begin() as conn:
            base = conn.execute(
                text("SELECT Basket_ID FROM my_holdings WHERE holding_id=:id"),
                {"id": holding_id}
            ).mappings().first()
            basket_id = base["Basket_ID"] if base and base.get("Basket_ID") is not None else None

    # Build a 'form' dict so the template shows current values & preselects the basket
    form = dict(row)
    form["Basket_ID"] = basket_id

    return render_template(
        "my_holdings/my_holdings_form.html",
        mode="edit", companies=companies, baskets=baskets,
        form=form, holding_id=holding_id
    )

@my_holdings_bp.route("/my_holdings/<int:holding_id>/delete", methods=["POST"])
@login_required
def my_holdings_delete(holding_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM my_holdings WHERE holding_id=:id"), {"id": holding_id})
    flash("Holding deleted.", "info")
    return redirect(url_for("my_holdings_bp.my_holdings_list"))

@my_holdings_bp.route("/my_holdings/<int:holding_id>/sell", methods=["GET", "POST"])
@login_required
def my_holdings_sell(holding_id):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM vw_my_holdings WHERE holding_id=:id"),
            {"id": holding_id}
        ).mappings().first()
    if not row:
        flash("Record not found.", "warning")
        return redirect(url_for("my_holdings_bp.my_holdings_list"))

    if request.method == "POST":
        data = {
            "Sell_Qty": request.form.get("Sell_Qty") or None,
            "Sell_Price": request.form.get("Sell_Price") or None,
            "Sell_Date": request.form.get("Sell_Date") or None,
            "holding_id": holding_id,
        }
        sql = text("""
            UPDATE my_holdings
               SET Sell_Qty=:Sell_Qty, Sell_Price=:Sell_Price, Sell_Date=:Sell_Date
             WHERE holding_id=:holding_id
        """)
        with engine.begin() as conn:
            conn.execute(sql, data)
        flash("Sell details saved.", "success")
        return redirect(url_for("my_holdings_bp.my_holdings_view", holding_id=holding_id))

    # GET -> show sell form with small defaults
    return render_template("my_holdings/my_holdings_sell.html", row=row)