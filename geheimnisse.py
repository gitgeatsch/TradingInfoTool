# -*- coding: utf-8 -*-
"""Zugangsschluessel aus Texten entfernen, bevor sie gespeichert oder geloggt werden.

⚠️⚠️⚠️ ANLASS - Befund 2.453-fredkey (Review 14.09.2026). `requests` nennt bei
einem HTTP-Fehler die VOLLE URL: ,502 Server Error: Bad Gateway for url:
https://api.stlouisfed.org/fred/series/observations?series_id=...&api_key=...'.
Dieser Text landete an drei Stellen:

    api_health_status.last_error_message   (Datenbank, damit in jeder Sicherung)
    data/tradinginfotool.log               (die Log-Zeile ,FRED-Abruf fehlgeschlagen')
    notebook_diagnose.json                 (Log-Auszug und Ampel - im Google-Drive-
                                            Austauschordner; am 15.09. 8 Treffer)

Betroffen sind alle Anbieter, die ihren Schluessel als URL-Parameter tragen:
FRED und EIA (`api_key`), Finnhub (`token`). Gemini schickt ihn im Header und
war nicht betroffen.

EINE REGEL AN EINER STELLE. Maskiert wird der WERT eines Parameters, dessen
NAME ein Schluessel ist - `?api_key=abc` wird `?api_key=***`. Nur nach `?` oder
`&`, damit Fliesstext wie ,key=value-Paare' unberuehrt bleibt. Der Name bleibt
stehen: ,welcher Anbieter, welcher Aufruf' soll man im Fehlertext weiter lesen
koennen.
"""
from __future__ import annotations

import logging
import re

# Parameternamen, deren Wert ein Geheimnis ist.
SCHLUESSEL_PARAMETER = ("api_key", "apikey", "api-key", "key", "token",
                        "access_token", "x_cg_demo_api_key", "x_cg_pro_api_key")

_MUSTER = re.compile(
    r"([?&](?:%s)=)[^&\s'\"<>]+" % "|".join(re.escape(p) for p in SCHLUESSEL_PARAMETER),
    re.IGNORECASE)

MASKE = "***"


def maskiere(text):
    """Text mit ersetzten Schluesselwerten - andere Typen unveraendert zurueck."""
    if not isinstance(text, str) or "=" not in text:
        return text
    return _MUSTER.sub(r"\1" + MASKE, text)


def maskiere_tief(obj):
    """Wie `maskiere`, aber durch Listen und dicts hindurch (fuer den Export)."""
    if isinstance(obj, str):
        return maskiere(obj)
    if isinstance(obj, list):
        return [maskiere_tief(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(maskiere_tief(x) for x in obj)
    if isinstance(obj, dict):
        return {k: maskiere_tief(v) for k, v in obj.items()}
    return obj


class MaskierFormatter(logging.Formatter):
    """Formatiert wie gewohnt und maskiert danach die FERTIGE Zeile.

    Auf der fertigen Zeile, nicht auf `record.msg`: der Schluessel steckt oft in
    den Argumenten (`%s` mit der Exception) oder im Traceback, den erst
    `formatException` anhaengt."""

    def format(self, record: logging.LogRecord) -> str:
        return maskiere(super().format(record))


def maskiere_handler(handlers) -> int:
    """Setzt auf jedem Handler einen MaskierFormatter mit dessen bisherigem Format."""
    n = 0
    for h in handlers or []:
        alt = h.formatter
        if isinstance(alt, MaskierFormatter):
            continue
        h.setFormatter(MaskierFormatter(
            getattr(alt, "_fmt", None), getattr(alt, "datefmt", None)))
        n += 1
    return n
