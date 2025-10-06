import os
from pathlib import Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles")  # keep it consistent & absolute

# -------- Paths (robust & absolute) --------
PROJECT_ROOT = Path(__file__).resolve().parent      # /home/you/yourproject
UPLOAD_DIR1 = PROJECT_ROOT / "datafiles"          # /home/you/yourproject/datafiles

print(f'Base DIR:{BASE_DIR}')
print(f'UPLOAD_DIR:{UPLOAD_DIR}')

print(f'PROJECT_ROOT:{PROJECT_ROOT}')
print(f'UPLOAD_DIR1:{UPLOAD_DIR1}')