# -*- coding: utf-8 -*-
"""O-29: Ist die Verkaufsseite ein Befund oder ein Muenzwurf? (14.08.2026)

DIE FRAGE. Die alte Kette urteilte ueber ihre gesamte Historie NULL von 1.142
Krypto-Spot-Signalen als VERKAUFEN - 98,2 % HALTEN (Befund 01.08., Root-Cause
Prompt-Bias, nicht Gates). Die Rollen-Kette liefert im ersten Echtbetrieb ELF
Verkaufsurteile aus 45. Von null auf ein Viertel.

Ist das die gesuchte Korrektur, oder ist die Kalibrierung ins andere Extrem
gekippt? Der Nutzer dazu: *"die Frage mag u.U. billig sein aber die Antwort
eher nicht."*

WAS DIESES SKRIPT BEANTWORTEN KANN - ohne einen einzigen Modellaufruf:

  1. Haengt die Aktion nur am BESTAND? Ein Modell, das "verkaufen" sagt, weil
     im Faktentext "ist im Bestand" steht, urteilt nicht ueber das Asset.
  2. Unterscheidet es INNERHALB des Bestands? Wenn Verkaufen und Halten sich in
     keinem gemessenen Merkmal unterscheiden, ist die Aufteilung durch nichts
     erklaert, was wir dem Modell gegeben haben.

WAS ES NICHT BEANTWORTEN KANN, und das ist die eigentliche Frage: ob die
Verkaeufe sich TRAGEN. Dafuer braucht es aufgeloeste Ausgaenge, also Wochen.
Ein Skript, das so tut, als koennte es das heute, waere schlimmer als keines.

DIE STICHPROBE IST KLEIN, und das steht im Ergebnis. Bei 11 gegen 8 hat jeder
Test wenig Trennschaerfe - "nicht unterscheidbar" heisst hier NICHT "zufaellig
bewiesen", sondern "wir koennen es nicht zeigen". Der Unterschied ist wichtig
genug, um ihn auszudrucken.

AUFRUF:  python messe_verkaufsseite.py [--db PFAD]
"""
from __future__ import annotations

import argparse
import random
import sqlite3
import statistics as st
from collections import defaultdict

VERKAUFSSEITE = ("REDUZIEREN", "VERKAUFEN", "SCHLIESSEN")
KAUFSEITE = ("KAUFEN", "NACHKAUFEN", "ERÖFFNEN")
ZIEHUNGEN = 20000
# Fester Startwert: dieselbe Datenlage soll dieselbe Zahl ergeben. Ein Test,
# dessen Ergebnis beim zweiten Lauf anders aussieht, taugt nicht als Beleg.
SAAT = 20260814


def _auc(a: list, b: list) -> float:
    """Trennschaerfe eines Merkmals. 0,5 = keine, 1,0 = perfekt.

    Anteil der Paare, in denen die erste Gruppe den hoeheren Wert hat. Robust
    gegen Ausreisser und ohne Verteilungsannahme - bei zwei Dutzend Faellen ist
    beides noetig."""
    if not a or not b:
        return 0.5
    paare = len(a) * len(b)
    groesser = sum(1 for x in a for y in b if x > y)
    gleich = sum(1 for x in a for y in b if x == y)
    return (groesser + 0.5 * gleich) / paare


def _permutation(a: list, b: list, ziehungen: int = ZIEHUNGEN) -> float:
    """p-Wert fuer den Median-Unterschied, ohne Verteilungsannahme."""
    if len(a) < 2 or len(b) < 2:
        return 1.0
    rnd = random.Random(SAAT)
    echt = abs(st.median(a) - st.median(b))
    alle = list(a) + list(b)
    treffer = 0
    for _ in range(ziehungen):
        rnd.shuffle(alle)
        if abs(st.median(alle[:len(a)]) - st.median(alle[len(a):])) >= echt:
            treffer += 1
    return treffer / ziehungen


