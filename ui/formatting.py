"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation).
Staleness-Erkennung (P-10) lebt in staleness.py (Domaenenlogik, auch vom Agent
gebraucht) - hier nur re-exportiert, damit bestehende Imports unveraendert bleiben."""
from __future__ import annotations

from staleness import format_price_age, is_history_stale, is_price_stale

__all__ = [
    "format_money", "format_price_age", "is_history_stale", "is_price_stale",
    "format_risikofaktoren_lines", "RISIKOFAKTOREN_LEGENDE",
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
