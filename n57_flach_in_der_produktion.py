# -*- coding: utf-8 -*-
"""N-57 — WIEVIEL LAEUFT FLACH AUS? Kalibrierungsbasis gegen Produktion (06.09.)

## ⚠️ Die Frage hat sich beim Nachsehen geaendert

Erste Fassung der Frage: *„`q` in der Potentialformel ist die
Barrieren-Trefferquote, und die zaehlt einen flachen Auslauf wie einen
Stop — obwohl er fast nichts kostet."*

**Das war falsch adressiert.** In der Kette gibt es **keinen
Zeitausstieg**: `haltedauer_tage` wird nur als Information mitgegeben
(`rollen_lauf` Zeilen 2042/2377/2532), `positionsfuehrung` kennt keine
Frist, und `GRENZEN["tage_max"] = 120` deckelt nur die Kostenschaetzung.

> **In der Produktion laeuft eine Position bis Stop oder Ziel. Flach
> auslaufen gibt es dort nicht.** Damit ist `q = P(Ziel vor Stop)` die
> richtige Groesse und `wert_r = q x CRV - (1 - q)` korrekt.

## ⚠️⚠️ Das Problem loest sich nicht auf, es verschiebt sich

**Jede Kalibrierung misst mit FESTEM Horizont** (H5, H20). Dort zaehlt ein
nicht aufgeloester Anker als 0 — also wie ein Stop. Die Kalibrierungsbasis
tut etwas, was die Produktion nicht tut.

    Wieviel ist das? Das ist die Zahl, die die Reihenfolge entscheidet.

## Was gemessen wird — in der ECHTEN Geometrie

    Stop  = max(5 % vom Kurs, 0,75 x ATR), gedeckelt bei 25 % vom Kurs
            (`entscheidungsrechnung._boeden`, `GRENZEN`)
    Ziel  = Stopabstand x CRV 2,0
    ⚠️ NICHT die Messgeometrie (1,0 x ATR) - die ist eine Konvention

    1  Wieviel loest bis Tag 5 / 20 / 60 / 120 auf?
    2  Wie lange dauert es im Median?
    3  Was kostet der Unterschied? Der Erwartungswert in R einmal mit
       „flach = 0 wie ein Stop" (Kalibrierung) und einmal mit
       „flach = weiterlaufen lassen" (Produktion).

## Gegenpruefungen — vorab benannt

    A  DIESELBE Frage in der MESSgeometrie (1,0 x ATR). Ist der
       Unterschied gross, ist ein Teil des Befundes die Geometrie.
    B  BEIDE Historienhaelften. Was ueber die Zeit nicht haelt, gilt nicht.
    C  Die Same-Bar-Regel: Gleichstand an den STOP (N-55). Zur Kontrolle
       wird auch die optimistische Variante gezeigt - sie darf die
       AUFLOESUNGSQUOTE nicht veraendern, nur ihre Aufteilung.

    python n57_flach_in_der_produktion.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
from agent import entscheidungsrechnung as E                 # noqa: E402

BRUCH = 5.0
CRV = float(E.GRENZEN["crv"])
K_ATR = float(E.GRENZEN["stop_min_atr"])          # 0,75
MIN_REL = float(E.GRENZEN["stop_min_relativ"])    # 0,05
MAX_REL = float(E.GRENZEN["stop_max_relativ"])    # 0,25
MAXH = int(E.GRENZEN["tage_max"])                 # 120
MARKEN = (5, 20, 60, 120)


def fenster(x, breite):
    from numpy.lib.stride_tricks import sliding_window_view
    return sliding_window_view(x[1:], breite)


def stopweite(c, br, produktion=True):
    """Die Stopweite in Kurseinheiten.

    ⚠️ DIE EINE STELLE ist `entscheidungsrechnung._boeden`; hier wird nur
    ihr Rauschboden nachgebildet (Struktur und These brauchen Modell-
    ausgaben, die es in der Historie nicht gibt). Das ist die UNTERGRENZE
    der echten Weite - die echte ist eher weiter, also loest sie eher
    NOCH seltener aus. Der Befund ist damit konservativ.
    """
    if not produktion:
        return br.copy()                     # Messkonvention: 1,0 x ATR
    return np.minimum(np.maximum(MIN_REL * c, K_ATR * br), MAX_REL * c)


def lauf(reihen, produktion=True, gleichstand_ziel=False, halb=None):
    """Zaehlt Ausgaenge je Tag-bis-Aufloesung."""
    tz_alle, ts_alle, ewr_prod, ewr_kal = [], [], {}, {}
    weiten_rel = []
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        n = len(c)
        if n < MAXH + B.SCHWANKUNG + 5:
            continue
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        kaputt = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        bruch_f = fenster(np.concatenate([[False], kaputt]), MAXH).any(axis=1)
        hoch_f, tief_f = fenster(h, MAXH), fenster(t, MAXH)
        gueltig = min(len(hoch_f), n - MAXH)
        idx = np.arange(B.SCHWANKUNG, gueltig)
        idx = idx[np.isfinite(br[idx]) & (br[idx] > 0) & ~bruch_f[idx]]
        if halb is not None:
            m = len(tage) // 2
            idx = idx[idx < m] if halb == 0 else idx[idx >= m]
        if not len(idx):
            continue
        weite = stopweite(c[idx], br[idx], produktion)
        weiten_rel.append(weite / c[idx])
        ziel, stop = c[idx] + CRV * weite, c[idx] - weite
        tr_z = hoch_f[idx] >= ziel[:, None]
        tr_s = tief_f[idx] <= stop[:, None]
        tz = np.where(tr_z.any(axis=1), tr_z.argmax(axis=1) + 1, 0)
        ts = np.where(tr_s.any(axis=1), tr_s.argmax(axis=1) + 1, 0)
        tz_alle.append(tz)
        ts_alle.append(ts)
    tz = np.concatenate(tz_alle)
    ts = np.concatenate(ts_alle)
    rel = np.concatenate(weiten_rel)
    return tz, ts, rel


def ausgang(tz, ts, hz, gleichstand_ziel=False):
    """+1 Ziel, -1 Stop, 0 flach - innerhalb von hz Tagen."""
    z = np.where((tz > 0) & (tz <= hz), tz, 0)
    s = np.where((ts > 0) & (ts <= hz), ts, 0)
    if gleichstand_ziel:
        gewinn = (z > 0) & ((s == 0) | (z <= s))
        verlust = (s > 0) & ~gewinn
    else:
        verlust = (s > 0) & ((z == 0) | (s <= z))
        gewinn = (z > 0) & ~verlust
    return gewinn, verlust, ~(gewinn | verlust)


def zeige(tz, ts, rel, titel, gleichstand_ziel=False):
    print()
    print("  %s  (%d Anker)" % (titel, len(tz)))
    print("     Stopweite im Median %.2f %% vom Kurs" % (100 * np.median(rel)))
    print("     %-8s %9s %9s %9s   %s"
          % ("bis Tag", "Ziel", "Stop", "FLACH", "Erwartungswert in R"))
    for hz in MARKEN:
        g, v, f = ausgang(tz, ts, hz, gleichstand_ziel)
        n = len(tz)
        # KALIBRIERUNG: flach zaehlt als 0 -> also wie ein Stop im Zaehler
        # der Quote. Der Erwartungswert dazu rechnet flach mit -1? Nein -
        # die Quote ist q = Treffer/alle, und wert_r = q*CRV - (1-q).
        q = g.sum() / n
        wert_kal = q * CRV - (1.0 - q)
        # PRODUKTION: nur die Aufgeloesten zaehlen, der Rest laeuft weiter
        auf = g.sum() + v.sum()
        q_prod = g.sum() / auf if auf else float("nan")
        wert_prod = q_prod * CRV - (1.0 - q_prod)
        print("     %-8d %8.1f%% %8.1f%% %8.1f%%   Kalibrierung %+.4f · "
              "Produktion %+.4f"
              % (hz, 100 * g.sum() / n, 100 * v.sum() / n, 100 * f.sum() / n,
                 wert_kal, wert_prod))
    beide = np.where((tz > 0) | (ts > 0),
                     np.where(tz > 0, tz, 10 ** 6), 10 ** 6)
    beide = np.minimum(beide, np.where(ts > 0, ts, 10 ** 6))
    fertig = beide < 10 ** 6
    print("     Median Tage bis Aufloesung: %.0f  (von den %.1f %%, die "
          "binnen %d Tagen aufloesen)"
          % (np.median(beide[fertig]) if fertig.any() else float("nan"),
             100 * fertig.mean(), MAXH))


def main() -> int:
    t0 = time.time()
    print("=" * 92)
    print("N-57 — wieviel laeuft FLACH aus? Kalibrierungsbasis gegen "
          "Produktion")
    print("=" * 92)
    print("  Produktionsgeometrie: Stop = max(%.0f %% Kurs, %.2f x ATR), "
          "Deckel %.0f %%, CRV %.1f" % (100 * MIN_REL, K_ATR,
                                        100 * MAX_REL, CRV))
    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()

    tz, ts, rel = lauf(reihen, produktion=True)
    zeige(tz, ts, rel, "1  PRODUKTIONSGEOMETRIE")

    print()
    print("  " + "-" * 88)
    print("  GEGENPRUEFUNG A — dieselbe Frage in der MESSgeometrie "
          "(1,0 x ATR)")
    tz2, ts2, rel2 = lauf(reihen, produktion=False)
    zeige(tz2, ts2, rel2, "2  MESSGEOMETRIE")

    print()
    print("  " + "-" * 88)
    print("  GEGENPRUEFUNG B — beide Historienhaelften (Produktionsgeometrie)")
    for i, lab in ((0, "erste Haelfte"), (1, "zweite Haelfte")):
        a, b, r = lauf(reihen, produktion=True, halb=i)
        zeige(a, b, r, "3%s  %s" % ("ab"[i], lab))

    print()
    print("  " + "-" * 88)
    print("  GEGENPRUEFUNG C — Gleichstand an das ZIEL statt an den Stop")
    print("     ⚠️ Die AUFLOESUNGSQUOTE darf sich dadurch NICHT aendern,")
    print("        nur ihre Aufteilung. Aendert sie sich, ist die Zaehlung")
    print("        kaputt.")
    zeige(tz, ts, rel, "4  optimistischer Gleichstand", gleichstand_ziel=True)

    print()
    print("=" * 92)
    print("WAS DAS HEISST")
    print("=" * 92)
    g5, v5, f5 = ausgang(tz, ts, 5)
    g20, v20, f20 = ausgang(tz, ts, 20)
    print("  Bei H5 laufen %.1f %% flach aus, bei H20 noch %.1f %%."
          % (100 * f5.mean(), 100 * f20.mean()))
    print()
    print("  ⚠️ In der PRODUKTION gibt es diesen Ausgang nicht - dort laeuft")
    print("     die Position weiter. Jeder flache Anker in der Messung ist")
    print("     also ein Anker, den die Kalibrierung als Nicht-Treffer")
    print("     zaehlt, obwohl die Produktion ihn noch offen haette.")
    print()
    print("  Der Unterschied im Erwartungswert:")
    for hz, (g, v, f) in ((5, (g5, v5, f5)), (20, (g20, v20, f20))):
        n = len(tz)
        q = g.sum() / n
        auf = g.sum() + v.sum()
        qp = g.sum() / auf if auf else float("nan")
        print("     H%-4d Kalibrierung %+.4f R · Produktion %+.4f R · "
              "Luecke %+.4f R"
              % (hz, q * CRV - (1 - q), qp * CRV - (1 - qp),
                 (qp * CRV - (1 - qp)) - (q * CRV - (1 - q))))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
