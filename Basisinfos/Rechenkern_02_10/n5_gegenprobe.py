"""Gegenprobe N5 (Schritt7 §23.20) - eigener Rechenweg gegen n5_auswertung, auf einem PLATZHALTER-Lauf (Orakel) in einer Wegwerf-Ablage.

    python Basisinfos/Rechenkern_02_10/n5_gegenprobe.py

  G1 Mehrheitsurteile je Anker selbst gezaehlt (aus der Tabelle stimme) gegen die Verteilung im Bericht
  G2 Trennwerte je Jahr (LLM, Regel-Arm F) mit eigener Rechnung (numpy, Gruppenmittel) gegen das JSON
  G3 Regel-Arm F: je Jahr genau so viele stuetzt/dagegen wie das LLM; die Zuordnung folgt dem Rang des Werts
  G4 Regel F mit einem ZWEITEN Schaetzweg (Normalgleichungen auf den UNstandardisierten Merkmalen): gleiche Rangfolge der Anker
  G5 M-2 und M-3 selbst gerechnet (scipy.stats.binom.sf statt binomtest)
  G6 N5 zeigt dem Modell GENAU, was der Betrieb zeigen wuerde: an 10 Ankern trader_eingabe mit dem Betriebskatalog (ohne Produktion)
     gegen die eingefrorene, wieder in Betriebsreihenfolge gebrachte N5-Eingabe - Inhalt UND Reihenfolge der Schluessel
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import binom, spearmanr

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, PROJ)
os.chdir(PROJ)
import n5_pruefe as P          # noqa: E402
import n5_rueckspiel as N5     # noqa: E402
import n5_auswertung as W      # noqa: E402
import agent.regel0_llm as L   # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


with tempfile.TemporaryDirectory() as d:
    n4 = P.n4_kopie(os.path.join(d, "o"), ende=True)
    ab = os.path.join(d, "o", "n5.db")
    P.lauf(ab, n4, modus="orakel")
    subprocess.run([sys.executable, P.AUSW, "--ablage", ab, "--n4-ablage", n4], capture_output=True, text=True, encoding="utf-8",
                   errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    kz = json.load(open(os.path.join(d, "o", "n5_bericht.json"), encoding="utf-8"))
    an = pd.read_csv(os.path.join(d, "o", "n5_bericht_anker.csv"), sep=";")
    c = sqlite3.connect(ab)
    # G1
    st = pd.read_sql("SELECT pos, urteil, gueltig FROM stimme WHERE teil='T'", c)
    zaehl = {}
    for pos, g in st.groupby("pos"):
        gu = list(g[g.gueltig == 1].urteil)
        if len(g) < 5:
            continue
        if not gu:
            m = "fehlt"
        else:
            w = {u: gu.count(u) for u in set(gu)}
            b = max(w, key=w.get)
            m = b if (w[b] * 2 > len(gu) or len(gu) == 1) else "uneinig"
        zaehl[m] = zaehl.get(m, 0) + 1
    pruefe("G1", zaehl == kz["verteilung"], "%s / %s" % (zaehl, kz["verteilung"]))
    # G2
    for j, g in an.groupby("jahr"):
        s = g.spot.values
        llm = s[g.lab.values == 1].mean() - s[g.lab.values == -1].mean()
        rf = s[g.lab_f.values == 1].mean() - s[g.lab_f.values == -1].mean()
        r20 = s[g.lab_r20.values == 1].mean() - s[g.lab_r20.values == -1].mean()
        ref = ("F" if rf >= r20 else "20T") if max(rf, r20) > 0 else "Zufall"
        soll = llm - (rf if ref == "F" else r20) if ref != "Zufall" else llm
        m = kz["M"][str(j)]
        pruefe("G2", abs(llm - kz["H"][str(j)]["diff"]) < 1e-12 and abs(rf - m["regel_f"]) < 1e-12 and abs(r20 - m["regel20"]) < 1e-12
               and ref == m["referenz"] and abs(soll - m["obs"]) < 1e-12,
               "%d LLM %+.4f Regel F %+.4f Regel 20 T %+.4f Referenz %s" % (j, llm, rf, r20, ref))
    # G3
    g3 = True
    for j, g in an.groupby("jahr"):
        g3 &= (g.lab_f == 1).sum() == (g.lab == 1).sum() and (g.lab_f == -1).sum() == (g.lab == -1).sum()
        if (g.lab_f == 1).any() and (g.lab_f == 0).any():
            g3 &= g[g.lab_f == 1].wert_f.min() >= g[g.lab_f == 0].wert_f.max()
        if (g.lab_f == -1).any() and (g.lab_f == 0).any():
            g3 &= g[g.lab_f == -1].wert_f.max() <= g[g.lab_f == 0].wert_f.min()
    pruefe("G3", g3, "Auswahlanteil gleich dem LLM, Zuordnung nach Rang")
    # G4
    mod = json.load(open(os.path.join(d, "o", "n5_regel_f.json"), encoding="utf-8"))
    E = pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    E = E[E.jahr == 2024]
    X, y = [], []
    for r in E.itertuples():
        stt = (W.B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
        yy = W.ertrag24(r.symbol, stt)
        if not np.isfinite(yy):
            continue
        m = W.merkmale(r.symbol, stt)
        X.append([m[k] if np.isfinite(m[k]) else mod["median"][k] for k in W.MERK]); y.append(yy)
    X1 = np.column_stack([np.ones(len(X)), np.array(X)])
    b = np.linalg.solve(X1.T @ X1, X1.T @ np.array(y))
    e = pd.read_sql("SELECT pos, symbol, signalstunde FROM eingabe", c).set_index("pos")
    eig = []
    for r in an.itertuples():
        m = W.merkmale(r.symbol, e.at[r.pos, "signalstunde"])
        eig.append(float(b[0] + np.dot(b[1:], [m[k] if np.isfinite(m[k]) else mod["median"][k] for k in W.MERK])))
    rho = spearmanr(eig, an.wert_f).correlation
    pruefe("G4", rho > 0.9999 and len(y) == mod["n"], "Rangkorrelation zweiter Schaetzweg %.6f · Einstiege %d / %d" % (rho, len(y), mod["n"]))
    # G5
    gleich = float((an.lab == an.lab_f).mean())
    mit = an.groupby("jahr").spot.transform("mean")
    lref = pd.Series(0, index=an.index)
    for j, g in an.groupby("jahr"):                         # die Referenz aus den eigenen Trennwerten, nicht aus der Datei
        s_ = g.spot.values
        rf_ = s_[g.lab_f.values == 1].mean() - s_[g.lab_f.values == -1].mean()
        r20_ = s_[g.lab_r20.values == 1].mean() - s_[g.lab_r20.values == -1].mean()
        if max(rf_, r20_) > 0:
            lref[g.index] = g.lab_f if rf_ >= r20_ else g.lab_r20
    un = an[(an.lab != lref) & (an.spot != mit)]
    ri = int((((un.lab - lref[un.index]) * (un.spot - mit[un.index])) > 0).sum())
    p = float(binom.sf(ri - 1, len(un), 0.5)) if len(un) else 1.0
    pruefe("G5", abs(gleich - kz["M2_gleich"]) < 1e-12 and ri == kz["M3_richtig"] and len(un) == kz["M3_uneinig"] and abs(p - kz["M3_p"]) < 1e-9,
           "gleich %.4f · richtig %d von %d · p %.4g (Bericht %.4g)" % (gleich, ri, len(un), p, kz["M3_p"]))
    # G6
    K02 = L.lade(N5.KATALOG_N5)
    for pos, sym, sst, stufe, ein in c.execute("SELECT pos, symbol, signalstunde, stufe, eingabe FROM eingabe WHERE eingabe IS NOT NULL "
                                               "ORDER BY pos LIMIT 10").fetchall():
        betrieb = L.trader_eingabe({"symbol": sym, "signalstunde": sst, "stufe": stufe}, os.path.join(PROJ, "data"), K02, None)
        n5 = N5.variante5("T", json.loads(ein), None)
        pruefe("G6", json.dumps(betrieb, ensure_ascii=False) == json.dumps(n5, ensure_ascii=False), "pos %d %s %s · Schluessel %s" % (
            pos, sym, sst, list(n5)))
    c.close()
print("\n%d von %d gleich" % (ok, n))
