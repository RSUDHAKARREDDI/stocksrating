from flask import Blueprint, render_template
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from config_db import HOST, PORT, USER, PASSWORD, DB

engine = create_engine(
    f"mysql+mysqlconnector://{USER}:{quote_plus(PASSWORD)}@{HOST}:{int(PORT)}/{DB}?charset=utf8mb4",
    pool_pre_ping=True,
)

delvr_pct_graph_bp = Blueprint("delvr_pct_graph_bp", __name__)


@delvr_pct_graph_bp.route("/delvr-pct-graph")
def delvr_pct_graph():
    sql = """
    SELECT SYMBOL, SERIES, DATE1, CLOSE_PRICE, DELIV_PER 
    FROM bhav_copy;
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql)).mappings().all()

        # Convert SQLAlchemy RowMapping objects to plain Python dictionaries
        rows = [dict(row) for row in result]

    return render_template("delvr_pct_graph.html", rows=rows)

@delvr_pct_graph_bp.route("/delvr-pct-graph/<symbol>")
def delvr_pct_graph_symbol(symbol):
    # Filter the SQL query by the specific symbol
    sql = """
    SELECT SYMBOL, SERIES, DATE1, CLOSE_PRICE, DELIV_PER 
    FROM bhav_copy 
    WHERE SYMBOL = :symbol 
    ORDER BY DATE1 ASC;
    """
    with engine.connect() as conn:
        # Use parameters to prevent SQL injection
        result = conn.execute(text(sql), {"symbol": symbol}).mappings().all()

        # Handle Date serialization and convert RowMapping to dict
        rows = []
        for row in result:
            d = dict(row)
            if hasattr(d['DATE1'], 'isoformat'):
                d['DATE1'] = d['DATE1'].isoformat()
            rows.append(d)

    return render_template("delvr_pct_graph.html", rows=rows, selected_symbol=symbol)