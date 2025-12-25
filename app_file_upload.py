import os
from app_auth_utils import login_required
from flask import Flask, request, redirect, url_for, flash, render_template,jsonify,session,Blueprint
from werkzeug.utils import secure_filename
from datetime import datetime
import screeners_load as sf
from file_list_config import file_list_config
import files_data_cleanup as fclean


# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATAFILES_DIR = os.path.join(BASE_DIR, "datafiles")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")

bhav_copy_file = os.path.join(BASE_DIR, "datafiles","uploads","bhav_copy.csv")
wk_high_low=os.path.join(BASE_DIR, "datafiles","uploads","52_wk_High_low.csv")


file_upload_bp = Blueprint("file_upload_bp", __name__)


def get_all_files_info():
    files_info = []
    if os.path.exists(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            fpath = os.path.join(UPLOAD_DIR, fname)
            if os.path.isfile(fpath):
                mtime = os.path.getmtime(fpath)
                files_info.append({
                    "folder": "uploads",
                    "name": fname,
                    "last_modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
    return sorted(files_info, key=lambda x: x['last_modified'], reverse=True)


@file_upload_bp.route("/upload-files", methods=["GET", "POST"])
@login_required
def upload_file():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        if not file or file.filename.strip() == "":
            flash("No file selected")
            return redirect(request.url)

        try:
            original_name = secure_filename(file.filename)
            target_name = original_name  # Default name

            # --- LOGIC: Check for Pattern Match and Rename ---
            for key, config in file_list_config.items():
                pattern = config.get('file_pattern')
                rename_val = config.get('rename_to')

                # If a pattern exists and matches the start of the filename
                if pattern and original_name.startswith(pattern):
                    if rename_val:
                        target_name = rename_val
                        # Ensure extension is handled if rename_to is missing it
                        if not target_name.endswith('.csv') and original_name.endswith('.csv'):
                            target_name += '.csv'
                    break

                    # --- LOGIC: Always Save to UPLOAD_DIR ---
            save_path = os.path.join(UPLOAD_DIR, target_name)
            file.save(save_path)

            if target_name != original_name:
                flash(f"File detected as pattern match. Saved as '{target_name}' in uploads.")
            else:
                flash(f"File '{target_name}' uploaded successfully.")

            # --- LOGIC: Specific Post-Processing ---
            if target_name == "latest-results.csv":
                try:
                    sf.screeners_load()
                    flash("✅ Screeners processed successfully.")
                except Exception as e:
                    flash(f"⚠️ Screeners failed: {e}")

            if target_name =="52_wk_High_low.csv":
                fclean.clean_and_filter_52wk(wk_high_low)
            elif target_name =="bhav_copy.csv":
                fclean.clean_and_filter_bhavcopy(bhav_copy_file)
            else:
                pass

        except Exception as e:
            flash(f"Upload failed: {e}")

        return redirect(url_for("file_upload_bp.upload_file"))

    return render_template("upload_files.html", files=get_all_files_info())

@file_upload_bp.route("/delete-file/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    try:
        # Secure the filename to prevent directory traversal attacks
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_DIR, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f"File '{filename}' deleted successfully.")
        else:
            flash(f"Error: File '{filename}' not found.")

    except Exception as e:
        flash(f"Failed to delete file: {e}")

    return redirect(url_for("file_upload_bp.upload_file"))