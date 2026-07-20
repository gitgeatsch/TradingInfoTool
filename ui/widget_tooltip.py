"""Generische Mouseover-Tooltips fuer einzelne Widgets (Buttons, Checkbuttons)
und fuer Notebook-Tab-Kopfzeilen (2026-07-20, Nutzer-Wunsch: "fuer die
Primaerseiten - Tabs und Aktionen - eine konkrete Kurzbeschreibung bei
Mouseover was diese bewirken"). Ergaenzung zu ui/heading_tooltip.py
(Treeview-Spaltenkoepfe) und ui/row_tooltip.py (Treeview-Zeilen), die beide
NUR auf Treeviews funktionieren - hier geht es um Widgets ausserhalb einer
Treeview. Gleiches visuelles Muster (kleiner, unverzierter Toplevel,
400ms-Verzoegerung) fuer Konsistenz."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import ui.theme as theme

_SHOW_DELAY_MS = 400


def _show_tooltip(widget: tk.Widget, text: str) -> tk.Toplevel:
    bg, fg = theme.tooltip_colors()
    tip = tk.Toplevel(widget)
    tip.wm_overrideredirect(True)
    tip.attributes("-topmost", True)
    tip.wm_geometry(f"+{widget.winfo_pointerx() + 12}+{widget.winfo_pointery() + 18}")
    tk.Label(
        tip, text=text, background=bg, foreground=fg, relief="solid", borderwidth=1,
        wraplength=320, justify="left", padx=6, pady=3,
    ).pack()
    return tip


def add_widget_tooltip(widget: tk.Widget, text: str) -> None:
    """Statischer Mouseover-Tooltip fuer EIN Widget (z.B. ttk.Button/
    ttk.Checkbutton) - kein Region-/Zeilen-Lookup noetig wie bei Treeviews,
    einfaches Enter/Leave."""
    state: dict = {"tooltip": None, "after_id": None}

    def hide(_event=None) -> None:
        if state["after_id"] is not None:
            widget.after_cancel(state["after_id"])
            state["after_id"] = None
        if state["tooltip"] is not None:
            state["tooltip"].destroy()
            state["tooltip"] = None

    def show() -> None:
        state["tooltip"] = _show_tooltip(widget, text)

    def on_enter(_event=None) -> None:
        state["after_id"] = widget.after(_SHOW_DELAY_MS, show)

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", hide, add="+")
    widget.bind("<ButtonPress>", hide, add="+")


def add_notebook_tab_tooltips(notebook: ttk.Notebook, descriptions: dict[int, str]) -> None:
    """Mouseover-Tooltips fuer die Tab-Kopfzeilen eines ttk.Notebook.
    `descriptions` bildet den Tab-INDEX (Reihenfolge der notebook.add()-Aufrufe,
    0-basiert) auf den Erklaerungstext ab - Tabs ohne Eintrag bekommen keinen
    Tooltip."""
    state: dict = {"tooltip": None, "tab": None, "after_id": None}

    def hide() -> None:
        if state["after_id"] is not None:
            notebook.after_cancel(state["after_id"])
            state["after_id"] = None
        if state["tooltip"] is not None:
            state["tooltip"].destroy()
            state["tooltip"] = None
        state["tab"] = None

    def show(tab_index: int) -> None:
        text = descriptions.get(tab_index)
        if not text:
            return
        state["tooltip"] = _show_tooltip(notebook, text)

    def on_motion(event: tk.Event) -> None:
        try:
            element = notebook.identify(event.x, event.y)
        except tk.TclError:
            hide()
            return
        if "label" not in element and "tab" not in element:
            hide()
            return
        try:
            tab_index = notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            hide()
            return
        if tab_index == state["tab"]:
            return
        hide()
        state["tab"] = tab_index
        state["after_id"] = notebook.after(_SHOW_DELAY_MS, lambda: show(tab_index))

    notebook.bind("<Motion>", on_motion, add="+")
    notebook.bind("<Leave>", lambda _e: hide(), add="+")
