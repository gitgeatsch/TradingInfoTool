"""Wiederholungs-Erkennung (2026-07-17, urspruenglich nur in agent/krypto/
analyst.py eingebaut - 2026-07-18 hierher ausgelagert und auf Aktien/
Rohstoffe/Hedge/Themen-ETF ausgeweitet, Regelwerk-Konsistenzpruefung: die
Multi-Asset-Batch-Vollstaendigkeitspruefung ergab, dass nur die Krypto-
Pipeline dieses Feature hatte, obwohl die zugrundeliegende Frage - "wurde
eine vorherige VERKAUFEN-Empfehlung ignoriert?" - fuer jede Assetklasse
gleichermassen gilt).

Rein deterministischer Datumsvergleich, KEIN LLM-Call: markiert, wenn eine
vorherige risikorelevante Empfehlung (Krypto: VERKAUFEN/TAUSCHEN, alle
anderen Klassen ohne TAUSCHEN: nur VERKAUFEN) nicht umgesetzt wurde - die
Position wird laut aktuellem Bestand weiterhin gehalten."""
from __future__ import annotations

from datetime import datetime, timezone

DEFAULT_RELEVANTE_AKTIONEN = ("VERKAUFEN", "TAUSCHEN")
DEFAULT_MINDEST_STUNDEN = 4.0


def build_wiederholung_fact(
    letztes_signal,
    wird_aktuell_gehalten: bool,
    relevante_aktionen: tuple[str, ...] = DEFAULT_RELEVANTE_AKTIONEN,
    mindest_stunden: float = DEFAULT_MINDEST_STUNDEN,
) -> dict | None:
    if letztes_signal is None or letztes_signal.action not in relevante_aktionen or not wird_aktuell_gehalten:
        return None
    letzter_zeitpunkt = datetime.fromisoformat(letztes_signal.created_at)
    if letzter_zeitpunkt.tzinfo is None:
        letzter_zeitpunkt = letzter_zeitpunkt.replace(tzinfo=timezone.utc)
    stunden_seit = (datetime.now(timezone.utc) - letzter_zeitpunkt).total_seconds() / 3600
    if stunden_seit < mindest_stunden:
        return None
    return {
        "letzte_aktion": letztes_signal.action,
        "vor_stunden": round(stunden_seit, 1),
        "hinweis": (
            f"Vorherige Empfehlung '{letztes_signal.action}' vor {stunden_seit:.1f} Std. "
            "nicht umgesetzt - Position wird laut aktuellem Bestand weiterhin gehalten."
        ),
    }
