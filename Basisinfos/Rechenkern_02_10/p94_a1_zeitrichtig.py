"""P94 A1 MIT ZEITRICHTIGEM MARKTWERT-RANG (Voranalyse_Vorsprungs_Atlas §9, vorab 04d010cd, E-153).

    python -X utf8 Basisinfos/Rechenkern_02_10/p94_a1_zeitrichtig.py

B1  RANG_QUELLE=eigen reproduziert A1 (p86_a1_zerlegung.txt) BITGLEICH - eigener Prozess (gleicher Zufallsstrom wie p86)
B2  zeitrichtiger Rang gegen den CMC-Altcoin-Rang (gemeinsame Coins), Monatsstichtage 2019-01..2026-08 - Soll Mittel >= 0,95
B3  ENA/TIA 2024-06, WLD 2025-06 nicht mehr in den Top 30
B4  Wirkung auf die Grundgesamtheit: Anteil der Anker mit anderer Klasse H/M/S je Jahr (nur ausgewiesen)
dann A1 NEU: p86 mit RANG_QUELLE=cmc (eigener Prozess) -> p94_a1_neu.txt; Gegenprobe p86_gegenprobe mit cmc -> p94_gegenprobe_neu.txt
Nur lesend (Kindprozesse lesen nur).
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)


def kind(skript, quelle):
    env = dict(os.environ, MK_RANG_QUELLE=quelle, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HIER, skript)], capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        raise RuntimeError("%s (%s) brach ab: %s" % (skript, quelle, r.stderr[-800:]))
    return r.stdout


def b1():
    neu = kind("p86_a1_zerlegung.py", "eigen")
    alt = open(os.path.join(HIER, "p86_a1_zerlegung.txt"), encoding="utf-8").read()
    a, n = alt.rstrip().splitlines(), neu.rstrip().splitlines()
    gleich = a == n
    print("B1 RANG_QUELLE=eigen gegen p86_a1_zerlegung.txt: %d / %d Zeilen gleich -> %s" % (
        sum(x == y for x, y in zip(a, n)), max(len(a), len(n)), "BITGLEICH" if gleich else "UNGLEICH - Halt"))
    if not gleich:
        for x, y in zip(a, n):
            if x != y:
                print("  alt: %s\n  neu: %s" % (x[:160], y[:160]))
                break
    return gleich


def b2_b4():
    import mk_messung as MK
    import p92_l1c_cmc_eigene_basis as P92
    B = P92.Basis()
    assert MK.RANG_QUELLE == "cmc"
    rk, rk_alt = [], []
    for t in pd.date_range("2019-01-01", "2026-08-01", freq="MS"):
        if t not in MK.POS:
            continue
        _, r = MK.rang_mw(t)
        MK.RANG_QUELLE = "eigen"
        _, r_alt = MK.rang_mw(t)
        MK.RANG_QUELLE = "cmc"
        i = np.searchsorted(B.wochen, np.datetime64(t), side="right") - 1
        C = B.T[B.T.stichtag == B.wochen[i]]
        C = C[~C.symbol.duplicated(keep=False)].set_index("symbol").arang
        g = [s for s in r.index if s in C.index]
        if len(g) >= 20:
            rk.append(pd.Series(r[g]).rank().corr(C[g].rank()))
            ga = [s for s in g if s in r_alt.index]
            rk_alt.append(pd.Series(r_alt[ga]).rank().corr(C[ga].rank()))
    ok2 = np.mean(rk) >= 0.95
    print("B2 Rangkorrelation zum CMC-Altcoin-Rang (gemeinsame Coins, %d Stichtage): zeitrichtig %.3f (10. Perz. %.3f) · bisher %.3f -> %s" % (
        len(rk), np.mean(rk), np.percentile(rk, 10), np.mean(rk_alt), "ok" if ok2 else "UNTER SOLL 0,95"))
    proben = [("ENA", "2024-06-01"), ("TIA", "2024-06-01"), ("WLD", "2025-06-01")]
    zeilen, ok3 = [], True
    for s, t in proben:
        _, r = MK.rang_mw(pd.Timestamp(t))
        MK.RANG_QUELLE = "eigen"
        _, ra = MK.rang_mw(pd.Timestamp(t))
        MK.RANG_QUELLE = "cmc"
        ok3 &= r[s] > 30
        zeilen.append("%s %s Rang %d (bisher %d)" % (s, t[:7], r[s], ra[s]))
    print("B3 %s -> %s" % (" · ".join(zeilen), "ok, keiner mehr in den Top 30" if ok3 else "NICHT OK"))
    # B4 Wirkung auf die Grundgesamtheit
    D = MK.paare_mw(1)[["t", "sym", "kl"]].rename(columns={"kl": "kl_neu"})
    MK.RANG_QUELLE = "eigen"
    Da = MK.paare_mw(1)[["t", "sym", "kl"]].rename(columns={"kl": "kl_alt"})
    MK.RANG_QUELLE = "cmc"
    X = D.merge(Da, on=["t", "sym"])
    X["jahr"] = X.t.dt.year
    X["anders"] = X.kl_neu != X.kl_alt
    print("B4 Wirkung (Anker 1 M): %d Anker, andere Klasse %.1f %% · je Jahr %s" % (
        len(X), 100 * X.anders.mean(), " · ".join("%d %.0f %%" % (j, 100 * g.anders.mean()) for j, g in X.groupby("jahr"))))
    print("   Wechsel: " + " · ".join("%s->%s %d" % (a, b, n) for (a, b), n in X[X.anders].groupby(["kl_alt", "kl_neu"]).size().items()))
    print("   Klassengroessen je Stichtag (Mittel) bisher/neu: " + " · ".join(
        "%s %.0f/%.0f" % (k, (X.kl_alt == k).sum() / X.t.nunique(), (X.kl_neu == k).sum() / X.t.nunique()) for k in ("H", "M", "S")))
    return ok2 and ok3


def main():
    print("P94 A1 MIT ZEITRICHTIGEM MARKTWERT-RANG (E-153)\n")
    if not b1():
        return 1
    if not b2_b4():
        print("\nPruefung des Baus nicht bestanden - A1 neu wird nicht gerechnet.")
        return 1
    neu = kind("p86_a1_zerlegung.py", "cmc")
    open(os.path.join(HIER, "p94_a1_neu.txt"), "w", encoding="utf-8").write(neu)
    gp = kind("p86_gegenprobe.py", "cmc")
    open(os.path.join(HIER, "p94_gegenprobe_neu.txt"), "w", encoding="utf-8").write(gp)
    print("\nA1 NEU geschrieben: p94_a1_neu.txt · Gegenprobe: p94_gegenprobe_neu.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
