# -*- coding: utf-8 -*-
"""WAS TAETE EIN WECHSEL DES `turnover`-NENNERS AM RANG?

⚠️⚠️ DIE HAUSREGEL VERLANGT DIESE MESSUNG, nicht eine Abwaegung
(`grundgesamtheit-ist-keine-stellschraube`, Punkt 2): *„Wer sie aendert,
MISST die Wirkung: wie viele Werte wechseln das Fuenftel?"* Und die
Meta-Lehre vom 20.09. gilt hier genauso - ich hatte die Grundgesamtheit
dreimal als ENTSCHEIDUNG vorgelegt, obwohl sie eine MESSUNG war.

Mit dem Fuenftel rechnet die Bewertung (`wahrscheinlichkeit`), nicht mit
dem Rohwert. Ein Rangwechsel innerhalb eines Fuenftels ist folgenlos;
einer ueber die Grenze aendert den Zuschlag um bis zu 3,15 Punkte.

## Zwei Arme - dieselbe Zerlegung wie in der Kalibrierung

    A  GROESSE   nur die GEMEINSAMEN Symbole, einmal mit `SplyCur`,
                 einmal mit Free Float. Die Grundgesamtheit ist
                 identisch, also ist jeder Unterschied die GROESSE
    B  MENGE     Free Float auf ALLEN Symbolen gegen `SplyCur` auf
                 seinen 66. So sieht der Betrieb es tatsaechlich -
                 aber hier aendern sich zwei Dinge zugleich

⚠️ GEMESSEN WIRD AUF DER HISTORIE, nicht an einem Live-Abruf: 365 Tage
statt eines Augenblicks, und ohne jeden Netzzugriff. Der Betrieb rechnet
mit einem rollenden 24-Stunden-Fenster statt der Tageskerze - dieselbe
Boerse, dieselbe Einheit, andere Ausrichtung (2.418-teilkerze). Fuer die
Frage "wie viele wechseln das Fuenftel" ist das unerheblich.

⚠️ NUR LESEND. Keine api/*-Aufrufe (die buchen ueber `api_health` in die
Produktionsdatenbank).

    python phase4_c_rangwirkung_freefloat.py
"""
from __future__ import annotations

import os
import sqlite3
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import hole_umlaufmenge_cg as HU                           # noqa: E402

NEU_DB = "data/umlaufmenge_cg.db"
ALT_DB = "data/onchain_historie.db"
MIND_JE_TAG = 12


def fuenftel(rang: float) -> int:
    """⚠️ DIESELBE Einteilung wie im Betrieb - `marktrang._fuenftel`."""
    return MR._fuenftel(rang)


def raenge_je_tag(werte: dict) -> dict:
    """Querschnittsrang je Tag, mit dem ECHTEN `_rang` des Betriebs."""
    aus = {}
    for tag, je_sym in werte.items():
        if len(je_sym) < MIND_JE_TAG:
            continue
        aus[tag] = MR._rang(je_sym)
    return aus


def lade():
    c = sqlite3.connect("file:%s?mode=ro" % NEU_DB, uri=True)
    neu_roh = {}
    for sym, tag, w in c.execute(
            "SELECT u.symbol, u.datum, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol a ON a.symbol = u.symbol "
            " WHERE a.urteil = 'ok' AND u.wert > 0 ORDER BY u.symbol, u.datum"):
        neu_roh.setdefault(sym.upper(), []).append((str(tag)[:10], float(w)))
    neu = {}
    weg = 0
    for s, reihe in neu_roh.items():
        raus = HU.entferne_spitzen([w for _t, w in reihe])
        weg += len(raus)
        neu[s] = {t: w for i, (t, w) in enumerate(reihe) if i not in raus}
    a = sqlite3.connect("file:%s?mode=ro" % ALT_DB, uri=True)
    alt = {}
    for sym, tag, w in a.execute(
            "SELECT symbol, datum, wert FROM splycur WHERE wert > 0"):
        alt.setdefault(sym.upper(), {})[str(tag)[:10]] = float(w)
    datei, _sql = MR.MESSBASIS["schnitt"]
    ab = min(t for d in neu.values() for t in d)
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    vol = {}
    for sym, tag, v in m.execute(
            "SELECT symbol, date, volume FROM price_history_ohlc "
            " WHERE date >= ? AND volume > 0", (ab,)):
        vol.setdefault(sym.upper(), {})[str(tag)[:10]] = float(v)
    return neu, alt, vol, weg, ab


def umschlag(vol: dict, menge: dict, erlaubt=None) -> dict:
    """Je Tag: Symbol -> Volumen / Menge. Genau wie `turnover_werte`."""
    je_tag = {}
    for sym, tage in vol.items():
        if erlaubt is not None and sym not in erlaubt:
            continue
        m = menge.get(sym)
        if not m:
            continue
        for t, v in tage.items():
            q = m.get(t)
            if q and q > 0:
                je_tag.setdefault(t, {})[sym] = v / q
    return je_tag


