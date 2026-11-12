from __future__ import annotations

import builtins
import keyword
import re
from typing import Any

from PySide6.QtCore import QByteArray, QMimeData, QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor, QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent, QFontMetricsF,
    QKeyEvent, QMouseEvent, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import (
    QApplication, QGraphicsItem, QGraphicsRectItem, QGraphicsScene,
    QGraphicsSimpleTextItem, QGraphicsView, QInputDialog, QLabel, QMenu,
)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
PLACEHOLDER_RAW = "__CUSTOM__"   # replaced with the user's input as-is
PLACEHOLDER_STR = "__STRING__"   # replaced with the user's input as a Python string literal
_PLACEHOLDER_RE = re.compile(f"{PLACEHOLDER_STR}|{PLACEHOLDER_RAW}")

# MIME type used when an ExpressionBlockLabel is dragged onto the editor
LABEL_MIME = "application/x-expression-block-label"

BLOCK_H = 36.0
BLOCK_GAP = 0.0                  # blocks touch each other (joined look)
STEP = BLOCK_H + BLOCK_GAP       # height of one chain slot
CORNER_R = 6.0                   # corner radius of a block
TAB_X = 18.0                     # left edge of the joint tab/notch
TAB_W = 24.0                     # width of the joint tab/notch
TAB_H = 5.0                      # how far the tab sticks out below a block
MIN_BLOCK_W = 120.0
MAX_BLOCK_W = 360.0
H_PAD = 14.0

START_H = 30.0
CHAIN_X = 0.0                    # x position of the chain (scene coordinates)
CHAIN_TOP = START_H + BLOCK_GAP  # y position of the first block
SNAP_X = 90.0                    # max horizontal distance from the chain to snap
SNAP_Y = 60.0                    # max vertical distance beyond the chain ends to snap

INDENT = "    "

CATEGORY_COLORS = {
    "conditions": "#e67e22",
    "comparisons": "#27ae60",
    "operations": "#8e44ad",
    "custom": "#3498db",
    "data": "#16a085",           # DataBlock (created from an ExpressionBlockLabel)
}
CATEGORY_LABELS = {
    "conditions": "Conditions",
    "comparisons": "Comparisons",
    "operations": "Operations",
    "custom": "Input",
}


# --------------------------------------------------------------------------
# Pure helpers (no Qt dependency)
# --------------------------------------------------------------------------
def generate_python(tokens: list[tuple[str, str]]) -> str:
    """Turn (category, code) tokens, top to bottom, into Python source.

    - Tokens are joined with spaces into a single line.
    - "if" / "elif" / "else:" always start a new line.
    - ":" ("then") ends the line; the following lines are indented one level.
    - An empty block body gets a `pass`.
    - "if" resets the indentation to 0; "elif" / "else:" go back one level
      (nested blocks are not supported).
    """
    lines: list[str] = []
    parts: list[str] = []
    line_level = 0       # indentation of the line being built
    level = 0            # indentation of the next line
    need_body = False    # right after ":" and no body line yet

    def flush() -> None:
        nonlocal parts
        if parts:
            lines.append(INDENT * line_level + " ".join(parts))
            parts = []

    def close_empty_body() -> None:
        nonlocal need_body
        if need_body:
            lines.append(INDENT * level + "pass")
            need_body = False

    for category, text in tokens:
        text = text.strip()
        if not text:
            continue

        if category == "conditions" and text in ("if", "elif", "else:"):
            flush()
            close_empty_body()
            level = 0 if text == "if" else max(level - 1, 0)
            line_level = level
            if text == "else:":
                lines.append(INDENT * level + "else:")
                level += 1
                need_body = True
            else:
                parts = [text]
            continue

        if category == "conditions" and text == ":":
            if parts:
                parts[-1] += ":"
            else:
                parts = [":"]
            flush()
            level = line_level + 1
            need_body = True
            continue

        if not parts:            # first token of a new line
            line_level = level
            need_body = False
        parts.append(text)

    flush()
    close_empty_body()
    return "\n".join(lines)


