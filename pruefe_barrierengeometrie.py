# -*- coding: utf-8 -*-
"""Ist die Barrierengeometrie die BETRIEBSgeometrie? (25.09.2026)

Der Docstring von `k1c_hebel_barriere.barriere_je_reihe` behauptet:

    "Ziel vor Stop, auf der PRODUKTIONSGEOMETRIE (...)
     ⚠️ Genau die Geometrie, die `entscheidungsrechnung` baut - sonst misst
     der Test etwas anderes als das, was die App vorschlaegt."

Das ist PRUEFBAR, und es haengt viel daran: sechs Messwerkzeuge und der
Horizont `messnorm.HORIZONT_JE_LAGE[(hebel, einstieg)] = 3`.

═══════════════════════════════════════════════════════════════════════
 VIER GEOMETRIEN, und sie sind NICHT dieselbe
═══════════════════════════════════════════════════════════════════════

    MESSUNG          min(25%K, max(5%K, 0,75 x ATR))
                     ➤ nur die UNTERGRENZE. Der Zielwert 2,5 x ATR fehlt

    RUECKFALL Code   clamp(2,5 x ATR, max(5%K, 0,75 x ATR), 25%K)
                     ➤ `_stop_aus_atr` mit GRENZEN, also stop_min_atr 0,75

    RUECKFALL LIVE   clamp(2,5 x ATR, max(5%K, 2,0 x ATR), 25%K)
                     ⚠️ config.yaml Zeile 2205: `stop_min_atr: 2.0`.
                     Die Kette liest ihn ueber `BE.stop_min_atr(config)`,
                     NICHT aus GRENZEN (Hinweis 2.457-n3, 17.09.)

    BETRIEB          13 % des Kurses, flach
                     ⚠️ Befund 2.397: mit dem Widerlegungspreis des
                     Modells liegt der Median-Stop bei rund 13 %; ohne ihn
                     bei 25 % (dem Deckel). 81,5 % der Stops kommen von
                     dort. Das ist die Zahl, die tatsaechlich gehandelt
                     wird - ⚠️ und sie ist NICHT nachgemessen (2.397 ist
                     laut Register nicht reproduzierbar, das Werkzeug
                     `messe_widerlegung.py` fehlt). Sie steht hier als
                     Orientierung, nicht als Beleg

═══════════════════════════════════════════════════════════════════════
 WARUM DER STOP DEN HORIZONT MITBESTIMMT
═══════════════════════════════════════════════════════════════════════

Befund 2.445-wirkung (32.040 Anker) misst den Median bis zur ERSTEN Marke:

    Stop in ATR   0,75   1,0   1,5   2,0   2,5    3,0
    LONG             3     5    10    16    23     33

➤ Ein Horizont ist nur sinnvoll, wenn sich in ihm ueberhaupt etwas
aufloest. H=3 gehoert zu einem Stop von 0,75 bis 1 ATR.

⚠️⚠️ DIESES WERKZEUG ENTSCHEIDET NICHTS. Es stellt die Zahlen
nebeneinander. Welche Geometrie die Messung nehmen soll, ist eine
Nutzerentscheidung - acht Befunde haengen an der jetzigen.

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python pruefe_barrierengeometrie.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_eigenschaft_beitrag as B                          # noqa: E402
from agent.entscheidungsrechnung import GRENZEN, _stop_aus_atr  # noqa: E402
from indicators.calculations import atr_wilder                 # noqa: E402

HORIZONTE = (3, 5, 10, 16, 23, 40)
CRV = 2.0

# Der laufende Wert aus `Basisinfos/config.yaml` (rollen_kette.stop_min_atr).
# ⚠️ Er wird hier NICHT aus der Datei gelesen, damit das Werkzeug ohne
# config laeuft - dafuer steht die Fundstelle im Klartext daneben und die
# Abweichung von GRENZEN wird ausgewiesen.
STOP_MIN_ATR_LIVE = 2.0
BETRIEB_FLACH = 0.13          # 2.397, Median-Stop mit Widerlegungspreis


def _stop(kurs, atr, *, ziel_atr, min_atr):
    """Die Produktionsform: Zielwert, dann nach unten UND oben geklemmt."""
    ziel = ziel_atr * atr
    unten = max(GRENZEN["stop_min_relativ"] * kurs, min_atr * atr)
    oben = GRENZEN["stop_max_relativ"] * kurs
    return min(max(ziel, unten), oben)


def stop_messung(kurs, atr):
    """Woertlich wie `barriere_je_reihe` - ohne den Zielwert."""
    return min(GRENZEN["stop_max_relativ"] * kurs,
               max(GRENZEN["stop_min_relativ"] * kurs,
                   GRENZEN["stop_min_atr"] * atr))


VARIANTEN = (
    ("MESSUNG 0,75-Boden", lambda k, a: stop_messung(k, a)),
    ("RUECKFALL Code 2,5", lambda k, a: _stop(k, a, ziel_atr=2.5,
                                              min_atr=0.75)),
    ("RUECKFALL LIVE 2,5", lambda k, a: _stop(k, a, ziel_atr=2.5,
                                              min_atr=STOP_MIN_ATR_LIVE)),
    ("BETRIEB flach 13 %", lambda k, a: BETRIEB_FLACH * k),
)


def _ausgang(c, h, t, i, stop_abstand, H):
    """-> 1.0 Ziel, 0.0 Stop, None ungeloest. Reihenfolge wie
    `barriere_je_reihe`: der Stop wird ZUERST geprueft, Gleichstaende
    fallen also zum Stop (2.583: 0,63 % der Anker, unschaedlich)."""
    stop = c[i] - stop_abstand
    ziel = c[i] + CRV * stop_abstand
    for j in range(i + 1, min(i + 1 + H, len(c))):
        if t[j] <= stop:
            return 0.0
        if h[j] >= ziel:
            return 1.0
    return None


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("IST DIE BARRIERENGEOMETRIE DIE BETRIEBSGEOMETRIE?")
    print("=" * 100)
    print("  GRENZEN     stop_ziel_atr %.2f · stop_min_atr %.2f · "
          "min_rel %.2f · max_rel %.2f"
          % (GRENZEN["stop_ziel_atr"], GRENZEN["stop_min_atr"],
             GRENZEN["stop_min_relativ"], GRENZEN["stop_max_relativ"]))
    print("  config.yaml rollen_kette.stop_min_atr %.2f   %s"
          % (STOP_MIN_ATR_LIVE,
             "⚠️ WEICHT VON GRENZEN AB"
             if abs(STOP_MIN_ATR_LIVE - GRENZEN["stop_min_atr"]) > 1e-9
             else "= GRENZEN"))

    # ── Selbstprobe: ist mein `_stop` die echte Produktionsfunktion? ──
    fehl = 0
    for k in (0.01, 1.0, 137.0, 90000.0):
        for a in (k * 0.005, k * 0.02, k * 0.08, k * 0.2):
            if abs(_stop(k, a, ziel_atr=GRENZEN["stop_ziel_atr"],
                         min_atr=GRENZEN["stop_min_atr"])
                   - _stop_aus_atr(k, a)[0]) > 1e-9 * max(1.0, k):
                fehl += 1
    print("  Selbstprobe `_stop` gegen `_stop_aus_atr`: %s"
          % ("✔ bitgleich in 16 von 16" if not fehl
             else "⛔ %d von 16 abweichend - NACHBAU FALSCH" % fehl))
    if fehl:
        return 1

    reihen = B.lade()
    if grenze:
        reihen = {k: reihen[k] for k in list(reihen)[:grenze]}
    print("  %d Reihen geladen" % len(reihen))

    # ── 0) Die EINHEIT: ist es ueberhaupt dasselbe ATR? ───────────────
    sp_rel, wi_rel = [], []
    for sym, reihe in reihen.items():
        c = np.array([x[1] for x in reihe], float)
        hi = np.array([x[2] for x in reihe], float)
        lo = np.array([x[3] for x in reihe], float)
        sp = B.spanne(hi, lo, c, B.SCHWANKUNG)
        _w = atr_wilder(hi, lo, c)
        if not getattr(_w, "available", False):
            continue
        wi = np.asarray(_w.value, float)
        n_ = min(len(sp), len(wi), len(c))
        ok = np.isfinite(sp[:n_]) & np.isfinite(wi[:n_]) & (c[:n_] > 0)
        sp_rel.extend((sp[:n_][ok] / c[:n_][ok]).tolist())
        wi_rel.extend((wi[:n_][ok] / c[:n_][ok]).tolist())
    sp_rel, wi_rel = np.array(sp_rel), np.array(wi_rel)
    print()
    print("-" * 100)
    print("0) DIE EINHEIT - `B.spanne` (Messung) gegen `atr_wilder` "
          "(Produktion), %d Werte" % len(sp_rel))
    print("-" * 100)
    for nam, a in (("B.spanne", sp_rel), ("atr_wilder", wi_rel)):
        print("   %-12s ATR/Kurs  Median %.3f %% · 10./90. Perz %.3f / %.3f %%"
              % (nam, 100 * np.median(a), 100 * np.percentile(a, 10),
                 100 * np.percentile(a, 90)))
    print("   Verhaeltnis wilder/spanne: Median %.4f  ➤ %s"
          % (np.median(wi_rel) / np.median(sp_rel),
             "dieselbe Groesse, die Einheit ist NICHT die Ursache"))
    print("   ➤ 1 x ATR = %.2f %% des Kurses · 2,5 x ATR = %.2f %%"
          % (100 * np.median(sp_rel), 100 * 2.5 * np.median(sp_rel)))

    # ── 1) und 2) die Varianten ───────────────────────────────────────
    rel = {nam: [] for nam, _ in VARIANTEN}
    z = {nam: {H: [0, 0, 0] for H in HORIZONTE} for nam, _ in VARIANTEN}
    gleich, n = 0, 0

    for sym, reihe in reihen.items():
        c = np.array([x[1] for x in reihe], float)
        hi = np.array([x[2] for x in reihe], float)
        lo = np.array([x[3] for x in reihe], float)
        atr = B.spanne(hi, lo, c, B.SCHWANKUNG)
        for i in range(len(c) - 1):
            if not np.isfinite(atr[i]) or c[i] <= 0 or atr[i] <= 0:
                continue
            n += 1
            werte = {}
            for nam, f in VARIANTEN:
                s = f(c[i], atr[i])
                werte[nam] = s
                rel[nam].append(s / c[i])
                for H in HORIZONTE:
                    a = _ausgang(c, hi, lo, i, s, H)
                    z[nam][H][2 if a is None else (0 if a == 1.0 else 1)] += 1
            if abs(werte["MESSUNG 0,75-Boden"]
                   - werte["RUECKFALL LIVE 2,5"]) < 1e-12:
                gleich += 1

    if not n:
        print("  ⛔ keine Anker")
        return 1

    print()
    print("-" * 100)
    print("1) DIE STOPWEITEN - %d Anker" % n)
    print("-" * 100)
    print("   %-20s %9s %9s %9s %9s"
          % ("Variante", "10. Perz", "MEDIAN", "90. Perz", "Mittel"))
    for nam, _ in VARIANTEN:
        a = np.array(rel[nam])
        print("   %-20s %8.2f%% %8.2f%% %8.2f%% %8.2f%%"
              % (nam, 100 * np.percentile(a, 10), 100 * np.median(a),
                 100 * np.percentile(a, 90), 100 * a.mean()))
    m = np.array(rel["MESSUNG 0,75-Boden"])
    lv = np.array(rel["RUECKFALL LIVE 2,5"])
    print("   ➤ Messung gegen RUECKFALL LIVE: identisch in %.2f %% der Anker "
          "· Verhaeltnis Median %.3f"
          % (100.0 * gleich / n, np.median(lv) / np.median(m)))
    print("   ➤ %s"
          % ("✔ dieselbe Geometrie" if gleich == n
             else "⛔ NICHT dieselbe Geometrie - die Docstring-Behauptung "
                  "in `barriere_je_reihe` haelt NICHT"))

    print()
    print("-" * 100)
    print("2) AUFLOESUNG UND QUOTE JE HORIZONT")
    print("-" * 100)
    print("   ⚠️ Die Kelly-Nullstelle 1/(1+CRV) = %.4f gilt fuer den Pfad "
          "OHNE" % (1.0 / (1 + CRV)))
    print("      Zeitgrenze - dort loest sich JEDER Pfad auf. Sie ist damit")
    print("      die BEDINGTE Quote. Nur gegen `q bed.` darf sie verglichen")
    print("      werden.")
    for nam, _ in VARIANTEN:
        print()
        print("   %s" % nam)
        print("      %-4s %10s %10s %10s   %s"
              % ("H", "geloest", "q bed.", "q unbed.", "Probe 2.445"))
        for H in HORIZONTE:
            ziel, stop, offen = z[nam][H]
            ges = ziel + stop + offen
            gel = ziel + stop
            anteil = gel / ges if ges else float("nan")
            marke = ("  ⭐ ~50 % geloest = der Aufloesungsmedian"
                     if 0.45 <= anteil <= 0.58 else "")
            print("      %-4d %9.1f%% %10.4f %10.4f%s"
                  % (H, 100 * anteil,
                     ziel / gel if gel else float("nan"),
                     ziel / ges if ges else float("nan"), marke))
    print()
    print("   ⚠️ WAS DAS HEISST: der Horizont muss zum STOP passen. Befund")
    print("      2.445 misst 3 Tage bei 0,75 ATR und 23 bei 2,5 ATR - und")
    print("      `messnorm.HORIZONT_JE_LAGE[(hebel, einstieg)]` steht auf 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
