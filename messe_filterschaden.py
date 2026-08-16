# -*- coding: utf-8 -*-
"""SCHADET DER ANLASSFILTER? - gemessen, nicht geschaetzt (16.08.2026).

NUTZERFRAGE, woertlich: *"mach die Messung, ob der Filter schadet - meine
Meinung aktuell: ja, geringfuegig schadet er, da das Signal etwas am Zufall
haengt - Zeitpunkt des Aufrufes."*

DIE FRAGE LAESST SICH EXAKT STELLEN. `agent/anlass.py` schreibt zu jedem Urteil
einen Fingerabdruck des Faktensatzes mit. Damit gibt es Paare:

    Frage A   Faktensatz F, Antwort X
    Frage B   Faktensatz F (IDENTISCH), Antwort Y

Der Filter haette Frage B unterdrueckt. Die Frage "schadet das?" ist deshalb
die Frage: **ist Y jemals anders als X?**

    Y == X immer      der Wiederholungsaufruf traegt NICHTS bei. Der Filter
                      kostet nichts, er spart nur.
    Y != X manchmal    der Wiederholungsaufruf ist ein Los. Wer ihn
                      unterdrueckt, nimmt Lose aus der Trommel - genau der
                      Einwand des Nutzers, und dann ist er BEZIFFERBAR.

WARUM DAS NICHT AKADEMISCH IST. Dieses Projekt hat die Eigenvarianz gemessen:
nemotron drehte bei BITGLEICHER Eingabe in rund 12 % der Faelle die Richtung
(Memory: Formatmessung 09.08.). Wenn dasselbe hier gilt, ist jede
Wiederholung ein Muenzwurf - und die Signalzahl waere zum Teil eine Funktion
der Aufrufhaeufigkeit statt des Marktes.

WAS GEMESSEN WIRD:

    1. Bei identischem Faktensatz: wie oft dieselbe Aktion?
    2. Wieviele EINSTIEGE haette der Filter unterdrueckt?
    3. Haengen die Signalspitzen an App-Neustarts?

NUR LESEND, gegen eine Kopie oder ein entpacktes Backup.

AUFRUF:  python messe_filterschaden.py --db PFAD
"""
from __future__ import annotations

import argparse
import collections
import sqlite3
import sys

# Wie nah ein Signal am Anlass-Eintrag liegen muss, um dasselbe Urteil zu sein.
# Die Kette schreibt beides im selben Durchlauf; zwischen Anlassstufe und
# Signalzeile liegen der Modellaufruf und die Rechnung. 300 Sekunden sind
# grosszuegig und immer noch weit unter dem 15-Minuten-Takt, also eindeutig.
ZUORDNUNG_SEKUNDEN = 300

EINSTIEGE = ("ERÖFFNEN", "KAUFEN", "NACHKAUFEN")


