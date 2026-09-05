# -*- coding: utf-8 -*-
"""N-41: Beitragsstufen DIREKT aus der Barrieren-Quote (05.09.2026)

## Warum

Die registrierten Stufen werden auf `in_r` gefittet (Rendite in R nach
20 Tagen) und als Verschiebung der **Quote** interpretiert. Das sind zwei
verschiedene Groessen - der Formfehler aus Methodik 2.85.

Gegengeprueft (05.09., direkt auf der Barriere gemessen):

    FUNDING   Spanne direkt 1,06 Punkte gegen registriert 3,00  (Faktor 0,35)
              ⚠️ und NICHT monoton
    TURNOVER  Spanne direkt 2,93 Punkte gegen registriert 5,55  (Faktor 0,53)
              monoton, Richtung stimmt

**Die Stufen sind rund doppelt so gross, wie die Barriere hergibt.** Das
erklaert einen guten Teil des Kalibrierungsfaktors 0,168 aus F-215.

## Was hier gemacht wird

Die Stufen werden DIREKT aus der Quote gebildet:

    punkte(fuenftel) = 100 x (q_fuenftel - basisrate)

Das ist selbstkalibrierend - keine Umrechnung, kein Faktor. Was gemessen
wird, IST was das Potential behauptet.

⚠️ **OUT-OF-SAMPLE, sonst ist es zirkulaer**: erste Haelfte fitten, zweite
Haelfte pruefen - dieselbe Anlage wie N-37.

## ⚠️ Die Basisrate: 1/3 oder die gemessene?

Theoretisch ist `quote = 1/(1+CRV) = 33,3 %`. Gemessen liegt sie bei rund
31,5 % - erklaerbar durch die Tageskerze (der Stop kann vom Tief beruehrt
werden, und bei Gleichstand gewinnt der Stop, F-215).

Beides wird berichtet:
  gegen 1/3           die Definition - zeigt, wo wir gegen die Theorie stehen
  gegen die gemessene die Spreizung - zeigt, was die Groesse TRENNT

⚠️ Die Spreizung ist die entscheidende Zahl; das Niveau ist ein bekanntes
Artefakt und darf nicht wegkalibriert werden.

    python messe_stufen_aus_quote.py [--selbsttest]
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import (                  # noqa: E402
    _fuenftel_je_tag, _steigung, baue_gruppen, _mit_stufen)
from agent import wahrscheinlichkeit as W                   # noqa: E402

CRV = 2.0
VARIANTE = "ZIEL 2,0"
BASIS_THEORIE = 1.0 / (1.0 + CRV)
MIND_JE_FUENFTEL = 500
SAAT = 20260905


def quote_je_fuenftel(zeilen, tage_je_sym, f5, nur_tage=None) -> dict:
    """{fuenftel: (treffer, n)} - nur ENTSCHIEDENE Anker.

    ⚠️ Dieselbe Konvention wie N-37: exakt +CRV (Ziel) oder exakt -1 (Stop).
    Alles andere ist unaufgeloest und wird nicht gezaehlt.
    """
    je = defaultdict(lambda: [0, 0])
    for z in zeilen:
        tage = tage_je_sym.get(z["sym"])
        if not tage or z["i"] >= len(tage):
            continue
        tag = tage[z["i"]]
        if nur_tage is not None and tag not in nur_tage:
            continue
        f = (f5.get(tag) or {}).get(z["sym"])
        if f is None:
            continue
        w = z.get(VARIANTE)
        if w is None:
            continue
        if abs(w - CRV) < 1e-9:
            je[f][0] += 1
            je[f][1] += 1
        elif abs(w + 1.0) < 1e-9:
            je[f][1] += 1
    return {k: tuple(v) for k, v in je.items()}


def stufen_aus_quote(je: dict, basis: float) -> list | None:
    """punkte(f) = 100 x (q_f - basis) - selbstkalibrierend, kein Faktor."""
    if not je or any(je.get(f, (0, 0))[1] < MIND_JE_FUENFTEL for f in range(5)):
        return None
    return [round(100.0 * (je[f][0] / je[f][1] - basis), 2) for f in range(5)]


def _basis_gemessen(je: dict) -> float:
    tr = sum(v[0] for v in je.values())
    n = sum(v[1] for v in je.values())
    return tr / n if n else BASIS_THEORIE


def selbsttest() -> bool:
    """Eine Welt mit BEKANNTER Quote je Fuenftel - die Stufen muessen sie treffen."""
    rng = np.random.default_rng(4)
    wahr = {0: 0.40, 1: 0.37, 2: 0.34, 3: 0.31, 4: 0.28}
    zeilen, tage_je_sym, f5 = [], {}, {}
    for si in range(40):
        tage_je_sym["S%02d" % si] = ["t%03d" % t for t in range(300)]
    for t in range(300):
        tag = "t%03d" % t
        f5[tag] = {}
        for si in range(40):
            sym = "S%02d" % si
            f = si % 5
            f5[tag][sym] = f
            zeilen.append({"sym": sym, "i": t,
                           VARIANTE: (CRV if rng.random() < wahr[f] else -1.0)})
    je = quote_je_fuenftel(zeilen, tage_je_sym, f5)
    st = stufen_aus_quote(je, BASIS_THEORIE)
    soll = [round(100 * (wahr[f] - BASIS_THEORIE), 2) for f in range(5)]
    print("  SELBSTTEST — gepflanzte Quoten 40/37/34/31/28 %")
    print("    gemessen %s" % " ".join("%+6.2f" % x for x in st))
    print("    erwartet %s" % " ".join("%+6.2f" % x for x in soll))
    ab = max(abs(a - b) for a, b in zip(st, soll))
    # ⚠️ DIE SCHWELLE WIRD HERGELEITET, NICHT GERATEN (05.09.2026).
    #
    # Erste Fassung nahm 0,6 Punkte - und der Selbsttest fiel durch, obwohl
    # er die Wahrheit gut traf. Bei n je Fuenftel ist der Standardfehler
    # einer Quote sqrt(q(1-q)/n), in Punkten mal 100. Zwei Standardfehler
    # sind die faire Grenze; alles darunter ist Rauschen, nicht Fehler.
    n_min = min(je[f][1] for f in range(5))
    se = 100.0 * (0.34 * 0.66 / n_min) ** 0.5
    grenze = 2.0 * se
    ok = ab < grenze
    print("    groesste Abweichung %.2f Punkte · Grenze %.2f (2 Standardfehler"
          " bei n=%d)  ->  %s" % (ab, grenze, n_min, "OK" if ok else "✖ FEHLER"))
    return ok


def main() -> int:
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    print("Barrieren-Ausgaenge...", flush=True)
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {a: _fuenftel_je_tag(K.baue(reihen, a, quellen[a], horizont=20))
          for a in ("funding", "turnover")}
    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    mitte = alle[len(alle) // 2]
    erste = {t for t in alle if t < mitte}
    zweite = {t for t in alle if t >= mitte}
    print("  SPLIT bei %s · erste %d Tage · zweite %d" % (mitte, len(erste), len(zweite)))

    fit = {}
    for art in ("funding", "turnover"):
        print()
        print("=" * 92)
        print("%s — Stufen aus der Quote, ERSTE Haelfte" % art.upper())
        print("=" * 92)
        je1 = quote_je_fuenftel(zeilen, tage_je_sym, f5[art], erste)
        je2 = quote_je_fuenftel(zeilen, tage_je_sym, f5[art], zweite)
        b1, b2 = _basis_gemessen(je1), _basis_gemessen(je2)
        s1 = stufen_aus_quote(je1, BASIS_THEORIE)
        s1g = stufen_aus_quote(je1, b1)
        s2g = stufen_aus_quote(je2, b2)
        if not s1:
            print("  zu wenige Anker je Fuenftel")
            continue
        fit[art] = s1
        print("  Basisrate: Theorie %.1f %% · erste Haelfte %.1f %% · zweite %.1f %%"
              % (100 * BASIS_THEORIE, 100 * b1, 100 * b2))
        print()
        print("  gegen die THEORIE   %s" % " ".join("%+6.2f" % x for x in s1))
        print("  gegen die GEMESSENE %s   <- die Spreizung" % " ".join("%+6.2f" % x for x in s1g))
        print("  ZWEITE Haelfte      %s   <- haelt sie?" % " ".join("%+6.2f" % x for x in s2g))
        reg = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "%s_fuenftel" % art and b.stufen), None)
        if reg:
            print("  registriert         %s" % " ".join("%+6.2f" % x for x in reg))
        if s1g and s2g:
            # ⚠️ Rangkorrelation der Stufen zwischen den Haelften - haelt die ORDNUNG?
            r1 = np.argsort(np.argsort(s1g))
            r2 = np.argsort(np.argsort(s2g))
            gl = int((r1 == r2).sum())
            print()
            print("  Spanne erste %+.2f · zweite %+.2f · gleiche Rangplaetze %d von 5"
                  % (max(s1g) - min(s1g), max(s2g) - min(s2g), gl))
            print("  -> %s" % ("die Ordnung haelt" if gl >= 4 else
                               "⚠️ die Ordnung haelt NICHT - kein verwertbarer Beitrag"))

    if len(fit) < 2:
        print("\n  nicht genug Stufen gefittet - Abbruch")
        return 0

    print()
    print("=" * 92)
    print("OUT-OF-SAMPLE: kalibriert die Bewertung mit den Quote-Stufen?")
    print("=" * 92)
    alt = W.BEITRAEGE
    W.BEITRAEGE = _mit_stufen(fit["funding"], fit["turnover"])
    try:
        rng = np.random.default_rng(SAAT)
        g2 = baue_gruppen(zeilen, tage_je_sym, f5["funding"], f5["turnover"],
                          nur_tage=zweite)
        print("  Stufen: %d" % len(g2))
        _steigung(g2, rng)
        print()
        print("  ⚠️ N-37 mass mit den REGISTRIERTEN Stufen +0,056 gegen erwartet")
        print("     +0,333. Naeher an 0,333 heisst: der Umrechnungsfehler war")
        print("     die Ursache. Bleibt es bei ~0,056, war es schwache Ordnung.")
    finally:
        W.BEITRAEGE = alt
    return 0


if __name__ == "__main__":
    sys.exit(main())
