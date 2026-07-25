# -*- coding: utf-8 -*-
"""Signal-Stabilitaet ueber die letzten Bewertungszyklen (2026-07-25, echter
NEAR/LINK-Fund): bei 10-20 Signalen/Tag ist eine an der Gate-Schwelle
oszillierende Konfidenz kein Einzelfall, sondern ein strukturelles Muster -
macht sichtbar, ob ein Signal ueber mehrere Zyklen KONSISTENT war (wie eine
ueber Stunden bestaetigte Kontrathese) oder zwischen Aktionen/Konfidenzwerten
hin- und herspringt, ohne dass der Nutzer die Rohhistorie manuell nachvoll-
ziehen muss. Nutzt AUSSCHLIESSLICH bereits gespeicherte Signale (`hebel_
signals`/`signals`) - keine neue Datenquelle, reiner lokaler DB-Read.

Krypto Spot+Hebel. Kein Deckel/Veto - beeinflusst NICHT die eigene Konfidenz-
Berechnung des aktuellen Laufs (sonst zirkulaer), dient nur der Transparenz.

**Kategorie- vs. Tier-Wechsel (2026-07-25, Nutzer-Nachschaerfung nach echtem
Reproduktionstest):** ein roher String-Vergleich der `action`-Werte reicht
NICHT - er verwechselt zwei grundverschiedene Uebergaenge. Bei NEAR wechselte
die Aktion mehrfach zwischen TEILVERKAUF und SCHLIESSEN, WEIL die Kontrathese-
Uebersetzung (hebel_risk_gate.py) bei 70% Konfidenz auf SCHLIESSEN hochstuft
und bei 55-70% wieder auf TEILVERKAUF zurueckfaellt - eine reine Tier-
Feinjustierung INNERHALB derselben durchgehend gehaltenen Gegenthese (Modell
sah die ganze Zeit ueber SHORT gegen die offene LONG-Position), keine neue
Meinung. Bei LINK dagegen wechselte die Aktion zwischen ERÖFFNEN und HALTEN -
ein echter Wechsel zwischen "es gibt ein valides Setup" und "es gibt keins".
Deshalb werden die 7 Hebel-/5 Spot-Aktionen in drei Kategorien gruppiert -
nur ein Wechsel ZWISCHEN Kategorien zaehlt als echte Instabilitaet, ein
Wechsel INNERHALB derselben Kategorie (z.B. TEILVERKAUF<->SCHLIESSEN oder
ERÖFFNEN<->NACHKAUFEN) nur als informativer Tier-Wechsel ohne Warncharakter."""
from __future__ import annotations

DEFAULT_ANZAHL_ZYKLEN = 6
DEFAULT_SPANNWEITE_SCHWELLE_PCT = 10.0

# Aufbau (Risiko erhoehen/neue Position bullisch) vs. Abbau (Risiko
# reduzieren/Gegenthese) vs. Neutral - eine gemeinsame Zuordnung fuer beide
# Aktions-Vokabulare (Hebel 7, Spot 5), da sich die Strings nicht ueberschneiden.
_KATEGORIE_AUFBAU = "aufbau"
_KATEGORIE_ABBAU = "abbau"
_KATEGORIE_NEUTRAL = "neutral"

_AKTIONS_KATEGORIE = {
    # Hebel
    "ERÖFFNEN": _KATEGORIE_AUFBAU,
    "NACHKAUFEN": _KATEGORIE_AUFBAU,
    "HEBEL_ERHÖHEN": _KATEGORIE_AUFBAU,
    "TEILVERKAUF": _KATEGORIE_ABBAU,
    "SCHLIESSEN": _KATEGORIE_ABBAU,
    "HEBEL_SENKEN": _KATEGORIE_ABBAU,
    "HALTEN": _KATEGORIE_NEUTRAL,
    # Spot (NACHKAUFEN bereits oben gemeinsam mit Hebel)
    "KAUFEN": _KATEGORIE_AUFBAU,
    "VERKAUFEN": _KATEGORIE_ABBAU,
    "TAUSCHEN": _KATEGORIE_ABBAU,
}


def _kategorie(action: str) -> str:
    return _AKTIONS_KATEGORIE.get(action, _KATEGORIE_NEUTRAL)


