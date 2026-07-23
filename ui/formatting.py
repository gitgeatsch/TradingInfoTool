"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation).
Staleness-Erkennung (P-10) lebt in staleness.py (Domaenenlogik, auch vom Agent
gebraucht) - hier nur re-exportiert, damit bestehende Imports unveraendert bleiben."""
from __future__ import annotations

from staleness import format_price_age, is_history_stale, is_price_stale

__all__ = [
    "format_money", "format_price_age", "is_history_stale", "is_price_stale",
    "format_risikofaktoren_lines", "RISIKOFAKTOREN_LEGENDE",
    "classify_detail_line", "render_detail_html",
]


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    return f"{value:,.8f}"


_RISIKOFAKTOR_SYMBOL = {"positiv": "▲", "neutral": "●", "negativ": "▼"}

# 2026-07-20: urspruenglich farbige Kreis-Emoji (🟢/⚪/🔴) - Nutzer-Screenshot
# vom echten Notebook-App-Detail-Panel zeigte, dass Tkinters Standardfont
# (Windows) fuer 🟢/🔴 (ausserhalb der Basic Multilingual Plane) auf denselben
# Ersatzglyph zurueckfaellt, wodurch die Farbunterscheidung im laufenden
# Betrieb komplett verloren ging (nur ⚪ blieb sichtbar unterscheidbar). Wechsel
# auf die bereits im Projekt etablierten Form-Marker ▲/●/▼ (siehe
# ui/app.py/portfolio.py/screener_view.py: These-Marker, gleiche Semantik
# positiv/neutral/negativ) - Form statt Farbe macht die Unterscheidung robust
# gegen Emoji-Rendering, sowohl in der App als auch im reinen Text der E-Mail.
RISIKOFAKTOREN_LEGENDE = "(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)"


def format_risikofaktoren_lines(risikofaktoren_json: str | None) -> list[str]:
    """2026-07-19 (E-Mail-/App-Neustrukturierung in 3 Abschnitte - Mathematisch
    berechnet / LLM-Bewertung / Konklusion, echter AVAX-Hebel-Fund). Gemeinsame
    Anzeigelogik fuer ui/hebel_view.py + ui/signals_view.py, spiegelt
    scheduler/background.py::_formatiere_risikofaktoren() (dort eigene Kopie
    fuer den E-Mail-Textkontext - bewusst getrennt, unterschiedliche
    Ziel-Formate). Sortiert negativ vor neutral vor positiv, damit die
    wichtigsten Warnungen zuerst erscheinen."""
    import json

    if not risikofaktoren_json:
        return []
    try:
        faktoren = json.loads(risikofaktoren_json)
    except (ValueError, TypeError):
        return []
    if not faktoren:
        return []

    gruppen: dict[str, list[dict]] = {"negativ": [], "neutral": [], "positiv": []}
    for f in faktoren:
        gruppen.setdefault(f.get("bewertung", "neutral"), []).append(f)

    zeilen = []
    for bewertung in ("negativ", "neutral", "positiv"):
        for f in gruppen.get(bewertung, []):
            symbol = _RISIKOFAKTOR_SYMBOL.get(bewertung, "●")
            zeilen.append(f"{symbol} {f.get('name', '')}: {f.get('begruendung', '')}")
    return zeilen


# 2026-07-23: gemeinsame Zeilen-Klassifikation fuer Signal-Detail-Textbloecke
# (Hebel/Spot-Familie/Marktscan) - wird sowohl von ui/detail_panel.py (tk.Text-
# Tags im App-Detail-Panel) als auch von scheduler/background.py/
# api/email_notify.py (HTML-Hervorhebung in der Benachrichtigungs-E-Mail)
# genutzt. Bewusst hier in formatting.py (Tk-frei) statt in ui/detail_panel.py
# (importiert tkinter) - der Scheduler/E-Mail-Pfad soll kein Tkinter brauchen.
_SUBHEADER_MAX_LEN = 70
_RISK_TAG_BY_SYMBOL = {"▲": "risk_positiv", "●": "risk_neutral", "▼": "risk_negativ"}


def classify_detail_line(line: str) -> str | None:
    """Erkennt bekannte Zeilenmuster in den Signal-Detail-Textbloecken rein per
    Text-Pattern (keine Aenderung an den Zeilen-Bau-Funktionen selbst noetig):
    Abschnitts-Kopfzeilen ("--- N. ... ---"), Unter-Kopfzeilen, Warnungen (⚠),
    Risikofaktor-Marker (▲/●/▼) und die zugehoerige Legendenzeile. Gibt None
    zurueck, wenn die Zeile keinem bekannten Muster entspricht (normaler
    Fliesstext/eingerueckte Detailzeilen)."""
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


# Feste Light-Mode-Farben fuer die E-Mail-HTML-Variante (2026-07-23) - E-Mails
# haben kein Dark-Mode-Konzept wie die App (siehe ui/theme.py); die Farben hier
# sind bewusst als Literale fixiert, nicht von ui.theme abgeleitet, damit die
# E-Mail unabhaengig vom aktuellen App-Theme immer gleich (und immer lesbar)
# aussieht - siehe auch die color-scheme-Meta-Tags in api/email_notify.py, die
# Gmails automatische Dark-Mode-Invertierung fuer die ganze Mail unterdruecken.
_HTML_STYLE_BY_TAG = {
    "section_header": "font-weight:bold;font-size:1.05em;color:#0056b3;",
    "sub_header": "font-weight:bold;color:#000000;",
    "warning": "font-weight:bold;color:#c0392b;",
    "risk_positiv": "color:#1a7f37;",
    "risk_neutral": "color:#666666;",
    "risk_negativ": "color:#c0392b;",
    "legend": "color:#666666;font-style:italic;",
}


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_detail_html(text: str) -> str:
    """HTML-Pendant zu ui/detail_panel.py::render_detail_text() - baut aus
    demselben Zeilen-Text ein <pre>-basiertes HTML-Fragment mit Inline-Styles
    fuer dieselben Zeilenmuster (Abschnitts-Kopfzeilen fett+Akzentfarbe,
    Risikofaktor-Zeilen farbig etc.), damit die E-Mail dieselbe visuelle
    Hervorhebung zeigt wie das App-Detail-Panel."""
    teile = ["<pre style=\"font-family: monospace; color:#1a1a1a; margin:0;\">"]
    for line in text.split("\n"):
        escaped = _html_escape(line)
        tag = classify_detail_line(line)
        style = _HTML_STYLE_BY_TAG.get(tag)
        teile.append(f"<span style=\"{style}\">{escaped}</span>" if style else escaped)
        teile.append("\n")
    teile.append("</pre>")
    return "".join(teile)
