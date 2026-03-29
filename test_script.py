import commonfunctions as cf
import files_data_cleanup as fclean
import os

# -------- Paths (robust & absolute) --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(BASE_DIR, "datafiles","uploads")

in_FII_SECTOR_ACTIVITY = os.path.join(BASE_DIR, "datafiles","uploads","FII_SECTOR_ACTIVITY.csv")
out_FII_SECTOR_ACTIVITY=os.path.join(BASE_DIR, "datafiles","uploads","Proccessed_FII_SECTOR_ACTIVITY.csv")



fclean.denormalize_sector_activity(in_FII_SECTOR_ACTIVITY,out_FII_SECTOR_ACTIVITY)
cf.load_files_to_mysql_upsert(out_FII_SECTOR_ACTIVITY,"fii_sector_activity")