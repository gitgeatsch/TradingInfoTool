# -*- coding: utf-8 -*-
"""KONVERGIEREN DIE BEIDEN NENNER BEI ALTEN COINS?

⚠️ Nutzergedanke 21.09.2026: *„btc, eth, Link sind lange am Markt und
werden nicht so rasch verschwinden ... für diesen Indikator gibt es
einfach nur eine begrenzte Grundmenge."*

Die Frage dahinter ist praezise und messbar: der Unterschied zwischen
FREIEM UMLAUF und GESAMTAUSGABE entsteht durch NICHT FREIGEGEBENE
Bestaende - Team, Investoren, Treasury, Escrow. Diese Sperren laufen
ueber Jahre aus. Also:

    Je AELTER ein Token, desto naeher sollten die beiden Groessen
    beieinander liegen.

⚠️⚠️ WENN DAS STIMMT, hat es eine Folge, die den ganzen Streit
entschaerft: auf einer BEGRENZTEN, ALTEN Grundmenge waere die alte
Quelle gar nicht falsch - dort IST die Gesamtausgabe der freie Umlauf.
Der Vorteil der neuen Quelle laege dann ausschliesslich bei den jungen,
noch gesperrten Werten - also genau dort, wo wir nur 365 Tage haben.

⚠️ Gemessen wird das Verhaeltnis NEU/ALT gegen das Alter des Symbols
(erster Kurs in der Messbasis). Beobachtet, nicht behauptet.

    python phase4_c_alte_coins_konvergieren.py
"""
from __future__ import annotations

import datetime as dt
import os
import sqlite3
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402

# ⚠️ Die beiden, bei denen die ALTE Quelle nachweislich falsch liegt
# (21.09.2026, gegen CoinMarketCap belegt). Sie wuerden das Bild
# verzerren und werden AUSGEWIESEN, nicht stillschweigend entfernt.
FALSCH = ("XVG", "KNC")


def main() -> int:
    n = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    a = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
    neu = {}
    for sym, w in n.execute(
            "SELECT u.symbol, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol s ON s.symbol = u.symbol "
            " WHERE s.urteil='ok' AND u.datum = "
            "   (SELECT MAX(datum) FROM umlaufmenge x "
            "     WHERE x.symbol = u.symbol)"):
        neu[sym.upper()] = w
    alt = {}
    for sym, w in a.execute(
            "SELECT symbol, wert FROM splycur s WHERE wert > 0 AND datum = "
            " (SELECT MAX(datum) FROM splycur x WHERE x.symbol = s.symbol "
            "   AND x.wert > 0)"):
        alt[sym.upper()] = w
    datei, _sql = MR.MESSBASIS["schnitt"]
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    erst = {}
    for sym, d in m.execute("SELECT symbol, MIN(date) "
                            "  FROM price_history_ohlc GROUP BY symbol"):
        try:
            erst[sym.upper()] = dt.date.fromisoformat(str(d)[:10])
        except Exception:                                  # noqa: BLE001
            pass
    heute = dt.date.today()

    print("=" * 100)
    print("KONVERGIEREN DIE NENNER BEI ALTEN COINS?")
    print("=" * 100)
    zeilen = []
    for s in sorted(set(neu) & set(alt) & set(erst)):
        if alt[s] <= 0:
            continue
        zeilen.append(((heute - erst[s]).days, neu[s] / alt[s], s))
    zeilen.sort()
    print("  %d Symbole mit beiden Groessen und einem ersten Kurs"
          % len(zeilen))
    print()
    print("  %-14s %7s %10s %10s %10s   %s"
          % ("Altersgruppe", "Symbole", "Median", "unter 0,9", "ueber 1,0",
             "Bemerkung"))
    gruppen = ((0, 730, "unter 2 Jahre"), (730, 1460, "2 bis 4 Jahre"),
               (1460, 2190, "4 bis 6 Jahre"), (2190, 99999, "ueber 6 Jahre"))
    for lo, hi, name in gruppen:
        g = [(v, s) for tage, v, s in zeilen if lo <= tage < hi
             and s not in FALSCH]
        if not g:
            print("  %-14s %7d" % (name, 0))
            continue
        werte = sorted(v for v, _s in g)
        unter = sum(1 for v in werte if v < 0.90)
        ueber = sum(1 for v in werte if v > 1.00)
        print("  %-14s %7d %10.3f %10d %10d"
              % (name, len(g), st.median(werte), unter, ueber))
    print()
    print("  ⚠️ LESEART: 1,000 heisst ,die beiden Quellen sagen "
          "dasselbe`. Ein Wert")
    print("     unter 1 heisst, der freie Umlauf ist KLEINER als die "
          "Gesamtausgabe -")
    print("     also liegen noch Bestaende gesperrt. Faellt der Anteil "
          ",unter 0,9` mit")
    print("     dem Alter, stuetzt das den Gedanken; bleibt er, nicht.")
    print()
    print("  DIE ZEHN AELTESTEN EINZELN:")
    print("     %-8s %6s %9s   %s" % ("Symbol", "Jahre", "NEU/ALT",
                                      "Deutung"))
    for tage, v, s in zeilen[-10:][::-1]:
        deut = ("identisch" if 0.99 <= v <= 1.01 else
                ("gesperrt %.0f %%" % (100 * (1 - v)) if v < 1 else
                 "⛔ NEU groesser - unmoeglich"))
        print("     %-8s %6.1f %9.3f   %s%s"
              % (s, tage / 365.25, v, deut,
                 "   ⚠️ ALTE QUELLE FALSCH (belegt)" if s in FALSCH else ""))
    print()
    print("  ⚠️ AUSGEWIESEN, NICHT ENTFERNT: %s stehen in den Gruppen "
          "oben NICHT drin -" % ", ".join(FALSCH))
    for s in FALSCH:
        for tage, v, x in zeilen:
            if x == s:
                print("     %-6s Verhaeltnis %.4f nach %.1f Jahren - die "
                      "ALTE Quelle ist hier"
                      % (s, v, tage / 365.25))
                print("            nachweislich falsch (gegen "
                      "CoinMarketCap belegt), nicht der Token.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
