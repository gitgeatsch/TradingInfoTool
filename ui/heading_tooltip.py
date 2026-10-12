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


def platziere(tip: tk.Toplevel, widget, abstand_x: int = 12, abstand_y: int = 18) -> None:
    """P15c (12.10.2026, Nutzerbild: *"kann rechts in der Tabelle nicht gelesen werden, da es rechts von der Maus gerendert wird"*):
    das Tooltip-Fenster rechts unten neben den Mauszeiger - reicht der Bildschirm nicht, LINKS bzw. OBERHALB davon. Nach dem Packen
    des Inhalts aufrufen (die Groesse steht erst dann fest)."""
    tip.update_idletasks()
    w, h = tip.winfo_reqwidth(), tip.winfo_reqheight()
    sw, sh = widget.winfo_screenwidth(), widget.winfo_screenheight()
    px, py = widget.winfo_pointerx(), widget.winfo_pointery()
    x, y = lage(px, py, w, h, sw, sh, abstand_x, abstand_y)
    tip.wm_geometry(f"+{x}+{y}")


def lage(px: int, py: int, w: int, h: int, sw: int, sh: int, abstand_x: int = 12, abstand_y: int = 18) -> tuple:
    """Die reine Rechnung zu ``platziere`` (Pruefstand ohne Maus): rechts/unten, sonst links/oben vom Zeiger, nie ausserhalb des Bildschirms."""
    x = px + abstand_x if px + abstand_x + w <= sw else max(0, px - abstand_x - w)
    y = py + abstand_y if py + abstand_y + h <= sh else max(0, py - abstand_y - h)
    return x, y


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
        tk.Label(
            tip, text=text, background=bg, foreground=fg, relief="solid", borderwidth=1,
            wraplength=280, justify="left", padx=6, pady=3,
        ).pack()
        platziere(tip, tree)                                # P15c: am Bildschirmrand nach links/oben
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
