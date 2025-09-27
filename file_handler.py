import os
from flask import flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), "data_files")
ALLOWED_EXTENSIONS = {"csv"}   # only allow CSVs

# Make sure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file):
    """Save uploaded file to data_files directory and return file path."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        flash(f"File '{filename}' uploaded successfully!", "success")
        return filepath   # ✅ return path so we can insert into DB
    else:
        flash("Only CSV files are allowed.", "error")
        return None


def list_files():
    """List all files in upload directory."""
    return os.listdir(UPLOAD_FOLDER)