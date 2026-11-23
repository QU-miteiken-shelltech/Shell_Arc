#!/usr/bin/env python3
"""MSK debug table editor (Tk).

A small viewer/editor for one MSK Field: one row per container, one column per property.

    python msk_table_editor.py --root <dir that contains "msk/"> [--pkg-parent <dir that contains "shellarc_msk/">] [--field Main]

* --root       : data root. MSKUT_PathSolver.root_dir is replaced by this path *in this process only*
                 (the implementation's own hard-coded path is not touched). Without --root the
                 implementation's default root is used.
* --pkg-parent : directory that contains the `shellarc_msk` package (searched automatically
                 next to this script when omitted).

Behaviour (all through the implementation's own API):
* cells show the value of the address; "Show hex" shows the (shortened) address index instead,
  so that address equality can be eyeballed (same hex = same address).
* double-click a cell (not the id column) to edit it. Enter = write, Esc = cancel.
  The text becomes MSK_Address(type of the property, text) and is stored with write_entity.
  Properties that are not defined by the Field (overrides, marked with *) are written with do_override=True.
* Ref-typed properties use MSK_VersionedAdress. "Version +1" calls update_version() on the selected cell.
* Not supported on purpose: creating a container (a container exists only through its rows),
  writing null (write_entity rejects the null address: type mismatch), deleting anything (no such operation).
* Single-process tool: the implementation caches files in RAM, so do not run it next to another writer.
"""
import argparse
import re
import sys
import time
from pathlib import Path


# --------------------------------------------------------------------------- bootstrap
def bootstrap(root, pkg_parent):
    """Make `shellarc_msk` importable and (optionally) point MSKUT_PathSolver at `root`."""
    here = Path(__file__).resolve().parent
    if pkg_parent:
        sys.path.insert(0, str(Path(pkg_parent).expanduser().resolve()))
    else:
        for cand in (here, here.parent, here.parent.parent):
            if (cand / "shellarc_msk").is_dir():
                sys.path.insert(0, str(cand))
                break
    from shellarc_msk.mskut.path_solver import MSKUT_PathSolver

    if root:
        root_path = Path(root).expanduser().resolve()

        def _init(self):
            self.root_dir = root_path

        MSKUT_PathSolver.__init__ = _init
    cfg = MSKUT_PathSolver().mskfs_space
    # the implementation creates missing files on access: refuse to run on a wrong directory
    if not cfg.is_dir():
        raise SystemExit(f"'{cfg}' does not exist (is --root the directory that CONTAINS 'msk/'?)")
    return cfg


# --------------------------------------------------------------------------- model (no Tk)
def natural_key(text):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


class Column:
    def __init__(self, prop, type_name, is_override):
        self.prop = prop
        self.key = str(prop.prop_index)
        self.is_override = is_override
        self.label = f"{prop.prop_name}{'*' if is_override else ''} : {type_name}"


class MskTableModel:
    """One Field as a table. Cells are (value, address-index); absent/null = ("", NULL)."""

    def __init__(self, field_name):
        from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
        from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex

        self.NULL = str(MSK_HexIndex(value=None))
        self.field_name = field_name
        self.coll = MSK_ContainerCollection(field_name)
        self.columns = []
        self.rows = {}     # container id (str) -> {column key: (value, hex)}
        self.order = []    # container ids in file order

    # -- reading
    @staticmethod
    def _cells_of(container):
        cells = {}
        for e in container:
            value = e.address.value
            cells[str(e.prop.prop_index)] = ("" if value is None else value, str(e.address.adress_index))
        return cells

    def load(self):
        field_keys = set()
        self.columns = []
        for prop, typ in self.coll.field_ls:
            self.columns.append(Column(prop, typ.type_name, False))
            field_keys.add(str(prop.prop_index))
        self.rows, self.order = {}, []
        extra = {}
        for c in self.coll.container_iter():
            cid = str(c.container_index)
            self.rows[cid] = self._cells_of(c)
            self.order.append(cid)
            for e in c:
                k = str(e.prop.prop_index)
                if k not in field_keys and k not in extra:
                    extra[k] = Column(e.prop, e.prop.prop_type.type_name, True)
        self.columns.extend(extra.values())

    def refresh_row(self, cid):
        from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
        c = self.coll.request_container(MSK_HexIndex(value=cid))
        self.rows[cid] = self._cells_of(c)
        return self.rows[cid]

    def cell(self, cid, column):
        return self.rows[cid].get(column.key, ("", self.NULL))

    # -- writing
    @staticmethod
    def _address_class(column):
        from shellarc_msk.mskob.adress_obj import MSK_Address
        from shellarc_msk.mskob.versionedadress_obj import MSK_VersionedAdress
        return MSK_VersionedAdress if column.prop.prop_type.type_name == "Ref" else MSK_Address

    def write(self, cid, column, text):
        """Write `text` as the value of (cid, column). Returns the new (value, hex), or None if unchanged."""
        from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
        old_value, _ = self.cell(cid, column)
        if text == old_value:
            return None
        if text == "":
            raise ValueError("null cannot be written: write_entity rejects the null address (type mismatch)")
        address = self._address_class(column)(adress_type=column.prop.prop_type, adress_value=text)
        self.coll.write_entity(
            MSK_HexIndex(value=cid), column.prop, address, do_override=column.is_override
        )
        return self.refresh_row(cid)[column.key]

    # -- versions (Ref cells)
    def _versioned(self, cid, column):
        from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
        from shellarc_msk.mskob.versionedadress_obj import MSK_VersionedAdress
        value, hexidx = self.cell(cid, column)
        if hexidx == self.NULL:
            raise ValueError("the cell is null: no address, no version")
        if column.prop.prop_type.type_name != "Ref":
            raise ValueError("versions are only handled for Ref-typed properties")
        return MSK_VersionedAdress(adress_index=MSK_HexIndex(value=hexidx))

    def version(self, cid, column):
        return self._versioned(cid, column).version

    def bump_version(self, cid, column):
        return self._versioned(cid, column).update_version()


