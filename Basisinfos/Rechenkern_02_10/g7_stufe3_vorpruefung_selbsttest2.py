"""G7 Stufe 3 — SELBSTTEST DER VORPRÜFUNG, Fassung 2 (08.11.2026, nach der Gegenprüfung M2/S3 der Voranalyse Stufe 3 §6).

Fassung 1 (`g7_stufe3_vorpruefung_selbsttest.py`) pflanzte die Wirkung nur gleichmäßig über Menge b und nur bei einer Rate von 30 %.
Die Gegenprüfung rechnete nach: wirkt das Urteil NUR auf den gemailten Einstiegen (a, der Betriebsfall, Fall 1 der Scheideweg-Vorlage),
läuft die Vorprüfung bei 0,3 σ nur zu ≈ 62–70 % weiter; bei Raten von 10 % / 85 % fällt sie unter 90 %.

Kein LLM, kein Urteil, kein Netz. Echte Zielgrößen der Menge b, künstliche Urteile mit bekannter Wahrheit.

ENTWÜRFE (alle mit Endauswertung auf ALLEN Einstiegen wie Messplan §11.5; Abbruch nur für Vergeblichkeit):
  D1  1 je Tag aus b (Fassung 1, festgeschrieben)                      weiter, wenn p_b ≤ c
  D2  wie D1                                                            weiter, wenn p_b ≤ c ODER p_a ≤ c (a-Teil der Vorauswahl)
  D3  je Tag 1 aus a, wenn der Tag a-Einstiege hat, sonst 1 aus b       weiter, wenn p_b ≤ c ODER p_a ≤ c
  D4  je Tag 1 aus a (wenn vorhanden) UND 1 aus der übrigen Stichprobe  weiter, wenn p_b ≤ c ODER p_a ≤ c
  c ∈ {0,30; 0,40; 0,50}.  p_b = über die ganze Vorauswahl, p_a = über ihren a-Teil (je mit Tagesbahn, einseitig unten).
  Ist ein p nicht rechenbar (alle Urteile gleich), zählt nur das andere.

ERZEUGER MIT WIRKUNG:
  W1 G-Handel 30 % über b · W2 G-Tag Lauf 3 T über b · W3 G-Handel 30 %, Wirkung NUR auf a · W4 G-Handel 10 % · W5 G-Handel 85 %

AUSWAHLREGEL — festgelegt VOR dem Lauf:
  Ein Entwurf besteht mit c, wenn bei 0,3 σ in ALLEN fünf Erzeugern UND bei 0,2 σ in W1 und W2 die Vorprüfung zu ≥ 90 % weiterläuft.
  Unter den bestehenden: die wenigsten Aufrufe in der Vorprüfung, dann das kleinste c.
  Besteht keiner: der Entwurf mit dem höchsten kleinsten Weiter-Anteil bei 0,3 σ, c = 0,50, Verlust ausgewiesen.

MESSBARKEIT (vorab, wie Stufe 1 §5.5): Anteil Bedenken ≥ 1 in der Vorauswahl außerhalb 5–95 % → ENDE „nicht messbar“ (KEIN BEFUND).

    python g7_stufe3_vorpruefung_selbsttest2.py
"""
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import g7_stufe3_anlage as A                                          # noqa: E402
import g7_stufe3_vorpruefung_selbsttest as V1                         # noqa: E402

CS = (0.30, 0.40, 0.50)
N_NULL = 1000
N_PFL = 500
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def lade() -> pd.DataFrame:
    Z = V1.lade()
    M = pd.read_csv(V1.MENGE, sep=";")[["symbol", "stunde", "teil"]]
    Z = Z.merge(M, on=["symbol", "stunde"], how="left", validate="1:1")
    assert Z.teil.notna().all()
    Z["ist_a"] = (Z.teil == "a_gemailt").to_numpy()
    return Z.sort_values(["stunde", "symbol"]).reset_index(drop=True)


def entwuerfe(Z: pd.DataFrame) -> dict:
    rng = np.random.default_rng(20261109)
    d1 = V1.vorauswahl(Z, 1)
    d3, d4 = [], []
    for _t, g in Z.groupby("tag", sort=True):
        ga, gb = g[g.ist_a], g[~g.ist_a]
        if len(ga):
            ia = rng.choice(ga.index.to_numpy())
            d3.append(ia); d4.append(ia)
            if len(gb):
                d4.append(rng.choice(gb.index.to_numpy()))
        else:
            ib = rng.choice(g.index.to_numpy())
            d3.append(ib); d4.append(ib)
    return {"D1": (np.sort(d1), False), "D2": (np.sort(d1), True), "D3": (np.sort(np.array(d3)), True),
            "D4": (np.sort(np.array(d4)), True)}


def pw(Zs: pd.DataFrame, u: np.ndarray) -> float:
    if len(Zs) < 3 or u.sum() in (0, len(u)):
        return np.nan
    s, null = A.arm_handel_tage(u, Zs.ertrag_s.to_numpy(), A.bahn_tage(Zs))
    return float((null <= s).mean()) if np.isfinite(s) and len(null) else np.nan


