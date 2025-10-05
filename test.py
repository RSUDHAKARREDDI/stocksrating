import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles")  # keep it consistent & absolute

print(f'Base DIR:{BASE_DIR}')

print(f'UPLOAD_DIR:{UPLOAD_DIR}')