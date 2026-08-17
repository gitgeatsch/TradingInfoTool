# -*- coding: utf-8 -*-
"""Behauptet das Modell Zahlen, die es nie bekommen hat? (17.08.2026)

DER ANLASS - Nutzerpruefung einer echten SOL-Mail, Punkt A6:

    Belege (5, davon 3 unabhaengige Faktoren):
      - Umsatzvolumen im 35. Perzentil deutet auf fehlendes Momentum hin

Im Faktenblock derselben Mail stand *"Volumen das 0,4-fache des Mittels
(Vortag)"* - kein Perzentil. Und `faktenblock.kern()` sagt ausdruecklich:

    "Das Perzentil erscheint NICHT im Text - es bestimmt nur das
     Urteilswort."

Das Modell hat aus dem Urteilswort UNGUENSTIG eine plausible Zahl
zurueckgerechnet und sie als Messung hingeschrieben. Es ist die Umkehrung
von R-T12: wir geben ein Etikett, das Modell baut daraus die Zahl, die wir
ihm bewusst vorenthalten haben.

WARUM DAS MEHR IST ALS EIN SCHOENHEITSFEHLER. Die Belege sind der Block,
den die Mail als BEWEIS praesentiert - mit Gewicht (hoch/mittel/gering) und
gezaehlt als "unabhaengige Faktoren". Eine erfundene Messung darin ist eine
Behauptung mit Siegel. Und sie ist nicht als solche erkennbar: "im 92.
Perzentil der letzten 400 Tage" liest sich exakt wie unsere echten Saetze.

WAS DIESES WERKZEUG NICHT KANN. Es prueft nicht jede Zahl gegen die Fakten
des jeweiligen Laufs - die Fakten werden je Signal nicht gespeichert, und
sie liessen sich nachtraeglich nicht rekonstruieren, ohne den Ankertag zu
verletzen. Es prueft die Faelle, in denen wir OHNE den Lauf zu kennen
wissen, dass es die Zahl nicht gegeben haben kann.

    KEINE FEHLALARME, DAFUER UNVOLLSTAENDIG - in dieser Reihenfolge.
    Von 33 Funden der ersten Prompt-Pruefung waren 31 Fehlalarme; nach dem
    dritten sieht niemand mehr hin.

Die Liste steht in `faktenblock.PERZENTIL_NUR_INTERN`, also NEBEN dem
Code, der die Perzentile zurueckhaelt - nicht hier. Wer dort etwas
aendert, aendert diese Pruefung mit.

    python pruefe_belege_gegen_fakten.py --db <NB-Sicherung>
    python pruefe_belege_gegen_fakten.py --export <notebook_diagnose.json>
    python pruefe_belege_gegen_fakten.py --selbsttest
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys

sys.path.insert(0, ".")

# "im 35. Perzentil", "(84. Perzentil)", "im 0. Perzentil der letzten 400"
_PERZENTIL = re.compile(r"(\d{1,3})\.\s*Perzentil", re.IGNORECASE)


def _familien() -> dict:
    """Aus dem Modul, das die Perzentile zurueckhaelt - nicht aus einer
    Kopie hier. Zwei Definitionen desselben Begriffs sind in diesem Projekt
    schon einmal auseinandergelaufen (Umbauplan 70.4)."""
    from agent.faktenblock import PERZENTIL_NUR_INTERN

    return {k: v for k, v in PERZENTIL_NUR_INTERN.items()
            if not v.get("auch_woanders")}


def pruefe_beleg(text: str, familien: dict | None = None) -> list[dict]:
    """Die Befunde zu EINEM Beleg - leere Liste heisst: nichts zu melden.

    Gemeldet wird nur, wenn BEIDES zutrifft: der Beleg nennt ein Perzentil
    UND er handelt von einer Groesse, deren Perzentil in keinem unserer
    Saetze vorkommt. Ein Beleg ueber die Finanzierungsrate nennt ein
    Perzentil voellig zu Recht - dort steht eines in den Fakten."""
    familien = familien if familien is not None else _familien()
    t = str(text or "")
    treffer = _PERZENTIL.findall(t)
    if not treffer:
        return []
    klein = t.lower()
    aus = []
    for name, eintrag in familien.items():
        if any(w in klein for w in eintrag["woerter"]):
            aus.append({"familie": name, "perzentile": treffer, "beleg": t})
    return aus


def pruefe_belege(belege: list, familien: dict | None = None) -> list[dict]:
    familien = familien if familien is not None else _familien()
    aus = []
    for b in belege or []:
        text = b.get("fakt") if isinstance(b, dict) else b
        aus += pruefe_beleg(text, familien)
    return aus


def aus_zeilen(zeilen: list) -> dict:
    """Zaehlt ueber viele Signale. `zeilen` sind dicts mit `belege_json`."""
    familien = _familien()
    befunde, belege_gesamt, signale_betroffen = [], 0, 0
    for r in zeilen or []:
        roh = r.get("belege_json")
        if not roh:
            continue
        try:
            belege = json.loads(roh)
        except (TypeError, ValueError):
            continue
        belege_gesamt += len(belege)
        treffer = pruefe_belege(belege, familien)
        if treffer:
            signale_betroffen += 1
            for t in treffer:
                befunde.append(dict(t, symbol=r.get("symbol"),
                                    erfasst_am=r.get("created_at")))
    return {"signale": len(zeilen or []), "belege": belege_gesamt,
            "befunde": befunde, "signale_betroffen": signale_betroffen,
            "quote_prozent": (100.0 * len(befunde) / belege_gesamt
                              if belege_gesamt else 0.0),
            "geprueft_auf": sorted(familien)}


def _selbsttest() -> int:
    """Beide Richtungen. Eine Pruefung, die nur Alarm schlagen kann, ist
    keine - sie waere mit `return ["Befund"]` erfuellt."""
    faelle = [
        ("Umsatzvolumen im 35. Perzentil deutet auf fehlendes Momentum", True),
        ("MORPHO Handelsvolumen im 100. Perzentil der letzten 400 Tage", True),
        ("MON: Umsatzvolumen 6.0 % (84. Perzentil) deutet auf Liquiditaet", True),
        # Die Finanzierungsrate HAT ein Perzentil in den Fakten.
        ("Finanzierungsrate im 72. Perzentil bei positiven Werten", False),
        # Die Marktvolatilitaet auch - im Lagebild, fuer den Markt.
        ("Marktlage: Bitcoin-Volatilitaet im 0. Perzentil", False),
        # Volumen OHNE Perzentil ist genau das, was wir liefern.
        ("Volumen das 0,4-fache des Mittels deutet auf wenig Beteiligung", False),
        # Ein Perzentil ohne unsere Familien - nicht unser Fall.
        ("Der Abstand steht im 71. Perzentil der letzten 366 Messungen", False),
        # Leer und kaputt duerfen nicht knallen.
        ("", False),
        (None, False),
    ]
    fehler = 0
    for text, erwartet in faelle:
        ist = bool(pruefe_beleg(text))
        if ist != erwartet:
            fehler += 1
            print(f"  FEHL  erwartet {erwartet}, bekommen {ist}: {text!r}")
    print(f"Selbsttest: {len(faelle) - fehler}/{len(faelle)} BESTANDEN")
    return 1 if fehler else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--export")
    ap.add_argument("--selbsttest", action="store_true")
    a = ap.parse_args()
    if a.selbsttest:
        return _selbsttest()
    if not a.db and not a.export:
        print("[FEHLER] --db, --export oder --selbsttest angeben")
        return 2

    if a.export:
        d = json.load(io.open(a.export, encoding="utf-8"))
        zeilen = [r for r in (d.get("spot_signals") or [])
                  if r.get("quelle_kette") == "rollen"]
    else:
        import sqlite3

        c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
        zeilen = [dict(r) for r in c.execute(
            "SELECT symbol, created_at, belege_json FROM signals "
            "WHERE quelle_kette = 'rollen' AND belege_json IS NOT NULL")]

    e = aus_zeilen(zeilen)
    print("=" * 78)
    print("BELEGE GEGEN DIE FAKTEN - erfundene Perzentile")
    print("=" * 78)
    print(f"  Signale {e['signale']}, Belege {e['belege']}")
    print(f"  geprueft auf: {', '.join(e['geprueft_auf'])}")
    print(f"  BEFUNDE: {len(e['befunde'])} in {e['signale_betroffen']} "
          f"Signalen ({e['quote_prozent']:.2f} % der Belege)")
    if e["befunde"]:
        print()
        for b in e["befunde"][:25]:
            # NUR ASCII AUF DER KONSOLE. Windows gibt hier cp1252 aus;
            # ein Warnzeichen im Text laesst die ganze Ausgabe abbrechen -
            # und damit gaebe ein Werkzeug, das Fehler finden soll, selbst
            # einen aus, statt sie zu zeigen.
            print(f"  [!] {str(b.get('symbol') or '?'):<8} "
                  f"[{b['familie']}] {b['beleg'][:88]}")
        if len(e["befunde"]) > 25:
            print(f"  ... und {len(e['befunde']) - 25} weitere")
    else:
        print("\n  Kein Beleg nennt ein Perzentil, das es nie gegeben hat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
