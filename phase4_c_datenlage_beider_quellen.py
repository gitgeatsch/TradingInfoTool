# -*- coding: utf-8 -*-
"""DIE DATENLAGE BEIDER turnover-QUELLEN: Frische und echte Bewegung.

⚠️⚠️ NUTZERFRAGE 21.09.2026, woertlich: *„Wie ist jetzt die Datenlage
der beiden Quellen? prüfe auch ob die beiden Quellen unterschiede in
der Frische und echte Daten aktualsieren."*

Die zweite Haelfte ist die wichtigere und wird sonst nie gestellt:
**eine Reihe kann frisch aussehen und trotzdem stillstehen.** Wenn eine
Quelle denselben Wert taeglich neu schreibt, hat sie ein aktuelles
DATUM und keine aktuelle INFORMATION. Genau das ist im Haus schon
passiert (`stilllegung-wer-schreibt-das-noch`: Terminmarkt eingefroren,
13 Werte seit Juli, Befund 2.452) - und die Lehre daraus lautet:
**Frische je SYMBOL pruefen, nicht je Tabelle.**

## Was gemessen wird

    1  FRISCHE je Symbol - Verteilung, nicht Maximum
    2  BEWEGUNG - wie viele DISTINKTE Werte in den letzten 30 Tagen?
       Eine Reihe mit einem einzigen Wert steht still, egal wie
       aktuell ihr Datum ist
    3  die Symbole, die der BETRIEB tatsaechlich nimmt, gegen die,
       die nur in der Datei stehen

⚠️ NUR LESEND, `mode=ro`, kein Netzabruf.
"""
import datetime as dt
import os
import sqlite3
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                                # noqa: E402

HEUTE = dt.date.today()
QUELLEN = (
    ("Coin Metrics `SplyCur`  (LAEUFT)", "data/onchain_historie.db",
     "splycur", "Gesamtausgabe auf dem Ledger"),
    ("CoinGecko Free Float    (Alternative)", "data/umlaufmenge_cg.db",
     "umlaufmenge", "freier Umlauf = Marktkapitalisierung / Preis"),
)


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


def alter(tag):
    try:
        return (HEUTE - dt.date.fromisoformat(str(tag)[:10])).days
    except ValueError:
        return None


print("=" * 106)
print("DIE DATENLAGE BEIDER turnover-QUELLEN")
print("=" * 106)

lage = {}
for titel, datei, tab, was in QUELLEN:
    print()
    print("%s" % titel)
    print("   Datei %s · Tabelle `%s`" % (datei, tab))
    print("   Groesse: %s" % was)
    print("   " + "-" * 98)
    if not os.path.exists(datei):
        print("   ⛔ Datei fehlt")
        continue
    c = ro(datei)
    # letzter Tag JE SYMBOL
    letzte = {r[0].upper(): r[1] for r in c.execute(
        "SELECT symbol, MAX(datum) FROM %s WHERE wert > 0 "
        "GROUP BY symbol" % tab)}
    alt = {s: alter(t) for s, t in letzte.items()}
    alt = {s: a for s, a in alt.items() if a is not None}
    if not alt:
        print("   ⛔ keine lesbaren Daten")
        continue
    w = sorted(alt.values())
    print("   %-40s %d" % ("Symbole mit Werten:", len(alt)))
    print("   %-40s %d / %d / %d Tage"
          % ("Alter Median / 90. Perzentil / Max:", st.median(w),
             w[int(0.9 * (len(w) - 1))], w[-1]))
    for grenze in (2, 7, MR.SPLYCUR_FRISCHE_TAGE, 90, 365):
        n = sum(1 for a in alt.values() if a <= grenze)
        print("   %-40s %4d  (%5.1f %%)"
              % ("hoechstens %d Tage alt:" % grenze, n,
                 100.0 * n / len(alt)))

    # ---- ⚠️⚠️ BEWEGT SICH DIE REIHE UEBERHAUPT? -------------------
    #
    # Ein aktuelles Datum ist keine aktuelle Information. Gezaehlt wird
    # die Zahl DISTINKTER Werte in den letzten 30 Tagen je Symbol.
    stand = {"still": 0, "traege": 0, "lebt": 0, "zu_kurz": 0}
    for s, t in letzte.items():
        a = alt.get(s)
        if a is None or a > MR.SPLYCUR_FRISCHE_TAGE:
            continue
        r = c.execute(
            "SELECT COUNT(*), COUNT(DISTINCT wert) FROM %s "
            " WHERE symbol = ? AND wert > 0 "
            "   AND datum >= date(?, '-30 day')" % tab,
            (s, str(t)[:10])).fetchone()
        if not r or r[0] < 10:
            stand["zu_kurz"] += 1
        elif r[1] <= 1:
            stand["still"] += 1
        elif r[1] < 0.5 * r[0]:
            stand["traege"] += 1
        else:
            stand["lebt"] += 1
    print("   " + "-" * 98)
    print("   ⚠️ BEWEGUNG der FRISCHEN Reihen, letzte 30 Tage je Symbol:")
    print("   %-40s %4d" % ("LEBT (Wert aendert sich meist taeglich):",
                            stand["lebt"]))
    print("   %-40s %4d" % ("traege (aendert sich, aber selten):",
                            stand["traege"]))
    print("   %-40s %4d   ⚠️ frisches Datum, KEINE Information"
          % ("STILL (ein einziger Wert):", stand["still"]))
    print("   %-40s %4d" % ("zu kurz zum Urteilen (< 10 Punkte):",
                            stand["zu_kurz"]))
    lage[titel] = (alt, stand)

# ------------------------------------------------------------------
print()
print("=" * 106)
print("WAS DER BETRIEB DARAUS NIMMT")
print("=" * 106)
betrieb = MR.turnover_verfuegbar()
sply_alle = {r[0].upper() for r in
             ro("data/onchain_historie.db").execute(
                 "SELECT DISTINCT symbol FROM splycur")}
print("   %-52s %4d" % ("in der Datei `splycur`:", len(sply_alle)))
print("   %-52s %4d" % ("davon frisch, ungesperrt, in der Messbasis:",
                        len(betrieb)))
print("   %-52s %4d" % ("verworfen (zu alt oder gesperrt):",
                        len(sply_alle) - len(betrieb)))
print()
print("   ⚠️⚠️ Die Verworfenen im Einzelnen - das ist der Grund, warum")
print("      eine Symbolliste keine Verfuegbarkeitsliste ist:")
c = ro("data/onchain_historie.db")
for s in sorted(sply_alle - betrieb):
    r = c.execute("SELECT MAX(datum) FROM splycur WHERE symbol=? AND wert>0",
                  (s,)).fetchone()
    a = alter(r[0]) if r and r[0] else None
    grund = ("GESPERRT" if s in MR.NENNER_WIDERLEGT
             else "%d Tage alt" % a if a is not None
             else "kein Wert")
    print("      %-10s letzter Wert %-12s %s"
          % (s, str(r[0])[:10] if r and r[0] else "-", grund))
print()
print("=" * 106)
