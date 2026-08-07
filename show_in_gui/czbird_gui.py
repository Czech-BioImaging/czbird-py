"""czbird_gui.py — a plain, sequential PySide6 editor for CZBIRD records.

Option-B (buffer-then-validate): each modal dialog edits one strict object; the
widgets buffer edits and only on Apply/OK is the object rebuilt & validated (any
pydantic ValidationError is shown). Cancel discards. The app starts from a
prefilled, valid record so every dialog has content to click through.

This revision matches the cleanup-branch model:
  * no internal_id anywhere (the registry / copy / "Fill from…" feature is gone);
  * CZBIRDTool.tool_description is polymorphic -> a variant picker + nested edit;
  * employs_tool and the sinks are lists with the usual +Add / -remove.
"""
from __future__ import annotations

import sys
from typing import Any, Optional, Union, get_args, get_origin
import types

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QScrollArea, QPlainTextEdit, QMessageBox,
    QMainWindow, QComboBox,
)
from pydantic import BaseModel, ValidationError

from czbird import czbird_model as M
from czbird import czbird_prefill as P


# --------------------------------------------------------------------------- #
# Field classification by introspection
# --------------------------------------------------------------------------- #
_CZBIRD = {n: c for n, c in vars(M).items()
           if isinstance(c, type) and issubclass(c, BaseModel)
           and c.__module__ == M.__name__ and n != "_Base"}


def classify(ann: Any):
    """Return (kind, detail):
      ("scalar", pytype) | ("literal", [values]) |
      ("czbird", cls) | ("list_czbird", item_cls) | ("list_scalar", "str") |
      ("poly", [member classes])
    """
    from typing import Literal
    o = get_origin(ann)
    if o in (types.UnionType, Union):
        args = [a for a in get_args(ann) if a is not type(None)]
        members = [a for a in args if isinstance(a, type) and a in _CZBIRD.values()]
        if members:
            return "poly", members
        return classify(args[0]) if args else ("scalar", str)
    if o is Literal:
        return "literal", list(get_args(ann))
    if o in (list, tuple):
        (item,) = get_args(ann)
        if isinstance(item, type) and item in _CZBIRD.values():
            return "list_czbird", item
        return "list_scalar", getattr(item, "__name__", "str")
    if isinstance(ann, type) and ann in _CZBIRD.values():
        return "czbird", ann
    if isinstance(ann, type):
        return "scalar", ann.__name__
    return "scalar", "str"


def human(name: str) -> str:
    return name.replace("_", " ").capitalize()


def short(cls_name: str) -> str:
    return cls_name.replace("CZBIRD", "")


def _min_items(finfo) -> int:
    for m in getattr(finfo, "metadata", ()):
        ml = getattr(m, "min_length", None)
        if ml is not None:
            return ml
    return 0


def czbird_summary(obj: BaseModel) -> str:
    cls = type(obj).__name__
    if cls == "CZBIRDOntologyTerm":
        return f"OntoTerm: {getattr(obj, 'term_label', '') or '—'}"
    for key in ("title", "step_label", "internal_record_title",
                "data_path", "images_path", "url"):
        v = getattr(obj, key, None)
        if isinstance(v, str) and v:
            return f"{short(cls)}: {v}"
    return short(cls)