def signal_stabilitaet_fakt(verlauf: list, config: dict | None) -> dict | None:
    """Baut den Fakt fuer build_facts()/build_hebel_facts(). `verlauf` sind die
    letzten Bewertungen desselben (symbol[, richtung]) VOR dem aktuellen Lauf,
    neueste zuerst (siehe db.get_hebel_signal_history()/get_signal_history(),
    beide bereits ORDER BY created_at DESC) - der gerade entstehende Wert
    dieses Laufs ist bewusst NICHT enthalten, damit er sich nicht selbst
    vergleicht. None, wenn deaktiviert oder weniger als 2 historische
    Konfidenzwerte vorliegen (nichts zu vergleichen)."""
    cfg = (config or {}).get("signal_stabilitaet", {})
    if not cfg.get("aktiv", True):
        return None
    if not verlauf:
        return None

    anzahl_zyklen = cfg.get("anzahl_zyklen", DEFAULT_ANZAHL_ZYKLEN)
    zyklen = [s for s in verlauf[:anzahl_zyklen] if s.confidence_pct is not None]
    if len(zyklen) < 2:
        return None

    konfidenzen = [s.confidence_pct for s in zyklen]
    konfidenz_min = min(konfidenzen)
    konfidenz_max = max(konfidenzen)
    spannweite = konfidenz_max - konfidenz_min

    aktionen = [s.action for s in zyklen]
    kategorien = [_kategorie(a) for a in aktionen]
    anzahl_kategoriewechsel = sum(1 for a, b in zip(kategorien, kategorien[1:]) if a != b)
    # Aktionswechsel INNERHALB derselben Kategorie (z.B. TEILVERKAUF<->SCHLIESSEN) -
    # reine Tier-Feinjustierung, kein eigener Meinungswechsel.
    anzahl_tier_wechsel = sum(
        1 for a, b, ka, kb in zip(aktionen, aktionen[1:], kategorien, kategorien[1:])
        if a != b and ka == kb
    )

    schwelle = cfg.get("spannweite_schwelle_pct", DEFAULT_SPANNWEITE_SCHWELLE_PCT)
    stabil = spannweite < schwelle and anzahl_kategoriewechsel <= 1

    tier_hinweis = (
        f" (davon {anzahl_tier_wechsel}x reine Tier-Feinjustierung innerhalb derselben "
        "Kategorie, z.B. Teilverkauf/Schliessen)" if anzahl_tier_wechsel else ""
    )
    if stabil:
        einordnung = (
            f"Konfidenz blieb über die letzten {len(zyklen)} Bewertungen stabil zwischen "
            f"{konfidenz_min:.0f}% und {konfidenz_max:.0f}% ({anzahl_kategoriewechsel} echte(r) "
            f"Kategoriewechsel{tier_hinweis}) - verlässlicheres, durchgehend bestätigtes Signal."
        )
    else:
        einordnung = (
            f"Konfidenz schwankte über die letzten {len(zyklen)} Bewertungen zwischen "
            f"{konfidenz_min:.0f}% und {konfidenz_max:.0f}% ({anzahl_kategoriewechsel}x echter "
            f"Kategoriewechsel{tier_hinweis}) - instabiler als ein durchgehend bestätigtes Signal, "
            "geringere Verlässlichkeit."
        )

    return {
        "anzahl_bewertungen": len(zyklen),
        "konfidenz_min_pct": konfidenz_min,
        "konfidenz_max_pct": konfidenz_max,
        "konfidenz_spannweite_pct": round(spannweite, 1),
        "anzahl_kategoriewechsel": anzahl_kategoriewechsel,
        "anzahl_tier_wechsel": anzahl_tier_wechsel,
        "stabil": stabil,
        "einordnung": einordnung,
        # chronologisch aufsteigend (aeltester zuerst) - direkt nutzbar fuer
        # ui/signal_stabilitaet_chart.py, kein zweiter DB-Zugriff noetig.
        # `kategorie` bereits mitgeliefert, damit der Chart-Renderer die
        # Aufbau/Abbau/Neutral-Zuordnung nicht selbst dupliziert (eine Quelle
        # der Wahrheit fuer die Kategorie-Zuordnung).
        "verlauf": [
            {"datum": s.created_at, "konfidenz_pct": s.confidence_pct, "action": s.action,
             "kategorie": _kategorie(s.action)}
            for s in reversed(zyklen)
        ],
    }
