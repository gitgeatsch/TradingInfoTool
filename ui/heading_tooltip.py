"""Mouseover-Tooltips fuer Treeview-Spaltenkoepfe (Nutzer-Wunsch 2026-07-13) -
z.B. um zu erklaeren, was "G/V %" konkret bedeutet, ohne die Kopfzeile selbst
mit langem Text zu ueberladen. tkinter/ttk hat kein eingebautes Tooltip-Widget,
daher ein minimaler eigener Toplevel, analog zum Muster in
ui/sortable_tree.py (ein wiederverwendbares Verhalten pro Treeview-Spaltenkopf)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import ui.theme as theme

_SHOW_DELAY_MS = 400


def add_heading_tooltips(tree: ttk.Treeview, descriptions: dict[str, str]) -> None:
    """Bindet Mouseover-Tooltips an die Spaltenkoepfe von `tree`. `descriptions`
    bildet Spalten-ID (wie in tree["columns"]) auf den anzuzeigenden
    Erklaerungstext ab - Spalten ohne Eintrag bekommen keinen Tooltip."""
    columns = tree["columns"]
    state: dict = {"tooltip": None, "column": None, "after_id": None}

    def hide() -> None:
        if state["after_id"] is not None:
            tree.after_cancel(state["after_id"])
            state["after_id"] = None
        if state["tooltip"] is not None:
            state["tooltip"].destroy()
            state["tooltip"] = None
        state["column"] = None

    def show(col: str) -> None:
        text = descriptions.get(col)
        if not text:
            return
        bg, fg = theme.tooltip_colors()
        tip = tk.Toplevel(tree)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.wm_geometry(f"+{tree.winfo_pointerx() + 12}+{tree.winfo_pointery() + 18}")
        tk.Label(
            tip, text=text, background=bg, foreground=fg, relief="solid", borderwidth=1,
            wraplength=280, justify="left", padx=6, pady=3,
        ).pack()
        state["tooltip"] = tip

    def on_motion(event: tk.Event) -> None:
        if tree.identify_region(event.x, event.y) != "heading":
            hide()
            return
        col_id = tree.identify_column(event.x)
        try:
            col = columns[int(col_id.replace("#", "")) - 1]
        except (ValueError, IndexError):
            hide()
            return
        if col == state["column"]:
            return
        hide()
        state["column"] = col
        state["after_id"] = tree.after(_SHOW_DELAY_MS, lambda: show(col))

    tree.bind("<Motion>", on_motion, add="+")
    tree.bind("<Leave>", lambda _e: hide(), add="+")
