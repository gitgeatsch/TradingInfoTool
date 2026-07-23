"""Gemeinsame Hervorhebung fuer die Signal-Detail-Textfelder (Hebel/Spot-Familie/
Marktscan) - alle drei bauen eine flache Zeilen-Liste und uebergaben sie bisher als
reinen, unformatierten Text an tk.Text (Nutzer-Fund 2026-07-23: "Text und GUI ist
alles schwarz weiss"). Erkennt bekannte Zeilenmuster (Abschnitts-Kopfzeilen,
Unter-Kopfzeilen, Warnungen, Risikofaktor-Marker ▲/●/▼ aus ui/formatting.py) rein
per Text-Pattern - erfordert keine Aenderung an den drei Zeilen-Bau-Funktionen
selbst, nur einen Austausch der jeweiligen _set_detail_text()-Kernlogik."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from ui import theme

_SUBHEADER_MAX_LEN = 70
_RISK_TAG_BY_SYMBOL = {"▲": "risk_positiv", "●": "risk_neutral", "▼": "risk_negativ"}


def configure_tags(text_widget: tk.Text) -> None:
    """Einmalig direkt nach dem Erzeugen des tk.Text-Widgets aufrufen."""
    base = tkfont.nametofont(text_widget.cget("font"))
    header_font = tkfont.Font(font=base)
    header_font.configure(weight="bold", size=base.cget("size") + 1)
    bold_font = tkfont.Font(font=base)
    bold_font.configure(weight="bold")

    text_widget.tag_configure("section_header", font=header_font, foreground=theme.header_color())
    text_widget.tag_configure("sub_header", font=bold_font, foreground=theme.default_text_color())
    text_widget.tag_configure("warning", font=bold_font, foreground=theme.danger_color())
    text_widget.tag_configure("risk_positiv", foreground=theme.success_color())
    text_widget.tag_configure("risk_neutral", foreground=theme.info_color())
    text_widget.tag_configure("risk_negativ", foreground=theme.danger_color())
    text_widget.tag_configure("legend", foreground=theme.info_color())


def _classify(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped[0] in "⚠":
        return "warning"
    if stripped[0] in _RISK_TAG_BY_SYMBOL:
        return _RISK_TAG_BY_SYMBOL[stripped[0]]
    if stripped.startswith("(") and stripped.endswith(")") and "Warnsignal" in stripped:
        return "legend"
    if stripped.startswith("--- ") and stripped.endswith(" ---"):
        return "section_header"
    if line.startswith(" "):
        return None  # eingerueckte Detailzeilen nie als Kopfzeile behandeln
    core = stripped.split("(", 1)[0].strip()  # z.B. "STUFE-B-SCORES (0-100 je Kategorie)" -> "STUFE-B-SCORES"
    if core and core.isupper() and 1 <= len(core.split()) <= 6:
        return "sub_header"
    if stripped.endswith(":") and len(stripped) <= _SUBHEADER_MAX_LEN:
        return "sub_header"
    return None


def render_detail_text(text_widget: tk.Text, text: str) -> None:
    """Ersetzt den bisherigen dreifach duplizierten _set_detail_text()-Rumpf
    (state=normal -> delete -> insert -> state=disabled), zusaetzlich mit
    Zeilen-Tags fuer Hervorhebung. Tk-Zeilennummern (1-basiert, "L.C"-Index)
    entsprechen direkt der Python-seitigen text.split("\\n")-Enumeration, daher
    kein manuelles Positions-Tracking noetig."""
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", text)
    for line_no, line in enumerate(text.split("\n"), start=1):
        tag = _classify(line)
        if tag:
            text_widget.tag_add(tag, f"{line_no}.0", f"{line_no}.end")
    text_widget.config(state="disabled")
