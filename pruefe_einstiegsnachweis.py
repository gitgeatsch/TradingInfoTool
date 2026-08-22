# -*- coding: utf-8 -*-
"""Wurde der Einstieg ueberhaupt je erreicht? (22.08.2026, Umbauplan 127)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS - UND ER IST EIN VERDACHT AUF EINEN UMSETZUNGSFEHLER, nicht auf
ein Modell. Nutzerfrage, woertlich:

    "eigentlich sollten die 'LLM optimierten' Ergebnisse auch eine bessere
     Trefferquote bieten und wenn nicht - was der Trend aktuell sagt - machen
     wir etwas falsch oder es gibt noch Fehler in der Umsetzung, bevor wir
     das Modell als Begruendung sehen."

Der Trend sagt etwas anderes, und zwar etwas UNMOEGLICHES. Die Rollen-Kette
meldet ueber 116 aufgeloeste Signale eine Trefferquote von 82,8 %:

    CRV geplant (Zonenmitten)            2,00  ->  Basisrate 33,3 %
    CRV wie der Tracker rechnet          1,75  ->  Basisrate 36,4 %
    gemessene Trefferquote                        82,8 %
    unerklaerte Luecke                            +46 Punkte

⚠️ KEIN MODELL ERZEUGT +46 PUNKTE. Bevor irgendetwas ueber Modellqualitaet
gesagt wird, muss die MESSUNG geprueft werden.

BEREITS AUSGESCHLOSSEN (an der Quelle nachgesehen):

    Zonenkanten-Konvention      existiert, erklaert 3 Punkte - nicht 46
    Stop und Ziel in einer      korrekt: der Stop gewinnt (vorsichtig)
      Kerze
    Gap-bewusster Fill          vorhanden und richtig
    Aufloesung am selben Tag    83,3 % gegen 82,3 % - kein Unterschied

WAS UEBRIG BLEIBT, UND ES SIND ZWEI DINGE:

  E1  `check_signal_outcome` prueft NIE, ob der Einstieg erreicht wurde.
      Sie beginnt bei `entry_mid` und wartet auf Ziel oder Stop - auch wenn
      der Kurs die Einstiegszone nie beruehrt hat. Bei NACHKAUFEN (90 %
      Trefferquote) liegt die Zone typisch UNTER dem Markt; steigt der Kurs,
      gilt das Ziel als erreicht, ohne dass je gekauft worden waere.

  E2  `min_date = signal.created_at[:10]` nimmt die GANZE Tageskerze des
      Erstellungstags - samt Hoch und Tief, die VOR dem Signal lagen.

DIE FRAGE, VORAB FESTGELEGT:

    Wie viele der aufgeloesten Signale haetten ihr Ergebnis auch dann, wenn
    der Einstieg erreicht sein MUESSTE, bevor Ziel oder Stop zaehlen?

⚠️ VIER ARME, DAMIT SICH DIE ZWEI URSACHEN TRENNEN LASSEN:

    A  wie der Betrieb          Tag einschliessen, Einstieg NICHT verlangt
    B  Tag ausschliessen        ab dem Folgetag, Einstieg nicht verlangt
    C  Einstieg verlangt        Tag einschliessen, Einstieg zuerst
    D  beides                   ab dem Folgetag UND Einstieg zuerst

Arm A muss das reproduzieren, was in der Datenbank steht - tut er das nicht,
ist mein Nachbau falsch und nicht der Betrieb. DAS IST DIE ERSTE PRUEFUNG,
und sie entscheidet, ob der Rest ueberhaupt etwas wert ist.

DIE DATENQUELLE ist `preishistorie_signal_symbole` aus dem NB-Export - die
ECHTEN Kurse des Betriebs, nicht meine Binance-Messreihen. Gerechnet wird in
USD, weil die Zonen des Trackers in USD stehen.

    python pruefe_einstiegsnachweis.py [--export PFAD]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, ".")

AUFGELOEST = ("take_profit_erreicht", "stop_loss_erreicht")


def _lade(pfad: str) -> tuple:
    roh = io.open(pfad, encoding="utf-8").read()
    dec = json.JSONDecoder()

    def hol(name):
        m = re.search(r'"%s"\s*:\s*' % re.escape(name), roh)
        return dec.raw_decode(roh, m.end())[0] if m else None

    return hol("spot_signals") or [], hol("preishistorie_signal_symbole") or {}


def _kerzen(hist: dict) -> dict:
    """symbol -> [(datum, open, high, low), ...] in USD, aufsteigend.

    ⚠️ NUR USD. Die Zonen des Trackers stehen in USD; die Historie traegt
    beide Waehrungen als getrennte Zeilen. Sie zu mischen waere genau der
    Fehler, den `pruefe_waehrungen.py` seit dem 20.08. sucht."""
    aus: dict = {}
    for sym, zeilen in (hist.get("preishistorie_je_symbol") or {}).items():
        reihe = [(z["date"], z.get("open"), z.get("high"), z.get("low"))
                 for z in zeilen
                 if str(z.get("currency")).upper() == "USD"
                 and z.get("high") is not None and z.get("low") is not None]
        if reihe:
            aus[sym] = sorted(reihe)
    return aus


def _zonen(x: dict) -> tuple | None:
    """(entry_mid, entry_von, entry_bis, stop, ziel) - Kanten wie im Tracker.

    Bei LONG nimmt `_zonen_schwelle` die `_von`-Kante fuer Stop UND Ziel.
    Hier wird nur LONG geprueft; SHORT laeuft in der Spot-Familie nicht."""
    ev, eb = x.get("entry_usd_von"), x.get("entry_usd_bis")
    sv = x.get("stop_loss_usd_von")
    tv = x.get("take_profit_usd_von")
    if None in (ev, eb, sv, tv):
        return None
    e = (float(ev) + float(eb)) / 2.0
    if not (float(tv) > e > float(sv)):
        return None            # kein LONG-Aufbau
    return e, float(ev), float(eb), float(sv), float(tv)


def _durchlauf(reihe, ab_datum: str, z, tag_einschliessen: bool,
               einstieg_verlangt: bool) -> str:
    """'ziel' | 'stop' | 'offen' - ein Vorwaertsdurchlauf, vier Varianten."""
    _e, e_von, e_bis, stop, ziel = z
    erreicht = not einstieg_verlangt
    for datum, _o, hoch, tief in reihe:
        if datum < ab_datum or (not tag_einschliessen and datum == ab_datum):
            continue
        hoch, tief = float(hoch), float(tief)
        if not erreicht:
            # ⚠️ DIE ZONE GILT ALS BERUEHRT, wenn die Tagesspanne sie
            # schneidet. Grosszuegig zugunsten des Betriebs - eine strengere
            # Lesart wuerde den Befund nur verstaerken.
            if tief <= e_bis and hoch >= e_von:
                erreicht = True
            else:
                continue
        # Vorsichtige Lesart wie im Betrieb: faellt beides, gilt der Stop.
        if tief <= stop:
            return "stop"
        if hoch >= ziel:
            return "ziel"
    return "offen"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=None)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pfad = a.export
    if not pfad:
        from extract_notebook_diagnose import _google_drive_wurzel
        pfad = os.path.join(_google_drive_wurzel(), "Claude_Austauschordner",
                            "Notebook_Analysedaten", "notebook_diagnose.json")
    print("=" * 78)
    print("WURDE DER EINSTIEG UEBERHAUPT JE ERREICHT?")
    print(f"  Kurse aus dem NB-Export, USD: {os.path.basename(pfad)}")
    print("=" * 78)

    signale, hist = _lade(pfad)
    kerzen = _kerzen(hist)
    print(f"  {len(kerzen)} Symbole mit USD-Kerzen")

    faelle = []
    ohne_kurse = ohne_zonen = 0
    for x in signale:
        if x.get("quelle_kette") != "rollen":
            continue
        if x.get("outcome_status") not in AUFGELOEST:
            continue
        z = _zonen(x)
        if z is None:
            ohne_zonen += 1
            continue
        reihe = kerzen.get(x.get("symbol"))
        if not reihe:
            ohne_kurse += 1
            continue
        faelle.append((x, z, reihe))
    print(f"  {len(faelle)} aufgeloeste LONG-Signale der Rollen-Kette "
          f"pruefbar")
    print(f"  ({ohne_zonen} ohne brauchbare Zonen, {ohne_kurse} ohne Kurse)")
    if len(faelle) < 20:
        print("  ⚠️ ZU WENIGE - die Frage ist so nicht beantwortbar")
        return 2

    arme = {
        "A wie der Betrieb": (True, False),
        "B ab dem Folgetag": (False, False),
        "C Einstieg verlangt": (True, True),
        "D beides": (False, True),
    }
    ergebnis = {}
    for name, (tag, einstieg) in arme.items():
        z = [_durchlauf(r, x["created_at"][:10], zz, tag, einstieg)
             for x, zz, r in faelle]
        ergebnis[name] = z

    echt = [x["outcome_status"] for x, _z, _r in faelle]
    tp_echt = sum(1 for s in echt if s == "take_profit_erreicht")
    print(f"\n{'-' * 78}")
    print("DIE VIER ARME")
    print(f"{'-' * 78}")
    print(f"  {'Arm':24}{'Ziel':>7}{'Stop':>7}{'offen':>7}"
          f"{'Quote':>10}   Anmerkung")
    print(f"  {'DATENBANK (Betrieb)':24}{tp_echt:>7}"
          f"{len(echt) - tp_echt:>7}{0:>7}"
          f"{100 * tp_echt / len(echt):9.1f} %")
    for name, z in ergebnis.items():
        ziel = z.count("ziel")
        stop = z.count("stop")
        offen = z.count("offen")
        ent = ziel + stop
        print(f"  {name:24}{ziel:>7}{stop:>7}{offen:>7}"
              f"{(100 * ziel / ent if ent else float('nan')):9.1f} %")

    # ⚠️ DIE ERSTE PRUEFUNG IST DIE WICHTIGSTE: reproduziert Arm A den
    # Betrieb? Wenn nicht, ist mein Nachbau falsch und der Rest wertlos.
    a_ziel = sum(1 for s, e in zip(ergebnis["A wie der Betrieb"], echt)
                 if (s == "ziel") == (e == "take_profit_erreicht")
                 and s != "offen")
    a_ent = sum(1 for s in ergebnis["A wie der Betrieb"] if s != "offen")
    print(f"\n{'-' * 78}")
    print("GEGENPRUEFUNG: REPRODUZIERT ARM A DEN BETRIEB?")
    print(f"{'-' * 78}")
    print(f"  entschieden in A: {a_ent} von {len(echt)}")
    print(f"  davon gleich wie die Datenbank: {a_ziel} "
          f"({100 * a_ziel / max(a_ent, 1):.1f} %)")
    if a_ent and a_ziel / a_ent < 0.85:
        print("  ⚠️ ARM A REPRODUZIERT DEN BETRIEB NICHT.")
        print("     Damit ist MEIN NACHBAU verdaechtig, nicht der Betrieb -")
        print("     die Arme B/C/D sind erst zu lesen, wenn A stimmt.")
    else:
        print("  OK - der Nachbau trifft den Betrieb")

    if a_ent and a_ziel / a_ent >= 0.85:
        c = ergebnis["C Einstieg verlangt"]
        nie = sum(1 for s in c if s == "offen")
        print(f"\n{'-' * 78}")
        print("DER BEFUND")
        print(f"{'-' * 78}")
        print(f"  Signale, deren Einstieg NIE erreicht wurde: {nie} von "
              f"{len(faelle)} ({100 * nie / len(faelle):.1f} %)")
        print(f"  Sie stehen in der Datenbank trotzdem als aufgeloest.")
    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
