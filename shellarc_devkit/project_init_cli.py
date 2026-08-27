import asyncio
import json
import time
from pathlib import Path

import gspread

from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as SpreadSheet
from shellarc_core.cloudio.io_git import Git_IO


def make_spreadsheet(cut_num: int,
                     spreadsheet_map: dict,
                     spreadsheet: gspread.Worksheet
                     ) -> str :
    try:
        vert_offset = spreadsheet_map["vert_offset_0"]
        header_row_idx = spreadsheet_map["header"]
        for key, col_idx in spreadsheet_map["items"].items():
            spreadsheet.update_cell(
                row=header_row_idx,
                col=col_idx,
                value=key
            )
        if "cut_num" in spreadsheet_map["items"]:
            for cut_idx in range(1, cut_num + 1):
                spreadsheet.update_cell(
                    row=vert_offset + cut_idx,
                    col=spreadsheet_map["items"]["cut_num"],
                    value=cut_idx
                )
        return ""
    except Exception as e:
        return e
    

async def make_proj_repo(git_repo_local_dir: str,
                         project_settings: dict
                         ) -> None:
    git_io = Git_IO(git_repo_local_dir=git_repo_local_dir)
    await git_io.make_proj_repo(proj_settings=project_settings)

async def inilialize_project():
    proj_setting_path = str(input("Input path to project setting json file : ")).strip()
    if not proj_setting_path or not Path(proj_setting_path).exists():
        print("An existing project setting json file is needed")
        print("Process abolished")
        return
    
    proj_collection = str(input("Input project collection name : ")).strip()
    if not proj_collection:
        print("Input a valid collection name")
        print("Process abolished")
        return
    
    spreadsheet_key = str(input("Input spreadsheet key : ")).strip()
    if not spreadsheet_key:
        print("Input a valid spreadsheet key")
        print("Process abolished")
        return
    
    auto_make_spreadsheet = str(input("Auto-make spreadsheet ? (y/N)")).strip()
    is_auto_make_spreadsheet = auto_make_spreadsheet in ["y", "Y"]
    if is_auto_make_spreadsheet:
        spreadsheet_map_path = str(input("Input path to spreadsheet map json file : ")).strip()
        if not spreadsheet_map_path or not Path(spreadsheet_map_path).exists():
            print("An existing spreadsheet map json file is needed")
            print("Process abolished")
            return
        with open(spreadsheet_map_path, "r", encoding="utf-8") as f:
            spreadsheet_map = json.load(f)
        
    if not proj_setting_path or not proj_collection or not spreadsheet_key:
        print("Invalid inputs detected")
        print("Process abolished")
        return
    
    with open(proj_setting_path, "r", encoding="utf-8") as f:
        proj_settings = json.load(f)
    
        
    run_confirmation = str(input("Run project inilialization now ? (y/N) : ")).strip()
    if run_confirmation not in ["y", "Y"]:
        return
    
    time_s = time.time()
    print()
    print("--------------------")
    print("Start initialization process")

    #Make repo
    try:
        await make_proj_repo(
            git_repo_local_dir=proj_settings.get("git_repo_local", ""),
            project_settings=proj_settings
            )
    except Exception as e:
        print(f"Make project repository failed due to : {e}")
        print("Process abolished")
        return

    #try access
    try:
        spreadsheet_instance = SpreadSheet(spreadsheet_key)
        spreadsheet = spreadsheet_instance.spreadsheet_obj(page_idx=0)
        print("Spreadsheet (GCP) access successful")
    except Exception as e:
        print(f"Spreadsheet (GCP) access failed due to : {e}")
        print("Process abolished")
        return
        
    #Make spreadsheet
    if is_auto_make_spreadsheet:
        result = make_spreadsheet(
            cut_num=proj_settings["cut_num"],
            spreadsheet_map=spreadsheet_map,
            spreadsheet=spreadsheet
        )
        if result:
            print(f"Spreadsheet (GCP) access failed due to : {result}")
            print("Process abolished")
            return
    

    
    print(f"Inilialization completed in {time.time() - time_s} seconds")
    print("--------------------")
    print()

if __name__ == "__main__":
    asyncio.run(inilialize_project())