def vergleiche(name: str, ra: dict, rb: dict) -> None:
    """Wie oft wechselt das FUENFTEL - und in welche Richtung?"""
    gewechselt = gleich = 0
    zwei_plus = 0
    richtung = []
    je_sym_w, je_sym_n = {}, {}
    for tag in set(ra) & set(rb):
        for sym in set(ra[tag]) & set(rb[tag]):
            fa, fb = fuenftel(ra[tag][sym]), fuenftel(rb[tag][sym])
            je_sym_n[sym] = je_sym_n.get(sym, 0) + 1
            if fa == fb:
                gleich += 1
            else:
                gewechselt += 1
                je_sym_w[sym] = je_sym_w.get(sym, 0) + 1
                zwei_plus += (abs(fa - fb) >= 2)
                richtung.append(fb - fa)
    ges = gleich + gewechselt
    print("  %s" % name)
    if not ges:
        print("     keine gemeinsamen Symbol-Tage")
        return
    print("     Symbol-Tage verglichen: %d \u00b7 Fuenftel GEWECHSELT: "
          "%d = %.1f %%" % (ges, gewechselt, 100.0 * gewechselt / ges))
    print("     davon um ZWEI oder mehr Stufen: %d = %.1f %% aller Wechsel"
          % (zwei_plus, 100.0 * zwei_plus / gewechselt if gewechselt else 0))
    if richtung:
        hoch = sum(1 for x in richtung if x > 0)
        print("     Richtung: %d nach OBEN, %d nach UNTEN (Median %+.1f "
              "Stufen)" % (hoch, len(richtung) - hoch, st.median(richtung)))
        print("     \u26a0 Eine einseitige Richtung ist kein Rauschen - "
              "sie verschoebe")
        print("        die ganze Verteilung, nicht einzelne Werte.")
    je_sym = sorted(((je_sym_w.get(s, 0) / n, s, je_sym_w.get(s, 0), n)
                     for s, n in je_sym_n.items() if n >= 30), reverse=True)
    betroffen = sum(1 for a, _s, _w, _n in je_sym if a > 0.20)
    print("     Symbole mit ueber 20 %% gewechselten Tagen: %d von %d"
          % (betroffen, len(je_sym)))
    for a, s, w, n in je_sym[:8]:
        if a > 0:
            print("       %-10s %3d von %3d Tagen = %.0f %%" % (s, w, n,
                                                                100 * a))


def main() -> int:
    print("=" * 100)
    print("RANGWIRKUNG EINES NENNERWECHSELS - gemessen, nicht abgewogen")
    print("=" * 100)
    neu, alt, vol, weg, ab = lade()
    gemeinsam = set(neu) & set(alt) & set(vol)
    print("  Free Float: %d Symbole (%d Tagesartefakte ausgeworfen) \u00b7 "
          "SplyCur: %d \u00b7 gemeinsam: %d"
          % (len(neu), weg, len(alt), len(gemeinsam)))
    print("  Fenster ab %s \u00b7 Mindestbesetzung %d je Tag"
          % (ab, MIND_JE_TAG))
    print()
    print("-" * 100)
    print("  ARM A - NUR DIE GROESSE (gemeinsame Symbole, gleiche "
          "Grundgesamtheit)")
    print("-" * 100)
    ra = raenge_je_tag(umschlag(vol, alt, gemeinsam))
    rb = raenge_je_tag(umschlag(vol, neu, gemeinsam))
    vergleiche("SplyCur gegen Free Float, %d Symbole:" % len(gemeinsam),
               ra, rb)
    print()
    print("-" * 100)
    print("  ARM B - SO WIE DER BETRIEB ES SAEHE (alte Menge gegen neue)")
    print("-" * 100)
    rc = raenge_je_tag(umschlag(vol, alt))
    rd = raenge_je_tag(umschlag(vol, neu))
    n_alt = len({s for d in rc.values() for s in d})
    n_neu = len({s for d in rd.values() for s in d})
    print("  \u26a0\u26a0 HIER AENDERN SICH ZWEI DINGE ZUGLEICH: die "
          "Groesse UND die")
    print("     Grundgesamtheit (%d gegen %d Symbole). Die Zahl ist "
          "deshalb NICHT" % (n_alt, n_neu))
    print("     der Groesse zuzuschreiben - Arm A ist der saubere "
          "Vergleich.")
    vergleiche("alte Kette gegen neue:", rc, rd)
    print()
    print("=" * 100)
    print("  \u26a0 WAS DIESE MESSUNG NICHT SAGT: sie zaehlt, wie viele "
          "Werte das Fuenftel")
    print("     wechseln - nicht, welches Fuenftel RICHTIG ist. Das "
          "beantwortet nur")
    print("     eine Wirksamkeitsmessung (phase4_c_kalibrierung_"
          "freefloat).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
