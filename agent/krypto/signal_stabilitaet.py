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


def _aktive_kategorie_wiederholt(kategorien: list) -> str | None:
    """2026-07-25, echter INJ-Fund (Nutzer-Diskussion): die alte Logik zaehlte
    JEDEN rohen Uebergang (a != b) - ein einzelner Ausflug in eine aktive
    Kategorie, umrahmt von Neutral (z.B. Neutral-Neutral-Eroeffnen-Neutral-
    Neutral, der normale Lebenszyklus "abwarten -> einmal handeln ->
    beobachten"), erzeugt dabei IMMER genau 2 Uebergaenge und wurde damit
    faelschlich als instabil gewertet, obwohl nur eine einzige Entscheidung
    getroffen wurde. Echte Instabilitaet (das urspruengliche LINK-Vorbild:
    wiederholtes Eroeffnen/Zurueckziehen) zeigt sich NICHT an der Zahl der
    Uebergaenge, sondern daran, dass dieselbe aktive Kategorie in MEHR ALS
    EINEM getrennten, durch etwas anderes unterbrochenen Abschnitt auftaucht.
    Komprimiert die Folge zu 'Runs' (aufeinanderfolgende gleiche Werte = ein
    Ereignis) und gibt die zuerst wiederkehrende aktive Kategorie zurueck
    (None, wenn keine wiederkehrt)."""
    runs = []
    for k in kategorien:
        if not runs or runs[-1] != k:
            runs.append(k)
    if runs.count(_KATEGORIE_AUFBAU) > 1:
        return _KATEGORIE_AUFBAU
    if runs.count(_KATEGORIE_ABBAU) > 1:
        return _KATEGORIE_ABBAU
    return None


def juengste_richtungswende(verlauf: list) -> dict | None:
    """2026-07-25, Nutzer-Diskussion (echter INJ-Fund): eine echte Richtungswende
    (Aufbau<->Abbau) ist IMMER bemerkenswert, unabhaengig vom Signal-
    Stabilitaets-Gesamturteil oben - eigener Risikofaktor statt Nebensatz
    (siehe hebel_risk_gate.py::richtungswende_risikofaktor()). `verlauf` ist
    neueste-zuerst sortiert (wie signal_stabilitaet_fakt() es bekommt).
    Neutral-Eintraege werden uebersprungen (nur die beiden zuletzt
    eingenommenen AKTIVEN Kategorien zaehlen als Vergleich) - Aufbau-Neutral-
    Abbau gilt also ebenfalls als Wende, nicht nur ein direkter Aufbau-Abbau-
    Uebergang. None, wenn keine zwei aktiven Eintraege vorliegen oder die
    juengste aktive Kategorie mit der davor uebereinstimmt (keine Wende)."""
    aktive = [
        (s.created_at, _kategorie(s.action), s.action)
        for s in verlauf if _kategorie(s.action) != _KATEGORIE_NEUTRAL
    ]
    if len(aktive) < 2:
        return None
    neu_zeit, neu_kat, neu_aktion = aktive[0]
    alt_zeit, alt_kat, alt_aktion = aktive[1]
    if neu_kat == alt_kat:
        return None
    return {
        "neue_kategorie": neu_kat, "neue_aktion": neu_aktion, "neuer_zeitpunkt": neu_zeit,
        "alte_kategorie": alt_kat, "alte_aktion": alt_aktion, "alter_zeitpunkt": alt_zeit,
    }


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
    konfidenz_schwankt = spannweite >= schwelle
    wiederkehrende_kategorie = _aktive_kategorie_wiederholt(kategorien)
    zu_viele_kategoriewechsel = wiederkehrende_kategorie is not None
    stabil = not konfidenz_schwankt and not zu_viele_kategoriewechsel

    tier_hinweis = (
        f" (davon {anzahl_tier_wechsel}x reine Tier-Feinjustierung innerhalb derselben "
        "Kategorie, z.B. Teilverkauf/Schliessen)" if anzahl_tier_wechsel else ""
    )
    konfidenz_text = (
        f"zwischen {konfidenz_min:.0f}% und {konfidenz_max:.0f}%" if konfidenz_min != konfidenz_max
        else f"durchgehend bei {konfidenz_min:.0f}%"
    )
    if stabil:
        einordnung = (
            f"Konfidenz blieb über die letzten {len(zyklen)} Bewertungen stabil ({konfidenz_text}, "
            f"{anzahl_kategoriewechsel} echte(r) Kategoriewechsel{tier_hinweis}) - verlässlicheres, "
            "durchgehend bestätigtes Signal."
        )
    else:
        # 2026-07-25, echter LINK-Fund: die alte Formulierung behauptete IMMER
        # "Konfidenz schwankte zwischen X% und Y%", selbst wenn X==Y (Instabilitaet
        # kann rein aus Kategoriewechseln kommen, ohne jede Konfidenz-Schwankung) -
        # fuer den Nutzer nicht nachvollziehbar/widerspruechlich wirkende Meldung.
        # Jetzt wird nur noch der tatsaechlich zutreffende Grund genannt.
        gruende = []
        if konfidenz_schwankt:
            gruende.append(
                f"Konfidenz schwankte {konfidenz_text} (Spannweite {spannweite:.0f} Prozentpunkte, "
                f"Schwelle {schwelle:.0f})"
            )
        if zu_viele_kategoriewechsel:
            gruende.append(
                f"Aktion kehrte mehrfach, mit Unterbrechung dazwischen, zu '{wiederkehrende_kategorie}' "
                f"zurück (statt einer einmaligen, durchgehenden Entscheidung){tier_hinweis}"
            )
        einordnung = (
            f"Instabil über die letzten {len(zyklen)} Bewertungen: {' UND '.join(gruende)} - "
            "geringere Verlässlichkeit als ein durchgehend bestätigtes Signal."
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