def weiter_p(Z, z, u, idx, oder) -> tuple:
    Zs = Z.loc[idx].reset_index(drop=True).assign(ertrag_s=z[idx])
    pb = pw(Zs, u[idx])
    pa = np.nan
    if oder:
        ia = idx[Z.ist_a.to_numpy()[idx]]
        Za = Z.loc[ia].reset_index(drop=True).assign(ertrag_s=z[ia])
        pa = pw(Za, u[ia])
    return pb, pa


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    t0 = time.time()
    rng = np.random.default_rng(20261110)
    Z = lade()
    ia_all = np.flatnonzero(Z.ist_a.to_numpy())
    Za_full = Z.loc[ia_all].reset_index(drop=True)
    E = entwuerfe(Z)
    p("G7 STUFE 3 — SELBSTTEST DER VORPRÜFUNG, FASSUNG 2 · %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("Menge b %d Einstiege, davon a %d · Tage %d (a: %d)" % (len(Z), len(ia_all), Z.tag.nunique(), Za_full.tag.nunique()))
    for k, (idx, oder) in E.items():
        p("  %s: %d Aufrufe · a-Teil %d · Tage %d · Regel %s" % (k, len(idx), int(Z.ist_a.to_numpy()[idx].sum()),
                                                            Z.loc[idx].tag.nunique(), "p_b ODER p_a" if oder else "p_b"))

    def ziehe(gen, s, nur_a, n):
        """-> dict Entwurf -> (pb, pa) Arrays; dazu Fund voll auf b und auf a."""
        R = {k: (np.empty(n), np.empty(n)) for k in E}
        fb = np.empty(n, bool); fa = np.empty(n, bool)
        for j in range(n):
            u = gen()
            w = u * (Z.ist_a.to_numpy() if nur_a else 1.0)
            z = Z.ertrag_s.to_numpy() - s * w
            rb = A.messe(Z.assign(ertrag_s=z), u); fb[j] = rb["traegt"]
            ra = A.messe(Za_full.assign(ertrag_s=z[ia_all]), u[ia_all]) if 0 < u[ia_all].sum() < len(ia_all) else {"traegt": False}
            fa[j] = ra["traegt"]
            for k, (idx, oder) in E.items():
                R[k][0][j], R[k][1][j] = weiter_p(Z, z, u, idx, oder)
        return R, fb, fa

    def weiter(pb, pa, c):
        return (np.nan_to_num(pb, nan=1.0) <= c) | (np.nan_to_num(pa, nan=1.0) <= c)

    p("\n1  OHNE WIRKUNG (%d Ziehungen): Anteil WEITER je c · Fehlalarm voll b / a · mit Vorprüfung b" % N_NULL)
    for name, gen in (("G-Tag Lauf 1 T", lambda: A.g_tag(Z, rng, 1)), ("G-Handel 30 %", lambda: A.g_handel(Z, rng, 0.3))):
        R, fb, fa = ziehe(gen, 0.0, False, N_NULL)
        for k in E:
            p("   %-15s %s  weiter %s · Fehlalarm voll b %.1f %% / a %.1f %% · mit Vorprüfung b %s" % (
                name, k, " ".join("c%.2f %3.0f %%" % (c, 100 * weiter(*R[k], c).mean()) for c in CS), 100 * fb.mean(), 100 * fa.mean(),
                " ".join("%.1f" % (100 * (fb & weiter(*R[k], c)).mean()) for c in CS)))

    p("\n2  MIT WIRKUNG (%d Ziehungen): Fund voll (b / a) · WEITER je c" % N_PFL)
    gens = [("W1 G-Handel 30 %", lambda: A.g_handel(Z, rng, 0.3), False, (0.2, 0.3)),
            ("W2 G-Tag Lauf 3 T", lambda: A.g_tag(Z, rng, 3), False, (0.2, 0.3)),
            ("W3 nur a, 30 %", lambda: A.g_handel(Z, rng, 0.3), True, (0.3,)),
            ("W4 G-Handel 10 %", lambda: A.g_handel(Z, rng, 0.1), False, (0.3,)),
            ("W5 G-Handel 85 %", lambda: A.g_handel(Z, rng, 0.85), False, (0.3,))]
    ok = {(k, c): True for k in E for c in CS}
    mins = {k: 1.0 for k in E}
    for name, gen, nur_a, staerken in gens:
        for s in staerken:
            R, fb, fa = ziehe(gen, s, nur_a, N_PFL)
            for k in E:
                w = {c: float(weiter(*R[k], c).mean()) for c in CS}
                for c in CS:
                    ok[(k, c)] &= w[c] >= 0.90
                if s == 0.3:
                    mins[k] = min(mins[k], w[0.50])
                p("   %-18s %.1fσ %s  voll b %3.0f %% / a %3.0f %% · weiter %s · mit Vorprüfung b %s / a %s" % (
                    name, s, k, 100 * fb.mean(), 100 * fa.mean(), " ".join("c%.2f %3.0f" % (c, 100 * w[c]) for c in CS),
                    " ".join("%3.0f" % (100 * (fb & weiter(*R[k], c)).mean()) for c in CS),
                    " ".join("%3.0f" % (100 * (fa & weiter(*R[k], c)).mean()) for c in CS)))

    best = [(len(E[k][0]), c, k) for k in E for c in CS if ok[(k, c)]]
    if best:
        n_, c_, k_ = min(best)
        p("\n3  AUSWAHL nach der Regel im Kopf: %s, c = %.2f (%d Aufrufe in der Vorprüfung)" % (k_, c_, n_))
    else:
        k_ = max(mins, key=mins.get)
        p("\n3  AUSWAHL: keiner besteht → %s, c = 0,50 (kleinster Weiter-Anteil bei 0,3 σ: %.0f %%)" % (k_, 100 * mins[k_]))
    p("   Rechenzeit %.0f s" % (time.time() - t0))
    with open(os.path.join(HIER, "g7_stufe3_vorpruefung_selbsttest2.txt"), "w", encoding="utf-8") as f_:
        f_.write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    main()