# --------------------------------------------------------------------------- #
# The generic editor dialog
# --------------------------------------------------------------------------- #
class CzbirdDialog(QDialog):
    """Modal editor for one strict CZBIRD object (option-B commit)."""

    def __init__(self, obj: BaseModel, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.setWindowTitle(f"Edit {short(type(obj).__name__)}")
        self.setMinimumWidth(560)

        self._scalar_getters: dict[str, callable] = {}
        self._list_scalar_widgets: dict[str, QPlainTextEdit] = {}
        self._czbird_values: dict[str, BaseModel] = {}
        self._list_czbird_values: dict[str, list] = {}
        self._poly_getters: dict[str, callable] = {}

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        self.form = QFormLayout(holder)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(holder)
        outer.addWidget(scroll, 1)

        self._build_fields()

        self._status = QLabel("")
        self._status.setWordWrap(True)
        outer.addWidget(self._status)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        for label, slot in (("Apply", self._on_apply),
                            ("OK", self._on_ok),
                            ("Cancel", self.reject)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        outer.addLayout(btn_row)

    def _set_status(self, text: str, ok: bool = True) -> None:
        self._status.setText(text)
        self._status.setStyleSheet(
            "color:#2e7d32;" if ok else "color:#c62828;")

    # ---- build -------------------------------------------------------- #
    def _build_fields(self):
        for name, finfo in type(self.obj).model_fields.items():
            kind, detail = classify(finfo.annotation)
            value = getattr(self.obj, name)
            if kind == "literal":
                self._add_readonly(name, value)
            elif kind == "scalar":
                self._add_scalar(name, detail, value)
            elif kind == "list_scalar":
                self._add_list_scalar(name, value)
            elif kind == "czbird":
                self._add_single_czbird(name, value)
            elif kind == "poly":
                self._add_poly(name, detail, value)
            elif kind == "list_czbird":
                self._add_list_czbird(name, detail, value, _min_items(finfo))

    def _add_readonly(self, name, value):
        lbl = QLabel(str(value))
        lbl.setStyleSheet("color: gray; font-style: italic;")
        nlbl = QLabel(f"{human(name)}:")
        nlbl.setStyleSheet("color: gray; font-style: italic;")
        self.form.addRow(nlbl, lbl)

    def _add_scalar(self, name, pytype, value):
        if pytype == "bool":
            w = QCheckBox(); w.setChecked(bool(value))
            self._scalar_getters[name] = w.isChecked
        elif pytype == "int":
            w = QSpinBox(); w.setRange(-2_000_000_000, 2_000_000_000)
            w.setValue(int(value) if value is not None else 0)
            self._scalar_getters[name] = w.value
        elif pytype == "float":
            w = QDoubleSpinBox(); w.setRange(-1e12, 1e12); w.setDecimals(3)
            w.setValue(float(value) if value is not None else 0.0)
            self._scalar_getters[name] = w.value
        else:
            w = QLineEdit("" if value is None else str(value))
            self._scalar_getters[name] = w.text
        self.form.addRow(f"{human(name)}:", w)

    def _add_list_scalar(self, name, value):
        box = QGroupBox(f"{human(name)}  (one per line)")
        v = QVBoxLayout(box)
        editor = QPlainTextEdit("\n".join(str(x) for x in (value or [])))
        editor.setFixedHeight(70)
        v.addWidget(editor)
        self._list_scalar_widgets[name] = editor
        self.form.addRow(box)

    def _add_single_czbird(self, name, value):
        self._czbird_values[name] = value
        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0)
        summary = QLabel(czbird_summary(value)); summary.setStyleSheet("color:#555;")
        h.addWidget(summary); h.addStretch(1)
        btn = QPushButton(f"Edit {short(type(value).__name__)}…")

        def _open(_=False, n=name, lbl=summary):
            self._open_child(self._czbird_values[n])
            lbl.setText(czbird_summary(self._czbird_values[n]))
        btn.clicked.connect(_open)
        h.addWidget(btn)
        self.form.addRow(f"{human(name)}:", row)

    def _add_poly(self, name, members, value):
        """Polymorphic field: a variant picker + an Edit button. Changing the
        variant replaces the held object with a prefill of the chosen member.
        """
        self._czbird_values[name] = value
        box = QGroupBox(f"{human(name)}  (choose kind)")
        v = QVBoxLayout(box)
        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        member_names = [m.__name__ for m in members]
        for m in members:
            combo.addItem(short(m.__name__))
        combo.setCurrentIndex(member_names.index(type(value).__name__))
        summary = QLabel(czbird_summary(value)); summary.setStyleSheet("color:#555;")
        edit = QPushButton("Edit…")

        def _on_variant(idx, n=name, lbl=summary):
            chosen = members[idx]
            if type(self._czbird_values[n]) is not chosen:
                self._czbird_values[n] = P.prefill(chosen)
                lbl.setText(czbird_summary(self._czbird_values[n]))
        combo.currentIndexChanged.connect(_on_variant)

        def _open(_=False, n=name, lbl=summary):
            self._open_child(self._czbird_values[n])
            lbl.setText(czbird_summary(self._czbird_values[n]))
        edit.clicked.connect(_open)

        h.addWidget(combo); h.addWidget(edit); h.addStretch(1); h.addWidget(summary, 1)
        v.addWidget(row)
        self.form.addRow(f"{human(name)}:", box)

    def _add_list_czbird(self, name, elem_cls, value, min_required=0):
        self._list_czbird_values[name] = list(value) if value else []
        lst = self._list_czbird_values[name]
        box = QGroupBox(f"{human(name)}  [{short(elem_cls.__name__)}]")
        v = QVBoxLayout(box)
        rows = QWidget(); rows_l = QVBoxLayout(rows); rows_l.setContentsMargins(0,0,0,0)
        v.addWidget(rows)

        def render():
            while rows_l.count():
                it = rows_l.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            if not lst:
                e = QLabel("(none)"); e.setStyleSheet("color:#999; font-style:italic;")
                rows_l.addWidget(e)
            for idx, elem in enumerate(lst):
                r = QWidget(); rh = QHBoxLayout(r); rh.setContentsMargins(0,0,0,0)
                rh.addWidget(QLabel(f"{idx+1}. {czbird_summary(elem)}"))
                rh.addStretch(1)
                eb = QPushButton("Edit…")
                eb.clicked.connect(lambda _=False, o=elem: (self._open_child(o), render()))
                rh.addWidget(eb)
                db = QPushButton("−"); db.setFixedWidth(28)
                def _rm(_=False, o=elem):
                    if len(lst) > min_required:
                        lst.remove(o); render()
                    else:
                        self._set_status(
                            f"At least {min_required} item(s) must remain.",
                            ok=False)
                db.clicked.connect(_rm)
                rh.addWidget(db)
                rows_l.addWidget(r)

        add = QPushButton(f"+ Add {short(elem_cls.__name__)}")
        add.clicked.connect(lambda _=False: (lst.append(P.prefill(elem_cls)), render()))
        v.addWidget(add)
        render()
        self.form.addRow(box)

    # ---- child dialog ------------------------------------------------- #
    def _open_child(self, obj):
        dlg = CzbirdDialog(obj, self)
        dlg.exec()   # child commits into `obj` in place on its own Apply/OK

    def _field_is_optional(self, name) -> bool:
        f = type(self.obj).model_fields.get(name)
        return f is not None and not f.is_required()

    # ---- collect / validate / commit ---------------------------------- #
    def _collect(self) -> dict:
        data = {}
        for name, getter in self._scalar_getters.items():
            data[name] = getter()
        for name, editor in self._list_scalar_widgets.items():
            items = [ln for ln in editor.toPlainText().split("\n") if ln.strip()]
            # An optional array must be absent (None) rather than empty: the
            # schema forbids empty lists (absent, or non-empty).
            data[name] = items if items or not self._field_is_optional(name) else None
        for name, obj in self._czbird_values.items():
            data[name] = obj
        for name, lst in self._list_czbird_values.items():
            data[name] = lst if lst or not self._field_is_optional(name) else None
        # literals / readonly: keep existing
        for name in type(self.obj).model_fields:
            if name not in data:
                data[name] = getattr(self.obj, name)
        return data

    def _apply(self) -> bool:
        try:
            rebuilt = type(self.obj).model_validate(self._collect())
        except ValidationError as e:
            self._set_status("Not valid yet:\n" + _fmt_errors(e), ok=False)
            return False
        # copy validated field values back into the live object (in place)
        for name in type(self.obj).model_fields:
            object.__setattr__(self.obj, name, getattr(rebuilt, name))
        return True

    def _on_apply(self):
        if self._apply():
            self._set_status("Changes are valid and applied.", ok=True)

    def _on_ok(self):
        if self._apply():
            self.accept()


def _fmt_errors(e: ValidationError) -> str:
    out = []
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"])
        out.append(f"  • {loc}: {err['msg']}")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CZBIRD metadata editor (example)")
        self.record = P.prefill_Metadata()
        self.setMinimumSize(640, 240)

        central = QWidget(); self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.addWidget(QLabel(
            "Starting from a prefilled, valid record. Edit the root Metadata; "
            "drill into nested objects via their buttons."))
        self._summary = QLabel(); self._summary.setWordWrap(True)
        lay.addWidget(self._summary)

        row = QHBoxLayout()
        eb = QPushButton("Edit record (Metadata)…"); eb.clicked.connect(self._edit)
        db = QPushButton("Print JSON to console"); db.clicked.connect(self._dump)
        row.addWidget(eb); row.addWidget(db); row.addStretch(1)
        lay.addLayout(row); lay.addStretch(1)
        self._refresh()

    def _edit(self):
        CzbirdDialog(self.record, self).exec()
        self._refresh()

    def _refresh(self):
        self._summary.setText(
            f"<b>{self.record.internal_record_title}</b><br>"
            f"profile: {type(self.record.was_generated_by).__name__}")

    def _dump(self):
        print(self.record.model_dump_json(indent=2, exclude_none=True))
        QMessageBox.information(self, "Dumped", "Record JSON printed to console.")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()      # keep a reference: an unreferenced top-level widget
    win.show()              # can be garbage-collected, destroying the window and
    sys.exit(app.exec())    # leaving app.exec() running with nothing on screen.


if __name__ == "__main__":
    main()