def to_identifier(name: str) -> str:
    """Convert an arbitrary string into a safe Python identifier."""
    ident = re.sub(r"\W", "_", name.strip())
    if not ident:
        ident = "obj"
    if ident[0].isdigit():
        ident = "_" + ident
    if not ident.isidentifier():
        ident = "obj"
    # Never shadow keywords or builtins (e.g. a property named "print")
    if keyword.iskeyword(ident) or hasattr(builtins, ident):
        ident += "_"
    return ident


def make_unique_identifier(name: str, data: Any, used: dict[str, Any]) -> str:
    """Return an identifier for `data` that does not clash with a different object.

    `used` maps identifiers already in the scene to their objects. The same object
    always gets the same identifier; a different object with the same name gets
    a numeric suffix (name_2, name_3, ...).
    """
    base = to_identifier(name)
    candidate, n = base, 2
    while candidate in used and used[candidate] is not data:
        candidate = f"{base}_{n}"
        n += 1
    return candidate


# --------------------------------------------------------------------------
# ExpressionBlockLabel: a widget that carries a Python object
# --------------------------------------------------------------------------
class ExpressionBlockLabel(QLabel):
    """A label holding an arbitrary Python object in `data`.

    It cannot be spawned from the editor's context menu. Place it in your own
    layout and drag it onto a BlockyExpressionEditor: that creates a DataBlock
    which refers to `data` by identifier in the generated code. The matching
    objects are returned by BlockyExpressionEditor.get_namespace().

    `name` is the identifier suggested for the object in the generated code
    (it is sanitized and made unique by the editor).
    """

    def __init__(self,
                 text: str,
                 data: Any,
                 parent=None,
                 *,
                 name: str | None = None
                 ):
        super().__init__(text=text, parent=parent)
        self.setStyleSheet(
            "QLabel {"
            "   background-color: #16a085;"
            "   color: white;"
            "   border-radius: 6px;"
            "   padding: 10px;"
            "   font-size: 14px;"
            "}"
        )
        self.data = data
        self.block_name = name if name else "obj"
        self.adjustSize()
        self._drag_start: QPoint | None = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_start is not None:
            moved = (event.position().toPoint() - self._drag_start).manhattanLength()
            if moved >= QApplication.startDragDistance():
                hot_spot = self._drag_start
                self._drag_start = None
                self._start_drag(hot_spot)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def _start_drag(self, hot_spot: QPoint) -> None:
        drag = QDrag(self)
        mime = QMimeData()
        # The payload is only a marker; the editor reads the label via event.source()
        mime.setData(LABEL_MIME, QByteArray(self.block_name.encode("utf-8")))
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(hot_spot)
        drag.exec(Qt.DropAction.CopyAction)


# --------------------------------------------------------------------------
# Graphics items
# --------------------------------------------------------------------------
def block_outline(width: float, height: float,
                  top_notch: bool = True, bottom_tab: bool = True) -> QPainterPath:
    """Outline of a block: a notch cut into the top edge, a tab on the bottom edge.

    The tab of one block fits exactly into the notch of the block below it,
    so chained blocks look joined without any gap. The tab sticks out TAB_H
    below `height`.
    """
    w, h, r = width, height, CORNER_R
    x0, x1 = TAB_X, TAB_X + TAB_W
    path = QPainterPath()
    path.moveTo(r, 0)
    if top_notch:
        path.lineTo(x0, 0)
        path.lineTo(x0 + 2, TAB_H)
        path.lineTo(x1 - 2, TAB_H)
        path.lineTo(x1, 0)
    path.lineTo(w - r, 0)
    path.arcTo(QRectF(w - 2 * r, 0, 2 * r, 2 * r), 90, -90)          # top-right corner
    path.lineTo(w, h - r)
    path.arcTo(QRectF(w - 2 * r, h - 2 * r, 2 * r, 2 * r), 0, -90)   # bottom-right corner
    if bottom_tab:
        path.lineTo(x1, h)
        path.lineTo(x1 - 2, h + TAB_H)
        path.lineTo(x0 + 2, h + TAB_H)
        path.lineTo(x0, h)
    path.lineTo(r, h)
    path.arcTo(QRectF(0, h - 2 * r, 2 * r, 2 * r), 270, -90)         # bottom-left corner
    path.lineTo(0, r)
    path.arcTo(QRectF(0, 0, 2 * r, 2 * r), 180, -90)                 # top-left corner
    path.closeSubpath()
    return path


