from pathlib import Path
from typing import Optional
import time
import shutil

from shellarc_engine.config.read_config import ReadClientConfig

mounted_dir = ReadClientConfig.get_mounted_dir()

def scan_mounted_dir() -> dict:
    rtn = {
        "detected" : ReadClientConfig.get_config_item("managed_files").get("detected", []),
        "edited" : []
    }
    tracking_files = [f for f in ReadClientConfig.get_config_item("managed_files", "tracking")]
    recorded_files = (tracking_files + ReadClientConfig.get_config_item("managed_files", "untracked"))
    for f in mounted_dir.iterdir():
        path_f = Path(f)
        if str(path_f) in rtn["detected"]:
            continue
        if path_f.is_dir() or path_f.name.startswith("."):
            continue
        if str(path_f) not in recorded_files:
            rtn["detected"].append(str(path_f))
        elif (str(path_f) in tracking_files and 
              path_f.stat().st_mtime > float(ReadClientConfig.get_config_item("managed_files", "tracking", str(path_f), "last_scanned"))):
            rtn["edited"].append(str(path_f))
    return rtn

def get_mount_file_info() -> dict:
    info = ReadClientConfig.get_config_item("managed_files")
    return info

def update_scanned_time():
    managed_files_info = ReadClientConfig.get_config_item("managed_files")
    for tracking_file in managed_files_info["tracking"]:
        ReadClientConfig.write_config_item(str(time.time()), "managed_files", "tracking", tracking_file, "last_scanned")

def get_tag_info(file_path) -> Optional[dict[str, str]]:
    tag_info = ReadClientConfig.get_config_item("managed_files", "tracking", file_path, "custom_tags")
    return tag_info

def write_tag_info(
        file_path: str, 
        new_tag_title: str, 
        new_tag_expression: str,
        new_tag_basecolor: str):
    ReadClientConfig.write_config_item(
        {
            "expression" : new_tag_expression,
            "base_color" : new_tag_basecolor
        },
        "managed_files", "tracking", file_path, "custom_tags", new_tag_title
    )

def delete_tag_info(file_path: str, tag_title: str):
    current_tag_info = get_tag_info(file_path=file_path)
    if tag_title in current_tag_info:
        del current_tag_info[tag_title]
    ReadClientConfig.write_config_item(
        current_tag_info,
        "managed_files", "tracking", file_path, "custom_tags"
    )

def check_container_duplication(
        container_index: str,
        extra_source: Optional[dict]=None
        ) -> str | None:
    managed_files_info = ReadClientConfig.get_config_item("managed_files")
    current_tracking_files = managed_files_info["tracking"]
    for file_path, file_info in current_tracking_files.items():
        if file_info.get("affiliation") == container_index:
            return file_path
    if extra_source is not None:
        for file_path, file_info in extra_source.items():
            if file_info.get("affiliation") == container_index:
                return file_path
    return None

def write_file_status(info: dict):
    tracked_files = info.get("tracked", {}) # dict[filepath : {affiliation: ""}]
    untracked_files = info.get("untracked", [])
    detected_files = info.get("detected", [])
    remove_files = info.get("remove", [])
    managed_files_info = ReadClientConfig.get_config_item("managed_files")

    current_detected_files = managed_files_info["detected"] 
    current_untracked_files = managed_files_info["untracked"]
    current_tracking_files = managed_files_info["tracking"] # dict[filepath : {affiliation: "", last_scanned: ""}]

    for tracked_file, tracked_file_info in tracked_files.items():
        ReadClientConfig.write_config_item(str(time.time()), "managed_files", "tracking", tracked_file, "last_scanned")
        ReadClientConfig.write_config_item(str(tracked_file_info.get("affiliation", "")), "managed_files", "tracking", tracked_file, "affiliation")
        if tracked_file in current_detected_files:
            current_detected_files.remove(tracked_file)
        if tracked_file in current_untracked_files:
            current_untracked_files.remove(tracked_file)
        duplicated_file_path = check_container_duplication(
            container_index=str(tracked_file_info.get("affiliation", "")),
            extra_source=tracked_files
        )
        if duplicated_file_path is not None:
            if duplicated_file_path in current_tracking_files:
                del current_tracking_files[duplicated_file_path]
            elif duplicated_file_path in tracked_files:
                del tracked_files[duplicated_file_path]
            current_detected_files.append(duplicated_file_path)

    for untracked_file in untracked_files:
        if untracked_file not in current_untracked_files:
            current_untracked_files.append(untracked_file)
        if untracked_file in current_detected_files:
            current_detected_files.remove(untracked_file)
        if untracked_file in current_tracking_files:
            del current_tracking_files[untracked_file]

    for detected_file in detected_files:
        if detected_file not in current_detected_files:
            current_detected_files.append(detected_file)

    for remove_file in remove_files:
        if remove_file in current_detected_files:
            current_detected_files.remove(remove_file)
        if remove_file in current_untracked_files:
            current_untracked_files.remove(remove_file)
        if remove_file in current_tracking_files:
            del current_tracking_files[remove_file]

    ReadClientConfig.write_config_item(current_untracked_files, "managed_files", "untracked")
    ReadClientConfig.write_config_item(current_detected_files, "managed_files", "detected")

def copy_to_mount(src_filepath: str):
    shutil.copy2(src=src_filepath, dst=mounted_dir)


    