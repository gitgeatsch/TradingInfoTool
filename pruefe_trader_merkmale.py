# -*- coding: utf-8 -*-
"""Tragen die MERKMALE, die ein Trader laut Praxis liest?

WARUM ES DIESE DRITTE DATEI GIBT. Der Analogie-Test lief auf RSI, Abstand zum
200-Tage-Schnitt, Schwankungsbreite und zwei Renditen. Das sind genau die
nachlaufenden Indikatoren, die die Praxisliteratur als NICHT tragend bezeichnet.
Ich habe genommen, was schon da war, statt zu bauen, was die Recherche nennt - der
Nutzer hat den Widerspruch gefunden, bevor ich ihn selbst sah.

Hier stehen deshalb die Merkmale, die ein Price-Action-Trader tatsaechlich liest:

    STRUKTUR      hoehere Hochs und Tiefs, oder tiefere? Trend intakt oder gebrochen?
    NIVEAUS       wie weit bis zum naechsten Widerstand, wie weit bis zur
                  Unterstuetzung - in ATR, damit es zwischen Assets vergleichbar ist
    SPANNE        wo im letzten Schwung steht der Kurs, oben oder unten?
    REIFE         wie lange laeuft die aktuelle Bewegung schon?

ZWEI FALLEN, beide hier vermieden:

  * SWINGS SIND ERST SPAETER BEKANNT. Ein Williams-Fraktal bei Index j braucht
    `window` Kerzen DANACH, um bestaetigt zu sein. Wer an Index i alle Swings bis i
    benutzt, liest die Zukunft. Hier zaehlen nur Swings bis `i - window`.
  * TRAINING AUF DER ZUKUNFT. Das Modell wird zeitlich vorwaerts geprueft
    (walk-forward): trainiert wird nur auf Faellen, deren Ausgang vor dem
    Testzeitpunkt feststand.

Das Verfahren ist eine multinomiale logistische Regression mit quadratischen
Termen - staerker als Nachbarschaft, weil sie Schwellen und das Zusammenspiel
mehrerer Merkmale abbilden kann, und ohne neue Abhaengigkeit.

    python pruefe_trader_merkmale.py
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize

from agent.szenario_fakten import HORIZONT_KERZEN, STOP_IN_ATR, ZIEL_IN_ATR
from backtest_llm1_historisch import lade_reihen
from indicators.calculations import atr_wilder, rsi

FENSTER = 2  # Williams-Fraktal, 5-Kerzen-Muster

ALT = ("abstand_sma200_atr", "rsi", "atr_relativ", "rendite_20", "rendite_60")
NEU = ("struktur_hoch", "struktur_tief", "widerstand_atr", "unterstuetzung_atr",
       "position_spanne", "reife_kerzen")


def _swings(h: np.ndarray, l: np.ndarray) -> tuple[list, list]:
    """Indizes der Swing-Hochs und -Tiefs (Williams-Fraktal)."""
    hi, lo = [], []
    for i in range(FENSTER, len(h) - FENSTER):
        if h[i] == h[i - FENSTER:i + FENSTER + 1].max():
            hi.append(i)
        if l[i] == l[i - FENSTER:i + FENSTER + 1].min():
            lo.append(i)
    return hi, lo


def tabelle(reihe, symbol: str) -> list[dict]:
    c = np.array([k.close for k in reihe], dtype=float)
    h = np.array([k.high for k in reihe], dtype=float)
    l = np.array([k.low for k in reihe], dtype=float)
    if len(c) < 250:
        return []
    atr = np.asarray(atr_wilder(h, l, c).value, dtype=float)
    rs = np.asarray(rsi(c).value, dtype=float)
    hi, lo = _swings(h, l)

    zeilen = []
    for i in range(200, len(c) - HORIZONT_KERZEN):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(rs[i]):
            continue
        # NUR BESTAETIGTE SWINGS: ein Fraktal bei j ist erst ab j+FENSTER
        # sichtbar. Ohne diese Schranke liest das Merkmal die Zukunft.
        gh = [j for j in hi if j + FENSTER <= i]
        gl = [j for j in lo if j + FENSTER <= i]
        if len(gh) < 2 or len(gl) < 2:
            continue
        sma200 = float(c[i - 199:i + 1].mean())

        # STRUKTUR: +1 hoeheres Hoch / -1 tieferes, analog fuer Tiefs
        s_hoch = 1.0 if h[gh[-1]] > h[gh[-2]] else -1.0
        s_tief = 1.0 if l[gl[-1]] > l[gl[-2]] else -1.0

        # NIVEAUS: naechster bestaetigter Swing ueber und unter dem Kurs
        drueber = [h[j] for j in gh if h[j] > c[i]] + [l[j] for j in gl if l[j] > c[i]]
        drunter = [h[j] for j in gh if h[j] < c[i]] + [l[j] for j in gl if l[j] < c[i]]
        w_atr = (min(drueber) - c[i]) / a if drueber else 10.0
        u_atr = (c[i] - max(drunter)) / a if drunter else 10.0

        # SPANNE: 0 = am letzten Tief, 1 = am letzten Hoch
        hoch, tief = float(h[gh[-1]]), float(l[gl[-1]])
        spanne = (c[i] - tief) / (hoch - tief) if hoch > tief else 0.5

        zeilen.append({
            "abstand_sma200_atr": (c[i] - sma200) / a,
            "rsi": float(rs[i]),
            "atr_relativ": 100.0 * a / c[i],
            "rendite_20": 100.0 * (c[i] / c[i - 20] - 1.0),
            "rendite_60": 100.0 * (c[i] / c[i - 60] - 1.0),
            "struktur_hoch": s_hoch,
            "struktur_tief": s_tief,
            "widerstand_atr": min(w_atr, 10.0),
            "unterstuetzung_atr": min(u_atr, 10.0),
            "position_spanne": min(max(spanne, -1.0), 2.0),
            "reife_kerzen": float(i - max(gh[-1], gl[-1])),
            "symbol": symbol,
            "datum": str(reihe[i].date),
            "bekannt_ab": str(reihe[min(i + HORIZONT_KERZEN, len(reihe) - 1)].date),
            **_ausgaenge(c, h, l, i, a),
        })
    return zeilen


def _ausgaenge(c, h, l, i, a) -> dict:
    aus = {}
    for richtung in ("LONG", "SHORT"):
        vz = 1.0 if richtung == "LONG" else -1.0
        stop, ziel = c[i] - vz * STOP_IN_ATR * a, c[i] + vz * ZIEL_IN_ATR * a
        e = "keines"
        for j in range(i + 1, min(i + 1 + HORIZONT_KERZEN, len(c))):
            if (l[j] <= stop) if richtung == "LONG" else (h[j] >= stop):
                e = "stop"
                break
            if (h[j] >= ziel) if richtung == "LONG" else (l[j] <= ziel):
                e = "ziel"
                break
        aus[f"ausgang_{richtung}"] = e
    return aus


def _entwurf(X: np.ndarray) -> np.ndarray:
    """Lineare Terme, Quadrate und eine Eins-Spalte.

    Die Quadrate sind der Grund, warum das Verfahren mehr kann als eine gerade
    Linie: sie erlauben Schwellen ("zu nah am Widerstand UND zu weit vom
    Support" ist etwas anderes als jedes fuer sich)."""
    return np.hstack([np.ones((len(X), 1)), X, X ** 2])


def _passe_an(X: np.ndarray, y: np.ndarray, klassen: int = 3) -> np.ndarray:
    """Multinomiale logistische Regression, L2-regularisiert."""
    D = _entwurf(X)
    n, p = D.shape

    def verlust(w):
        W = w.reshape(p, klassen)
        z = D @ W
        z -= z.max(axis=1, keepdims=True)
        logsum = np.log(np.exp(z).sum(axis=1))
        ll = (z[np.arange(n), y] - logsum).sum()
        return -ll / n + 0.01 * (w @ w)

    r = minimize(verlust, np.zeros(p * klassen), method="L-BFGS-B",
                 options={"maxiter": 300})
    return r.x.reshape(p, klassen)


def _vorhersage(W: np.ndarray, X: np.ndarray) -> np.ndarray:
    z = _entwurf(X) @ W
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schnitte", type=int, default=4)
    p.add_argument("--seed", type=int, default=20260810)
    args = p.parse_args()

    reihen = lade_reihen()
    tab = []
    for sym, r in reihen.items():
        tab.extend(tabelle(r, sym))
    if len(tab) < 500:
        print(f"[FEHLER] nur {len(tab)} Faelle")
        return 2
    print(f"{len(tab)} Faelle ueber {len({z['symbol'] for z in tab})} Symbole")

    AUS = ("ziel", "stop", "keines")
    for richtung in ("LONG", "SHORT"):
        y_all = np.array([AUS.index(z[f"ausgang_{richtung}"]) for z in tab])
        daten = np.array([z["bekannt_ab"] for z in tab])
        sym_all = np.array([z["symbol"] for z in tab])
        ordnung = np.argsort(daten)

        print(f"\n{'=' * 70}\n{richtung}   "
              + "  ".join(f"{a}={100.0*(y_all==i).mean():.1f} %"
                          for i, a in enumerate(AUS)))
        print("=" * 70)

        for name, felder in (("nur alte Merkmale", ALT),
                             ("nur Trader-Merkmale", NEU),
                             ("beide", ALT + NEU)):
            X_all = np.array([[z[f] for f in felder] for z in tab], dtype=float)
            mu, sd = X_all.mean(axis=0), X_all.std(axis=0) + 1e-12
            X_all = (X_all - mu) / sd

            b_mod, b_bas, je_sym = [], [], defaultdict(list)
            # WALK-FORWARD: nur Vergangenheit im Training.
            for s in range(1, args.schnitte + 1):
                grenze = int(len(ordnung) * s / (args.schnitte + 1))
                tr = ordnung[:grenze]
                te = ordnung[grenze:int(len(ordnung) * (s + 1) / (args.schnitte + 1))]
                if len(tr) < 200 or len(te) < 50:
                    continue
                W = _passe_an(X_all[tr], y_all[tr])
                P = _vorhersage(W, X_all[te])
                # Basisrate aus dem TRAININGSteil - sonst kennt sie die Testzukunft.
                basis = np.array([(y_all[tr] == i).mean() for i in range(3)])
                for j, t in enumerate(te):
                    ziel_v = np.zeros(3)
                    ziel_v[y_all[t]] = 1.0
                    bm = float(((P[j] - ziel_v) ** 2).sum())
                    bb = float(((basis - ziel_v) ** 2).sum())
                    b_mod.append(bm)
                    b_bas.append(bb)
                    je_sym[str(sym_all[t])].append(bm - bb)
            if not b_mod:
                print(f"  {name:22} keine auswertbaren Schnitte")
                continue
            syms = list(je_sym)
            rng = random.Random(args.seed)
            dif = []
            for _ in range(2000):
                g = [x for s2 in rng.choices(syms, k=len(syms)) for x in je_sym[s2]]
                if g:
                    dif.append(statistics.fmean(g))
            dif.sort()
            u, o = dif[int(0.025 * len(dif))], dif[int(0.975 * len(dif))]
            pkt = statistics.fmean([a - b for a, b in zip(b_mod, b_bas)])
            zeichen = ("BESSER" if o < 0 else "schlechter" if u > 0 else "kein Befund")
            print(f"  {name:22} Brier {statistics.fmean(b_mod):.4f}  "
                  f"Basis {statistics.fmean(b_bas):.4f}  "
                  f"{pkt:+.4f} [{u:+.4f}..{o:+.4f}]  {zeichen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
