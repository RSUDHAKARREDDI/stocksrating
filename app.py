import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, flash, render_template,jsonify
from werkzeug.utils import secure_filename
from sreeja_bp import sreeja_bp
from sravani_bp import sravani_bp
from baskets_bp import baskets_bp
from my_holdings_bp import my_holdings_bp
import commonfunctions as cf
from file_list_config import file_list_config
import logging
import json
from pathlib import Path


# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles")


app = Flask(__name__)
app.secret_key = "dev"  # for flashing messages



# Register Blueprint
app.register_blueprint(sreeja_bp)
app.register_blueprint(sravani_bp)
app.register_blueprint(baskets_bp)
app.register_blueprint(my_holdings_bp)

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
@app.route("/upload-files", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Validate presence of file part
        if "file" not in request.files:
             
            return redirect(request.url)

        file = request.files["file"]

        # Validate a file was actually selected
        if not file or file.filename.strip() == "":
            flash("No file selected")
            return redirect(request.url)

        # Ensure temp upload folder exists
        temp_dir = f'{UPLOAD_DIR}/temp'
        os.makedirs(temp_dir, exist_ok=True)

        # Normalize filename and save temporarily
        filename = secure_filename(file.filename)
        save_path = os.path.join(temp_dir, filename)

        try:
            file.save(save_path)
            flash(f"File '{filename}' uploaded successfully!")

            # ➜ Move to respective folder based on file_list_config (mapped by basename)
            results = cf.move_files([save_path], target_dir=None, file_list_config=file_list_config)

            # Report move results
            if results.get("moved"):
                dsts = ", ".join(sorted({d for _, d in results["moved"]}))
                flash(f"Moved '{filename}' to: {dsts}")

            if results.get("skipped_no_target"):
                # Optional: remove the temp file if no mapping (so it doesn't linger)
                try:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                except Exception:
                    pass
                flash(f"No target mapping found for '{filename}' in file_list_config.")

            if results.get("errors"):
                for src, dest, err in results["errors"]:
                    flash(f"Move error to '{dest}': {err}")

        except Exception as e:
            flash(f"Failed to handle upload: {e}")
            return redirect(request.url)

        return redirect(url_for("upload_file"))

    # GET: list current files with last modified time (from target directories)
    files_info = []
    try:
        for section, cfg in file_list_config.items():
            folder = cfg.get("target_directory")
            abs_folder_path = os.path.join(BASE_DIR, folder)
            if not folder or not os.path.exists(abs_folder_path):
                continue

            for fname in sorted(os.listdir(abs_folder_path)):
                fpath = os.path.join(abs_folder_path, fname)

                if os.path.isfile(fpath):
                    last_modified = os.path.getmtime(fpath)
                    files_info.append({
                        "section": section,  # latest_files, screeners, etc.
                        "folder": folder,
                        "name": fname,
                        "last_modified": datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
                    })
    except Exception as e:
        flash(f"Error reading target directories: {e}")
        files_info = []

    if not files_info:
        flash("No files found in target directories.")

    return render_template("upload_files.html", files=files_info)


@app.route("/data-load", methods=["GET"])
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
def data_load_run():
    data = request.get_json(silent=True) or {}
    key = data.get("config")
    if not key or key not in file_list_config:
        return jsonify({
            "status": "error",
            "message": "Invalid or missing config key",
            "available": list(file_list_config.keys())
        }), 400

    cfg = file_list_config[key]
    try:
        res = cf.load_csvs_to_mysql(
            directory=os.path.join(BASE_DIR, cfg["target_directory"]),
            table_name=cfg["table_name"],

        )
        return jsonify({
            "status": "success",
            "config": key,
            "table": res["table"],
            "directory": res["directory"],
            "processed_files": res["processed_files"],
            "inserted_rows": res["inserted_rows"],
            "skipped_files": res["skipped_files"],
            "errors": res["errors"],
        })
    except Exception as e:
        logging.exception("Data load failed")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
