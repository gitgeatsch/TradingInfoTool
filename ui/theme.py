"""Zentrales UI-Theme (GUI-Usability-Wunschliste, Nutzer-Idee 2026-07-09).
Aktuell: Basis-Schriftgroesse/Zeilenhoehe/Abstaende fuer alle Tabs einheitlich statt
verstreuter font=(...)-Literale. DEFAULT_TEXT_COLOR ist bewusst schon jetzt ein
zentraler Name (nicht "black" direkt im UI-Code verstreut) - Vorbereitung fuer den
geplanten Dark-Mode-Nachfolgeschritt, der hier eine echte Light/Dark-Palette
ergaenzt, ohne die Aufrufstellen nochmal anfassen zu muessen."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

BASE_FONT_SIZE = 10
TREE_ROW_HEIGHT = 26
DEFAULT_TEXT_COLOR = "black"

_NAMED_FONTS = ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkFixedFont")


def apply_base_style(root: tk.Tk) -> None:
    """Bumpt die Groesse der von Tk benannten Standard-Fonts (wirkt automatisch auf
    praktisch alle klassischen Tk- UND ttk-Widgets, die sich nicht per font=(...)
    explizit ueberschreiben) + etwas grosszuegigere Treeview-Zeilenhoehe/
    Button-Innenabstaende."""
    for name in _NAMED_FONTS:
        try:
            tkfont.nametofont(name).configure(size=BASE_FONT_SIZE)
        except tk.TclError:
            pass

    heading_family = tkfont.nametofont("TkHeadingFont").actual("family")

    style = ttk.Style(root)
    style.configure("Treeview", rowheight=TREE_ROW_HEIGHT)
    style.configure("Treeview.Heading", font=(heading_family, BASE_FONT_SIZE, "bold"))
    style.configure("TButton", padding=(10, 6))
    style.configure("TCheckbutton", padding=(0, 2))
    style.configure("TRadiobutton", padding=(0, 2))
