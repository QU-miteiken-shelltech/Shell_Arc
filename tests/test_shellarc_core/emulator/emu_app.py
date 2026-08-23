"""
PySide6によるDiscord風テストエミュレータUI(実ビジネスロジック使用版)。

前回からの変更点(重要):
- 自作の簡易ロジックをやめ、ShellArc_Upload / ShellArc_Review / ShellArc_Query /
  SAPYC_Interpreter を「そのまま」呼び出す emu_backend.ShellArcEmulatorBackend を使用。
- これらは async メソッドなので、ボタン押下のたびに asyncio.run() で同期的に実行する
  (Mock IOのみのローカル処理なので、都度ブロッキングしても実用上問題ない想定)。
- Mock_R2_IO(前回作成分)はメモリ内保存のみで、tmpディレクトリへのファイル書き出しは
  行っていない。Gitの疑似リポジトリ(Mock_Git_IO)のみ、tmpディレクトリに実際に
  state.jsonを書き出す。この非対称性は意図的な妥協点(詳しい説明はREADME参照)。
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QTextEdit, QLineEdit,
    QPushButton, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPlainTextEdit, QFrame, QMessageBox,
)

from test_shellarc_core.emulator.emu_backend import ShellArcEmulatorBackend
from test_shellarc_core.utils.emu_state import FakeAttachment, FakeMessage
from test_shellarc_core.utils.mock_media import generate_mock_file

FAKE_CHANNELS = ["cut1_bg", "cut1_character", "cut2_bg", "cut2_effect", "general"]


def run_async(coro):
    """asyncメソッドをGUIのボタンハンドラから同期的に呼び出すためのヘルパー。"""
    return asyncio.run(coro)


class MainWindow(QMainWindow):
    def __init__(self, backend: ShellArcEmulatorBackend, git_repo_dir: Path):
        super().__init__()
        self.git_repo_dir = git_repo_dir
        self.backend = backend
        self.messages_by_channel: dict[str, list[FakeMessage]] = {c: [] for c in FAKE_CHANNELS}
        self.pending_attachments: list[FakeAttachment] = []

        self.setWindowTitle("ShellArc Discord Emulator (Mock専用 / 実APIには一切接続しません)")
        self.resize(1150, 680)
        self._build_ui()
        self._on_channel_changed(self._current_channel())
        self._refresh_debug_panels()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.addWidget(self._build_channel_panel(), 1)
        root_layout.addWidget(self._build_chat_panel(), 3)
        root_layout.addWidget(self._build_debug_panel(), 2)
        self.setCentralWidget(central)

    def _build_channel_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("チャンネル"))
        self.channel_list = QListWidget()
        self.channel_list.addItems(FAKE_CHANNELS)
        self.channel_list.currentTextChanged.connect(self._on_channel_changed)
        layout.addWidget(self.channel_list)
        self.channel_list.setCurrentRow(0)

        layout.addWidget(QLabel("あなたの表示名"))
        self.author_input = QLineEdit("TestUser")
        layout.addWidget(self.author_input)

        layout.addWidget(QLabel("クイックコマンド"))
        for label, handler in [
            ("..testarc", self._on_cmd_testarc),
            ("..myid", self._on_cmd_myid),
            ("..status", self._on_cmd_status),
            ("..sync", self._on_cmd_sync),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addWidget(QLabel("SAPYCコマンド"))
        self.sapyc_input = QLineEdit()
        self.sapyc_input.setPlaceholderText("例: get cut1 bg status")
        layout.addWidget(self.sapyc_input)
        sapyc_btn = QPushButton("..sapyc 実行")
        sapyc_btn.clicked.connect(self._on_cmd_sapyc)
        layout.addWidget(sapyc_btn)

        layout.addStretch(1)
        return panel

    def _build_chat_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        layout.addWidget(self.chat_view, 1)

        attach_row = QHBoxLayout()
        attach_row.addWidget(QLabel("疑似メディア添付:"))
        for ext in ["png", "jpg", "gif", "mp4"]:
            btn = QPushButton(f".{ext}")
            btn.clicked.connect(lambda _=False, e=ext: self._on_attach_mock_file(e))
            attach_row.addWidget(btn)
        self.attachment_label = QLabel("(添付なし)")
        attach_row.addWidget(self.attachment_label, 1)
        clear_btn = QPushButton("添付クリア")
        clear_btn.clicked.connect(self._on_clear_attachments)
        attach_row.addWidget(clear_btn)
        layout.addLayout(attach_row)

        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("メッセージを入力...")
        input_row.addWidget(self.message_input, 1)
        send_btn = QPushButton("送信")
        send_btn.clicked.connect(self._on_send_message)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        action_row = QHBoxLayout()
        action_row.addWidget(QLabel("コンポーネント:"))
        self.component_combo = QComboBox()
        action_row.addWidget(self.component_combo)
        submit_btn = QPushButton("提出 (UP)")
        submit_btn.clicked.connect(self._on_submit_clicked)
        action_row.addWidget(submit_btn)
        review_btn = QPushButton("承認 (APPR)")
        review_btn.clicked.connect(self._on_review_clicked)
        action_row.addWidget(review_btn)
        layout.addLayout(action_row)

        self.confirm_frame = QFrame()
        self.confirm_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.confirm_layout = QHBoxLayout(self.confirm_frame)
        self.confirm_label = QLabel()
        self.confirm_layout.addWidget(self.confirm_label, 1)
        self.confirm_frame.setVisible(False)
        layout.addWidget(self.confirm_frame)

        return panel

    def _build_debug_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("デバッグツール"))

        refresh_btn = QPushButton("状態を再読み込み")
        refresh_btn.clicked.connect(self._refresh_debug_panels)
        layout.addWidget(refresh_btn)

        paths_label = QLabel(
            f"Gitリポジトリ(tmp): {self.git_repo_dir}\n"
            f"R2ストレージ: メモリ内のみ(tmpには書き出していません)"
        )
        paths_label.setWordWrap(True)
        layout.addWidget(paths_label)

        self.debug_tabs = QTabWidget()

        self.git_state_view = QPlainTextEdit()
        self.git_state_view.setReadOnly(True)
        self.debug_tabs.addTab(self.git_state_view, "Git状態")

        self.r2_table = QTableWidget(0, 2)
        self.r2_table.setHorizontalHeaderLabels(["キー", "サイズ(MB, 切り捨て)"])
        self.debug_tabs.addTab(self.r2_table, "R2ストレージ")

        self.event_log_view = QPlainTextEdit()
        self.event_log_view.setReadOnly(True)
        self.debug_tabs.addTab(self.event_log_view, "イベントログ")

        layout.addWidget(self.debug_tabs, 1)
        return panel

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _current_channel(self) -> str:
        item = self.channel_list.currentItem()
        return item.text() if item else FAKE_CHANNELS[0]

    def _current_author(self) -> str:
        return self.author_input.text().strip() or "TestUser"

    def _extract_cut_num(self, channel_name: str) -> int | None:
        match = re.search(r"cut(\d+)", channel_name)
        return int(match.group(1)) if match else None

    def _append_system_message(self, content: str) -> None:
        msg = FakeMessage(author="[system]", channel=self._current_channel(), content=content)
        self.messages_by_channel[self._current_channel()].append(msg)
        self._render_chat()

    def _render_chat(self) -> None:
        channel = self._current_channel()
        self.chat_view.clear()
        for msg in self.messages_by_channel.get(channel, []):
            attach_note = ""
            if msg.attachments:
                names = ", ".join(a.filename for a in msg.attachments)
                attach_note = f"  📎 {names}"
            self.chat_view.append(f"[{msg.timestamp}] <b>{msg.author}</b>: {msg.content}{attach_note}")

    # ------------------------------------------------------------------
    # イベントハンドラ
    # ------------------------------------------------------------------

    def _on_channel_changed(self, _channel: str) -> None:
        cut_num = self._extract_cut_num(self._current_channel())
        self.component_combo.clear()
        if cut_num is not None:
            components = self.backend.get_components_enname(cut_num)
            self.component_combo.addItems(components)
        self._render_chat()

    def _on_attach_mock_file(self, ext: str) -> None:
        filename, data = generate_mock_file(ext)
        self.pending_attachments.append(FakeAttachment(filename=filename, data=data))
        names = ", ".join(a.filename for a in self.pending_attachments)
        self.attachment_label.setText(f"添付予定: {names} ({len(data)} bytes 最新)")

    def _on_clear_attachments(self) -> None:
        self.pending_attachments = []
        self.attachment_label.setText("(添付なし)")

    def _on_send_message(self) -> None:
        content = self.message_input.text().strip()
        if not content and not self.pending_attachments:
            return
        msg = FakeMessage(
            author=self._current_author(),
            channel=self._current_channel(),
            content=content,
            attachments=list(self.pending_attachments),
        )
        self.messages_by_channel[self._current_channel()].append(msg)
        self.message_input.clear()
        self._on_clear_attachments()
        self._render_chat()

    def _on_submit_clicked(self) -> None:
        cut_num = self._extract_cut_num(self._current_channel())
        if cut_num is None:
            QMessageBox.warning(self, "エラー", "このチャンネル名からカット番号を抽出できません(例: cut1_bg)")
            return
        if self.component_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "コンポーネントが見つかりません")
            return
        component = self.component_combo.currentText()
        attachments = list(self.pending_attachments)
        self._show_confirm(
            text=f"カット{cut_num}・{component} を提出しますか",
            options={
                "はい": lambda: self._do_submit(cut_num, component, attachments),
                "いいえ": lambda: self._append_system_message("提出プロセスが棄却されました"),
            },
        )

    def _do_submit(self, cut_num: int, component: str, attachments: list[FakeAttachment]) -> None:
        attachments_dict = {a.filename: a.data for a in attachments}
        result = run_async(self.backend.submit_component(
            cut_num=cut_num, component_en=component,
            submitter_name=self._current_author(), attachments=attachments_dict,
        ))
        self._append_system_message(result)
        self._on_clear_attachments()
        self._refresh_debug_panels()

    def _on_review_clicked(self) -> None:
        cut_num = self._extract_cut_num(self._current_channel())
        if cut_num is None:
            QMessageBox.warning(self, "エラー", "このチャンネル名からカット番号を抽出できません(例: cut1_bg)")
            return
        if self.component_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "コンポーネントが見つかりません")
            return
        component = self.component_combo.currentText()
        self._show_confirm(
            text=f"カット{cut_num}・{component} を確定しますか",
            options={
                "確定": lambda: self._do_review(cut_num, component, True),
                "要修正": lambda: self._do_review(cut_num, component, False),
                "キャンセル": lambda: self._append_system_message("承認プロセスが棄却されました"),
            },
        )

    def _do_review(self, cut_num: int, component: str, is_approve: bool) -> None:
        result = run_async(self.backend.review_component(
            cut_num=cut_num, component_en=component,
            reviewer_name=self._current_author(), is_approve=is_approve,
        ))
        self._append_system_message(result)
        self._refresh_debug_panels()

    def _show_confirm(self, text: str, options: dict[str, callable]) -> None:
        while self.confirm_layout.count() > 1:
            item = self.confirm_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self.confirm_label.setText(text)
        for label, callback in options.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, cb=callback: self._on_confirm_choice(cb))
            self.confirm_layout.addWidget(btn)
        self.confirm_frame.setVisible(True)

    def _on_confirm_choice(self, callback) -> None:
        self.confirm_frame.setVisible(False)
        callback()

    def _on_cmd_testarc(self) -> None:
        self._append_system_message(run_async(self.backend.cmd_testarc()))

    def _on_cmd_myid(self) -> None:
        self._append_system_message(run_async(self.backend.cmd_myid(self._current_author())))

    def _on_cmd_status(self) -> None:
        self._append_system_message(run_async(self.backend.cmd_status()))

    def _on_cmd_sync(self) -> None:
        self._append_system_message(run_async(self.backend.cmd_sync()))
        self._refresh_debug_panels()

    def _on_cmd_sapyc(self) -> None:
        cmd = self.sapyc_input.text().strip()
        if not cmd:
            return
        self._append_system_message(run_async(self.backend.cmd_sapyc(cmd)))
        self._refresh_debug_panels()

    # ------------------------------------------------------------------
    # デバッグパネル更新
    # ------------------------------------------------------------------

    def _refresh_debug_panels(self) -> None:
        state_path = self.git_repo_dir / "state.json"
        if state_path.exists():
            self.git_state_view.setPlainText(state_path.read_text(encoding="utf-8"))
        else:
            self.git_state_view.setPlainText("(state.json未作成)")

        keys = self.backend.r2_io.get_paths_with_prefix("") or []
        self.r2_table.setRowCount(len(keys))
        for row, key in enumerate(keys):
            size = self.backend.r2_io.get_s3obj_size(key)
            self.r2_table.setItem(row, 0, QTableWidgetItem(key))
            self.r2_table.setItem(row, 1, QTableWidgetItem(str(size)))

        self.event_log_view.setPlainText("\n".join(self.backend.event_log))

    # ------------------------------------------------------------------
    # 終了処理
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        # 要件: 削除操作(shutil.rmtree等)は一切行わない。パスをprintするのみ。
        print("=" * 60)
        print("エミュレータを終了します。以下は削除されていません:")
        print(f"  Git疑似リポジトリ(tmp) : {self.git_repo_dir}")
        print("  R2疑似ストレージ: メモリ内のみで保持していたため、アプリ終了とともに消えます"
              "(ディスクには何も残っていません)")
        print("=" * 60)
        super().closeEvent(event)


def run_app(backend: ShellArcEmulatorBackend, git_repo_dir: Path) -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(backend=backend, git_repo_dir=git_repo_dir)
    window.show()
    return app.exec()
