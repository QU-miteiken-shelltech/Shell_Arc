from pathlib import Path
import time

from shellarc_client.engine.config.read_config import ReadClientConfig

mounted_dir = ReadClientConfig.get_mounted_dir()

def scan_mounted_dir() -> dict:
    rtn = {
        "detected" : [],
        "edited" : []
    }
    tracking_files = [f for f in ReadClientConfig.get_config_item("managed_files", "tracking")]
    recorded_files = (tracking_files + ReadClientConfig.get_config_item("managed_files", "untracked"))
    for f in mounted_dir.iterdir():
        path_f = Path(f)
        if path_f.is_dir() or path_f.name.startswith("."):
            continue
        if str(path_f) not in recorded_files:
            rtn["detected"].append(str(path_f))
        elif (str(path_f) in tracking_files and 
              path_f.stat().st_mtime > float(ReadClientConfig.get_config_item("managed_files", "tracking", str(path_f), "last_scanned"))):
            rtn["edited"].append(str(path_f))
    return rtn

def write_file_status(info: dict):
    tracked_files = info.get("tracked", []) # list[tuple[filepath, affiliated_container_index]]
    untracked_files = info.get("untracked", [])
    detected_files = info.get("detected", [])
    managed_files_info = ReadClientConfig.get_config_item("managed_files")
    for tracking_file in managed_files_info["tracking"]:
        ReadClientConfig.write_config_item(str(time.time()), "managed_files", "tracking", tracking_file, "last_scanned")

    current_detected_files = managed_files_info["detected"] # dict[filepath : {affiliation: "", last_scanned: ""}]
    current_untracked_files = managed_files_info["untracked"]
    current_tracking_files = managed_files_info["tracking"]
    
    for tracked_file_tuple in tracked_files:
        tracked_file = tracked_file_tuple[0]
        ReadClientConfig.write_config_item(str(time.time()), "managed_files", "tracking", tracked_file, "last_scanned")
        ReadClientConfig.write_config_item(str(tracked_file_tuple[1]), "managed_files", "tracking", tracked_file, "affiliation")
        if tracked_file in current_detected_files:
            current_detected_files.remove(tracked_file)
        if tracked_file in current_untracked_files:
            current_untracked_files.remove(tracked_file)

    for untracked_file in untracked_files:
        current_untracked_files.append(untracked_file)
        if untracked_file in current_detected_files:
            current_detected_files.remove(untracked_file)
        if untracked_file in current_tracking_files:
            del current_tracking_files[untracked_file]

    for detected_file in detected_files:
        current_detected_files.append(detected_file)

    ReadClientConfig.write_config_item(current_untracked_files, "managed_files", "untracked")
    ReadClientConfig.write_config_item(current_detected_files, "managed_files", "detected")

    print(ReadClientConfig.CLIENT_CONFIG)#DEBUG

    