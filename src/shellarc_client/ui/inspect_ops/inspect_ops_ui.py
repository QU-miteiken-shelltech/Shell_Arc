from __future__ import annotations

import struct
from itertools import islice
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QLabel, QListWidget, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

MAX_LINES = 20000   # a QLabel with a huge text freezes the UI; longer files are cut with a notice
PAGE_SLOTS = 120000  # slots per page of '.msk_adress_offset' (8 bytes each)


def _hex(b: bytes) -> str:
    return "0x" + b.hex()


def _text(b: bytes) -> str:
    # keep one record on one line: escape line breaks inside values
    return b.decode("utf-8", errors="replace").replace("\r", "\\r").replace("\n", "\\n")


def _fixed_rows(raw: bytes, size: int) -> list[list[str]]:
    """Cut `raw` into rows of `size` bytes; every 16 bytes is one hex element."""
    rows = []
    for i in range(0, len(raw), size):
        row = raw[i:i + size]
        rows.append([_hex(row[j:j + 16]) for j in range(0, len(row), 16)])
    return rows


def _u64_list(raw: bytes) -> list[int]:
    return [v[0] for v in struct.iter_unpack("<Q", raw[:len(raw) // 8 * 8])]


def _records_by_offsets(raw: bytes, offsets_raw: bytes) -> list[bytes]:
    """Variable-length records; '<name>_offset' holds the start offset (u64) of every record."""
    starts = _u64_list(offsets_raw)
    ends = starts[1:] + [len(raw)]
    return [raw[s:e] for s, e in zip(starts, ends)]


def _parse_container(raw: bytes, _off: bytes | None) -> list[list[str]]:
    return _fixed_rows(raw, 48)           # container id, property, address


def _parse_type(raw: bytes, off: bytes | None) -> list[list[str]]:
    rows = []
    for rec in _records_by_offsets(raw, off or b""):
        index, (n,) = rec[:16], struct.unpack("<Q", rec[16:24])
        name, lits = rec[24:24 + n], rec[24 + n:]
        rows.append([_hex(index), _text(name)] + [_hex(lits[j:j + 16]) for j in range(0, len(lits), 16)])
    return rows                           # index, name, literal address indices...


def _parse_property(raw: bytes, off: bytes | None) -> list[list[str]]:
    return [[_hex(r[:16]), _hex(r[16:32]), _text(r[32:])]
            for r in _records_by_offsets(raw, off or b"")]   # property, type, name


def _parse_field(raw: bytes, off: bytes | None) -> list[list[str]]:
    rows = []
    for rec in _records_by_offsets(raw, off or b""):
        (n,) = struct.unpack("<Q", rec[:8])
        defs = rec[8 + n:]
        rows.append([_text(rec[8:8 + n])] +
                    [_hex(defs[j:j + 16]) for j in range(0, len(defs), 16)])
    return rows                           # name, (property, type) pairs...


def _parse_adress(raw: bytes, _off: bytes | None) -> list[list[str]]:
    rows, pos = [], 0
    while pos + 40 <= len(raw):           # index 16 + type 16 + value length 8 + value
        (n,) = struct.unpack("<Q", raw[pos + 32:pos + 40])
        rows.append([_hex(raw[pos:pos + 16]), _hex(raw[pos + 16:pos + 32]), _text(raw[pos + 40:pos + 40 + n])])
        pos += 40 + n
    return rows                           # index, type, value


def _parse_adress_offset(raw: bytes, _off: bytes | None) -> list[list[str]]:
    rows = []
    for p in range(len(raw) // (PAGE_SLOTS * 8)):
        vals = _u64_list(raw[p * PAGE_SLOTS * 8:(p + 1) * PAGE_SLOTS * 8])
        rows.append([f"page{p}", f"filled={vals[0]}"])
        rows += [[f"slot{s}", f"record_offset={v - 1}"] for s, v in enumerate(vals) if s and v]
    return rows                           # only occupied slots are listed


def _parse_offsets(raw: bytes, _off: bytes | None) -> list[list[str]]:
    return [[str(v)] for v in _u64_list(raw)]


def _parse_unknown(raw: bytes, _off: bytes | None) -> list[list[str]]:
    return _fixed_rows(raw, 16)


def decode_msk_file(path: Path) -> str:
    """Readable text of one MSK binary file: elements split by a space, items by a line break."""
    raw = path.read_bytes()
    name = path.name
    off_path = path.with_name(name + "_offset")
    off = off_path.read_bytes() if off_path.exists() else None

    if name.startswith(".msk_container_"):
        parser = _parse_container
    elif name == ".msk_adress_offset":
        parser = _parse_adress_offset
    elif name.endswith("_offset"):
        parser = _parse_offsets
    else:
        parser = {".msk_type": _parse_type, ".msk_property": _parse_property,
                  ".msk_field": _parse_field, ".msk_adress": _parse_adress}.get(name, _parse_unknown)
    try:
        rows = parser(raw, off)
    except (struct.error, ValueError):    # unexpected layout: fall back to a plain hex view
        rows = _parse_unknown(raw, None)

    lines = [" ".join(r) for r in rows]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"... ({len(lines) - MAX_LINES} more lines not shown)"]
    return "\n".join(lines)


CONTAINER_PREFIX = ".msk_container_"


def interpret_container(field_name: str) -> str:
    """Container file read through the MSK objects: '<container id> <property name> <address value>'.
    A null address (absent value) is shown as 'null'."""
    from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

    coll = MSK_ContainerCollection(field_name)
    total = len(coll.container_bin) // 48
    lines = []
    for entity in islice(coll.entities_iter(), MAX_LINES):   # build objects only for the lines shown
        value = entity.address.value
        lines.append(f"{entity.container_index} {entity.prop.prop_name} {'null' if value is None else value}")
    if total > MAX_LINES:
        lines.append(f"... ({total - MAX_LINES} more lines not shown)")
    return "\n".join(lines)


def list_msk_files(space_dir: Path) -> list[Path]:
    return sorted(p for p in space_dir.glob(".msk_*") if p.is_file())


# ----------------------------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------------------------
class _FilePickerDialog(QDialog):
    """Lists the MSK binary files; a double-click selects one and closes the dialog."""

    def __init__(self, files: list[Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select an MSK binary file")
        self.selected: Path | None = None
        self._list = QListWidget()
        for f in files:
            self._list.addItem(f.name)
        self._list.itemDoubleClicked.connect(self._on_double_clicked)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        self._files = files

    def _on_double_clicked(self, _item) -> None:
        self.selected = self._files[self._list.currentRow()]
        self.accept()


class InspectOpsUi(QWidget):
    def __init__(self, space_dir: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MSK Inspect")
        if space_dir is None:     # default: the folder the implementation itself uses
            from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
            space_dir = MSKUT_PathSolver().mskfs_space
        self._space_dir = Path(space_dir)

        self._current: Path | None = None   # the file shown now (re-rendered when the toggle changes)

        self._button = QPushButton("Inspect...")
        self._button.clicked.connect(self._open_picker)

        self._interpret = QCheckBox("Interpret as MSK objects (unchecked: plain ASCII)")
        self._interpret.toggled.connect(self._render)

        self._display = QLabel("")
        self._display.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self._display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        scroll = QScrollArea()          # the label can be large: let it scroll
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._display)

        layout = QVBoxLayout(self)
        layout.addWidget(self._interpret)
        layout.addWidget(self._button)
        layout.addWidget(scroll, 1)
        self.resize(900, 600)

    def _open_picker(self) -> None:
        # the list is read every time, so it always shows the files that exist now
        dialog = _FilePickerDialog(list_msk_files(self._space_dir), self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected is not None:
            self._current = dialog.selected
            self._render()

    def _render(self, *_args) -> None:
        if self._current is None:
            return
        self._display.setText("")       # clear the previous inspection first
        path = self._current
        if self._interpret.isChecked() and path.name.startswith(CONTAINER_PREFIX):
            try:
                text = interpret_container(path.name[len(CONTAINER_PREFIX):])
            except Exception as e:      # e.g. shellarc_msk not importable or its root_dir points elsewhere
                text = f"MSK interpretation failed: {type(e).__name__}: {e}"
        else:
            text = decode_msk_file(path)
        self._display.setText(text)