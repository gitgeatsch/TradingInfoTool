# -*- coding: utf-8 -*-
"""WIE SAEHE DIE BEITRAGSTABELLE AUF DEM FREIEN UMLAUF AUS?

⚠️ Damit die Entscheidung ueber einen Nennerwechsel nicht abstrakt
bleibt: hier steht, was konkret an die Stelle der registrierten Zeile
traete. Gerechnet mit DERSELBEN Mechanik wie `rechne_turnover_beitrag`
(Fuenftel-Median je Tag, Mittel ueber die Tage, gegen den Gesamtschnitt,
mal 100/(1+CRV), halbiert wegen In-Sample) - nur mit anderem Nenner.

## ⚠️⚠️ WAS DIESE TABELLE NICHT IST

Sie ist **kein Ersatz** fuer die registrierte Zeile. Die steht auf
**H20 und der langen Historie**; hier sind es **H2/H3/H5 und ein Jahr**.
Zwei verschiedene Messungen, und R-R11 verlangt Reproduktion vor
Widerruf. Was sie beantwortet, ist eine andere, kleinere Frage:

    Behaelt die Tabelle auf dem freien Umlauf ihre FORM?

Die registrierte Zeile faellt monoton: +3,15 / +0,83 / +0,22 / -1,79 /
-2,40 - je NIEDRIGER der Umschlag, desto besser. Bleibt das so, ist der
Wechsel eine Praezisierung. Dreht es, ist er ein anderer Beitrag mit
demselben Namen.

⚠️ IN-SAMPLE, wie das Original: dieselben Daten, aus denen das Urteil
kommt. Deshalb halbiert - dieselbe Vorsicht wie dort.

    python phase4_c_stufen_freefloat.py
    python phase4_c_stufen_freefloat.py --horizonte 2,3,5 --crv 2.0
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

import hole_umlaufmenge_cg as HU                           # noqa: E402
import messe_bewertungskennzahl as MB                      # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402

# ⚠️ Die registrierte Zeile, zum Vergleich - nicht getippt, sondern aus
# dem laufenden Modul gezogen, damit sie nicht auseinanderlaeuft.
import agent.wahrscheinlichkeit as WA                      # noqa: E402

MIND_JE_TAG = 15                 # wie im Original


def _arg(flagge, vorgabe):
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def menge_neu(db="data/umlaufmenge_cg.db"):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    roh = {}
    for sym, tag, w in c.execute(
            "SELECT u.symbol, u.datum, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol a ON a.symbol = u.symbol "
            " WHERE a.urteil='ok' AND u.wert > 0 ORDER BY u.symbol, u.datum"):
        roh.setdefault(sym.upper(), []).append((str(tag)[:10], float(w)))
    aus = {}
    for s, reihe in roh.items():
        raus = HU.entferne_spitzen([w for _t, w in reihe])
        aus[s] = {t: w for i, (t, w) in enumerate(reihe) if i not in raus}
    return aus


def tabelle(je_tag: dict, crv: float, ab: str):
    """Fuenftel-Stufen - dieselbe Rechnung wie `rechne_turnover_beitrag`."""
    sammel = {k: [] for k in range(5)}
    tage = 0
    for tag, z in je_tag.items():
        if str(tag)[:10] < ab or len(z) < MIND_JE_TAG:
            continue
        tage += 1
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if not tage or any(not sammel[k] for k in range(5)):
        return None, 0, None
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    faktor = 1.0 / (1.0 + crv)
    stufen = [round(100.0 * (werte[k] - mittel) * faktor / 2.0, 2)
              for k in range(5)]
    return stufen, tage, werte


def monoton(stufen) -> bool:
    return all(stufen[i] >= stufen[i + 1] for i in range(4))


def main() -> int:
    horizonte = tuple(int(x) for x in _arg("--horizonte", "2,3,5").split(","))
    crv = float(_arg("--crv", "2.0"))
    print("=" * 100)
    print("DIE BEITRAGSTABELLE AUF DEM FREIEN UMLAUF - behaelt sie ihre "
          "FORM?")
    print("=" * 100)
    # ⚠️ Ueber `merkmal`, nicht ueber `name`: der Name ist Fliesstext
    # ("Turnover-Rang im Markt"), das Merkmal ist der Schluessel, mit dem
    # die Bewertung rechnet. Eine Suche im Namen fand null Treffer.
    reg = next((b.stufen for b in WA.BEITRAEGE
                if b.merkmal == "turnover_fuenftel"), None)
    print("  registriert (H20, lange Historie): %s"
          % (", ".join("%+.2f" % x for x in reg) if reg else "nicht "
             "gefunden"))
    print("  ⚠️ Sie ist KEIN Vergleichsmassstab fuer die Zahlen unten - "
          "anderer Horizont,")
    print("     anderes Fenster. Verglichen wird die FORM, nicht der "
          "Betrag.")
    print()
    neu = menge_neu()
    alt = MB.reihe("data/onchain_historie.db", "splycur")
    ab = min(t for d in neu.values() for t in d)
    reihen = B.lade()
    print("  Fenster ab %s · CRV %.1f · Mindestbesetzung %d je Tag"
          % (ab, crv, MIND_JE_TAG))
    print()
    print("  %-10s %3s %6s %7s %7s %7s %7s %7s   %s"
          % ("Nenner", "H", "Tage", "F0", "F1", "F2", "F3", "F4", "Form"))
    # ⚠⚠ DREI ARME, NICHT ZWEI. Die Form allein zwischen ALT (44
    # Symbole) und NEU (375) zu vergleichen waere unzulaessig: Fuenftel
    # aus 44 Werten sind mit je 8 bis 9 Symbolen besetzt und deshalb
    # schon fuer sich unruhig. Ein glatterer Verlauf koennte allein von
    # der groesseren Menge kommen.
    #
    # NEU-GEM ist der saubere Vergleich: neuer Nenner, aber NUR die
    # gemeinsamen Symbole - dieselbe Grundgesamtheit wie ALT. Dieselbe
    # Zerlegung wie in der Kalibrierung.
    gemeinsam = set(neu) & set(alt)
    neu_gem = {s: v for s, v in neu.items() if s in gemeinsam}
    print("  ARME: ALT %d Symbole · NEU-GEM %d (gemeinsam) · "
          "NEU %d" % (len(alt), len(neu_gem), len(neu)))
    print()
    for H in horizonte:
        for name, quelle in (("ALT", alt), ("NEU-GEM", neu_gem),
                             ("NEU", neu)):
            je = K.baue(reihen, "turnover", quelle, horizont=H)
            stufen, tage, _w = tabelle(je, crv, ab)
            if stufen is None:
                print("  %-10s %3d -> zu wenige Tage" % (name, H))
                continue
            print("  %-10s %3d %6d %+7.2f %+7.2f %+7.2f %+7.2f %+7.2f   %s"
                  % (name, H, tage, stufen[0], stufen[1], stufen[2],
                     stufen[3], stufen[4],
                     "MONOTON fallend" if monoton(stufen) else
                     "⚠️ NICHT monoton"))
        print()
    print("=" * 100)
    print("  ⚠️ LESEART: Fuenftel 0 ist der NIEDRIGSTE Umschlag. Die "
          "registrierte Zeile")
    print("     faellt monoton - je niedriger der Umschlag, desto "
          "besser. Bleibt das,")
    print("     ist der Wechsel eine Praezisierung; dreht es, ist es ein "
          "anderer Beitrag")
    print("     mit demselben Namen.")
    print("  ⚠️ IN-SAMPLE und halbiert - wie das Original. Diese Zahlen "
          "sind keine")
    print("     Vorhersage, sondern die Form derselben Daten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
