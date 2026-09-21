# -*- coding: utf-8 -*-
"""IST `turnover` UEBER EMISSIONSREGIME HINWEG VERGLEICHBAR?

⚠️⚠️ NUTZEREINWAND 21.09.2026: *„es gibt Assets ohne (wenig) Aenderung
also Statisch und andere mit laufenden Aenderungen, somit anderes
Verhalten bis die Ausgabegrenze erreicht wird."*

Der Einwand trifft die Konstruktion der Groesse selbst:

    turnover(t) = Volumen(t) / Umlaufmenge(t)

    log turnover = log Volumen - log Menge

Bei einem Asset mit STATISCHER Menge ist der zweite Term eine
Konstante - `turnover` bewegt sich dann ausschliesslich mit dem
Volumen. Bei einem VERWAESSERNDEN Asset hat der zweite Term einen
TREND: die Menge waechst, also faellt `turnover` MECHANISCH, ohne dass
am Handelsinteresse irgendetwas passiert.

⚠️⚠️ UND JETZT DIE SCHARFE FOLGE. Die registrierte Tabelle sagt:
NIEDRIGER Umschlag ist GUT (+3,15 im untersten Fuenftel). Ein Token in
der Freischaltungsphase driftet mechanisch NACH UNTEN im Rang - also
in das Fuenftel, das belohnt wird. Wenn Freischaltungsdruck zugleich
schlecht fuer den Kurs ist, bewertet der Beitrag dort das Falsche.

⚠️ DAS IST EINE HYPOTHESE, KEIN BEFUND - und sie ist messbar. Vier
Messungen:

    1 REGIME     wie verteilen sich die Symbole auf statisch,
                 wachsend, schrumpfend? Erst zaehlen, dann reden
    2 DRIFT      wandert der Rang eines wachsenden Assets ueber das
                 Jahr systematisch nach unten? Das ist die mechanische
                 Komponente, und sie ist direkt messbar
    3 ZERLEGUNG  welcher der beiden Terme bewegt den RANG - das
                 Volumen oder die Menge?
    4 TRENNUNG   sitzen die Regime in verschiedenen Fuenfteln? Wenn
                 ja, rangiert der Beitrag teilweise EMISSIONSMODELLE
                 statt Handelslagen

⚠️ DAS PROBLEM IST NEU. Mit der alten Quelle waren 24 von 42 Nennern
praktisch starr (Spanne unter 1 Prozent im Jahr) - der Kanal existierte
gar nicht. Mit dem freien Umlauf wird er aktiv. Wer die Quelle
wechselt, schaltet ihn ein.

⚠️ Und es gibt eine stehende Hausregel dafuer:
`zielgroesse-ueber-klassen-normieren` - eine Groesse, die ueber
verschiedene Klassen hinweg etwas anderes bedeutet, gehoert normiert
oder getrennt, nicht in einen Topf.

    python phase4_c_statisch_gegen_verwaessernd.py
"""
from __future__ import annotations

import os
import sqlite3
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import hole_umlaufmenge_cg as HU                           # noqa: E402

# ⚠️ Die Grenzen sind SETZUNGEN und werden als solche ausgewiesen. Sie
# stehen hier, damit die Gruppen benennbar sind - nicht, weil bei 5
# Prozent etwas Besonderes passiert. Teil 2 und 3 brauchen sie nicht:
# dort wird gegen die STETIGE Wachstumsrate gerechnet.
STATISCH = 0.01
DEUTLICH = 0.05


def lade():
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    roh = {}
    for sym, tag, w in c.execute(
            "SELECT u.symbol, u.datum, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol a ON a.symbol=u.symbol "
            " WHERE a.urteil='ok' AND u.wert>0 ORDER BY u.symbol, u.datum"):
        roh.setdefault(sym.upper(), []).append((str(tag)[:10], float(w)))
    neu = {}
    for s, reihe in roh.items():
        raus = HU.entferne_spitzen([w for _t, w in reihe])
        neu[s] = {t: w for i, (t, w) in enumerate(reihe) if i not in raus}
    datei, _sql = MR.MESSBASIS["schnitt"]
    ab = min(t for d in neu.values() for t in d)
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    vol = {}
    for sym, tag, v in m.execute(
            "SELECT symbol, date, volume FROM price_history_ohlc "
            " WHERE date >= ? AND volume > 0", (ab,)):
        s = sym.upper()
        if s in neu:
            vol.setdefault(s, {})[str(tag)[:10]] = float(v)
    return neu, vol, ab