def _sek(a: str, b: str) -> float:
    from datetime import datetime
    return abs((datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds())


def messe(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row
    anl = [dict(r) for r in conn.execute(
        "SELECT * FROM anlass_beobachtung ORDER BY symbol, instrument, erfasst_am")]
    sig = [dict(r) for r in conn.execute(
        "SELECT symbol, action, created_at, prompt_stand FROM signals "
        "WHERE quelle_kette = 'rollen' ORDER BY created_at")]

    # Signale nach Symbol, damit die Zuordnung nicht ueber 3.000 Zeilen sucht.
    je_symbol = collections.defaultdict(list)
    for s in sig:
        je_symbol[str(s["symbol"]).upper()].append(s)

    def aktion_zu(eintrag) -> str | None:
        """Welche Aktion gehoert zu diesem Anlass-Eintrag?

        KEINE ERFINDUNG BEI MEHRDEUTIGKEIT: gibt es kein Signal im Fenster,
        kommt None zurueck - und der Fall faellt aus der Messung, statt sie
        mit einer Annahme zu fuellen."""
        nah = [s for s in je_symbol.get(str(eintrag["symbol"]).upper(), [])
               if _sek(s["created_at"], eintrag["erfasst_am"]) <= ZUORDNUNG_SEKUNDEN]
        return str(nah[0]["action"]) if len(nah) == 1 else None

    # --- Paare bilden: aufeinanderfolgende Fragen zum selben (Symbol, Instrument)
    paare_gleich, paare_anders = [], []
    ohne_zuordnung = 0
    vorher: dict = {}
    for e in anl:
        schluessel = (e["symbol"], e["instrument"])
        a_jetzt = aktion_zu(e)
        v = vorher.get(schluessel)
        vorher[schluessel] = (e, a_jetzt)
        if v is None:
            continue
        e_alt, a_alt = v
        # NUR wo der Faktensatz WIRKLICH identisch war - das ist die
        # Population, die der Filter entfernt haette.
        if not e.get("wuerde_sperren_asset"):
            continue
        if a_jetzt is None or a_alt is None:
            ohne_zuordnung += 1
            continue
        (paare_gleich if a_jetzt == a_alt else paare_anders).append(
            {"symbol": e["symbol"], "instrument": e["instrument"],
             "vorher": a_alt, "nachher": a_jetzt,
             "abstand_h": e.get("alter_stunden")})

    # --- Was haette der Filter an EINSTIEGEN gekostet?
    gesperrt_einstieg = sum(
        1 for e in anl if e.get("wuerde_sperren_asset")
        and (aktion_zu(e) or "") in EINSTIEGE)
    einstiege_gesamt = sum(1 for s in sig if str(s["action"]) in EINSTIEGE)

    return {
        "beobachtungen": len(anl),
        "gleich": len(paare_gleich),
        "anders": len(paare_anders),
        "ohne_zuordnung": ohne_zuordnung,
        "beispiele_anders": paare_anders[:12],
        "wechsel": collections.Counter(
            (p["vorher"], p["nachher"]) for p in paare_anders),
        "gesperrt_einstieg": gesperrt_einstieg,
        "einstiege_gesamt": einstiege_gesamt,
    }


def bericht(e: dict) -> list[str]:
    z = ["=" * 74, "SCHADET DER ANLASSFILTER?", "=" * 74,
         f"Anlass-Beobachtungen: {e['beobachtungen']}", ""]
    n = e["gleich"] + e["anders"]
    if not n:
        return z + ["Keine Paare mit identischem Faktensatz UND zuordenbarem",
                    "Urteil - ohne sie ist die Frage nicht beantwortbar.",
                    f"(nicht zuordenbar: {e['ohne_zuordnung']})"]

    z += ["BEI IDENTISCHEM FAKTENSATZ - antwortet das Modell gleich?",
          f"  gleiche Aktion   {e['gleich']:>5}   {100*e['gleich']/n:>5.1f} %",
          f"  ANDERE Aktion    {e['anders']:>5}   {100*e['anders']/n:>5.1f} %",
          f"  nicht zuordenbar {e['ohne_zuordnung']:>5}   (aus der Messung "
          f"heraus, nicht geschaetzt)", ""]

    if e["anders"]:
        z += ["WAS SICH AENDERTE (vorher -> nachher)"]
        for (a, b), k in e["wechsel"].most_common(10):
            z.append(f"  {k:>4}x  {a:14} -> {b}")
        z.append("")

    z += ["WAS DER FILTER GEKOSTET HAETTE",
          f"  Einstiege gesamt          {e['einstiege_gesamt']:>5}",
          f"  davon aus Wiederholungen  {e['gesperrt_einstieg']:>5}"
          + (f"   ({100*e['gesperrt_einstieg']/e['einstiege_gesamt']:.0f} %)"
             if e["einstiege_gesamt"] else ""), ""]

    if e["anders"] == 0:
        z += ["LESART: der Wiederholungsaufruf hat in KEINEM Fall etwas anderes",
              "ergeben. Er traegt nichts bei - der Filter spart, ohne zu kosten."]
    else:
        anteil = 100 * e["anders"] / n
        z += [f"LESART: in {anteil:.1f} % der Faelle antwortet das Modell auf "
              f"DIESELBEN Fakten anders.",
              "Der Wiederholungsaufruf ist damit teilweise ein Los - der Einwand",
              "des Nutzers trifft, und er ist jetzt beziffert. Die Frage ist",
              "nicht mehr OB, sondern ob dieser Zufall ETWAS WERT ist: das",
              "entscheidet erst die Trefferbilanz, nicht diese Messung."]
    z.append("=" * 74)
    return z


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    try:
        print("\n".join(bericht(messe(conn))))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
