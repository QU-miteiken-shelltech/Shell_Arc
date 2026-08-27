import datetime
from pathlib import Path

from shellarc_core.auth.access_database import AccessDB
from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access
from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet


def db_access_failed_action():
    pass

def r2_access_failed_action():
    pass

def gcp_access_failed_action():
    pass

def check_completed_action():
    pass

def access_check():
    print("Test start")
    print("--------------------")
    
    db_instance = AccessDB()
    if db_instance.database is not None:
        print("Firebase Database access : NORMAL")
    else:
        print("Firebase Database access : FAILED !!!!!!!!!!!!")
        db_access_failed_action()

    r2_instance = Cloudflare_R2_service_Access()
    if r2_instance.s3_client is not None:
        print("Cloudflare R2 access : NORMAL")
    else:
        print("Cloudflare R2 access : FAILED !!!!!!!!!!!!")
        r2_access_failed_action()

    spreadsheet_id_txt = Path(__file__).resolve().parent / "spreadsheet_id.txt"
    if not spreadsheet_id_txt.exists():
        print("Spreadsheet ID not found. Checking abolished")
        return
    with open(spreadsheet_id_txt, "r", encoding="utf-8") as f:
        spreadsheet_id = f.read()
    gcp_instance = AccessSpreadSheet(spreadsheet_key=str(spreadsheet_id))
    if gcp_instance.spreadsheet_obj(page_idx=0) is not None:
        print("GCP access : NORMAL")
    else:
        print("GCP access : FAILED !!!!!!!!!!!!")
        gcp_access_failed_action()
    
    check_completed_action()
    print(f"Access check finished ({datetime.datetime.now().strftime("%Y%m%d%H%M%S")})")
    print("--------------------")
    print()

if __name__ == "__main__":
    access_check()

