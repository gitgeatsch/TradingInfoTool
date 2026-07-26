"""Gemeinsame Hervorhebung fuer die Signal-Detail-Textfelder (Hebel/Spot-Familie/
Marktscan) - alle drei bauen eine flache Zeilen-Liste und uebergaben sie bisher als
reinen, unformatierten Text an tk.Text (Nutzer-Fund 2026-07-23: "Text und GUI ist
alles schwarz weiss"). Erkennt bekannte Zeilenmuster (Abschnitts-Kopfzeilen,
Unter-Kopfzeilen, Warnungen, Risikofaktor-Marker ▲/●/▼ aus ui/formatting.py) rein
per Text-Pattern - erfordert keine Aenderung an den drei Zeilen-Bau-Funktionen
selbst, nur einen Austausch der jeweiligen _set_detail_text()-Kernlogik.

Die Zeilen-Klassifikation selbst (classify_detail_line()) lebt bewusst in
ui/formatting.py (Tk-frei) statt hier - api/email_notify.py nutzt dieselbe
Funktion fuer die HTML-Hervorhebung in der Benachrichtigungs-E-Mail, ohne
tkinter importieren zu muessen."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from ui import theme
from ui.formatting import _split_fazit_label, classify_detail_line

_FAZIT_TAGS = {"fazit_positiv", "fazit_neutral", "fazit_negativ"}


def configure_tags(text_widget: tk.Text) -> None:
    """Einmalig direkt nach dem Erzeugen des tk.Text-Widgets aufrufen."""
    base = tkfont.nametofont(text_widget.cget("font"))
    header_font = tkfont.Font(font=base)
    header_font.configure(weight="bold", size=base.cget("size") + 1)
    bold_font = tkfont.Font(font=base)
    bold_font.configure(weight="bold")
    # 2026-07-25 (Nutzer-Wunsch "Fazit-Label deutlicher"): eigene Fett-
    # Variante nur fuer die Fazit-Zeile, siehe ui/formatting.py::
    # _FAZIT_TAG_BY_SYMBOL. 2026-07-26 (Nutzer-Wunsch "nur das Wort Fazit
    # unterstreichen, nicht der ganze Text"): die Unterstreichung wandert in
    # einen ZWEITEN, hoeher priorisierten Tag (fazit_label_*, siehe unten),
    # der NUR ueber die "Fazit:"-Teilzeichenkette gelegt wird - Tk mischt
    # Font-Eigenschaften ueberlappender Tags NICHT (der zuletzt konfigurierte
    # Tag gewinnt komplett fuer den ueberlappenden Bereich), daher braucht es
    # zwei vollstaendig eigene Font-Objekte statt eines gemeinsamen.
    bold_underline_font = tkfont.Font(font=base)
    bold_underline_font.configure(weight="bold", underline=True)

    text_widget.tag_configure("section_header", font=header_font, foreground=theme.header_color())
    text_widget.tag_configure("sub_header", font=bold_font, foreground=theme.default_text_color())
    text_widget.tag_configure("warning", font=bold_font, foreground=theme.danger_color())
    text_widget.tag_configure("risk_positiv", foreground=theme.success_color())
    text_widget.tag_configure("risk_neutral", foreground=theme.info_color())
    text_widget.tag_configure("risk_negativ", foreground=theme.danger_color())
    text_widget.tag_configure("fazit_positiv", font=bold_font, foreground=theme.success_color())
    text_widget.tag_configure("fazit_neutral", font=bold_font, foreground=theme.info_color())
    text_widget.tag_configure("fazit_negativ", font=bold_font, foreground=theme.danger_color())
    # Konfiguriert NACH den Basis-fazit_*-Tags -> hoehere Rendering-Prioritaet
    # fuer den ueberlappenden "Fazit:"-Bereich (spaeter konfigurierte Tags
    # gewinnen bei ueberlappenden Font-Eigenschaften in Tk.Text).
    text_widget.tag_configure("fazit_label_positiv", font=bold_underline_font, foreground=theme.success_color())
    text_widget.tag_configure("fazit_label_neutral", font=bold_underline_font, foreground=theme.info_color())
    text_widget.tag_configure("fazit_label_negativ", font=bold_underline_font, foreground=theme.danger_color())
    text_widget.tag_configure("legend", foreground=theme.info_color())


def render_detail_text(text_widget: tk.Text, text: str) -> None:
    """Ersetzt den bisherigen dreifach duplizierten _set_detail_text()-Rumpf
    (state=normal -> delete -> insert -> state=disabled), zusaetzlich mit
    Zeilen-Tags fuer Hervorhebung. Tk-Zeilennummern (1-basiert, "L.C"-Index)
    entsprechen direkt der Python-seitigen text.split("\\n")-Enumeration, daher
    kein manuelles Positions-Tracking noetig. Fazit-Zeilen bekommen ZUSAETZLICH
    den hoeher priorisierten fazit_label_*-Tag nur ueber die "Fazit:"-
    Teilzeichenkette (2026-07-26, siehe configure_tags()-Docstring - nur das
    Wort "Fazit" ist unterstrichen, nicht der ganze Text)."""
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", text)
    for line_no, line in enumerate(text.split("\n"), start=1):
        tag = classify_detail_line(line)
        if not tag:
            continue
        text_widget.tag_add(tag, f"{line_no}.0", f"{line_no}.end")
        if tag in _FAZIT_TAGS:
            split = _split_fazit_label(line)
            if split:
                praefix_laenge = len(split[0])
                label_tag = "fazit_label_" + tag.removeprefix("fazit_")
                text_widget.tag_add(label_tag, f"{line_no}.0", f"{line_no}.{praefix_laenge}")
    text_widget.config(state="disabled")
