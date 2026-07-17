"""Zentrales UI-Theme (GUI-Usability-Wunschliste, Nutzer-Idee 2026-07-09):
Basis-Schriftgroesse/Zeilenhoehe/Abstaende + Light/Dark-Palette + semantische
Farbfunktionen. Alle Tabs fragen Farben hier ab (z.B. theme.action_color(...)),
statt eigene "black"/"#666666"-Literale zu verstreuen - das macht Dark Mode auf
alle vier Tabs gleichzeitig wirksam, ohne jede Ansicht einzeln zu duplizieren.

Bewusster Scope-Schnitt (2026-07-09, mit Nutzer abgestimmt): Dark Mode wird beim
Programmstart einmal angewendet (aus ui/settings.py gelesen), kein Live-Umschalten
waehrend die App laeuft - Umschalten im Menue speichert die Einstellung nur und
bittet um einen Neustart. Das vermeidet, jede Farbkonstante bei jedem Toggle live
neu durchrechnen und alle bereits gerenderten Widgets/Treeview-Tags nachtraeglich
umfaerben zu muessen."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

BASE_FONT_SIZE = 10
TREE_ROW_HEIGHT = 26

_NAMED_FONTS = ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkFixedFont")

# Semantische Rollen, nicht direkt die alten Variablennamen (STALE_COLOR/
# ACTION_COLORS/...) - mehrere frueher zufaellig identische Werte (z.B.
# INFO_COLOR und "kein_treffer" waren beide "#666666") sind hier bewusst
# zusammengefuehrt.
_LIGHT = {
    "fg": "black",
    "info": "#666666",
    "muted": "#555555",
    "warn": "#b36b00",
    "danger": "#c0392b",
    "success": "#1a7f37",
    "swap": "#8a5a00",
    "bg": "#f0f0f0",
    "entry_bg": "#ffffff",
    "select_bg": "#0078d7",
    "select_fg": "#ffffff",
    "zebra_odd": "#ebebeb",
}
_DARK = {
    "fg": "#e0e0e0",
    "info": "#9a9a9a",
    "muted": "#8a8a8a",
    "warn": "#e0a030",
    "danger": "#e06c75",
    "success": "#4caf50",
    "swap": "#d7ab5f",
    "bg": "#1e1e1e",
    "entry_bg": "#2d2d2d",
    "select_bg": "#094771",
    "select_fg": "#ffffff",
    "zebra_odd": "#404040",
}

_dark_mode = False


def set_dark_mode(enabled: bool) -> None:
    global _dark_mode
    _dark_mode = enabled


def is_dark() -> bool:
    return _dark_mode


def _palette() -> dict:
    return _DARK if _dark_mode else _LIGHT


def default_text_color() -> str:
    return _palette()["fg"]


def info_color() -> str:
    return _palette()["info"]


def warn_color() -> str:
    return _palette()["warn"]


def stale_color() -> str:
    return _palette()["warn"]


def danger_color() -> str:
    return _palette()["danger"]


def action_color(action: str) -> str:
    p = _palette()
    return {
        "KAUFEN": p["success"],
        "NACHKAUFEN": p["success"],
        "VERKAUFEN": p["danger"],
        "TAUSCHEN": p["swap"],
        "HALTEN": p["muted"],
        # Hebel-Aktionsvokabular (2026-07-14, Phase 6, siehe agent/krypto/
        # hebel_analyst.py::REQUIRED_HEBEL_ACTIONS) - NACHKAUFEN/HALTEN oben
        # bereits abgedeckt, gelten identisch.
        "ERÖFFNEN": p["success"],
        "HEBEL_ERHÖHEN": p["warn"],  # Risiko steigt
        "HEBEL_SENKEN": p["success"],  # Risiko sinkt, vorsichtiger Schritt
        "TEILVERKAUF": p["swap"],
        "SCHLIESSEN": p["danger"],
    }.get(action, p["fg"])


def einstufung_color(einstufung: str) -> str:
    p = _palette()
    return {
        "kaufkandidat": p["success"],
        "watchlist_wuerdig": p["swap"],
        "kein_treffer": p["info"],
    }.get(einstufung, p["fg"])


def regime_color(regime: str) -> str:
    """Regime-Status-Anzeige (2026-07-17) - mappt die 5 REGIME_STATES
    (agent/krypto/regime.py) auf bestehende Paletten-Toene, keine neuen Farben
    noetig. krise_extrem am gefaehrlichsten (danger), euphorie_extrem als
    "swap" wiederverwendet (einzige verbleibende, klar unterscheidbare Farbe)."""
    p = _palette()
    return {
        "krise_extrem": p["danger"],
        "baer": p["warn"],
        "seitwaerts": p["muted"],
        "bulle": p["success"],
        "euphorie_extrem": p["swap"],
    }.get(regime, p["fg"])


def chart_facecolor() -> str:
    """Etwas heller als der Fenster-Hintergrund (wie Treeview/Entry) - hebt die
    Chart-Flaeche im Dark Mode leicht vom Rest des Fensters ab, analog zu
    Panel-Hintergruenden in anderen dunklen Oberflaechen."""
    return _palette()["entry_bg"]


def chart_grid_color() -> str:
    return _palette()["muted"] if _dark_mode else "#cccccc"


def chart_price_line_color() -> str:
    return _palette()["fg"]


def tooltip_colors() -> tuple[str, str]:
    """(Hintergrund, Vordergrund) fuer Mouseover-Tooltips (z.B. Spaltenkopf-
    Erklaerungen, siehe ui/heading_tooltip.py) - wiederverwendet die bestehende
    entry_bg/fg-Palette statt einer eigenen dritten Tooltip-Farbe."""
    p = _palette()
    return p["entry_bg"], p["fg"]


def success_color() -> str:
    return _palette()["success"]


def umgesetzt_color() -> str:
    return _palette()["success"]


def nicht_umgesetzt_color() -> str:
    return _palette()["info"]


def restripe_treeview(tree: ttk.Treeview) -> None:
    """Zebra-Streifen fuer Treeview-Zeilen (Nutzer-Wunsch 2026-07-12: 'Rasterlinien
    fuer schoen getrennte Zeilen'). Echte Rasterlinien zwischen Zeilen unterstuetzt
    ttk.Treeview unter Windows nicht zuverlaessig nativ (per Nutzer-Entscheidung
    bewusst NICHT nachgebaut) - abwechselnde Zeilenfarben sind die robuste
    Standard-Alternative. Nur `background` gesetzt, nie `foreground` - kollidiert
    dadurch nie mit den bestehenden semantischen Tags (stale/kaufkandidat/...), die
    ausschliesslich `foreground` setzen, unabhaengig von der Tag-Reihenfolge.

    Muss nach JEDER Neubefuellung (Zeilen loeschen+neu einfuegen) UND nach jeder
    Sortierung erneut aufgerufen werden, da sich dabei die Zeilenreihenfolge
    aendert - sortable_tree.py::make_sortable() ruft das bereits automatisch nach
    jedem Sortier-Klick auf, Aufrufer muessen es nur nach eigenen
    Tabelleninhalts-Aenderungen selbst aufrufen."""
    tree.tag_configure("zebra_odd", background=_palette()["zebra_odd"])
    for index, item in enumerate(tree.get_children("")):
        tags = tuple(t for t in tree.item(item, "tags") if t != "zebra_odd")
        if index % 2 == 1:
            tags = tags + ("zebra_odd",)
        tree.item(item, tags=tags)


def apply_base_style(root: tk.Tk) -> None:
    """Bumpt die Groesse der von Tk benannten Standard-Fonts (wirkt automatisch auf
    praktisch alle klassischen Tk- UND ttk-Widgets, die sich nicht per font=(...)
    explizit ueberschreiben) + etwas grosszuegigere Treeview-Zeilenhoehe/
    Button-Innenabstaende. Danach ggf. apply_dark_mode() (separat, da unabhaengig
    vom Dark-Mode-Status immer gewuenscht)."""
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


def apply_dark_mode(root: tk.Tk) -> None:
    """Muss VOR dem Bau der Tabs/Widgets aufgerufen werden (root.option_add() wirkt
    nur auf danach erzeugte Widgets). Zwei Mechanismen kombiniert: option_add() fuer
    klassische Tk-Widgets (tk.Text/tk.Toplevel/tk.Menu/tk.Frame - erreicht ttk.Style
    nicht), ttk.Style(clam) fuer ttk-Widgets (option_add wirkt dort nicht
    zuverlaessig). 'clam' ist die einzige eingebaute Theme-Basis, die Farben auf
    Windows tatsaechlich vollstaendig uebernimmt (vista/xpnative zeichnen viele
    Elemente OS-nativ und ignorieren Farb-Overrides)."""
    p = _DARK

    root.configure(bg=p["bg"])
    root.option_add("*Background", p["bg"])
    root.option_add("*Foreground", p["fg"])
    root.option_add("*Entry.Background", p["entry_bg"])
    root.option_add("*Entry.Foreground", p["fg"])
    root.option_add("*Text.Background", p["entry_bg"])
    root.option_add("*Text.Foreground", p["fg"])
    root.option_add("*selectBackground", p["select_bg"])
    root.option_add("*selectForeground", p["select_fg"])
    root.option_add("*insertBackground", p["fg"])  # Cursor in Entry/Text

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["entry_bg"])
    for widget_class in (
        "TFrame", "TLabel", "TButton", "TCheckbutton", "TRadiobutton", "TPanedwindow",
        "TNotebook", "TNotebook.Tab", "TEntry", "TCombobox",
    ):
        style.configure(widget_class, background=p["bg"], foreground=p["fg"])
    style.map(
        "TNotebook.Tab",
        background=[("selected", p["entry_bg"])],
        foreground=[("selected", p["fg"])],
    )
    style.configure(
        "Treeview", background=p["entry_bg"], fieldbackground=p["entry_bg"], foreground=p["fg"],
    )
    style.map(
        "Treeview",
        background=[("selected", p["select_bg"])],
        foreground=[("selected", p["select_fg"])],
    )
    style.configure("Treeview.Heading", background=p["bg"], foreground=p["fg"])
    style.map("TButton", background=[("active", p["entry_bg"])])
