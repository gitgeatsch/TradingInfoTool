# -*- coding: utf-8 -*-
"""Schritt 1 des Umbaus: traegt die Analogie ALLEIN - ohne Sprachmodell?

WORUM ES GEHT. Der neue Faktensatz soll dem Modell vergleichbare vergangene Faelle
mitgeben: "In den letzten Jahren gab es 46 aehnliche Lagen, 1 erreichte das Ziel,
27 den Stop." Das ist die staerkste neue Zutat - und im Kern ein
Naechste-Nachbarn-Modell.

DESHALB WIRD SIE ZUERST ALLEIN GEMESSEN. Wenn diese Rechnung die Basisrate schlaegt,
haben wir eine Kante ohne jedes Modellrisiko. Wenn nicht, wird auch ein Sprachmodell
nichts daraus machen - dann fehlt die Information im Merkmalsraum, nicht in der
Aufbereitung. In beiden Faellen wissen wir es VOR dem ersten Aufruf.

KAUSALITAET IST HIER DIE GANZE SCHWIERIGKEIT. Ein Nachbar darf nur zaehlen, wenn
sein Ausgang zum Zeitpunkt des Ankers bereits feststand - also Nachbardatum plus
Horizont vor dem Ankerdatum. Wer das vergisst, misst die Zukunft und bekommt
grossartige Werte. Genau diese Fehlerklasse hat am 10.08. mehrfach zugeschlagen.

    python pruefe_analogie.py --k 20
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from collections import Counter

import numpy as np

from agent.szenario_fakten import (AUSGAENGE, HORIZONT_KERZEN, STOP_IN_ATR,
                                   ZIEL_IN_ATR, brier)
from backtest_llm1_historisch import lade_reihen
from indicators.calculations import atr_wilder, rsi

# Die Merkmale, ueber die Aehnlichkeit definiert wird. Bewusst wenige und alle
# dimensionslos - ein Abstand in ATR ist zwischen BTC und ALGO vergleichbar, ein
# Abstand in Euro nicht.
MERKMALE = ("abstand_sma200_atr", "rsi", "atr_relativ", "rendite_20", "rendite_60")


def _merkmalstabelle(reihe, symbol: str) -> list[dict]:
    """Fuer jeden auswertbaren Index: Merkmale UND tatsaechlicher Ausgang.

    Alle Indikatoren werden einmal ueber die volle Reihe gerechnet. Das ist
    zulaessig, weil Wilder-Glaettung und RSI rekursiv von vorne laufen: der Wert
    an Position i haengt nur von 0..i ab. Der gleitende Mittelwert ebenso. Die
    Kausalitaetsprobe unten prueft genau das nach, statt es zu glauben."""
    c = np.array([k.close for k in reihe], dtype=float)
    h = np.array([k.high for k in reihe], dtype=float)
    l = np.array([k.low for k in reihe], dtype=float)
    if len(c) < 250:
        return []
    atr = np.asarray(atr_wilder(h, l, c).value, dtype=float)
    rs = np.asarray(rsi(c).value, dtype=float)

    # AB INDEX 200, nicht 250. Der erste Anlauf begann bei 250 - "sicherheitshalber",
    # ohne Grund. Folge: 48 der 80 Anker fielen heraus, und zwar nicht zufaellig,
    # sondern systematisch die fruehen. Der Vergleich lief damit auf einer
    # verschobenen Teilmenge, erkennbar an der Basisrate (0,6478 statt 0,6272).
    # 200 ist das echte Minimum - so viele Werte braucht der 200-Tage-Schnitt.
    zeilen = []
    for i in range(200, len(c) - HORIZONT_KERZEN):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(rs[i]):
            continue
        sma200 = float(c[i - 199:i + 1].mean())
        m = {
            "abstand_sma200_atr": (c[i] - sma200) / a,
            "rsi": float(rs[i]),
            "atr_relativ": 100.0 * a / c[i],
            "rendite_20": 100.0 * (c[i] / c[i - 20] - 1.0),
            "rendite_60": 100.0 * (c[i] / c[i - 60] - 1.0),
        }
        # Ausgang je Richtung - beide, damit LONG und SHORT eigene Nachbarn haben.
        for richtung in ("LONG", "SHORT"):
            vz = 1.0 if richtung == "LONG" else -1.0
            stop = c[i] - vz * STOP_IN_ATR * a
            ziel = c[i] + vz * ZIEL_IN_ATR * a
            aus = "keines"
            for j in range(i + 1, min(i + 1 + HORIZONT_KERZEN, len(c))):
                # Stop gewinnt bei Gleichstand - dieselbe Regel wie in loese_auf().
                if (l[j] <= stop) if richtung == "LONG" else (h[j] >= stop):
                    aus = "stop"
                    break
                if (h[j] >= ziel) if richtung == "LONG" else (l[j] <= ziel):
                    aus = "ziel"
                    break
            # WANN der Ausgang feststand - nicht wann der Fall begann. Das ist
            # der Unterschied zwischen einer sauberen und einer leckenden
            # Nachbarsuche, und beim ersten Anlauf hatte ich genau ihn
            # uebersehen: gefiltert wurde nach Beginndatum, wodurch Nachbarn
            # zaehlten, deren Ausgang zum Ankerzeitpunkt noch offen war.
            ende = min(i + HORIZONT_KERZEN, len(reihe) - 1)
            zeilen.append({**m, "symbol": symbol, "index": i,
                           "datum": str(reihe[i].date),
                           "bekannt_ab": str(reihe[ende].date),
                           "richtung": richtung, "ausgang": aus})
    return zeilen


def _normiere(tab: list[dict]) -> tuple[dict, dict]:
    """Mittelwert und Streuung je Merkmal - sonst dominiert der RSI (Spanne 0-100)
    jeden Abstand in ATR (Spanne etwa -5 bis +5)."""
    mit, streu = {}, {}
    for m in MERKMALE:
        w = [z[m] for z in tab]
        mit[m] = statistics.fmean(w)
        streu[m] = statistics.pstdev(w) or 1.0
    return mit, streu


def _distanz(a: dict, b: dict, mit: dict, streu: dict) -> float:
    return sum(((a[m] - mit[m]) / streu[m] - (b[m] - mit[m]) / streu[m]) ** 2
               for m in MERKMALE)


def schaetze(fall: dict, kandidaten: list[dict], k: int,
             mit: dict, streu: dict) -> dict | None:
    """Verteilung aus den k naechsten Nachbarn."""
    if len(kandidaten) < k:
        return None
    naechste = sorted(kandidaten,
                      key=lambda z: _distanz(fall, z, mit, streu))[:k]
    z = Counter(n["ausgang"] for n in naechste)
    # Laplace-Glaettung: ohne sie wuerde ein Ausgang, der unter k Nachbarn nie
    # vorkommt, mit 0 % geschaetzt - und ein einziger Treffer in der Wirklichkeit
    # kostet dann den vollen Brier-Beitrag von 1,0.
    return {f"{a}_zuerst_pct" if a != "keines" else "keines_pct":
            100.0 * (z.get(a, 0) + 1) / (k + len(AUSGAENGE)) for a in AUSGAENGE}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--k", type=int, default=20)
    p.add_argument("--faelle", default=None,
                   help="JSON aus messe_szenario_stufe1.py - dieselben Anker")
    p.add_argument("--nur-eigenes-asset", action="store_true")
    args = p.parse_args()

    reihen = lade_reihen()
    print("Merkmalstabelle bauen ...")
    tab = []
    for sym, r in reihen.items():
        tab.extend(_merkmalstabelle(r, sym))
    print(f"  {len(tab)} auswertbare Faelle ueber {len({z['symbol'] for z in tab})} Symbole")
    if not tab:
        print("[FEHLER] keine Daten")
        return 2
    mit, streu = _normiere(tab)

    # --- Die Anker: dieselben wie im Messlauf, damit vergleichbar --------------
    if args.faelle:
        d = json.loads(pathlib.Path(args.faelle).read_text(encoding="utf-8"))
        anker = [(f["symbol"], f["datum"], f["richtung"], f["wahrheit"])
                 for f in d["faelle"]]
        print(f"  {len(anker)} Anker aus {args.faelle}")
    else:
        print("[FEHLER] --faelle noetig, sonst sind die Zahlen nicht vergleichbar")
        return 2

    nach_schluessel = {(z["symbol"], z["datum"], z["richtung"]): z for z in tab}
    ergebnisse, basis_w, fehlend = [], [], 0
    auswertbar = []
    ausgangs_zaehler = Counter(w for *_, w in anker)
    n_anker = len(anker)
    basisrate = {f"{a}_zuerst_pct" if a != "keines" else "keines_pct":
                 100.0 * ausgangs_zaehler.get(a, 0) / n_anker for a in AUSGAENGE}

    for sym, datum, richtung, wahrheit in anker:
        fall = nach_schluessel.get((sym, datum, richtung))
        if fall is None:
            fehlend += 1
            auswertbar.append(False)
            continue
        # KAUSAL: nur Nachbarn, deren Ausgang zum Ankerzeitpunkt bereits
        # FESTSTAND - `bekannt_ab`, nicht `datum`. Ein Nachbar von vor fuenf
        # Tagen loest sich erst in fuenfzehn Tagen auf; ihn mitzuzaehlen hiesse,
        # die Zukunft zu befragen.
        kand = [z for z in tab
                if z["richtung"] == richtung
                and z["bekannt_ab"] < datum
                and (z["symbol"] == sym if args.nur_eigenes_asset else z["symbol"] != sym)]
        v = schaetze(fall, kand, args.k, mit, streu)
        if v is None:
            fehlend += 1
            auswertbar.append(False)
            continue
        auswertbar.append(True)
        ergebnisse.append(brier(v, wahrheit))
        basis_w.append(brier(basisrate, wahrheit))

    # --- Die anderen Verfahren auf DERSELBEN Teilmenge -----------------------
    # Sonst vergleicht man Aepfel mit Birnen: die Analogie ist nur dort
    # auswertbar, wo genug aufgeloeste Nachbarn existieren, und das sind
    # systematisch die spaeteren Anker. Die Basisrate liegt auf dieser
    # Teilmenge bei 0,6478 statt 0,6272 - der Unterschied ist keine Nuance.
    andere = {}
    for name, eintraege in d.get("ergebnisse", {}).items():
        w = [e["brier"] for e, ok in zip(eintraege, auswertbar)
             if ok and e.get("brier") is not None]
        if len(w) >= 10:
            andere[name] = (statistics.fmean(w), len(w))

    quelle = "nur eigenes Asset" if args.nur_eigenes_asset else "andere Assets"
    print(f"\n{'=' * 66}")
    print(f"ANALOGIE ALLEIN  (k={args.k}, Nachbarn aus: {quelle})")
    print(f"{'=' * 66}")
    if not ergebnisse:
        print(f"  Keine auswertbaren Faelle (fehlend: {fehlend})")
        return 1
    a_brier = statistics.fmean(ergebnisse)
    b_brier = statistics.fmean(basis_w)
    print(f"  Analogie   Brier {a_brier:.4f}   (n={len(ergebnisse)}, "
          f"fehlend {fehlend})")
    print(f"  Basisrate  Brier {b_brier:.4f}")
    for name, (w, n) in sorted(andere.items(), key=lambda x: x[1][0]):
        if "Basisrate" in name:
            continue
        print(f"  {name:10} Brier {w:.4f}   (n={n})")
    print(f"\n  -> {'JA, die Analogie traegt' if a_brier < b_brier else 'NEIN, sie traegt nicht'}"
          f"  (Differenz {b_brier - a_brier:+.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