class StartMarker(QGraphicsRectItem):
    """Start of the chain. Not movable."""

    def __init__(self):
        super().__init__(0, 0, MIN_BLOCK_W, START_H)
        self.setPos(CHAIN_X, 0)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        label = QGraphicsSimpleTextItem("▶ START", self)
        label.setBrush(QColor("white"))
        label.setPos(12, (START_H - label.boundingRect().height()) / 2)

    def boundingRect(self) -> QRectF:
        return self.rect().adjusted(0, 0, 0, TAB_H)      # include the bottom tab

    def shape(self) -> QPainterPath:
        return block_outline(self.rect().width(), START_H, top_notch=False)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#34495e"))
        painter.drawPath(self.shape())


class ExpressionBlock(QGraphicsRectItem):
    def __init__(self, display: str, expr: str, category: str = "operations",
                 parent=None):
        super().__init__(parent)
        self.display = display
        self.expression_strip = expr      # code fragment (may contain placeholders)
        self.category = category
        self.input_text = ""              # text typed into an input block
        self.in_chain = False             # whether the block is attached to the chain
        self._press_pos = QPointF()
        self._dragged = False

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(1)

        self.title = QGraphicsSimpleTextItem(self)
        font = self.title.font()
        font.setPointSize(10)
        self.title.setFont(font)
        self.title.setBrush(QColor("white"))
        # Let clicks go straight to the block instead of the text child
        self.title.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.set_in_chain(False)
        self.refresh()

    # ---- content --------------------------------------------------------
    @property
    def editable(self) -> bool:
        return PLACEHOLDER_RAW in self.expression_strip or PLACEHOLDER_STR in self.expression_strip

    def code_text(self) -> str:
        """The Python code fragment this block emits."""
        def repl(m: re.Match) -> str:
            return repr(self.input_text) if m.group() == PLACEHOLDER_STR else self.input_text
        return _PLACEHOLDER_RE.sub(repl, self.expression_strip)

    def refresh(self) -> None:
        """Update the displayed text and the block width."""
        text = self.display
        if self.editable:
            text = f"{self.display}: {self.input_text if self.input_text else '…'}"
        metrics = QFontMetricsF(self.title.font())
        max_text_w = MAX_BLOCK_W - 2 * H_PAD
        text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_text_w)
        self.title.setText(text)
        width = max(MIN_BLOCK_W, metrics.horizontalAdvance(text) + 2 * H_PAD)
        self.setRect(0, 0, width, BLOCK_H)
        self.title.setPos(H_PAD, (BLOCK_H - self.title.boundingRect().height()) / 2)
        self.update()

    def set_in_chain(self, value: bool) -> None:
        self.in_chain = value
        self.setOpacity(1.0 if value else 0.7)   # detached blocks are drawn dimmed
        self.update()

    # ---- painting -------------------------------------------------------
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(CATEGORY_COLORS.get(self.category, "#7f8c8d"))
        if self.isSelected():
            pen = QPen(QColor("#f1c40f"), 3)
        elif not self.in_chain:
            pen = QPen(color.darker(140), 1.5, Qt.PenStyle.DashLine)
        else:
            pen = QPen(color.darker(140), 1.5)
        painter.setPen(pen)
        painter.setBrush(color)
        painter.drawPath(self.shape())

    def boundingRect(self) -> QRectF:
        # Room for the bottom tab and for the selection outline
        return self.rect().adjusted(-2, -2, 2, TAB_H + 2)

    def shape(self) -> QPainterPath:
        return block_outline(self.rect().width(), self.rect().height())

    # ---- keep the block inside the scene rect ---------------------------
    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
                and self.scene() is not None):
            area = self.scene().sceneRect()
            x = min(max(value.x(), area.left()), area.right() - self.rect().width())
            y = min(max(value.y(), area.top()), area.bottom() - self.rect().height())
            return QPointF(x, y)
        return super().itemChange(change, value)

    # ---- mouse handling -------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.scene() is not None:
                self.scene().clearSelection()      # only one block is selected at a time
            self._press_pos = self.pos()
            self._dragged = False
            self.setZValue(100)                    # keep the dragged block on top
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if (event.buttons() & Qt.MouseButton.LeftButton
                and self.pos() != self._press_pos
                and isinstance(self.scene(), BlockExpressionScene)):
            self._dragged = True
            self.scene().on_block_dragged(self)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.setZValue(1)
            if self._dragged and isinstance(self.scene(), BlockExpressionScene):
                self._dragged = False
                self.scene().on_block_dropped(self)

    def mouseDoubleClickEvent(self, event):
        if self.editable and isinstance(self.scene(), BlockExpressionScene):
            self.scene().edit_block(self)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class DataBlock(ExpressionBlock):
    """A graph block that stands for a Python object (from an ExpressionBlockLabel).

    It emits `identifier` into the generated code; `data` is the real object,
    available through BlockyExpressionEditor.get_namespace().
    """

    def __init__(self, identifier: str, data: Any, parent=None):
        super().__init__(display=identifier, expr=identifier, category="data", parent=parent)
        self.identifier = identifier
        self.data = data

    @property
    def editable(self) -> bool:
        return False        # never takes typed input

    def code_text(self) -> str:
        return self.identifier


