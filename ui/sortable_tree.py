"""Wiederverwendbares Klick-zum-Sortieren fuer ttk.Treeview-Spaltenkoepfe
(GUI-Usability-Wunschliste, Nutzer-Idee 2026-07-09). Sortiert nur die Zeilenreihenfolge
um (tree.move), Anzeige-Text/Tags/Werte bleiben unveraendert."""
from __future__ import annotations

import re
from tkinter import ttk

_STRIP_RE = re.compile(r"[⚠✓✗€$\s]")
_ARROW_UP = " ▲"
_ARROW_DOWN = " ▼"


def _numeric_key(raw: str) -> float | None:
    """Parst Anzeige-Strings wie '⚠ 1,234.56', '+2.34', '1e-08' in einen sortierbaren
    float. Gibt None fuer '-'/leere/unparsebare Werte zurueck (bleiben unabhaengig
    von der Sortierrichtung am Ende)."""
    text = _STRIP_RE.sub("", raw).replace(",", "")
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def make_sortable(tree: ttk.Treeview, numeric_columns: frozenset[str] = frozenset()) -> None:
    """Bindet jeden Spaltenkopf von `tree` an eine Klick-Sortierung (erneuter Klick
    kehrt die Richtung um, Pfeil im Spaltenkopf zeigt die aktive Richtung). Spalten in
    `numeric_columns` werden zahlenbasiert sortiert (fehlende Werte '-' immer ans
    Ende), alle anderen alphabetisch."""
    columns = tree["columns"]
    original_text = {col: tree.heading(col)["text"] for col in columns}
    state = {"column": None, "reverse": False}

    def sort_by(col: str) -> None:
        reverse = state["column"] == col and not state["reverse"]
        rows = [(tree.set(item, col), item) for item in tree.get_children("")]

        if col in numeric_columns:
            keyed = [(item, _numeric_key(value)) for value, item in rows]
            present = sorted(
                (pair for pair in keyed if pair[1] is not None),
                key=lambda pair: pair[1],
                reverse=reverse,
            )
            missing = [item for item, key in keyed if key is None]
            ordered = [item for item, _ in present] + missing
        else:
            rows.sort(key=lambda pair: pair[0].lower(), reverse=reverse)
            ordered = [item for _, item in rows]

        for index, item in enumerate(ordered):
            tree.move(item, "", index)

        state["column"] = col
        state["reverse"] = reverse
        for c in columns:
            suffix = (_ARROW_DOWN if reverse else _ARROW_UP) if c == col else ""
            tree.heading(c, text=original_text[c] + suffix)

    for col in columns:
        tree.heading(col, command=lambda c=col: sort_by(c))
