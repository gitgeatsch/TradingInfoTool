"""P-10-Schwellenwerte fuer "veraltet" - Domaenenlogik, kein UI-Detail. Wird sowohl von
ui/formatting.py (Anzeige) als auch von agent/pipeline.py (Datenqualitaets-Gate R-5.0)
gebraucht - lebt deshalb auf Top-Level statt in ui/, um eine agent/ -> ui/ Abhaengigkeit
zu vermeiden."""
from __future__ import annotations

from datetime import datetime, timezone

# P-10 / Spezifikation Kap. 16: Schwellenwerte fuer "veraltet"
PRICE_STALE_THRESHOLD_MINUTES = 30  # 2x 15-Min-Scheduler-Takt
HISTORY_STALE_THRESHOLD_DAYS = 2  # 1 Tag Rueckstand ist normal, 2+ deutet auf Ausfall hin


def _parse_utc(timestamp: str) -> datetime:
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_price_stale(fetched_at: str | None) -> bool:
    if fetched_at is None:
        return True
    age_minutes = (datetime.now(timezone.utc) - _parse_utc(fetched_at)).total_seconds() / 60
    return age_minutes > PRICE_STALE_THRESHOLD_MINUTES


def format_price_age(fetched_at: str | None) -> str:
    if fetched_at is None:
        return "nie aktualisiert"
    age_minutes = int((datetime.now(timezone.utc) - _parse_utc(fetched_at)).total_seconds() / 60)
    if age_minutes < 1:
        return "gerade eben"
    if age_minutes < 60:
        return f"vor {age_minutes} Min."
    age_hours = age_minutes // 60
    return f"vor {age_hours} Std."


def is_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > HISTORY_STALE_THRESHOLD_DAYS


# Makro-Daten (api/macro.py, api/onchain.py) haben eine grundlegend andere natuerliche
# Aktualisierungs-Kadenz als Preise - CPI/M2 werden nur monatlich veroeffentlicht, mit
# typischerweise 4-8 Wochen Meldeverzug; Leitzinsen aendern sich nur an Notenbank-
# Sitzungsterminen (alle 6-8 Wochen). Die 30-Minuten-Preis-Schwelle waere hier
# permanent falsch (jeder CPI-Wert waere staendig "veraltet").
#
# WICHTIGE EINSCHRAENKUNG (bewusst nicht geloest, siehe Spezifikation Kap. 16):
# `MacroSnapshot.fetched_at` ist EIN Zeitstempel fuers gesamte Zeilen-Upsert, nicht
# je Einzelfeld (COALESCE-Upsert, siehe agent/pipeline.py::_update_macro_snapshot).
# Faellt z.B. FRED laengere Zeit aus, aber PBoC wird weiterhin taeglich erfolgreich
# aktualisiert, bumped das `fetched_at` trotzdem - ohne dass die FRED-Felder wirklich
# neu sind. Echte feld-genaue Frische braeuchte eine Schema-Erweiterung (pro Feld ein
# eigenes "zuletzt erfolgreich aktualisiert"). Diese Funktion prueft nur "haben wir
# ueberhaupt kuerzlich erfolgreich IRGENDEINEN Wert der Zeile geschrieben", nicht
# "ist genau dieses Feld frisch" - besser als gar keine Pruefung, aber keine exakte.
MACRO_STALE_THRESHOLD_DAYS = {
    "zins": 60,  # Fed/EZB/BoJ/BoK/PBoC-LPR - Notenbanken tagen alle 6-8 Wochen
    "wirtschaftsdaten": 60,  # CPI/M2/ISM-Ersatz (Philly-Fed) - monatlich, Meldeverzug
    "onchain": 4,  # MVRV/NUPL/Realized-Price/Exchange-Flows/Stablecoin-Supply - taeglich
    "krypto_makro": 2,  # BTC-Dominanz/Fear&Greed - bereits bestehend, taeglich
}


def is_macro_value_stale(fetched_at: str | None, category: str) -> bool:
    if category not in MACRO_STALE_THRESHOLD_DAYS:
        raise ValueError(
            f"Unbekannte Makro-Kategorie: {category!r} - erwartet einen von "
            f"{sorted(MACRO_STALE_THRESHOLD_DAYS)}"
        )
    if fetched_at is None:
        return True
    threshold_days = MACRO_STALE_THRESHOLD_DAYS[category]
    age_days = (datetime.now(timezone.utc) - _parse_utc(fetched_at)).total_seconds() / 86400
    return age_days > threshold_days
