"""Merkmalsaufbereitung fuer die Ausschuss-Suche (2026-08-04, Phase 1.2).

Wandelt Signalzeilen in die Merkmalsmatrix, die ausschuss_suche.py erwartet.
Drei Entscheidungen praegen das Ergebnis und stehen deshalb hier oben:

1. ZONEN NUR RELATIV. Absolute Preisfelder haben eine Intraklassen-
   Korrelation von 0,998-1,000 (gemessen 04.08.) - sie SIND Symbol-Kennungen.
   Ein Schnitt auf `entry_usd_von` trennt BTC von KAIA, nicht gute von
   schlechten Signalen. Stattdessen werden `stop_rel`, `crv` und
   `ziel_abstand_rel` abgeleitet; die tragen dieselbe Information
   symbolunabhaengig.

2. KATEGORIEN WERDEN EINZELN AUFGETRENNT, nicht durchnummeriert. Ein
   Schwellenschnitt auf einen willkuerlichen Zahlencode ("regime >= 2")
   trennt eine zufaellige Gruppe von Regimes von einer anderen - das ist
   keine Regel, die jemand umsetzen koennte. Jede Auspraegung wird deshalb
   ein eigenes 0/1-Merkmal ("regime ist krise_extrem"). Nur Auspraegungen
   mit ausreichend Faellen, sonst entstehen Merkmale, die genau einen
   Fall markieren.

3. FREITEXT FAELLT RAUS. `short_reasoning`, `key_risks_text` und die
   `top_grund_*_text` tragen Information, aber ihre Auswertung waere eine
   eigene Methodik (Einbettungen, Themenmodelle) mit eigener
   Falschtrefferproblematik. Bewusst nicht in diesem Schritt - dokumentiert
   als offener Punkt statt still weggelassen.
"""
from __future__ import annotations

import json
import math

import numpy as np

# Auspraegungen unter dieser Haeufigkeit werden nicht zu eigenen Merkmalen -
# sonst entsteht ein 0/1-Merkmal, das drei Faelle markiert, und der
# Max-Statistik-Suchraum blaeht sich mit reinem Rauschen auf.
MIN_KATEGORIE_ANTEIL = 0.05

# Felder, die kein Merkmal sind: Ergebnis, Zeitstempel, Identitaet, Freitext.
# `risk_veto` steht hier, weil es die Gruppeneinteilung IST - als Merkmal
# waere es ein perfekter, zirkulaerer Praediktor.
KEIN_MERKMAL = frozenset({
    "id", "symbol", "created_at", "risk_veto", "gate_passed",
    "risk_veto_reason", "cash_veto",
    # Freitext ohne erkennbare Endung. `gegenargument` rutschte im ersten
    # Lauf durch und wurde je FORMULIERUNG zu einem eigenen 0/1-Merkmal -
    # beim Spot-Tier war der "beste Kandidat" prompt ein Textbaustein
    # ("Die technische Konfluenz ist gemischt, und das CRV ist nur knapp
    # ueber der Mindestgrenze von 2.0"). Solche Merkmale sind doppelt
    # untauglich: sie zerfallen bei jeder Umformulierung des Prompts, und
    # sie bilden nur ab, was das Gate ohnehin schon entschieden hat.
    "gegenargument",
})
FREITEXT_ENDUNGEN = ("_text", "_reasoning", "_note", "_hinweis",
                     "_kurzbegruendung", "_begruendung", "_bedingung_text")
# Zusaetzlicher Schutz: eine Auspraegung mit mehr Zeichen als hier ist
# Freitext, egal wie das Feld heisst. Kategorien sind kurz ("krise_extrem",
# "makro"), Saetze nicht.
MAX_KATEGORIE_LAENGE = 40


def _zahl(v):
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(float(v)) else None
    return None


def _zonen_relativ(row) -> dict[str, float] | None:
    """stop_rel, crv und Zielabstand aus den Zonen - symbolunabhaengig.

    Kantenwahl wie im Risk-Gate und in _zonen_absolut(): bei bullischer These
    die konservativen Kanten (stop_von/take_von), bei bearischer die
    gespiegelten. Eine zweite Fassung derselben Formel waere ein
    Driftrisiko - die Werte muessen zu backward_tracking.py passen."""
    def f(name):
        v = row.get(name)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    e_von, e_bis = f("entry_usd_von"), f("entry_usd_bis")
    s_von, s_bis = f("stop_loss_usd_von"), f("stop_loss_usd_bis")
    t_von, t_bis = f("take_profit_usd_von"), f("take_profit_usd_bis")
    if e_von is None or s_von is None or t_von is None:
        return None
    e = (e_von + (e_bis if e_bis is not None else e_von)) / 2.0
    if e <= 0:
        return None
    ist_short = t_von < e
    if ist_short:
        if s_bis is None or t_bis is None:
            return None
        stop, ziel = s_bis, t_bis
    else:
        stop, ziel = s_von, t_von
    risiko = (stop - e) if ist_short else (e - stop)
    if risiko <= 0:
        return None
    chance = (e - ziel) if ist_short else (ziel - e)
    if chance <= 0:
        return None
    return {"z_stop_rel": risiko / e, "z_crv": chance / risiko,
            "z_ziel_abstand_rel": chance / e, "z_ist_short": 1.0 if ist_short else 0.0}


