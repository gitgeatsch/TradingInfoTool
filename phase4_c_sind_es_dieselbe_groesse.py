# -*- coding: utf-8 -*-
"""SIND ALT UND NEU DIESELBE GROESSE - WIRKEN SIE ANALOG?

⚠️ Nutzerfrage 21.09.2026: *„das alte turnover war ein anderer Wert als
der neue, somit stellt sich fuer mich die Frage ob diese analog wirken
bzw. als Beitrag gelten"*.

Die Frage ist RICHTIG GESTELLT und bisher nicht beantwortet. Ich habe
gemessen, wie viele Fuenftel WECHSELN (76,7 Prozent) - das sagt, dass
sie verschieden sind, aber nicht WORIN. Vier Messungen, die es sagen:

    1 RANGGLEICHLAUF  Rangkorrelation JE TAG auf den gemeinsamen
                      Symbolen. Nahe 1 hiesse: dieselbe Ordnung mit
                      Rauschen. Weit darunter: verschiedene Ordnungen
    2 WER BEWEGT SICH  `turnover` ist Volumen / Menge. Wenn die Menge
                      praktisch stillsteht, ist `turnover` nur das
                      VOLUMEN in anderer Schreibweise - dann traegt
                      nicht der Umschlag, sondern die Handelsaktivitaet
    3 ZEITACHSE       wie stark schwankt der NENNER selbst je Symbol?
                      Gesamtausgabe waechst monoton und langsam; ein
                      freier Umlauf kann springen (Unlocks, Escrow)
    4 ZERLEGUNG       wie viel der Rangunterschiede kommt aus dem
                      NIVEAU (ein Symbol steht dauerhaft anders) und
                      wie viel aus der BEWEGUNG (es bewegt sich anders)?

⚠️ NUR LESEND, kein Netz.

    python phase4_c_sind_es_dieselbe_groesse.py
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


def spearman(a: list, b: list) -> float:
    """Rangkorrelation - ohne scipy, weil wir sie nur hier brauchen."""
    if len(a) < 4:
        return float("nan")
    ra = np.argsort(np.argsort(np.asarray(a, float)))
    rb = np.argsort(np.argsort(np.asarray(b, float)))
    if ra.std() < 1e-12 or rb.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


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
    a = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
    alt = {}
    for sym, tag, w in a.execute(
            "SELECT symbol, datum, wert FROM splycur WHERE wert>0"):
        alt.setdefault(sym.upper(), {})[str(tag)[:10]] = float(w)
    datei, _sql = MR.MESSBASIS["schnitt"]
    ab = min(t for d in neu.values() for t in d)
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    vol = {}
    for sym, tag, v in m.execute(
            "SELECT symbol, date, volume FROM price_history_ohlc "
            " WHERE date >= ? AND volume > 0", (ab,)):
        vol.setdefault(sym.upper(), {})[str(tag)[:10]] = float(v)
    return neu, alt, vol, ab


def main() -> int:
    neu, alt, vol, ab = lade()
    gem = sorted(set(neu) & set(alt) & set(vol))
    print("=" * 100)
    print("SIND ALT UND NEU DIESELBE GROESSE? - vier Messungen")
    print("=" * 100)
    print("  gemeinsame Symbole: %d \u00b7 Fenster ab %s" % (len(gem), ab))

    # ---- 1  Ranggleichlauf je Tag ------------------------------------
    print()
    print("-" * 100)
    print("  1) RANGGLEICHLAUF - dieselbe Ordnung oder zwei Ordnungen?")
    print("-" * 100)
    je_tag_rho = []
    tage = sorted({t for s in gem for t in vol.get(s, {})})
    for t in tage:
        xa, xb = [], []
        for s in gem:
            va = vol.get(s, {}).get(t)
            ma, mb = alt.get(s, {}).get(t), neu.get(s, {}).get(t)
            if va and ma and mb:
                xa.append(va / ma)
                xb.append(va / mb)
        if len(xa) >= 12:
            r = spearman(xa, xb)
            if r == r:
                je_tag_rho.append(r)
    if je_tag_rho:
        je_tag_rho.sort()
        print("     %d Tage mit mindestens 12 gemeinsamen Symbolen" %
              len(je_tag_rho))
        for q in (5, 25, 50, 75, 95):
            i = int(round(q / 100.0 * (len(je_tag_rho) - 1)))
            print("       %2d. Perzentil  %+.4f" % (q, je_tag_rho[i]))
        print("     ➤ MEDIAN %+.4f" % st.median(je_tag_rho))
        print()
        print("     \u26a0 LESEART: 1,0 hiesse ,dieselbe Ordnung`. Der "
              "Median sagt, wie viel")
        print("        der ALTEN Ordnung in der NEUEN steckt - und "
              "umgekehrt.")

    # ---- 2  wer bewegt den Umschlag? ---------------------------------
    print()
    print("-" * 100)
    print("  2) WER BEWEGT DEN UMSCHLAG - der Zaehler oder der Nenner?")
    print("-" * 100)
    print("     Gemessen als Rangkorrelation je Tag zwischen `turnover` "
          "und dem reinen VOLUMEN.")
    print("     Nahe 1 heisst: der Nenner ordnet nichts um - `turnover` "
          "IST das Volumen.")
    for name, menge in (("ALT (SplyCur)", alt), ("NEU (Free Float)", neu)):
        rr = []
        for t in tage:
            xv, xt = [], []
            for s in gem:
                va = vol.get(s, {}).get(t)
                mm = menge.get(s, {}).get(t)
                if va and mm:
                    xv.append(va)
                    xt.append(va / mm)
            if len(xv) >= 12:
                r = spearman(xv, xt)
                if r == r:
                    rr.append(r)
        if rr:
            print("     %-18s Median %+.4f  (%d Tage)"
                  % (name, st.median(rr), len(rr)))
    print("     \u26a0 Beide sollten DEUTLICH unter 1 liegen - sonst "
          "traegt nicht der")
    print("        Umschlag, sondern die Handelsaktivitaet unter anderem "
          "Namen.")

    # ---- 3  Zeitachse: wie lebendig ist der Nenner? ------------------
    print()
    print("-" * 100)
    print("  3) DIE ZEITACHSE - wie stark bewegt sich der NENNER selbst?")
    print("-" * 100)
    print("     %-18s %10s %10s %10s" % ("Quelle", "Median", "90. Perz.",
                                         "unbewegt"))
    for name, menge in (("ALT (SplyCur)", alt), ("NEU (Free Float)", neu)):
        spanne = []
        starr = 0
        for s in gem:
            w = [menge[s][t] for t in sorted(menge.get(s, {}))
                 if t >= ab]
            if len(w) < 60:
                continue
            m = st.median(w)
            if m <= 0:
                continue
            sp = (max(w) - min(w)) / m
            spanne.append(sp)
            starr += (sp < 0.01)
        if spanne:
            spanne.sort()
            print("     %-18s %9.4f %10.4f %6d von %d"
                  % (name, st.median(spanne),
                     spanne[int(0.9 * (len(spanne) - 1))], starr,
                     len(spanne)))
    print("     \u26a0 ,unbewegt` = Spanne unter 1 Prozent des Medians "
          "ueber das ganze Jahr.")
    print("        Ein starrer Nenner kann keinen eigenen Beitrag "
          "liefern - er ist dann")
    print("        nur ein fester Teiler je Symbol, und der faellt im "
          "Querschnittsrang")
    print("        NICHT heraus, aber er bewegt sich nicht mit.")

    # ---- 4  Niveau gegen Bewegung ------------------------------------
    print()
    print("-" * 100)
    print("  4) ZERLEGUNG - Niveau oder Bewegung?")
    print("-" * 100)
    print("     Je Symbol: wie gross ist der MEDIANE Rangabstand "
          "(Niveau),")
    print("     und wie stark SCHWANKT er (Bewegung)?")
    r_alt, r_neu = {}, {}
    for t in tage:
        paare = [(s, vol[s][t], alt[s].get(t), neu[s].get(t)) for s in gem
                 if t in vol.get(s, {}) and t in alt.get(s, {})
                 and t in neu.get(s, {})]
        if len(paare) < 12:
            continue
        ra = MR._rang({s: v / a for s, v, a, _b in paare})
        rb = MR._rang({s: v / b for s, v, _a, b in paare})
        for s in ra:
            r_alt.setdefault(s, []).append(ra[s])
            r_neu.setdefault(s, []).append(rb[s])
    zeilen = []
    for s in r_alt:
        if len(r_alt[s]) < 60:
            continue
        d = [b - a for a, b in zip(r_alt[s], r_neu[s])]
        zeilen.append((abs(st.median(d)), st.median(d),
                       st.pstdev(d) if len(d) > 1 else 0.0, s, len(d)))
    zeilen.sort(reverse=True)
    if zeilen:
        niveau = st.median([abs(x[1]) for x in zeilen])
        bewegung = st.median([x[2] for x in zeilen])
        print("     ueber %d Symbole: medianer NIVEAU-Versatz %.4f "
              "Rangpunkte," % (len(zeilen), niveau))
        print("     mediane SCHWANKUNG des Versatzes %.4f" % bewegung)
        print("     ➤ %s"
              % ("das NIVEAU ueberwiegt - die neue Quelle stellt "
                 "Symbole dauerhaft anders ein"
                 if niveau > bewegung else
                 "die BEWEGUNG ueberwiegt - der Versatz wandert, die "
                 "Quellen laufen auseinander und wieder zusammen"))
        print()
        print("     die acht groessten NIVEAU-Versaetze:")
        print("       %-10s %9s %9s %6s" % ("Symbol", "Versatz", "Schwank.",
                                            "Tage"))
        for _a, med, sd, s, n in zeilen[:8]:
            print("       %-10s %+9.4f %9.4f %6d" % (s, med, sd, n))
    print()
    print("=" * 100)
    print("  \u26a0 WAS HIER NICHT BEANTWORTET WIRD: welche der beiden "
          "RICHTIG ist. Diese")
    print("     Messungen sagen, WORIN sie sich unterscheiden - nicht, "
          "wer recht hat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
