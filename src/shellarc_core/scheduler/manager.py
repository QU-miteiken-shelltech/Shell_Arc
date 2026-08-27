import asyncio
import datetime
import json
from collections.abc import Callable
from pathlib import Path

from shellarc_core.scheduler.main_timer import shellarc_maintimer


class ShellArc_ScheduleManager:
    timer_process = None

    def __init__(self,
                 task_callable: Callable,
                 schedule_file_path: Path | str="default",
                 ) -> None:
        if schedule_file_path == "default":
            schedule_file_path = Path.home() / ".config" / "shellarc" / "default_schedule.json"
        else:
            schedule_file_path = Path(schedule_file_path)
        if not schedule_file_path.parent.exists():
            schedule_file_path.parent.mkdir(parents=True)
        print(schedule_file_path)
        if not schedule_file_path.exists():
            with open(schedule_file_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        self.schedule_file_path = schedule_file_path
        with open(self.schedule_file_path, "r", encoding="utf-8") as f:
            self.schedule = json.load(f)
        self.task_callable = task_callable

    def _get_current_schedule(self,
                              task_timemark: str | int
                              ) -> list:
        try:
            task_timemark = int(task_timemark)
        except:
            raise
        current_schedule = self.schedule.get(task_timemark, [])
        return current_schedule
    
    def stop_scheduler(self,
                       recauculate: bool=True
                       ) -> None:
        if self.__class__.timer_process and not self.__class__.timer_process.done():
            self.__class__.timer_process.cancel()
            self.__class__.timer_process = None
        if recauculate:
            self.__class__.timer_process = asyncio.create_task(shellarc_maintimer(
                schedule_file_path=self.schedule_file_path,
                task_callable=self.task_callable
            ))

    def make_schedule(self,
                      task_datetime: datetime.datetime,
                      task: list
                      ) -> None:
        print(task_datetime)
        print(task)
        print("----------")
        datetime_str = str(task_datetime.strftime("%y%m%d%H%M"))
        for current_timemarks in list(self.schedule.keys()):
            schedule_datetime = datetime.datetime.strptime(current_timemarks, "%y%m%d%H%M")
            if (schedule_datetime - datetime.datetime.now()).total_seconds() <= 0:
                del self.schedule[current_timemarks]
        current_scheduled = self.schedule.get(datetime_str, [])
        current_scheduled.append(task)
        self.schedule[datetime_str] = current_scheduled
        print(self.schedule[datetime_str])
        with open(self.schedule_file_path, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)

    def delete_schedule(self,
                        task_timemark: str,
                        index: int=0
                        ) -> None:
        current_scheduled = self._get_current_schedule(task_timemark=task_timemark)
        if len(current_scheduled) <= index:
            raise
        current_scheduled.pop(index)
        self.schedule[task_timemark] = current_scheduled
        with open(self.schedule_file_path, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, sort_keys=True, ensure_ascii=False, indent=2)

    def ask_schedule(self,
                     max_output: int=10
                     ) -> dict[int, str]:
        sorted_schedule_key = sorted(self.schedule)
        sorted_schedule = {k: self.schedule[k] for k in sorted_schedule_key}
        i = 1
        rtn = {}
        for k, v in sorted_schedule.items():
            rtn[k] = v
            i += 1
            if i > max_output:
                break
        return rtn
    