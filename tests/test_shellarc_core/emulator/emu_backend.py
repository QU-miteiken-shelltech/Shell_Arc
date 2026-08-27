"""
discord_connection.py が実際に使っているビジネスロジッククラスを、
簡易な自作ロジックに置き換えず「そのまま」importして使うバックエンド。

前提(ユーザーからの指示に基づく):
- shellarc_core.process.uploader.ShellArc_Upload
- shellarc_core.process.reviewing.ShellArc_Review
- shellarc_core.process.query.ShellArc_Query
- shellarc_core.sapyc.sapyc_interpreter.SAPYC_Interpreter
  は「すでに仮想化されたもの」であり、中身を知らなくてもそのまま使ってよい。
  これらは r2_io / git_io / gcp_io を DI で受け取る設計になっているため、
  ここに Mock_R2_IO / Mock_Git_IO / Mock_Spreadsheet_IO を渡す限り、
  実際のR2 / Git / Google Spreadsheet APIには一切触れない。
- Mock_Git_IO は本番の Git_IO と全く同じロジック(実際の `git` コマンドを
  subprocessで実行する実装)。「一時ディレクトリを渡すだけ」という指示に基づき、
  git_repo_dir(tempfile.mkdtemp()で作成)を渡している点だけが本番との違い。

呼び出しシグネチャについての注意:
- discord_connection.py 内の呼び出し例から推測して呼んでいる。
  実際のシグネチャと異なる場合、実行時に TypeError 等が発生しうるが、
  その場合は GUI 側でエラーメッセージとして表示されるようにしている
  (アプリごと落ちないようにハンドリング済み)。

初期化フローについて:
- 社内の初期化スクリプト(inilialize_project.py相当)にある make_proj_repo() 関数
      async def make_proj_repo(git_repo_local_dir, project_settings):
          git_io = Git_IO(git_repo_local_dir=git_repo_local_dir)
          await git_io.make_proj_repo(proj_settings=project_settings)
  と同じ手順を ShellArcEmulatorBackend.create() で踏襲している。
  Mockのコンストラクタで直接状態を注入するのではなく、必ず make_proj_repo() を
  await して初期化する。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from test_shellarc_core.mockio.mock_git_io import Mock_Git_IO
from test_shellarc_core.mockio.mock_r2_io import Mock_R2_IO
from test_shellarc_core.mockio.mock_spreadsheet_io import Mock_Spreadsheet_IO

from shellarc_core.exception.structure_error import ShellArcError
from shellarc_core.exception.user_exception import ShellArcException
from shellarc_core.process.query import ShellArc_Query
from shellarc_core.process.reviewing import ShellArc_Review
from shellarc_core.process.uploader import ShellArc_Upload
from shellarc_core.sapyc.sapyc_interpreter import SAPYC_Interpreter


class ShellArcEmulatorBackend:
    def __init__(self, git_repo_dir: Path):
        self.git_repo_dir = git_repo_dir
        self.git_io = Mock_Git_IO(git_repo_local_dir=str(git_repo_dir))
        self.r2_io = Mock_R2_IO(bucket_name="mock-bucket")
        self.gcp_io = Mock_Spreadsheet_IO()

        # discord_connection.py の setup_shellarc_io と同じ組み立て方
        self.shellarc_query = ShellArc_Query(gcp_io=self.gcp_io, git_io=self.git_io)
        self.sapyc_interpreter = SAPYC_Interpreter(git_io=self.git_io, gcp_io=self.gcp_io)

        self.event_log: list[str] = []

    @classmethod
    async def create(cls, git_repo_dir: Path, proj_settings: dict) -> ShellArcEmulatorBackend:
        """
        社内の初期化スクリプトにある make_proj_repo() 関数と同じ手順で疑似リポジトリを
        生成してからバックエンドを返す:

            git_io = Git_IO(git_repo_local_dir=git_repo_local_dir)
            await git_io.make_proj_repo(proj_settings=project_settings)

        proj_settings は同スクリプトが読み込む project_settings.json と同じ形式:
            {"cut_num": int, "components": {"bg": {"format": "png"}, ...}}
        """
        self = cls(git_repo_dir=git_repo_dir)
        self._log(f"[init] make_proj_repo(proj_settings={proj_settings})")
        await self.git_io.make_proj_repo(proj_settings=proj_settings)
        return self

    def _log(self, msg: str) -> None:
        self.event_log.append(msg)

    def _format_error(self, e: Exception) -> str:
        if isinstance(e, (ShellArcException, ShellArcError)):
            return getattr(e, "frontend_msg", str(e))
        return f"予期しないエラー: {e!r}"

    # ---- 単純コマンド ----

    async def cmd_testarc(self) -> str:
        self._log("[cmd] ..testarc")
        return "MyReply"

    async def cmd_myid(self, display_name: str) -> str:
        self._log(f"[cmd] ..myid ({display_name})")
        creator_id = hashlib.shake_128(display_name.encode("utf-8")).hexdigest(3)
        return f"{display_name}さんのIDは {creator_id} です"

    async def cmd_status(self) -> str:
        self._log("[cmd] ..status")
        try:
            pending_status = await self.shellarc_query.get_pending_status(is_raw=False)
        except Exception as e:
            return self._format_error(e)
        if not pending_status:
            return "承認待ちの提出はありません"
        return "\n".join(f"カット{s[0]} - {s[1]}" for s in pending_status)

    async def cmd_sync(self) -> str:
        self._log("[cmd] ..sync")
        try:
            await ShellArc_Upload.sync_vps_with_remote(git_io=self.git_io)
        except Exception as e:
            return self._format_error(e)
        return "同期しました"

    async def cmd_history(self, cut_num: int, component: str, approve_only: bool = False, max_length: int | None = None) -> str:
        self._log(f"[cmd] ..log cut{cut_num} {component} (approve_only={approve_only})")
        try:
            if approve_only:
                history_dict = await self.shellarc_query.get_approve_history(
                    cut_num=cut_num, component=component, max_length=max_length
                )
            else:
                history_dict = await self.shellarc_query.get_history(
                    cut_num=cut_num, component=component, max_length=max_length
                )
        except Exception as e:
            return self._format_error(e)
        if not history_dict:
            return f"カット{cut_num}履歴はありません"
        return "\n".join(f"{k} - {v}" for k, v in history_dict.items())

    async def cmd_sapyc(self, cmd: str) -> str:
        self._log(f"[cmd] ..sapyc {cmd}")
        try:
            return await self.sapyc_interpreter.interpret_sapyc(cmd=cmd)
        except Exception as e:
            return self._format_error(e)

    def get_components_enname(self, cut_num: int) -> list[str]:
        """コンポーネント一覧(英語名)を取得する。ShellArc_Queryが同期メソッドとして
        提供している想定(discord_connection.py内でawaitされていないため)。"""
        try:
            return list(self.shellarc_query.get_components_enname(cut_num=cut_num))
        except Exception as e:
            self._log(f"[warn] get_components_enname 失敗、フォールバックを使用: {e}")
            return ["bg", "character", "effect", "compo"]

    async def debug_git_snapshot(self) -> str:
        """
        デバッグパネル表示用。実クラスに切り替えたことで state.json (Mock専用の
        可視化ファイル)が無くなったため、実際のリポジトリから情報を取得して
        テキストにまとめる。
        """
        lines: list[str] = []

        project_main_path = self.git_repo_dir / "project_main.json"
        if project_main_path.exists():
            lines.append("== project_main.json ==")
            lines.append(project_main_path.read_text(encoding="utf-8"))
        else:
            lines.append("(project_main.json未作成 - make_proj_repo未実行の可能性)")

        lines.append("")
        lines.append("== git status --porcelain (pendingブランチ) ==")
        try:
            pending_status = await self.git_io.get_pending_status()
            lines.append(pending_status or "(変更なし)")
        except Exception as e:
            lines.append(self._format_error(e))

        lines.append("")
        lines.append("== コミット履歴 (pendingブランチ、SUBMIT/APPROVE/DECLINE等) ==")
        try:
            log_entries = await self.git_io.get_log(
                output_format=[0, 1, 2, 3, 4, 5, 6], branch="pending"
            )
            if log_entries:
                for commit_hash, record in log_entries.items():
                    lines.append(f"{commit_hash}  {record}")
            else:
                lines.append("(該当するコミットはまだありません)")
        except Exception as e:
            lines.append(self._format_error(e))

        return "\n".join(lines)

    # ---- 提出/承認フロー(実クラスをそのまま使用) ----

    async def submit_component(
        self,
        cut_num: int,
        component_en: str,
        submitter_name: str,
        attachments: dict[str, bytes],
        message: str = "",
    ) -> str:
        self._log(f"[submit] cut{cut_num} / {component_en} by {submitter_name} ({len(attachments)}件添付)")
        try:
            shellarc_upload = ShellArc_Upload(
                cut_num=cut_num,
                working_component=component_en,
                r2_io=self.r2_io,
                git_io=self.git_io,
                gcp_io=self.gcp_io,
            )
            await shellarc_upload.upload_file(
                file=attachments,
                submitter_name=submitter_name,
                message=message,
            )
        except Exception as e:
            return self._format_error(e)
        return f"カット{cut_num} {component_en} が提出されました"

    async def review_component(
        self,
        cut_num: int,
        component_en: str,
        reviewer_name: str,
        is_approve: bool,
        message: str = "",
    ) -> str:
        self._log(
            f"[review] cut{cut_num} / {component_en} by {reviewer_name} "
            f"({'承認' if is_approve else '要修正'})"
        )
        try:
            shellarc_review = ShellArc_Review(
                cut_num=cut_num,
                reviewing_component=component_en,
                git_io=self.git_io,
                gcp_io=self.gcp_io,
            )
            await shellarc_review.pending_action(
                reviewer_name=reviewer_name,
                is_approve=is_approve,
                message=message,
            )
        except Exception as e:
            return self._format_error(e)
        if is_approve:
            return f"カット{cut_num} {component_en} が確定されました"
        return f"カット{cut_num} {component_en} がアーカイブされました"