def main() -> int:
    neu, vol, ab = lade()
    gem = sorted(set(neu) & set(vol))
    print("=" * 100)
    print("IST `turnover` UEBER EMISSIONSREGIME HINWEG VERGLEICHBAR?")
    print("=" * 100)
    print("  %d Symbole mit Menge UND Volumen \u00b7 Fenster ab %s"
          % (len(gem), ab))

    # ---- 1  Regime zaehlen -------------------------------------------
    wachstum = {}
    for s in gem:
        t = sorted(neu[s])
        if len(t) < 200:
            continue
        a, b = neu[s][t[0]], neu[s][t[-1]]
        if a > 0:
            wachstum[s] = (b - a) / a
    print()
    print("-" * 100)
    print("  1) DIE REGIME - erst zaehlen")
    print("-" * 100)
    gruppen = {
        "STATISCH (< 1 %)": [s for s, w in wachstum.items()
                             if abs(w) < STATISCH],
        "leicht wachsend": [s for s, w in wachstum.items()
                            if STATISCH <= w < DEUTLICH],
        "WACHSEND (> 5 %)": [s for s, w in wachstum.items()
                             if w >= DEUTLICH],
        "schrumpfend": [s for s, w in wachstum.items()
                        if w <= -STATISCH],
    }
    print("     %-22s %8s %12s   %s"
          % ("Regime", "Symbole", "Median-Wachstum", "Beispiele"))
    for name, syms in gruppen.items():
        if not syms:
            print("     %-22s %8d" % (name, 0))
            continue
        med = st.median([wachstum[s] for s in syms])
        bsp = ", ".join(sorted(syms, key=lambda x: -abs(wachstum[x]))[:5])
        print("     %-22s %8d %+11.1f %%   %s"
              % (name, len(syms), 100 * med, bsp))

    # ---- 2  Drift des Rangs ------------------------------------------
    print()
    print("-" * 100)
    print("  2) DRIFT - wandert der Rang mechanisch?")
    print("-" * 100)
    tage = sorted({t for s in gem for t in vol[s]})
    rang = {}
    for t in tage:
        je = {s: vol[s][t] / neu[s][t] for s in gem
              if t in vol[s] and t in neu[s] and neu[s][t] > 0}
        if len(je) < 12:
            continue
        for s, r in MR._rang(je).items():
            rang.setdefault(s, []).append(r)
    drift = {}
    for s, r in rang.items():
        if len(r) < 200:
            continue
        n = len(r) // 4
        drift[s] = st.mean(r[-n:]) - st.mean(r[:n])
    print("     %-22s %8s %14s %14s"
          % ("Regime", "Symbole", "Median-Drift", "davon fallend"))
    for name, syms in gruppen.items():
        d = [drift[s] for s in syms if s in drift]
        if not d:
            print("     %-22s %8d" % (name, 0))
            continue
        print("     %-22s %8d %+13.4f %10d von %d"
              % (name, len(d), st.median(d), sum(1 for x in d if x < 0),
                 len(d)))
    paare = [(wachstum[s], drift[s]) for s in drift if s in wachstum]
    if len(paare) > 10:
        x = np.array([np.log1p(max(p[0], -0.99)) for p in paare])
        y = np.array([p[1] for p in paare])
        r = float(np.corrcoef(x, y)[0, 1])
        print()
        print("     ➤ KORRELATION Mengenwachstum gegen Rangdrift: "
              "%+.4f (%d Symbole)" % (r, len(paare)))
        print("        \u26a0 Negativ hiesse: wer verwaessert, rutscht im "
              "Rang nach UNTEN -")
        print("          also in das Fuenftel, das die registrierte "
              "Tabelle BELOHNT.")

    # ---- 3  Zerlegung: wer bewegt den Rang? --------------------------
    print()
    print("-" * 100)
    print("  3) ZERLEGUNG - Volumen oder Menge?")
    print("-" * 100)
    print("     Je Symbol die Streuung der beiden Terme von "
          "log(turnover) = log V - log S:")
    sv, sm = [], []
    for s in gem:
        t = sorted(set(vol[s]) & set(neu[s]))
        if len(t) < 200:
            continue
        lv = [np.log(vol[s][x]) for x in t if vol[s][x] > 0]
        ls = [np.log(neu[s][x]) for x in t if neu[s][x] > 0]
        if len(lv) > 100 and len(ls) > 100:
            sv.append(float(np.std(lv)))
            sm.append(float(np.std(ls)))
    if sv:
        print("     Streuung log VOLUMEN : Median %.4f" % st.median(sv))
        print("     Streuung log MENGE   : Median %.4f" % st.median(sm))
        print("     ➤ Verhaeltnis %.1f zu 1 - der %s dominiert die "
              "Bewegung INNERHALB eines Symbols"
              % (st.median(sv) / max(st.median(sm), 1e-9),
                 "ZAEHLER" if st.median(sv) > st.median(sm) else "NENNER"))
        print("     \u26a0 ABER: der QUERSCHNITTSRANG lebt nicht von der "
              "Bewegung innerhalb")
        print("        eines Symbols, sondern vom NIVEAU zwischen den "
              "Symbolen. Dort")
        print("        wirkt die Menge voll - sie ist der einzige "
              "Unterschied zwischen")
        print("        ,viel gehandelt` und ,viel gehandelt GEMESSEN AN "
          "seiner Groesse`.")

    # ---- 4  Sitzen die Regime in verschiedenen Fuenfteln? -----------
    print()
    print("-" * 100)
    print("  4) TRENNUNG - rangiert der Beitrag EMISSIONSMODELLE?")
    print("-" * 100)
    print("     %-22s %8s   %s" % ("Regime", "Symbole",
                                   "mittleres Fuenftel (0 = wenig "
                                   "Umschlag = belohnt)"))
    for name, syms in gruppen.items():
        f = []
        for s in syms:
            if s in rang and len(rang[s]) >= 200:
                f.append(st.mean([MR._fuenftel(r) for r in rang[s]]))
        if f:
            print("     %-22s %8d   %.2f" % (name, len(f), st.mean(f)))
    print()
    print("     \u26a0 Liegen die Regime bei verschiedenen Fuenfteln, "
          "rangiert der Beitrag")
    print("        teilweise das EMISSIONSMODELL statt der Handelslage - "
          "und dann ist")
    print("        die Frage, ob das gewollte Information oder ein "
          "Artefakt ist.")
    print()
    print("=" * 100)
    print("  \u26a0 WAS HIER NICHT BEANTWORTET WIRD: ob die Drift dem "
          "Ergebnis schadet.")
    print("     Dafuer braeuchte es die Messung JE REGIME - das ist der "
          "naechste Schritt,")
    print("     nicht dieser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
