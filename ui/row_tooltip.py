"""Mouseover-Tooltips fuer einzelne Treeview-ZEILEN (2026-07-16, Nutzer-Wunsch
im Rahmen des GUI-Refresh-Fixes) - Pendant zu ui/heading_tooltip.py (das nur
Spaltenkoepfe abdeckt). `text_provider` wird bewusst LAZY erst beim Hover
aufgerufen (nicht bei jedem Mausereignis) - vermeidet unnoetige Arbeit
(z.B. eine DB-Abfrage) fuer Zeilen, die der Nutzer nie tatsaechlich betrachtet."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

import ui.theme as theme

_SHOW_DELAY_MS = 400


def add_row_tooltips(tree: ttk.Treeview, text_provider: Callable[[str], str | None]) -> None:
    """Bindet Mouseover-Tooltips an die Datenzeilen von `tree`. `text_provider(iid)`
    liefert den anzuzeigenden Text fuer die Zeile mit dieser iid, oder `None`
    (kein Tooltip fuer diese Zeile - z.B. wenn noch keine Daten vorliegen)."""
    state: dict = {"tooltip": None, "row": None, "after_id": None}

    def hide() -> None:
        if state["after_id"] is not None:
            tree.after_cancel(state["after_id"])
            state["after_id"] = None
        if state["tooltip"] is not None:
            state["tooltip"].destroy()
            state["tooltip"] = None
        state["row"] = None

    def show(row: str) -> None:
        text = text_provider(row)
        if not text:
            return
        bg, fg = theme.tooltip_colors()
        tip = tk.Toplevel(tree)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.wm_geometry(f"+{tree.winfo_pointerx() + 12}+{tree.winfo_pointery() + 18}")
        tk.Label(
            tip, text=text, background=bg, foreground=fg, relief="solid", borderwidth=1,
            wraplength=360, justify="left", padx=6, pady=3,
        ).pack()
        state["tooltip"] = tip

    def on_motion(event: tk.Event) -> None:
        if tree.identify_region(event.x, event.y) != "cell":
            hide()
            return
        row = tree.identify_row(event.y)
        if not row or row == state["row"]:
            if not row:
                hide()
            return
        hide()
        state["row"] = row
        state["after_id"] = tree.after(_SHOW_DELAY_MS, lambda: show(row))

    tree.bind("<Motion>", on_motion, add="+")
    tree.bind("<Leave>", lambda _e: hide(), add="+")
