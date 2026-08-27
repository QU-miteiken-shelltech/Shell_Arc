"""
疑似Discordのデータモデル(FakeMessage / FakeAttachment)を定義する。

【変更履歴】当初はここに MockGitIO / MockR2IO / MockSpreadsheetIO という
このエミュレータ専用の自己完結版Mockを実装していたが、「shellarc_core.process.*等の
中身を見せていないものはすでに仮想化されているのでそのまま使ってよい」という指示を受け、
emu_backend.py が mock_git_io.py / mock_r2_io.py / mock_spreadsheet_io.py
(shellarc_coreのio_git.py/io_r2.py/io_spreadsheet.py向けに前回作成したMock)を
直接使う構成に変更した。そのため、ここでは疑似Discordのデータモデルのみを残している。

- discord.py はimportしない(本物のゲートウェイに接続しようとする設計のため)。
  かわりに FakeMessage / FakeAttachment という最小限のデータクラスで代替する。
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 疑似Discordデータモデル
# ---------------------------------------------------------------------------

@dataclass
class FakeAttachment:
    filename: str
    data: bytes


@dataclass
class FakeMessage:
    author: str
    channel: str
    content: str
    attachments: list[FakeAttachment] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now().strftime("%H:%M:%S")
    )

