"""N5 - Endbericht des Rueckspiels der Fassung 0.2 (Voranalyse_Schritt7 §23.20). VORAB FESTGELEGT 07.10.2026, vor dem ersten Aufruf.

    python Basisinfos/Rechenkern_02_10/n5_auswertung.py [--ablage PFAD] [--n4-ablage PFAD]

Erst wenn T fertig oder am Zwischenentscheid beendet ist (kein Zwischenblick). Mehrheit aus 5 Stimmen wie im Betrieb; *neutral* und
*uneinig* zaehlen als 0. Ertrag = 24-h-Ertrag des Ankers (b0_spur_bestand, wie N4).

  H     wie N4: Unterschied stuetzt - dagegen je Jahr gegen die Nullwelt (Vertauschen im Tag, einseitig 5 %); TRAEGT = beide Jahre ueber
        dem Band und staerker als der Regel-Arm 20 T von N4
  V1    0.2 gegen 0.1e GEPAART auf denselben Ankern (N4-T): Unterschied der beiden Trennwerte, Nullwelt = je Anker die Urteile der
        beiden Fassungen zufaellig tauschen (2.000). AUSKUNFT - entscheidet nichts
  REGEL-ARM F (*die Regel mit denselben Fakten*, §23.16): lineare Regel auf den Zahlen der Lage zur Signalstunde (log Umsatz 24 h, Fall
        6 h, Fall 24 h, Docht, log Kapitulation, Praemie, Bitcoin 24 h, Bitcoin 7 T; standardisiert, fehlend = Median), geschaetzt auf den
        REGEL0-Einstiegen 2024 (kern48jbz bestand) gegen den 24-h-Ertrag - die Anker (2025/26) liegen ausserhalb. AUSWAHLANTEIL
        ANGEGLICHEN: je Jahr bekommt der Arm GENAU so viele *stuetzt* und *dagegen* wie das LLM (oberes / unteres Ende des Werts)
  REFERENZ je Jahr (KORREKTUR 07.10., VOR dem ersten Aufruf - n5_pruefe P8: ein ZUFALLS-LLM erreichte *besser als Regel F*, weil Regel F
        2025/26 unter dem Zufall liegt; eine schlechte Regel zu schlagen beweist nichts): die BESSERE der beiden Regeln (F, 20 T), wenn
        ihr Trennwert > 0 ist - sonst der ZUFALL (die Nullwelt von H; fuer M-3 die Regel *alles neutral*)
  M-1   nicht schlechter: in KEINEM Jahr signifikant unter der Referenz (Regel: gepaart, Tausch je Anker, einseitig 5 %; Zufall: H-Nullwelt,
        P(Null <= LLM) < 5 %)
  M-2   kein Echo: Urteil gleich dem Arm F UND gleich dem Arm 20 T in hoechstens 90 % der Anker
  M-3   die Gegenmeinung traegt: wo LLM und Referenz verschieden urteilen, liegt das LLM in mehr als 50 % richtig (richtig = die Richtung
        des Unterschieds (LLM - Referenz) passt zum Vorzeichen von Ertrag minus Jahresmittel; Binomialtest einseitig 5 %)
  ZIEL  in BEIDEN Jahren: H ueber dem Band UND (Referenz Regel: gepaart signifikant darueber, einseitig 5 %)
  R_v   Bloecke vertauscht (Anker 0-99): gleiches Mehrheitsurteil wie T - AUSKUNFT zu F3
Die Kennzahlen gehen zusaetzlich nach <Ablageordner>/n5_bericht.json (fuer n5_gegenprobe.py).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
import n4_auswertung as A      # noqa: E402

PERM = 2000
MERK = ("lumsatz", "fall6", "fall24", "docht", "lkapit", "praemie", "btc24", "btc168")
B0 = pd.Timestamp("2020-01-01")


def merkmale(symbol: str, signalstunde: str) -> dict:
    import agent.regel0_llm as L
    w = L.signal_werte({"symbol": symbol, "signalstunde": signalstunde}, os.path.join(PROJ, "data"), None)
    return {"lumsatz": np.log(w["umsatz_usd_24h"]) if w.get("umsatz_usd_24h", 0) > 0 else np.nan,
            "fall6": w.get("fall6", np.nan), "fall24": w.get("fall24", np.nan), "docht": w.get("docht", np.nan),
            "lkapit": np.log(w["kapitulation"]) if w.get("kapitulation", 0) > 0 else np.nan,
            "praemie": w.get("praemie", np.nan), "btc24": w.get("btc24", np.nan), "btc168": w.get("btc168", np.nan)}


def ertrag24(symbol: str, signalstunde: str) -> float:
    import agent.regel0_llm as L
    t = pd.Timestamp(signalstunde)
    k = L._reihe_stunden(os.path.join(PROJ, "data"), ("stundenkurse.db", "stundenkurse_alle.db"), "stundenkurse", "close", symbol,
                         t + timedelta(hours=1), t + timedelta(hours=25))
    a, b = k.get((t + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")), k.get((t + timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"))
    return float(b[0]) / float(a[0]) - 1.0 if a and b and a[0] else np.nan


def regel_f_modell(cache: str | None = None) -> dict:
    """OLS auf den REGEL0-Einstiegen 2024 (bestand). Ergebnis zwischengespeichert, weil 2.300 Einstiege einige Sekunden brauchen."""
    if cache and os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    E = pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    E = E[E.jahr == 2024]
    zeilen = []
    for r in E.itertuples():
        st = (B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
        m = merkmale(r.symbol, st)
        m["y"] = ertrag24(r.symbol, st)
        zeilen.append(m)
    X = pd.DataFrame(zeilen).dropna(subset=["y"])
    med = {k: float(X[k].median()) for k in MERK}
    Xf = X[list(MERK)].fillna(med)
    mu, sd = Xf.mean(), Xf.std().replace(0, 1)
    Z = ((Xf - mu) / sd).values
    Z1 = np.column_stack([np.ones(len(Z)), Z])
    beta = np.linalg.lstsq(Z1, X["y"].values, rcond=None)[0]
    mod = {"median": med, "mu": mu.to_dict(), "sd": sd.to_dict(), "beta": beta.tolist(), "n": int(len(X))}
    if cache:
        json.dump(mod, open(cache, "w", encoding="utf-8"), indent=1)
    return mod


def regel_f_wert(mod: dict, m: dict) -> float:
    z = [((m[k] if np.isfinite(m[k]) else mod["median"][k]) - mod["mu"][k]) / mod["sd"][k] for k in MERK]
    return float(mod["beta"][0] + np.dot(mod["beta"][1:], z))


def regel_f_label(d: pd.DataFrame) -> pd.Series:
    """Je Jahr GENAU so viele +1 / -1 wie das LLM - oberes / unteres Ende des Werts (Auswahlanteil angeglichen)."""
    lab = pd.Series(0, index=d.index)
    for _, g in d.groupby("jahr"):
        n_st, n_dg = int((g["lab"] == 1).sum()), int((g["lab"] == -1).sum())
        o = g["wert_f"].sort_values(kind="mergesort")
        if n_dg:
            lab[o.index[:n_dg]] = -1
        if n_st:
            lab[o.index[len(o) - n_st:]] = 1
    return lab


def gepaart(r, la, lb, n, rng) -> tuple:
    """Unterschied diff(la) - diff(lb); Nullwelt: je Anker la/lb mit 1/2 tauschen. -> (obs, p_besser, p_schlechter)."""
    obs = A._diff(r, la) - A._diff(r, lb)
    nul = np.empty(n)
    for i in range(n):
        t = rng.random(len(r)) < 0.5
        x, y = np.where(t, lb, la), np.where(t, la, lb)
        nul[i] = A._diff(r, x) - A._diff(r, y)
    return obs, float(np.mean(nul >= obs)), float(np.mean(nul <= obs))


def bericht(ablage: str, n4_ablage: str) -> int:
    from scipy.stats import binomtest
    c = sqlite3.connect("file:%s?mode=ro" % ablage.replace("\\", "/"), uri=True)
    gest = c.execute("SELECT v FROM meta WHERE k='t_gestoppt'").fetchone()
    n_e = c.execute("SELECT COUNT(*) FROM eingabe WHERE eingabe IS NOT NULL").fetchone()[0]
    fertig = c.execute("SELECT COUNT(*) FROM (SELECT pos FROM stimme WHERE teil='T' GROUP BY pos HAVING COUNT(*)>=5)").fetchone()[0]
    if not gest and fertig < n_e:
        print("T ist nicht fertig (%d von %d) und nicht am Zwischenentscheid beendet - KEIN Bericht (kein Zwischenblick)." % (fertig, n_e))
        return 1
    rng = A._rng()
    d = A.urteile(c, "T")
    d = d[d["stimmen"] >= 5].reset_index(drop=True)
    kz = {"n": len(d), "verteilung": d["urteil"].value_counts().to_dict(), "gestoppt": gest[0] if gest else None}
    print("N5 ENDBERICHT · Fassung 0.2 · Ablage %s · T %d Anker%s" % (ablage, len(d), (" (beendet am " + gest[0] + ")") if gest else ""))
    print("Verteilung:", kz["verteilung"])
    # H
    r1 = A.r1_je_jahr(d, PERM, "tag")
    rl = A.regel_arm(d)
    d["lab_r20"] = rl.values
    print("\nH  Unterschied stuetzt - dagegen (24 h) je Jahr, Nullwelt im Tag")
    h_ok = True
    kz["H"] = {}
    for j in sorted(r1):
        g = d[d.jahr == j]
        dr = A._diff(g["spot"].values, g["lab_r20"].values)
        h_ok &= r1[j]["diff"] > r1[j]["band"] and r1[j]["diff"] > dr
        kz["H"][str(j)] = {"diff": r1[j]["diff"], "band": r1[j]["band"], "p": r1[j]["p"], "regel20": dr}
        print("  %d: n %d (stuetzt %d, dagegen %d) · %+.2f Pp · Band %+.2f · p %.3f · Regel-Arm 20 T %+.2f Pp" % (
            j, r1[j]["n"], r1[j]["n_st"], r1[j]["n_dg"], 100 * r1[j]["diff"], 100 * r1[j]["band"], r1[j]["p"], 100 * dr))
    print("  -> H %s" % ("TRAEGT" if h_ok else "TRAEGT NICHT"))
    kz["H_traegt"] = bool(h_ok)
    # V1
    print("\nV1 0.2 gegen 0.1e GEPAART (dieselben Anker aus N4-T) - Auskunft")
    kz["V1"] = {}
    if os.path.exists(n4_ablage):
        c4 = sqlite3.connect("file:%s?mode=ro" % n4_ablage.replace("\\", "/"), uri=True)
        d4 = A.urteile(c4, "T")
        d4 = d4[d4["stimmen"] >= 5][["pos", "symbol", "std", "lab"]].rename(columns={"lab": "lab01"})
        v = d.merge(d4, on=["pos", "symbol", "std"])
        for j, g in v.groupby("jahr"):
            obs, pb, ps = gepaart(g["spot"].values, g["lab"].values, g["lab01"].values, PERM, rng)
            kz["V1"][str(j)] = {"n": len(g), "obs": obs, "p_besser": pb, "gleich": float((g["lab"] == g["lab01"]).mean())}
            print("  %d: n %d · 0.2 minus 0.1e %+.2f Pp · p (0.2 besser) %.3f · gleiches Urteil %.0f %%" % (
                j, len(g), 100 * obs, pb, 100 * (g["lab"] == g["lab01"]).mean()))
    # Regel-Arm F und M-1..M-3
    mod = regel_f_modell(os.path.join(os.path.dirname(ablage), "n5_regel_f.json"))
    d["wert_f"] = [regel_f_wert(mod, merkmale(r.symbol, r.signalstunde)) for r in d.itertuples()]
    d["lab_f"] = regel_f_label(d).values
    print("\nREGEL-ARM F (lineare Regel auf denselben Zahlen, geschaetzt auf %d Einstiegen 2024; Auswahlanteil = LLM)" % mod["n"])
    m1, ziel, kz["M"] = True, True, {}
    d["lab_ref"] = 0
    for j, g in d.groupby("jahr"):
        s_ = g["spot"].values
        dF, d20 = A._diff(s_, g["lab_f"].values), A._diff(s_, g["lab_r20"].values)
        if max(dF, d20) > 0:
            ref = "F" if dF >= d20 else "20T"
            lr = g["lab_f"].values if ref == "F" else g["lab_r20"].values
            obs, pb, ps = gepaart(s_, g["lab"].values, lr, PERM, rng)
            d.loc[g.index, "lab_ref"] = lr
        else:
            ref, obs = "Zufall", r1[int(j)]["diff"]
            pb = r1[int(j)]["p"]
            ps = 1.0 - pb
        m1 &= ps >= 0.05
        ziel &= (r1[int(j)]["diff"] > r1[int(j)]["band"]) and (ref == "Zufall" or pb < 0.05)
        kz["M"][str(j)] = {"referenz": ref, "obs": obs, "p_besser": pb, "p_schlechter": ps, "regel_f": dF, "regel20": d20}
        print("  %d: Regel F %+.2f Pp · Regel 20 T %+.2f Pp · LLM %+.2f Pp -> Referenz %s · LLM minus Referenz %+.2f Pp · p besser %.3f · "
              "p schlechter %.3f" % (j, 100 * dF, 100 * d20, 100 * A._diff(s_, g["lab"].values), ref, 100 * obs, pb, ps))
    gleich = float((d["lab"] == d["lab_f"]).mean())
    gleich20 = float((d["lab"] == d["lab_r20"]).mean())
    mittel = d.groupby("jahr")["spot"].transform("mean")
    un = d[(d["lab"] != d["lab_ref"]) & (d["spot"] != mittel)]
    richtig = int((((un["lab"] - un["lab_ref"]) * (un["spot"] - mittel[un.index])) > 0).sum())
    p3 = binomtest(richtig, len(un), 0.5, alternative="greater").pvalue if len(un) else 1.0
    m2 = gleich <= 0.90 and gleich20 <= 0.90
    kz.update({"M1": bool(m1), "M2_gleich": gleich, "M2_gleich20": gleich20, "M2": bool(m2), "M3_uneinig": len(un), "M3_richtig": richtig,
               "M3_p": p3, "M3": bool(p3 < 0.05), "ZIEL": bool(ziel)})
    print("  M-1 nicht schlechter: %s" % ("ERFUELLT" if m1 else "NICHT erfuellt"))
    print("  M-2 kein Echo: gleiches Urteil wie F %.1f %%, wie 20 T %.1f %% -> %s" % (100 * gleich, 100 * gleich20, "ERFUELLT" if m2 else "NICHT erfuellt"))
    print("  M-3 Gegenmeinung: richtig %d von %d uneinigen (%.1f %%), p %.3f -> %s" % (
        richtig, len(un), 100 * richtig / max(1, len(un)), p3, "ERFUELLT" if p3 < 0.05 else "NICHT erfuellt"))
    print("  ZIEL ueber der Nullwelt UND besser als die bessere Regel (beide Jahre): %s" % ("ERREICHT" if ziel else "nicht erreicht"))
    # R_v
    t100 = A.urteile(c, "T", bis=N_RV_BIS).set_index("pos")
    rv = A.urteile(c, "R_v", bis=N_RV_BIS).set_index("pos")
    gm = t100.index.intersection(rv.index)
    kz["R_v_gleich"] = float((t100.loc[gm, "urteil"] == rv.loc[gm, "urteil"]).mean()) if len(gm) else None
    print("\nR_v Bloecke vertauscht: gleiches Mehrheitsurteil %s (%d Anker) - Auskunft zu F3" % (
        "%.0f %%" % (100 * kz["R_v_gleich"]) if kz["R_v_gleich"] is not None else "-", len(gm)))
    k = c.execute("SELECT ergebnis, kennzahlen FROM entscheid WHERE name='ENTSCHEID_K'").fetchone()
    print("KONTAMINATION (K_a):", k[0] if k else "-", k[1] if k else "")
    for name, erg, kzz in c.execute("SELECT name, ergebnis, kennzahlen FROM entscheid WHERE name LIKE 'ENTSCHEID_T%' ORDER BY name"):
        print("ZWISCHENENTSCHEID %s: %s %s" % (name, erg, kzz))
    sb = d.groupby("symbol").agg(n=("lab", "size"), st=("lab", lambda x: int((x == 1).sum())), dg=("lab", lambda x: int((x == -1).sum())),
                                 ertrag=("spot", "mean")).sort_values("n", ascending=False)
    print("\nSIGNALBILANZ JE ASSET: " + " · ".join("%s %d (%d/%d) %+.1f %%" % (s, r.n, r.st, r.dg, 100 * r.ertrag) for s, r in sb.head(25).iterrows()))
    print("\nERGEBNIS (vorab): Minimum M-1..M-3 %s · Ziel %s · H %s" % (
        "ERFUELLT" if (m1 and kz["M2"] and kz["M3"]) else "NICHT erfuellt", "ERREICHT" if ziel else "nicht erreicht", "traegt" if h_ok else "traegt nicht"))
    json.dump(kz, open(os.path.join(os.path.dirname(ablage), "n5_bericht.json"), "w", encoding="utf-8"), indent=1, default=float)
    d[["pos", "symbol", "std", "jahr", "spot", "lab", "lab_f", "lab_r20", "lab_ref", "wert_f"]].to_csv(
        os.path.join(os.path.dirname(ablage), "n5_bericht_anker.csv"), sep=";", index=False)
    return 0


N_RV_BIS = 100

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ablage", default=os.path.join(PROJ, "data", "_n5", "n5_ablage.db"))
    ap.add_argument("--n4-ablage", default=os.path.join(PROJ, "data", "_n4", "n4_ablage.db"))
    x = ap.parse_args()
    sys.exit(bericht(x.ablage, x.n4_ablage))
