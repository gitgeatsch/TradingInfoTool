"""Wiederverwendbares Klick-zum-Sortieren fuer ttk.Treeview-Spaltenkoepfe
(GUI-Usability-Wunschliste, Nutzer-Idee 2026-07-09). Sortiert nur die Zeilenreihenfolge
um (tree.move), Anzeige-Text/Tags/Werte bleiben unveraendert."""
from __future__ import annotations

import re
from tkinter import ttk
from typing import Callable

import ui.theme as theme

_STRIP_RE = re.compile(r"[⚠✓✗€$x\s]")
_ARROW_UP = " ▲"
_ARROW_DOWN = " ▼"


def _numeric_key(raw: str) -> float | None:
    """Parst Anzeige-Strings wie '⚠ 1,234.56', '+2.34', '1e-08', '5.0x' (Hebel-
    Multiplikator-Suffix) in einen sortierbaren float. Gibt None fuer '-'/leere/
    unparsebare Werte zurueck (bleiben unabhaengig von der Sortierrichtung am
    Ende)."""
    text = _STRIP_RE.sub("", raw).replace(",", "")
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _date_key(raw: str) -> str | None:
    """Datums-Anzeige-Strings ('YYYY-MM-DD HH:MM') sortieren als reiner String
    bereits korrekt chronologisch (fixe Breite, fuehrende Nullen) - anders als
    bei _numeric_key() ist hier also kein Parsing noetig, nur dieselbe '-'
    (kein Wert) -> None-Behandlung, damit fehlende Werte wie bei Zahlen IMMER
    ans Ende rutschen, unabhaengig von der Sortierrichtung (bei reinem
    String-Vergleich wuerde '-' je nach Richtung mal vorne, mal hinten
    landen, da '-' in ASCII vor Ziffern sortiert)."""
    text = raw.strip()
    if not text or text == "-":
        return None
    return text


def make_sortable(
    tree: ttk.Treeview, numeric_columns: frozenset[str] = frozenset(),
    date_columns: frozenset[str] = frozenset(),
) -> Callable[[], None]:
    """Bindet jeden Spaltenkopf von `tree` an eine Klick-Sortierung (erneuter Klick
    kehrt die Richtung um, Pfeil im Spaltenkopf zeigt die aktive Richtung). Spalten in
    `numeric_columns` werden zahlenbasiert sortiert, Spalten in `date_columns`
    chronologisch (beide: fehlende Werte '-' immer ans Ende, unabhaengig von der
    Richtung), alle anderen alphabetisch.

    2026-07-25 (Nutzer-Fund "manchmal Vermischungen beim Sortieren"): `numeric_columns`
    ohne echten Zahlen-Parse haette Werte wie Hebel-Multiplikatoren ('5.0x' vs '10.0x')
    oder gemischte Formate (Hebel-Signal '5.0x' vs. Kandidaten-Score '78' in derselben
    Spalte) rein alphabetisch sortiert - '10.0x' landet dann VOR '5.0x', weil '1' < '5'
    als Zeichen. `_STRIP_RE` entfernt jetzt auch das 'x'-Suffix, `date_columns` ist neu
    (Datumsspalten wurden bisher als ganz normale String-Spalten sortiert - fuer sich
    genommen bereits korrekt chronologisch, aber '-' rutschte je nach Richtung
    inkonsistent mal vorne/mal hinten rein statt wie bei Zahlen IMMER ans Ende).

    Gibt eine `reapply_sort()`-Funktion zurueck (2026-07-16, GUI-Refresh-Fix,
    Nutzer-Fund: periodische Refreshs bauen die Zeilen komplett neu auf und
    zerstoeren dabei jede aktive Sortierung) - ruft man das nach einem
    Neuaufbau der Zeilen auf, wird die zuletzt vom Nutzer gewaehlte Spalte/
    Richtung erneut angewendet. No-Op, solange noch nie sortiert wurde."""
    columns = tree["columns"]
    original_text = {col: tree.heading(col)["text"] for col in columns}
    state = {"column": None, "reverse": False}

    def sort_by(col: str, *, toggle: bool = True) -> None:
        reverse = (state["column"] == col and not state["reverse"]) if toggle else state["reverse"]
        rows = [(tree.set(item, col), item) for item in tree.get_children("")]

        if col in numeric_columns or col in date_columns:
            key_fn = _numeric_key if col in numeric_columns else _date_key
            keyed = [(item, key_fn(value)) for value, item in rows]
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
        theme.restripe_treeview(tree)  # Zeilenreihenfolge hat sich geaendert -
        # Zebra-Streifen (2026-07-12) muessen neu zugeordnet werden.

        state["column"] = col
        state["reverse"] = reverse
        for c in columns:
            suffix = (_ARROW_DOWN if reverse else _ARROW_UP) if c == col else ""
            tree.heading(c, text=original_text[c] + suffix)

    for col in columns:
        tree.heading(col, command=lambda c=col: sort_by(c))

    def reapply_sort() -> None:
        if state["column"] is not None:
            sort_by(state["column"], toggle=False)

    return reapply_sort