def _risikofaktoren_anzahl(row) -> float | None:
    """Wie viele Risikofaktoren hat das Signal? Aus risikofaktoren_json.

    Die Anzahl ist eine echte Merkmalsgroesse - der Inhalt waere Freitext.
    Am 29.07. wurde die Haeufung einmal untersucht und kein belastbarer
    Zusammenhang gefunden; hier geht sie neu und mit Falschtrefferkontrolle
    in die Suche ein statt als Einzelbefund."""
    roh = row.get("risikofaktoren_json")
    if not roh:
        return None
    try:
        daten = json.loads(roh) if isinstance(roh, str) else roh
    except (ValueError, TypeError):
        return None
    if isinstance(daten, list):
        return float(len(daten))
    if isinstance(daten, dict):
        return float(len(daten))
    return None


def baue_merkmale(rows: list[dict], min_befuellung: float = 0.6,
                  ) -> tuple[np.ndarray, list[str], list[str]]:
    """Merkmalsmatrix, Merkmalsnamen und Bericht ueber das Weggelassene.

    Rueckgabe (X, namen, bericht). Zeilen, in denen ein aufgenommenes Merkmal
    fehlt, bekommen den Median dieses Merkmals - bei Befuellungsquoten ueber
    60 % ist das unkritisch und ehrlicher als die Zeile zu verwerfen, was die
    Population verzerren wuerde."""
    n = len(rows)
    spalten: dict[str, list] = {}
    bericht: list[str] = []

    # 1. Abgeleitete Zonen-Merkmale, relativ
    zonen = [_zonen_relativ(r) for r in rows]
    for schluessel in ("z_stop_rel", "z_crv", "z_ziel_abstand_rel", "z_ist_short"):
        spalten[schluessel] = [(z or {}).get(schluessel) for z in zonen]
    spalten["z_risikofaktoren_anzahl"] = [_risikofaktoren_anzahl(r) for r in rows]

    # 2. Rohfelder sichten
    alle_felder = sorted({k for r in rows for k in r})
    for feld in alle_felder:
        if feld in KEIN_MERKMAL or feld in FREITEXT_ENDUNGEN:
            continue
        if feld.endswith(FREITEXT_ENDUNGEN):
            continue
        if feld.startswith(("outcome_", "veto_outcome_", "selbst_halten_")):
            continue
        werte = [r.get(feld) for r in rows]
        befuellt = sum(1 for v in werte if v is not None) / n
        if befuellt < min_befuellung:
            continue

        zahlen = [_zahl(v) for v in werte]
        if sum(1 for z in zahlen if z is not None) / n >= min_befuellung:
            # Konstante Merkmale koennen nie trennen
            gueltig = [z for z in zahlen if z is not None]
            if len(set(gueltig)) > 1:
                spalten[feld] = zahlen
            continue

        # Kategorie: je Auspraegung ein 0/1-Merkmal
        if all(v is None or isinstance(v, str) for v in werte):
            # Lange Auspraegungen sind Freitext, unabhaengig vom Feldnamen
            if any(len(v) > MAX_KATEGORIE_LAENGE for v in werte if v):
                bericht.append(f"{feld}: als Freitext uebersprungen "
                               f"(Auspraegung laenger als {MAX_KATEGORIE_LAENGE} Zeichen)")
                continue
            haeufig = {}
            for v in werte:
                if v is not None:
                    haeufig[v] = haeufig.get(v, 0) + 1
            for auspraegung, anzahl in sorted(haeufig.items()):
                if anzahl / n < MIN_KATEGORIE_ANTEIL or anzahl == n:
                    continue
                spalten[f"{feld}={auspraegung}"] = [
                    (1.0 if v == auspraegung else 0.0) if v is not None else None
                    for v in werte]

    # 3. Matrix bauen, fehlende Werte auf den Median
    namen = sorted(spalten)
    if not namen:
        return np.empty((n, 0)), [], ["keine brauchbaren Merkmale"]
    X = np.empty((n, len(namen)))
    for j, name in enumerate(namen):
        spalte = spalten[name]
        gueltig = np.array([v for v in spalte if v is not None], dtype=float)
        if len(gueltig) == 0:
            X[:, j] = 0.0
            continue
        median = float(np.median(gueltig))
        fehlend = sum(1 for v in spalte if v is None)
        if fehlend:
            bericht.append(f"{name}: {fehlend} Werte auf Median {median:.4g} gesetzt")
        X[:, j] = [median if v is None else float(v) for v in spalte]

    # Konstante Spalten entfernen - sie erzeugen nur -inf-Statistiken
    behalten = [j for j in range(len(namen)) if X[:, j].std() > 0]
    if len(behalten) < len(namen):
        weg = [namen[j] for j in range(len(namen)) if j not in behalten]
        bericht.append(f"{len(weg)} konstante Merkmale entfernt: {weg[:5]}")
    return X[:, behalten], [namen[j] for j in behalten], bericht
