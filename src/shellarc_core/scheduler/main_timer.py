import asyncio
import datetime
import json
from collections.abc import Callable
from pathlib import Path


async def shellarc_maintimer(schedule_file_path: Path | str,
                             task_callable: Callable):
    schedule_file_path = Path(schedule_file_path)
    with open(schedule_file_path, "r", encoding="utf-8") as f:
        latest_schedule = json.load(f)
    sorted_schedule_key = sorted(latest_schedule)
    sorted_schedule = {k: latest_schedule[k] for k in sorted_schedule_key}
    start_task_time_datetime = datetime.datetime.now()
    try:
        for timemark, tasks in sorted_schedule.items():
            timemark_datetime = datetime.datetime.strptime(timemark, "%y%m%d%H%M")
            time_until_next_task = (timemark_datetime - start_task_time_datetime).total_seconds() 
            if time_until_next_task <= 0:
                continue
            print(f"Itemi wait {time_until_next_task}")
            await asyncio.sleep(time_until_next_task)
            for task in tasks:
                await task_callable(*task)
            start_task_time_datetime = datetime.datetime.now()
    except asyncio.CancelledError:
        pass
    finally:
        # with open(schedule_file_path, "w", encoding="utf-8") as f:
        #     json.dump(_copy_sorted_schedule, f, ensure_ascii=False, indent=2)
        pass