def messe(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row
    kurse = {r["symbol"].upper(): r["price_eur"]
             for r in conn.execute("SELECT symbol, price_eur FROM price_cache")}
    bestand = {r["symbol"].upper(): r for r in conn.execute(
        "SELECT symbol, quantity, avg_buy_price_eur, avg_buy_price_manual_eur "
        "FROM holdings WHERE quantity > 0")}
    zeilen = conn.execute(
        "SELECT symbol, action, schwankung_perzentil, momentum_perzentil, "
        "volumen_perzentil FROM signals WHERE quelle_kette = 'rollen'"
    ).fetchall()

    kreuz = defaultdict(lambda: [0, 0])
    verkauf, halten = [], []
    for r in zeilen:
        s = r["symbol"].upper()
        im_bestand = s in bestand
        kreuz[r["action"]][0 if im_bestand else 1] += 1
        if not im_bestand:
            continue
        h = bestand[s]
        ein = h["avg_buy_price_manual_eur"] or h["avg_buy_price_eur"]
        k = kurse.get(s)
        eintrag = {
            "symbol": s,
            "pl": (100.0 * (k / ein - 1.0)) if (ein and k and ein > 0) else None,
            "schwankung": r["schwankung_perzentil"],
            "momentum": r["momentum_perzentil"],
            "volumen": r["volumen_perzentil"]}
        if r["action"] in VERKAUFSSEITE:
            verkauf.append(eintrag)
        elif r["action"] not in KAUFSEITE:
            halten.append(eintrag)

    merkmale = {}
    for name in ("pl", "schwankung", "momentum", "volumen"):
        a = [x[name] for x in verkauf if x[name] is not None]
        b = [x[name] for x in halten if x[name] is not None]
        if len(a) < 2 or len(b) < 2:
            continue
        merkmale[name] = {
            "median_verkauf": st.median(a), "median_halten": st.median(b),
            "auc": _auc(a, b), "p": _permutation(a, b), "n": (len(a), len(b))}
    return {"kreuz": dict(kreuz), "verkauf": verkauf, "halten": halten,
            "merkmale": merkmale}


def bericht(e: dict) -> list[str]:
    z = ["O-29: VERKAUFSSEITE - BEFUND ODER MUENZWURF?", ""]
    z.append("1. HAENGT DIE AKTION AM BESTAND?")
    z.append(f"   {'Aktion':14}{'im Bestand':>12}{'nicht':>8}")
    for a, (mit, ohne) in sorted(e["kreuz"].items(), key=lambda x: -sum(x[1])):
        z.append(f"   {a:14}{mit:>12}{ohne:>8}")
    v_ohne = sum(e["kreuz"].get(a, [0, 0])[1] for a in VERKAUFSSEITE)
    k_mit = sum(e["kreuz"].get(a, [0, 0])[0] for a in ("KAUFEN",))
    z += ["",
          f"   Verkaufsurteile OHNE Bestand: {v_ohne}",
          f"   KAUFEN-Urteile MIT Bestand:   {k_mit}",
          "   Beides sollte 0 sein - man verkauft nicht, was man nicht hat,",
          "   und ein Zukauf heisst NACHKAUFEN. Sagt fuer sich nichts ueber",
          "   die Qualitaet: die Trennung ist erzwungen, nicht geurteilt.", ""]

    z.append("2. UNTERSCHEIDET DAS MODELL INNERHALB DES BESTANDS?")
    if not e["merkmale"]:
        z.append("   Zu wenige Faelle fuer einen Vergleich.")
        return z
    z.append(f"   {'Merkmal':12}{'Verkauf':>10}{'Halten':>10}{'AUC':>7}{'p':>8}")
    for name, m in e["merkmale"].items():
        z.append(f"   {name:12}{m['median_verkauf']:>10.2f}"
                 f"{m['median_halten']:>10.2f}{m['auc']:>7.3f}{m['p']:>8.3f}")
    beste = max(e["merkmale"].values(), key=lambda m: abs(m["auc"] - 0.5))
    n_v, n_h = beste["n"]
    z += ["",
          f"   Stichprobe: {n_v} Verkaufsurteile gegen {n_h} Halten.",
          "   AUC 0,50 heisst: das Merkmal trennt die beiden Gruppen nicht."]
    if all(m["p"] >= 0.05 for m in e["merkmale"].values()):
        z += ["",
              "   ERGEBNIS: kein gemessenes Merkmal trennt Verkaufen von",
              "   Halten. Die Aufteilung ist durch nichts erklaert, was wir",
              "   dem Modell gegeben haben.",
              "",
              "   ABER: bei dieser Stichprobe hat der Test wenig Trennschaerfe.",
              "   'Nicht unterscheidbar' heisst NICHT 'zufaellig bewiesen',",
              "   sondern 'wir koennen es nicht zeigen'. Der Unterschied ist",
              "   der zwischen einem Befund und einer offenen Frage."]
    else:
        z += ["", "   ERGEBNIS: mindestens ein Merkmal trennt die Gruppen."]
    z += ["",
          "3. WAS DIESES SKRIPT NICHT BEANTWORTET",
          "   Ob die Verkaeufe sich TRAGEN. Dafuer braucht es aufgeloeste",
          "   Ausgaenge, also Wochen. Bis dahin bleibt die Frage offen -",
          "   und `rollen_kette.verkauf_mailt` entscheidet, ob sie in der",
          "   Zwischenzeit im Postfach landet oder nur in der Datenbank."]
    return z


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    try:
        print("\n".join(bericht(messe(conn))))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
