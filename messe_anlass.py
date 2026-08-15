# -*- coding: utf-8 -*-
"""Wie oft haette der Anlassfilter gegriffen? - O-36 (15.08.2026).

DIE FRAGE DES NUTZERS: *"warum eine neue Bewertung und Signal, wenn sich nichts
geaendert hat?"* - und seine Vorgabe dazu: *"erstmal soviele Daten wie moeglich
zulassen und spaeter selektiv einschraenken."*

`agent/anlass.py` schreibt seit dem 15.08. bei jedem Urteil mit, ob der
Faktensatz derselbe war wie beim letzten Mal innerhalb von 24 Stunden. Es
SPERRT nichts. Dieses Skript liest die Beobachtungen und beantwortet die eine
Frage, die vor der Entscheidung fehlt:

    Greift der Filter in 5 % der Faelle, lohnt er nicht.
    Greift er in 60 %, stellt die Kette dieselbe Frage sechsmal.

ZWEI ABDRUECKE, ZWEI ANTWORTEN. `voll` nimmt das Lagebild mit, `asset` laesst
es weg. Der Unterschied zwischen beiden ist die eigentliche Erkenntnis: er
sagt, wieviel Bewegung allein aus der Modellprosa des Lagebilds kommt und nicht
aus dem Asset.

AUFRUF:  python messe_anlass.py [--db PFAD] [--tage N]
"""
from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict


def messe(conn: sqlite3.Connection, tage: float = 30.0) -> dict:
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM anlass_beobachtung "
            "WHERE erfasst_am >= datetime('now', ?) ORDER BY erfasst_am",
            (f"-{float(tage)} days",)).fetchall()
    except sqlite3.Error:
        return {"fehlt": True}

    je_instrument = defaultdict(lambda: {"n": 0, "voll": 0, "asset": 0})
    je_symbol = defaultdict(lambda: {"n": 0, "asset": 0})
    abstaende = []
    for r in rows:
        i = str(r["instrument"])
        je_instrument[i]["n"] += 1
        je_instrument[i]["voll"] += int(r["wuerde_sperren_voll"] or 0)
        je_instrument[i]["asset"] += int(r["wuerde_sperren_asset"] or 0)
        s = str(r["symbol"])
        je_symbol[s]["n"] += 1
        je_symbol[s]["asset"] += int(r["wuerde_sperren_asset"] or 0)
        if r["alter_stunden"] is not None:
            abstaende.append(float(r["alter_stunden"]))
    return {"fehlt": False, "n": len(rows),
            "je_instrument": {k: dict(v) for k, v in je_instrument.items()},
            "je_symbol": {k: dict(v) for k, v in je_symbol.items()},
            "abstaende": abstaende, "tage": tage}


def bericht(e: dict) -> list[str]:
    z = ["WIE OFT HAETTE DER ANLASSFILTER GEGRIFFEN?", ""]
    if e.get("fehlt"):
        return z + ["Keine Tabelle `anlass_beobachtung` - die Messung laeuft",
                    "erst seit dem 15.08.2026 und nur im scharfen Betrieb."]
    if not e["n"]:
        return z + [f"Keine Beobachtungen in den letzten {e['tage']:.0f} Tagen.",
                    "Nach dem naechsten Lauf hat dieses Skript Datenlage."]

    z.append(f"Beobachtungen: {e['n']} (letzte {e['tage']:.0f} Tage)")
    z += ["", f"  {'Instrument':14}{'Urteile':>9}{'voll':>10}{'asset':>10}"]
    gv = ga = gn = 0
    for i, v in sorted(e["je_instrument"].items()):
        gn += v["n"]
        gv += v["voll"]
        ga += v["asset"]
        z.append(f"  {i:14}{v['n']:>9}"
                 f"{100.0 * v['voll'] / v['n']:>9.0f}%"
                 f"{100.0 * v['asset'] / v['n']:>9.0f}%")
    if gn:
        z.append(f"  {'GESAMT':14}{gn:>9}{100.0 * gv / gn:>9.0f}%"
                 f"{100.0 * ga / gn:>9.0f}%")

    # DER UNTERSCHIED IST DIE ERKENNTNIS, nicht die einzelne Zahl.
    if gn:
        z += ["", "WAS DAS HEISST"]
        z.append(f"  Ohne Lagebild waeren {100.0 * ga / gn:.0f} % der Fragen "
                 f"woertlich Wiederholungen.")
        z.append(f"  Mit Lagebild nur {100.0 * gv / gn:.0f} % - die Differenz "
                 f"von {100.0 * (ga - gv) / gn:.0f} Punkten kommt allein aus "
                 f"der Prosa des Lagebilds,")
        z.append("  nicht aus dem Asset.")
        if ga < 0.05 * gn:
            z.append("  UNTER 5 %: der Filter lohnt sich nicht - die Fakten "
                     "aendern sich schneller als der Takt.")
        elif ga > 0.5 * gn:
            z.append("  UEBER 50 %: die Kette stellt dieselbe Frage mehr als "
                     "doppelt so oft wie noetig.")

    if e["abstaende"]:
        a = sorted(e["abstaende"])
        z += ["", f"Abstand zur vorigen Frage (Stunden): "
                  f"Median {a[len(a) // 2]:.1f}, "
                  f"kleinster {a[0]:.2f}, groesster {a[-1]:.1f}"]

    schlimm = sorted(((v["asset"] / v["n"], s, v) for s, v in
                      e["je_symbol"].items() if v["n"] >= 3), reverse=True)[:8]
    if schlimm:
        z += ["", "MEISTE WIEDERHOLUNGEN (mindestens 3 Urteile)",
              f"  {'Symbol':10}{'Urteile':>9}{'davon gleich':>14}"]
        for q, s, v in schlimm:
            z.append(f"  {s:10}{v['n']:>9}{v['asset']:>10} ({100 * q:.0f}%)")

    z += ["", "ES WURDE NICHTS GESPERRT. Diese Zahlen sagen, was ein Filter",
          "getan HAETTE - die Entscheidung, ob er scharf geschaltet wird,",
          "steht damit auf einer Messung statt auf einer Schaetzung."]
    return z


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--tage", type=float, default=30.0)
    a = p.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    try:
        print("\n".join(bericht(messe(conn, a.tage))))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
