import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, flash, render_template,jsonify,session
from werkzeug.utils import secure_filename
from sreeja_bp import sreeja_bp
from sravani_bp import sravani_bp
from baskets_bp import baskets_bp
from my_holdings_bp import my_holdings_bp
from app_file_upload import file_upload_bp
import commonfunctions as cf
from file_list_config import file_list_config
import logging
from app_auth_utils import login_required
import json
from pathlib import Path
import screeners_load as sf


# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")


app = Flask(__name__)
app.secret_key = "dev"  # for flashing messages



# Register Blueprint
app.register_blueprint(sreeja_bp)
app.register_blueprint(sravani_bp)
app.register_blueprint(baskets_bp)
app.register_blueprint(my_holdings_bp)
app.register_blueprint(file_upload_bp)

# ------------------------
# Home, Dashboard, Index
# ------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("index.html")

# ------------------------
# Upload CSV/File
# ------------------------
# --- helper: decide if a moved file is latest-results.csv ---
def _is_latest_results(path: str) -> bool:
    try:
        return os.path.basename(path).lower() == "latest-results.csv"
    except Exception:
        return False



@app.route("/data-load", methods=["GET"])
@login_required
def data_load_ui():
    """
    Renders the UI with buttons for each config.
    URL: /data-load
    """
    rows = []
    for key, cfg in file_list_config.items():
        rows.append({
            "key": key,
            "files": ", ".join(cfg.get("file_list", [])),
            "dir": cfg.get("target_directory", ""),
            "table": cfg.get("table_name", ""),
        })
    return render_template("data_load.html", configs=rows)


@app.route("/data-load/run", methods=["POST"])
@login_required
def data_load_run():
    data = request.get_json(silent=True) or {}
    key = data.get("config")

    if not key or key not in file_list_config:
        return jsonify({
            "status": "error",
            "message": "Invalid or missing config key"
        }), 400

    cfg = file_list_config[key]

    try:
        # 1. Prepare the full paths for all files in this config's file_list
        # We look for them in UPLOAD_DIR because your upload logic saves them there.
        file_paths = []
        for filename in cfg.get("file_list", []):
            full_path = os.path.join(UPLOAD_DIR, filename)
            file_paths.append(full_path)

        if not file_paths:
            return jsonify({"status": "error", "message": "No files defined in this config"}), 400

        # 2. Call the function with the correct argument name: 'file_paths'
        res = cf.load_files_to_mysql(
            file_paths=file_paths,
            mode=cfg["mode"],
            table_name=cfg["table_name"]
        )

        # 3. Return the response using the keys defined in your load_files_to_mysql function
        return jsonify({
            "status": "success",
            "config": key,
            "table": res["table"],
            "processed_files": res["processed_files"],
            "inserted_rows": res["inserted_rows"],
            "skipped_files": res["skipped_files"],
            "errors": res["errors"],
        })

    except Exception as e:
        logging.exception(f"Data load failed for config: {key}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "inno-labs" and password == "Abc12345@":
            session["user"] = username
            flash("✅ Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("❌ Invalid username or password", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