# --------------------------------------------------------------------------- UI (Tk)
def run_ui(field_name):
    import tkinter as tk
    from tkinter import messagebox, ttk
    from shellarc_msk.mskob.field_obj import MSK_Field

    class App(tk.Tk):
        def __init__(self, first_field):
            super().__init__()
            self.title("MSK table editor (debug)")
            self.geometry("1280x760")
            self.model = None
            self.columns = []            # Column objects shown in the tree (after the id column)
            self.sort_state = (None, False)
            self.sel = (None, None)      # (container id, column index)
            self.editor = None

            top = ttk.Frame(self)
            top.pack(fill="x", padx=6, pady=4)
            ttk.Label(top, text="Field").pack(side="left")
            self.field_var = tk.StringVar()
            self.field_box = ttk.Combobox(top, textvariable=self.field_var, state="readonly",
                                          values=MSK_Field.field_names(), width=14)
            self.field_box.pack(side="left", padx=4)
            self.field_box.bind("<<ComboboxSelected>>", lambda e: self.load_field(self.field_var.get()))
            ttk.Button(top, text="Reload", command=lambda: self.load_field(self.field_var.get())).pack(side="left")
            self.hex_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(top, text="Show hex", variable=self.hex_var, command=self.rebuild).pack(side="left", padx=8)
            ttk.Label(top, text="Filter").pack(side="left", padx=(12, 2))
            self.fcol_var = tk.StringVar(value="(all)")
            self.fcol_box = ttk.Combobox(top, textvariable=self.fcol_var, state="readonly", width=22)
            self.fcol_box.pack(side="left")
            self.fcol_box.bind("<<ComboboxSelected>>", lambda e: self.rebuild())
            self.ftext_var = tk.StringVar()
            self.ftext_var.trace_add("write", lambda *a: self.rebuild())
            ttk.Entry(top, textvariable=self.ftext_var, width=22).pack(side="left", padx=4)
            ttk.Button(top, text="Version +1", command=self.bump).pack(side="right")

            mid = ttk.Frame(self)
            mid.pack(fill="both", expand=True, padx=6)
            self.tree = ttk.Treeview(mid, show="headings", selectmode="browse")
            ys = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
            xs = ttk.Scrollbar(mid, orient="horizontal", command=self.tree.xview)
            self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
            ys.pack(side="right", fill="y")
            xs.pack(side="bottom", fill="x")
            self.tree.pack(fill="both", expand=True)
            self.tree.bind("<Button-1>", self.on_click, add="+")
            self.tree.bind("<Double-1>", self.on_double)

            self.status = tk.StringVar(value="")
            ttk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=6)
            self.log_text = tk.Text(self, height=7)
            self.log_text.pack(fill="x", padx=6, pady=(2, 6))

            self.field_var.set(first_field)
            self.load_field(first_field)

        # -- helpers
        def log(self, msg):
            self.log_text.insert("end", time.strftime("%H:%M:%S ") + msg + "\n")
            self.log_text.see("end")

        def show_text(self, cell):
            value, hexidx = cell
            if not self.hex_var.get():
                return value
            return "" if hexidx == self.model.NULL else hexidx[:10] + "…"

        def load_field(self, name):
            self.cancel_edit()
            self.status.set(f"loading {name} ...")
            self.update_idletasks()
            try:
                t0 = time.time()
                self.model = MskTableModel(name)
                self.model.load()
            except Exception as e:  # keep the UI alive: this is a debugging tool
                self.model = None
                messagebox.showerror("load failed", repr(e))
                self.log(f"load {name} FAILED: {e!r}")
                return
            self.columns = self.model.columns
            ids = ["id"] + [f"c{i}" for i in range(len(self.columns))]
            self.tree.configure(columns=ids)
            self.tree.heading("id", text="container id", command=lambda: self.sort_by(-1))
            self.tree.column("id", width=270, stretch=False)
            for i, col in enumerate(self.columns):
                self.tree.heading(f"c{i}", text=col.label, command=lambda i=i: self.sort_by(i))
                self.tree.column(f"c{i}", width=170, stretch=False)
            self.fcol_box.configure(values=["(all)"] + [c.label for c in self.columns])
            self.fcol_var.set("(all)")
            self.sort_state = (None, False)
            self.rebuild()
            self.log(f"loaded {name}: {len(self.model.order)} containers, {len(self.columns)} columns, "
                     f"{time.time() - t0:.1f}s")

        def visible_ids(self):
            ids = list(self.model.order)
            text = self.ftext_var.get().strip().lower()
            if text:
                label = self.fcol_var.get()
                idxs = [i for i, c in enumerate(self.columns) if label in ("(all)", c.label)]
                ids = [cid for cid in ids
                       if any(text in self.model.cell(cid, self.columns[i])[0].lower() for i in idxs)]
            col, rev = self.sort_state
            if col is not None:
                if col == -1:
                    ids.sort(key=lambda cid: cid, reverse=rev)
                else:
                    ids.sort(key=lambda cid: natural_key(self.model.cell(cid, self.columns[col])[0]), reverse=rev)
            return ids

        def row_values(self, cid):
            return [cid] + [self.show_text(self.model.cell(cid, c)) for c in self.columns]

        def rebuild(self):
            if self.model is None:
                return
            self.cancel_edit()
            self.tree.delete(*self.tree.get_children())
            ids = self.visible_ids()
            for cid in ids:
                self.tree.insert("", "end", iid=cid, values=self.row_values(cid))
            self.status.set(f"{self.model.field_name}: showing {len(ids)} / {len(self.model.order)} containers")

        def sort_by(self, col):
            prev, rev = self.sort_state
            self.sort_state = (col, (not rev) if prev == col else False)
            self.rebuild()

        # -- selection
        def cell_at(self, event):
            row = self.tree.identify_row(event.y)
            colid = self.tree.identify_column(event.x)   # "#1" = id column
            if not row or not colid:
                return None, None
            return row, int(colid[1:]) - 2               # -1 = id column, 0.. = property columns

        def on_click(self, event):
            self.cancel_edit()
            row, ci = self.cell_at(event)
            self.sel = (row, ci)
            if row is None:
                return
            if ci < 0:
                self.status.set(f"container {row}")
                return
            col = self.columns[ci]
            value, hexidx = self.model.cell(row, col)
            msg = f"{col.label} | value={value!r} | address={hexidx}"
            if col.prop.prop_type.type_name == "Ref" and hexidx != self.model.NULL:
                try:
                    msg += f" | version={self.model.version(row, col)}"
                except Exception as e:
                    msg += f" | version: error {e!r}"
            self.status.set(msg)

        # -- editing
        def cancel_edit(self):
            if self.editor is not None:
                self.editor.destroy()
                self.editor = None

        def on_double(self, event):
            row, ci = self.cell_at(event)
            if row is None or ci is None or ci < 0:
                return
            self.cancel_edit()
            col = self.columns[ci]
            bbox = self.tree.bbox(row, f"#{ci + 2}")
            if not bbox:
                return
            x, y, w, h = bbox
            entry = ttk.Entry(self.tree)
            entry.insert(0, self.model.cell(row, col)[0])
            entry.select_range(0, "end")
            entry.place(x=x, y=y, width=w, height=h)
            entry.focus_set()
            entry.bind("<Return>", lambda e: self.commit(row, ci, entry.get()))
            entry.bind("<Escape>", lambda e: self.cancel_edit())
            self.editor = entry

        def commit(self, row, ci, text):
            col = self.columns[ci]
            self.cancel_edit()
            try:
                new = self.model.write(row, col, text)
            except Exception as e:
                messagebox.showerror("write failed", str(e))
                self.log(f"write {row} {col.label} <- {text!r} FAILED: {e!r}")
                return
            if new is None:
                return
            self.tree.item(row, values=self.row_values(row))
            self.log(f"write_entity {row} {col.label} <- {text!r}  address={new[1]}")

        def bump(self):
            row, ci = self.sel
            if row is None or ci is None or ci < 0:
                messagebox.showinfo("Version +1", "select a Ref-typed cell first")
                return
            col = self.columns[ci]
            try:
                v = self.model.bump_version(row, col)
            except Exception as e:
                messagebox.showerror("version failed", str(e))
                self.log(f"update_version {row} {col.label} FAILED: {e!r}")
                return
            self.log(f"update_version {row} {col.label} -> {v}")
            self.status.set(f"{col.label} | version={v}")

    app = App(field_name)
    app.mainloop()


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="MSK debug table editor")
    ap.add_argument("--root", help='directory that contains "msk/" (default: the implementation\'s own root)')
    ap.add_argument("--pkg-parent", help='directory that contains "shellarc_msk/"')
    ap.add_argument("--field", help="Field to open first (default: the first Field)")
    args = ap.parse_args()
    bootstrap(args.root, args.pkg_parent)
    from shellarc_msk.mskob.field_obj import MSK_Field
    names = MSK_Field.field_names()
    if not names:
        raise SystemExit("no Field in this store")
    field = args.field or names[0]
    if field not in names:
        raise SystemExit(f"Field '{field}' not found; available: {names}")
    run_ui(field)


if __name__ == "__main__":
    main()