# --------------------------------------------------------------------------
# Scene (owns the chain)
# --------------------------------------------------------------------------
class BlockExpressionScene(QGraphicsScene):
    chainChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(QRectF(-40, -40, 1400, 4000))
        self.chain: list[ExpressionBlock] = []

        self._start = StartMarker()
        self.addItem(self._start)

        self._hint = QGraphicsSimpleTextItem(
            "Right-click to add blocks\nDrag blocks under START to chain them"
        )
        self._hint.setBrush(QColor("#95a5a6"))
        self._hint.setPos(CHAIN_X + 8, CHAIN_TOP + 8)
        self._hint.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.addItem(self._hint)

        # Yellow bar showing where a dragged block will be inserted
        self._indicator = QGraphicsRectItem(0, 0, 220, 4)
        self._indicator.setBrush(QColor("#f1c40f"))
        self._indicator.setPen(QPen(Qt.PenStyle.NoPen))
        self._indicator.setZValue(50)
        self._indicator.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._indicator.hide()
        self.addItem(self._indicator)

    # ---- geometry -------------------------------------------------------
    @staticmethod
    def slot_pos(index: int) -> QPointF:
        return QPointF(CHAIN_X, CHAIN_TOP + index * STEP)

    def _insert_index_for(self, block: ExpressionBlock) -> int | None:
        """Insertion index for the block's current position, or None if too far."""
        pos = block.pos()
        n = len(self.chain)
        if abs(pos.x() - CHAIN_X) > SNAP_X:
            return None
        bottom = CHAIN_TOP + n * STEP
        if pos.y() < CHAIN_TOP - SNAP_Y or pos.y() > bottom + SNAP_Y:
            return None
        index = round((pos.y() - CHAIN_TOP) / STEP)
        return max(0, min(n, index))

    def _show_indicator(self, index: int | None) -> None:
        if index is None:
            self._indicator.hide()
            return
        y = CHAIN_TOP + index * STEP - BLOCK_GAP / 2 - self._indicator.rect().height() / 2
        self._indicator.setPos(CHAIN_X - 10, y)
        self._indicator.show()

    def _relayout(self) -> None:
        for i, block in enumerate(self.chain):
            block.setPos(self.slot_pos(i))
        self._hint.setVisible(not self.chain)
        # Grow the scene downward when the chain gets long
        needed = CHAIN_TOP + len(self.chain) * STEP + 300
        rect = self.sceneRect()
        if needed > rect.bottom():
            rect.setBottom(needed)
            self.setSceneRect(rect)

    # ---- block operations -----------------------------------------------
    def add_block(self, display: str, data: str, pos: QPointF,
                  category: str = "operations", input_text: str = "") -> ExpressionBlock:
        block = ExpressionBlock(display=display, expr=data, category=category)
        block.input_text = input_text
        block.refresh()
        self.addItem(block)
        block.setPos(pos)
        self.on_block_dropped(block)    # same snapping rule as a drag-and-drop
        return block

    def add_data_block(self, name: str, data: Any, pos: QPointF | None = None) -> DataBlock:
        """Add a DataBlock for `data`. With pos=None it is appended to the chain."""
        used = {b.identifier: b.data for b in self.items() if isinstance(b, DataBlock)}
        block = DataBlock(make_unique_identifier(name, data, used), data)
        self.addItem(block)
        if pos is None:
            block.setPos(self.slot_pos(len(self.chain)))
            self.append_to_chain(block)
        else:
            block.setPos(pos)
            self.on_block_dropped(block)
        return block

    def remove_block(self, block: ExpressionBlock) -> None:
        if block in self.chain:
            self.chain.remove(block)
        self.removeItem(block)
        self._relayout()
        self.chainChanged.emit()

    def append_to_chain(self, block: ExpressionBlock) -> None:
        if block not in self.chain:
            self.chain.append(block)
            block.set_in_chain(True)
            self._relayout()
            self.chainChanged.emit()

    def clear_blocks(self) -> None:
        for item in list(self.items()):
            if isinstance(item, ExpressionBlock):
                self.removeItem(item)
        self.chain.clear()
        self._indicator.hide()
        self._relayout()
        self.chainChanged.emit()

    def ask_input(self, display: str, current: str = "") -> tuple[bool, str]:
        parent = self.views()[0] if self.views() else None
        text, ok = QInputDialog.getText(
            parent, "Block input", f'Content for "{display}":', text=current)
        return ok, text

    def edit_block(self, block: ExpressionBlock) -> None:
        ok, text = self.ask_input(block.display, block.input_text)
        if ok:
            block.input_text = text
            block.refresh()
            self._relayout()
            self.chainChanged.emit()

    # ---- drag and drop --------------------------------------------------
    def on_block_dragged(self, block: ExpressionBlock) -> None:
        """While dragging: detach from the chain and show the insertion marker."""
        if block in self.chain:
            self.chain.remove(block)
            block.set_in_chain(False)
            self._relayout()
            self.chainChanged.emit()
        self._show_indicator(self._insert_index_for(block))

    def on_block_dropped(self, block: ExpressionBlock) -> None:
        """On drop: insert into the chain if close enough, else leave detached."""
        if block in self.chain:
            self.chain.remove(block)
        index = self._insert_index_for(block)
        self._indicator.hide()
        if index is None:
            block.set_in_chain(False)
        else:
            self.chain.insert(index, block)
            block.set_in_chain(True)
        self._relayout()
        self.chainChanged.emit()

    # ---- for code generation --------------------------------------------
    def chain_tokens(self) -> list[tuple[str, str]]:
        return [(b.category, b.code_text()) for b in self.chain]

    def chain_namespace(self) -> dict[str, Any]:
        """identifier -> object for every DataBlock that is part of the chain."""
        return {b.identifier: b.data for b in self.chain if isinstance(b, DataBlock)}


