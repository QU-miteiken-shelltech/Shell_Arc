"""
Git_IO の Mock 実装。

設計判断（要確認事項）:
- 実物の `git` コマンドは一切叩かない。branch/commit/pending の状態はすべて
  インスタンス内の辞書で模擬している。
- そのため「実際のgitコマンドの構文エラー」や「マージコンフリクト」のような
  git特有の失敗は再現できない。そのレベルのテストが必要なら、前回話した
  「pytestのtmp_pathで一時gitリポジトリを作る」方式を別途使うことを推奨する。
- コンストラクタは `project_main` を直接受け取れるようにしている
  （実クラスは git_repo_local_dir 内の project_main.json ファイルを読むが、
  Mockではファイルを介さずテストコードから直接注入できる）。
"""

import hashlib
import datetime
from typing import Any

from io_git import (
    GitCommands,  # noqa: F401  (実クラスとの対応関係を明示するためimportだけしておく)
    SA_CommitType,
    ShellArcGitBranch,
    SA_GitLogFilter,
)
from shellarc_core.exception.user_exception import SA_InvalidRequestObj


class Mock_Git_IO:
    def __init__(
        self,
        git_repo_local_dir: str | None = None,  # 実クラスとシグネチャを揃えるためだけに受け取り、使用しない
        project_main: dict[str, Any] | None = None,
    ):
        self.git_repo_local_dir = git_repo_local_dir
        self._project_main: dict[str, Any] = project_main or {"common": []}
        # branch -> cut_num -> component -> info_dict
        self._branches: dict[str, dict[int, dict[str, dict]]] = {
            ShellArcGitBranch.MAIN: {},
            ShellArcGitBranch.PENDING: {},
        }
        self._pending_flags: set[tuple[int, str]] = set()
        self._log: list[dict[str, str]] = []
        self.sync_remote_call_count = 0  # sync_remoteが呼ばれたことをテストで検証するためのカウンタ

    # ---- 内部ヘルパー ----

    def _get_timemark(self) -> str:
        t_delta = datetime.timedelta(hours=9)
        now = datetime.datetime.now(datetime.timezone(t_delta, "JST"))
        return now.strftime("%Y%m%d%H%M%S")

    def _make_index_name(self, cut_num: int, component: str, creator_name: str) -> str:
        component = component.replace("_", "-")
        creator_id = hashlib.shake_128(creator_name.encode("utf-8")).hexdigest(3)
        return f"cut{cut_num}_{component}_{creator_id}_{self._get_timemark()}"

    def _append_log(self, commit_type, cut_num, component, creator, message, file_index="na"):
        commit_hash = hashlib.shake_128(
            f"{commit_type}{cut_num}{component}{self._get_timemark()}".encode("utf-8")
        ).hexdigest(4)
        record = {
            "commit_type": str(commit_type),
            "cut_num": str(cut_num),
            "component": component,
            "creator_name": creator,
            "commit_message": message,
            "timemark": self._get_timemark(),
            "file_index_name": file_index,
        }
        self._log.append({"hash": commit_hash, **record})

    # ---- 公開API（Git_IOと同じシグネチャ） ----

    async def make_proj_repo(self, proj_settings: dict) -> None:
        self._project_main = {
            "cut_num": int(proj_settings["cut_num"]),
            "common": {
                c: [c_info["format"]] for c, c_info in proj_settings["components"].items()
            },
        }
        for cut in range(1, int(proj_settings["cut_num"]) + 1):
            self._branches[ShellArcGitBranch.MAIN].setdefault(cut, {})
            self._branches[ShellArcGitBranch.PENDING].setdefault(cut, {})

    def get_components(self, cut_num: int) -> list[str]:
        components = self._project_main.get("common", [])
        components = self._project_main.get(f"cut{cut_num}", components)
        return [c for c in components]

    async def get_component_info(
        self,
        branch,
        cut_num: int,
        component: str,
        commit_id: str | None = None,
    ) -> dict[str, str]:
        requested_info = self._branches.get(str(branch), {}).get(cut_num, {}).get(component, {})
        repointer = requested_info.get("repointer", None)
        if repointer is not None:
            return await self.get_component_info(
                branch=branch, cut_num=int(repointer), component=component, commit_id=branch
            )
        return requested_info

    async def get_log(
        self,
        output_format: list[int],
        log_filter: SA_GitLogFilter | None = None,
        limit_scope: str | None = None,
        branch=ShellArcGitBranch.PENDING,
    ) -> dict[str, str]:
        if log_filter is None:
            log_filter = SA_GitLogFilter()
        field_order = [
            "commit_type", "cut_num", "component", "creator_name",
            "commit_message", "timemark", "file_index_name",
        ]
        rtn: dict[str, str] = {}
        for record in self._log:
            if log_filter.commit_type is not None and str(log_filter.commit_type) != record["commit_type"]:
                continue
            if log_filter.cut_num is not None and str(log_filter.cut_num) != record["cut_num"]:
                continue
            if log_filter.component is not None and log_filter.component != record["component"]:
                continue
            values = [record[field_order[i]] for i in output_format]
            rtn[record["hash"]] = " ".join(values)
            if log_filter.log_length is not None and len(rtn) >= log_filter.log_length:
                break
        return rtn

    async def get_pending_status(self) -> str:
        lines = [
            f"?? stage/cut{cut}/.sa_pending_{component}"
            for (cut, component) in sorted(self._pending_flags)
        ]
        return "\n".join(lines)

    async def repoint_data(self, be_repointed_cut: int, repoint_target_cut: int, component: str) -> None:
        self._branches[ShellArcGitBranch.PENDING].setdefault(be_repointed_cut, {})[component] = {
            "repointer": repoint_target_cut
        }
        self._pending_flags.add((be_repointed_cut, component))
        self._append_log(
            SA_CommitType.REPOINT, be_repointed_cut, component, "na",
            f"REPOINT {be_repointed_cut}->{repoint_target_cut}",
        )

    async def absorb_data(
        self,
        absorbing_cut: int,
        absorb_target_cut: int,
        component: str,
        commit_id: str | None = None,
        branch=ShellArcGitBranch.PENDING,
    ) -> None:
        requested_info = self._branches.get(str(branch), {}).get(absorb_target_cut, {}).get(component, {})
        self._branches[ShellArcGitBranch.PENDING].setdefault(absorbing_cut, {})[component] = dict(requested_info)
        self._pending_flags.add((absorbing_cut, component))
        self._append_log(
            SA_CommitType.ABSORPTION, absorbing_cut, component, "na",
            f"ABSORB {absorb_target_cut}->{absorbing_cut}",
        )

    async def pend_data(
        self,
        cut_num: int,
        component: str,
        processing_person: str,
        is_approve: bool,
        message: str = "",
    ) -> None:
        if not message:
            message = "No message"
        message = message.replace("*", "+")
        if (cut_num, component) not in self._pending_flags:
            raise SA_InvalidRequestObj(
                error_log=f"c{cut_num} {component} pending attempted by {processing_person} but not exist",
                frontend_msg="承認待ちの提出はありません",
            )
        self._pending_flags.discard((cut_num, component))
        commit_type = SA_CommitType.APPROVE if is_approve else SA_CommitType.DECLINE
        if is_approve:
            pending_info = self._branches[ShellArcGitBranch.PENDING].get(cut_num, {}).get(component, {})
            self._branches[ShellArcGitBranch.MAIN].setdefault(cut_num, {})[component] = dict(pending_info)
        self._append_log(commit_type, cut_num, component, processing_person, message)

    async def update_data(self, cut_num: int, component: str, creator_name: str, message: str = "") -> str:
        if not message:
            message = "No message"
        message = message.replace("*", "+")
        file_index_name = self._make_index_name(cut_num=cut_num, component=component, creator_name=creator_name)
        self._branches[ShellArcGitBranch.PENDING].setdefault(cut_num, {})[component] = {
            "creator": creator_name,
            "fileindex": file_index_name,
        }
        self._pending_flags.add((cut_num, component))
        self._append_log(SA_CommitType.SUBMIT, cut_num, component, creator_name, message, file_index_name)
        return file_index_name

    async def sync_remote(self) -> None:
        self.sync_remote_call_count += 1
