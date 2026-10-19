"""P67 Auswertung L-C2 (19.10.2026) - genau nach Schritt7 §23.74 (vorab fa3aac7e). Nur lesend.

    python Basisinfos/Rechenkern_02_10/p67_auswertung.py [--ablage <pfad>]
"""
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p66_lc2_voranalyse as V  # noqa: E402  (nur die vorab festgelegte Warnwort-Liste)
import p67_lc2_rueckspiel as R  # noqa: E402  (derselbe Eingabebau fuer den Warnwort-Massstab)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def tagtabelle():
    E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
    E["tag"] = E.zeit.dt.strftime("%Y-%m-%d")
    T = E.groupby("tag").agg(n=("tief", "size"), anteil=("tief", lambda x: float((x <= -0.10).mean())))
    T["absturz"] = (T.n >= 5) & (T.anteil >= 0.25)
    return T


def lift(mask, ziel):
    p = ziel.mean()
    return (ziel[mask].mean() / p) if mask.sum() and p else float("nan")


def main():
    ablage = sys.argv[sys.argv.index("--ablage") + 1] if "--ablage" in sys.argv else os.path.join("data", "_lc", "p67_rueckspiel.db")
    T = tagtabelle()
    c = sqlite3.connect("file:%s?mode=ro" % ablage.replace("\\", "/"), uri=True)
    U = pd.read_sql("SELECT tag, n_meldungen, risiko, grund FROM urteil", c).set_index("tag")
    c.close()
    D = T.join(U, how="left")
    fehlend = int(D.risiko.isna().sum())
    D["risiko"] = D.risiko.fillna("ohne Abfrage")
    print("P67 AUSWERTUNG L-C2 (§23.74) · %d Einstiegstage, Absturztage %d · Urteile %s · ohne Abfrage %d\n" % (
        len(D), int(D.absturz.sum()), dict(D.risiko.value_counts()), fehlend))
    ziel = D.absturz.to_numpy()
    rng = np.random.default_rng(19102026)
    for name, maske_fn, ohne_fehlt in (("Hauptfrage 'hoch'", lambda X: (X.risiko == "hoch").to_numpy(), False),
                                       ("Gegenrechnung ohne 'fehlt'", lambda X: (X.risiko == "hoch").to_numpy(), True),
                                       ("Auskunft 'mittel oder hoch'", lambda X: X.risiko.isin(["mittel", "hoch"]).to_numpy(), False)):
        X = D[D.risiko != "fehlt"] if ohne_fehlt else D
        z = X.absturz.to_numpy()
        m = maske_fn(X)
        k = int(m.sum())
        L = lift(m, z)
        bs = []
        idx = np.arange(len(X))
        for _ in range(2000):
            s = rng.choice(idx, len(idx), replace=True)
            bs.append(lift(m[s], z[s]))
        bs = np.array([b for b in bs if b == b])
        lo, hi = (np.percentile(bs, 2.5), np.percentile(bs, 97.5)) if len(bs) else (float("nan"), float("nan"))
        zuf = np.array([lift(np.isin(idx, rng.choice(idx, k, replace=False)), z) for _ in range(10000)]) if k else np.array([np.nan])
        p_zuf = float((zuf >= L).mean()) if L == L else float("nan")
        text = M_TEXT.reindex(X.index).fillna("keine Meldungen")
        w = text.str.lower().apply(lambda t: sum(len(re.findall(r"\b%s" % re.escape(x), t)) for x in V.WARN)).to_numpy()
        zufall_rang = rng.random(len(X))
        o = np.lexsort((zufall_rang, -w))[:k]
        u = np.lexsort((zufall_rang, w))[:k]
        mo, mu = np.isin(idx, o), np.isin(idx, u)
        Lo, Lu = lift(mo, z), lift(mu, z)
        print("%s: %d Tage markiert, davon Absturztage %d von %d" % (name, k, int(z[m].sum()), int(z.sum())))
        print("   Lift %.2f [95 %%: %.2f..%.2f] · Zufall >= Lift in %.1f %% der Ziehungen · Warnwoerter meiste %.2f / wenigste %.2f" % (
            L, lo, hi, 100 * p_zuf, Lo, Lu))
        if name.startswith("Hauptfrage"):
            if k < 5:
                urteil = "ZU WENIGE WARNUNGEN (%d Tage 'hoch')" % k
            else:
                urteil = "TRAEGT" if (L >= 2 and lo > 1 and L > max(Lo, Lu)) else "TRAEGT NICHT"
            haupt = (urteil, L, lo, hi, Lo, Lu, k)
    print("\nAuskunft je Urteil: Tage · Absturztage · mittlerer Anteil der Tief-Faelle")
    for r, g in D.groupby("risiko"):
        print("   %-13s %3d Tage · %2d Absturztage (%.1f %%) · Tief-Anteil %.1f %%" % (r, len(g), int(g.absturz.sum()), 100 * g.absturz.mean(), 100 * g.anteil.mean()))
    print("\nAuskunft: die 16 Absturztage")
    for d, r in D[D.absturz].iterrows():
        print("   %s  %2d/%2d Tief · Meldungen %3s · %-7s · %s" % (d, round(r.anteil * r.n), r.n, int(r.n_meldungen) if r.n_meldungen == r.n_meldungen else "-",
                                                             r.risiko, (r.grund if isinstance(r.grund, str) else "")[:120]))
    print("\nURTEIL L-C2 (vorab §23.74): %s · Lift %.2f [%.2f..%.2f] · Warnwoerter %.2f / %.2f · 'hoch' an %d Tagen" % haupt)


def _texte():
    M = R.meldungen()
    T = tagtabelle()
    return pd.Series({d: R.eingabe(M, d)[0] for d in T.index})


M_TEXT = None
if __name__ == "__main__":
    M_TEXT = _texte()
    main()
