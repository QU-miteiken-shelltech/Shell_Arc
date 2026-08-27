import datetime
import json
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


class Cloudflare_R2_service_Access:
    def __init__(self):
        load_dotenv(verbose=True)
        dotenv_path = Path(__file__).resolve().parent / ".env"
        if not dotenv_path.exists():
            print(f"dotenv_path {dotenv_path} not exist")
            raise Exception
        load_dotenv(dotenv_path)
        R2_ACCESS_KEY_ID = os.environ.get("CloudflareR2_access_key_id")
        R2_SECRET_ACCESS_KEY = os.environ.get("CloudflareR2_secret_access_key")
        R2_ENDPOINT_URL = os.environ.get("CloudflareR2_jurisdiction_specific_endpoints")

        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto"
            )
        except Exception as e:
            self._s3_client = None
            print(f"Auth error in CloudflareR2 [{e}]")
            raise Exception

    @property
    def s3_client(self) -> boto3.client:
        """Get the Cloudflare R2 S3 client instance (Property)

        Returns:
            _s3_client (boto3.client): The S3 client instance for Cloudflare R2 operations.
        """
        return self._s3_client
        

def validate_paths() -> dict:
    backup_environ = os.environ.get("SHELLARC_LOCAL_BACKUP", None)
    if backup_environ is None:
        print("Environment variable not set")
        raise Exception
    local_backup_dir = Path(os.environ.get("SHELLARC_LOCAL_BACKUP"))
    if not local_backup_dir.exists():
        print(f"{local_backup_dir} not exist")
        return
    backup_config_path = local_backup_dir / "backup_config.json"
    if backup_config_path.exists():
        with open(backup_config_path, "r", encoding="utf-8") as f:
            backup_config = json.load(f)
    else:
        backup_config = {
            "last_backup_time" : "19991231235959",
            "local_backup_dir" : str(local_backup_dir)
        }
    return backup_config

def backup_on_local() -> None:
    backup_config = validate_paths()
    if ("last_backup_time" not in backup_config or \
        "local_backup_dir" not in backup_config):
        print("Invalid backup config file")
        return
    last_backup_time = datetime.datetime.strptime(backup_config["last_backup_time"], "%Y%m%d%H%M%S")
    local_backup_dir = backup_config["local_backup_dir"]
    s3_client = Cloudflare_R2_service_Access().s3_client
    bucket = "null-portal"
    collection_name = "null_2026_main"
    payload = {
        "Bucket": bucket,
        "Prefix" : f"{collection_name}/stage/"
    }
    obj_info_dict = {}
    for response in s3_client.get_paginator('list_objects_v2').paginate(**payload):
        obj_info_dict = response.get("Contents")
        for obj_info in obj_info_dict:
            try:
                obj_key = obj_info.get("Key")
                obj_name = obj_key.split("/")[-1]
                saved_timemark = datetime.datetime.strptime(obj_name.split("_")[-1].split(".")[0], "%Y%m%d%H%M%S")
                if saved_timemark <= last_backup_time:
                    continue
                print(f"Fetching : {obj_key}")
                cut_num = obj_name.split("_")[0]
                cut_dir = Path(local_backup_dir) / cut_num
                if not cut_dir.exists():
                    cut_dir.mkdir()
                s3_client.download_file(
                    bucket,
                    obj_key,
                    f"{cut_dir}/{obj_name}"
                )
            except Exception as e:
                print(f"ERROR : {e}")
                continue
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_config["last_backup_time"] = current_datetime
        with open(Path(local_backup_dir) / "backup_config.json", "w", encoding="utf-8") as f:
            json.dump(backup_config, f, ensure_ascii=False, indent=2)
        print(f"Backup completed at {current_datetime}")
    

if __name__ == "__main__":
    backup_on_local()