# --------------------------------------------------------------------------
# View (the editor widget)
# --------------------------------------------------------------------------
class BlockyExpressionEditor(QGraphicsView):
    codeChanged = Signal(str)

    allowed_operators = {
        "conditions": {
            "if": "if",
            "else if": "elif",
            "else": "else:",
            "then": ":",
        },
        "comparisons": {
            "and": "and",
            "or": "or",
            "equal": "==",
            "not equal": "!=",
            "greater than": ">",
            "greater than or equal to": ">=",
            "less than": "<",
            "less than or equal to": "<=",
        },
        # Set with set_operations(). A value containing __CUSTOM__ / __STRING__
        # gets an input field on the block.
        "operations": {},
        "custom": {
            "string": PLACEHOLDER_STR,   # typed text is emitted as 'text'
            "value": PLACEHOLDER_RAW,    # typed text is emitted as-is (numbers, names...)
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 400)
        # Per-instance copy so instances do not share (or mutate) the class dict
        self.allowed_operators = {
            k: dict(v) for k, v in type(self).allowed_operators.items()
        }
        self._scene = BlockExpressionScene(self)
        self.setScene(self._scene)
        self._scene.chainChanged.connect(self._on_chain_changed)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setAcceptDrops(True)       # accept ExpressionBlockLabel drops
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.build_context_menu)

    # ---- public API -----------------------------------------------------
    def set_operations(self, operations: dict):
        self.allowed_operators["operations"] = operations

    def get_intepreted_python(self) -> str:
        return generate_python(self._scene.chain_tokens())

    def get_namespace(self) -> dict[str, Any]:
        """Objects referenced by the generated code, keyed by identifier.

        Merge this with your own names before running the code, e.g.
        exec(code, {"node_widget": node_widget, **editor.get_namespace()}).
        """
        return self._scene.chain_namespace()

    def add_data_block(self, name: str, data: Any, pos: QPointF | None = None) -> DataBlock:
        """Add a block for `data` programmatically (appended to the chain if pos is None)."""
        return self._scene.add_data_block(name, data, pos)

    def clear(self) -> None:
        self._scene.clear_blocks()

    # ---- internals ------------------------------------------------------
    def _on_chain_changed(self) -> None:
        self.codeChanged.emit(self.get_intepreted_python())

    def _block_at(self, view_pos) -> ExpressionBlock | None:
        item = self.itemAt(view_pos)
        while item is not None and not isinstance(item, ExpressionBlock):
            item = item.parentItem()
        return item

    def build_context_menu(self, position):
        # `position` is in viewport coordinates, which is also what mapToScene expects
        scene_pos = self.mapToScene(position)
        menu = QMenu(self)

        block = self._block_at(position)
        if block is not None:
            block.setSelected(True)
            if block.editable:
                act = menu.addAction("Edit content...")
                act.triggered.connect(lambda checked=False, b=block: self._scene.edit_block(b))
            if not block.in_chain:
                act = menu.addAction("Add to end of chain")
                act.triggered.connect(lambda checked=False, b=block: self._scene.append_to_chain(b))
            act = menu.addAction("Delete")
            act.triggered.connect(lambda checked=False, b=block: self._scene.remove_block(b))
        else:
            # Only allowed_operators can be spawned here; DataBlocks never appear
            for category, operators in self.allowed_operators.items():
                if not operators:
                    continue
                sub = menu.addMenu(CATEGORY_LABELS.get(category, category))
                for name, code in operators.items():
                    act = sub.addAction(name)
                    act.triggered.connect(
                        lambda checked=False, n=name, c=code, cat=category, p=scene_pos:
                        self.spawn_block(n, c, cat, p)
                    )

        menu.exec(self.viewport().mapToGlobal(position))

    def spawn_block(self, name: str, code: str, category: str, spawn_pos: QPointF):
        input_text = ""
        if PLACEHOLDER_RAW in code or PLACEHOLDER_STR in code:
            ok, input_text = self._scene.ask_input(name)
            if not ok:          # cancelled: do not create the block
                return
        self._scene.add_block(display=name, data=code, pos=spawn_pos,
                              category=category, input_text=input_text)

    # ---- ExpressionBlockLabel drops -------------------------------------
    @staticmethod
    def _label_from_drop(event) -> ExpressionBlockLabel | None:
        source = event.source()
        if isinstance(source, ExpressionBlockLabel) and event.mimeData().hasFormat(LABEL_MIME):
            return source
        return None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._label_from_drop(event) is not None:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if self._label_from_drop(event) is not None:
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        label = self._label_from_drop(event)
        if label is None:
            super().dropEvent(event)
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        self._scene.add_data_block(label.block_name, label.data, scene_pos)
        event.acceptProposedAction()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in self._scene.selectedItems():
                if isinstance(item, ExpressionBlock):
                    self._scene.remove_block(item)
            event.accept()
            return
        super().keyPressEvent(event)