"""N4 - Entscheide und Auswertung (Voranalyse_Schritt7 §23, vorab festgelegt). Wird vom Laeufer an den Entscheidpunkten gerufen;
der Endbericht laeuft erst, wenn T fertig oder am Zwischenentscheid beendet ist.

    python Basisinfos/Rechenkern_02_10/n4_auswertung.py [--ablage PFAD]

HAUPTREGEL R1 (vorab §20.5): Unterschied 24-h-Ertrag *stuetzt* minus *spricht dagegen* (Mehrheit aus 5 Stimmen wie im Betrieb),
Nullwelt = Vertauschen der Urteile innerhalb des Tages, je Jahr, einseitig 5 %. TRAEGT = in BEIDEN Jahren ueber dem Band UND staerker
als der Regel-Arm. Daneben (entscheiden nichts): R2 Vertauschen in der Woche, R3 Rangkorrelation Stimmen-Saldo.

ZWISCHENENTSCHEIDE (geeicht mit n4_sequenz_selbsttest.py): nach 250/500/750 Ankern
  STOP-TRAEGT-FRUEH   p < 0,001 in beiden Jahren (Haybittle-Peto)
  STOP-ANPASSEN       gepoolt z <= GRENZE[Blick]  - der Trader trennt erkennbar nicht: Zeit in Anpassungen (§23.5)
  WEITER              sonst; ausgegeben wird nur das Wort, keine Zahl (kein Zwischenblick)
KONTAMINATION (P2b): K_a Kuerzel >= 2 oder Monat+Jahr >= 6 von 50 erkannt; K_b benannt trennt besser als anonym (p < 0,05) -> STOP.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
GRENZE = {250: -1.0, 500: 0.0, 750: 0.5}                  # KANDIDAT D, geeicht 05.10. (n4_sequenz_kandidat_D.txt, Nachpruefung 1.000 Welten:
                                                           # falscher Abbruch bei echtem Effekt 1,8 %, Abbruch ohne Effekt 75 %; A fiel mit 5,3 % durch)
PERM_ZWISCHEN, PERM_ENDE = 1000, 2000


def _rng():
    return np.random.default_rng(20261007)


def spot_tabelle() -> dict:
    s = pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "b0_spur_bestand.csv"), sep=";")
    return {(r.symbol, int(r.std)): float(r.spot) for r in s.itertuples()}


def urteile(c, teil: str, bis: int | None = None) -> pd.DataFrame:
    """Je Anker: Mehrheit wie im Betrieb (gueltige Stimmen; Mehrheit > Haelfte, sonst *uneinig*), Saldo, Ertrag, Jahr, Tag, Woche."""
    e = pd.read_sql("SELECT pos, symbol, std, jahr, signalstunde FROM eingabe", c)
    s = pd.read_sql("SELECT pos, urteil, gueltig FROM stimme WHERE teil=?", c, params=(teil,))
    if bis is not None:
        e, s = e[e["pos"] < bis], s[s["pos"] < bis]
    zeilen = []
    for pos, g in s.groupby("pos"):
        gu = g[g["gueltig"] == 1]["urteil"].tolist()
        if not gu:
            m = "fehlt"
        else:
            w = pd.Series(gu).value_counts()
            m = w.index[0] if (w.iloc[0] * 2 > len(gu) or len(gu) == 1) else "uneinig"
        zeilen.append((pos, m, gu.count("stuetzt") - gu.count("spricht_dagegen"), len(g)))
    u = pd.DataFrame(zeilen, columns=["pos", "urteil", "saldo", "stimmen"])
    d = e.merge(u, on="pos")
    sp = spot_tabelle()
    d["spot"] = [sp[(a, int(b))] for a, b in zip(d["symbol"], d["std"])]
    d["tag"] = d["signalstunde"].str[:10]
    d["woche"] = pd.to_datetime(d["signalstunde"]).dt.strftime("%G-%V")
    d["lab"] = d["urteil"].map({"stuetzt": 1, "spricht_dagegen": -1}).fillna(0).astype(int)
    return d


def _diff(r, lab):
    a, b = r[lab == 1], r[lab == -1]
    return a.mean() - b.mean() if len(a) > 1 and len(b) > 1 else 0.0


def _perm(r, x, gruppen, stat, n, rng):
    s0 = stat(r, x)
    ix = [np.where(gruppen == g)[0] for g in np.unique(gruppen)]
    nul = np.empty(n)
    for i in range(n):
        p = np.arange(len(r))
        for g in ix:
            if len(g) > 1:
                p[g] = rng.permutation(g)
        nul[i] = stat(r, x[p])
    sd = nul.std() or 1e-12
    return s0, float(np.mean(nul >= s0)), float(np.percentile(nul, 95)), (s0 - nul.mean()) / sd


def _spearman(r, x):
    return float(np.corrcoef(pd.Series(r).rank(), pd.Series(x).rank())[0, 1]) if np.std(x) > 0 else 0.0


def r1_je_jahr(d: pd.DataFrame, n: int, gruppe: str = "tag") -> dict:
    rng = _rng()
    out = {}
    for j, g in d.groupby("jahr"):
        s0, p, band, z = _perm(g["spot"].values, g["lab"].values, g[gruppe].values, _diff, n, rng)
        out[int(j)] = dict(diff=s0, p=p, band=band, z=z, n=len(g), n_st=int((g["lab"] == 1).sum()), n_dg=int((g["lab"] == -1).sum()))
    return out


# ---------------------------------------------------------------------------- Entscheide (vom Laeufer gerufen)
def entscheide(c, name: str) -> dict:
    if name == "ENTSCHEID_K":
        return _entscheid_k(c)
    b = int(name.replace("ENTSCHEID_T", ""))
    d = urteile(c, "T", bis=b)
    r = r1_je_jahr(d, PERM_ZWISCHEN)
    zp = sum(v["z"] for v in r.values()) / np.sqrt(len(r))
    kz = {"blick": b, "z_gepoolt": round(zp, 3), "p_je_jahr": {k: round(v["p"], 4) for k, v in r.items()}}
    if max(v["p"] for v in r.values()) < 0.001:
        return {"ergebnis": "STOP-TRAEGT-FRUEH (beide Jahre p < 0,001) - weiter zur Bestaetigung", "kennzahlen": kz}
    if zp <= GRENZE[b]:
        return {"ergebnis": "STOP-ANPASSEN (der Trader trennt erkennbar nicht) - Zeit in Anpassungen, Schritt7 §23.7", "kennzahlen": kz}
    return {"ergebnis": "WEITER", "kennzahlen": kz}


def _entscheid_k(c) -> dict:
    roh = pd.read_sql("SELECT s.pos, s.roh, e.symbol, e.signalstunde FROM stimme s JOIN eingabe e ON e.pos = s.pos WHERE s.teil='K_a'", c)
    kz_t = zt = 0
    for r in roh.itertuples():
        try:
            a = json.loads(json.loads(r.roh)) if isinstance(json.loads(r.roh), str) else json.loads(r.roh)
        except Exception:                                    # noqa: BLE001
            continue
        kz_t += str(a.get("kuerzel") or "").upper().replace("USDT", "") == r.symbol.upper()
        zt += str(a.get("jahr")) == r.signalstunde[:4] and str(a.get("monat")).zfill(2) == r.signalstunde[5:7]
    an = urteile(c, "T", bis=100).set_index("pos")
    be = urteile(c, "K_b", bis=100).set_index("pos")
    gem = an.index.intersection(be.index)
    r_, la, lb = an.loc[gem, "spot"].values, an.loc[gem, "lab"].values, be.loc[gem, "lab"].values
    obs = _diff(r_, lb) - _diff(r_, la)
    rng = _rng()
    nul = []
    for _ in range(PERM_ENDE):
        t = rng.random(len(gem)) < 0.5
        x, y = np.where(t, la, lb), np.where(t, lb, la)
        nul.append(_diff(r_, y) - _diff(r_, x))
    p = float(np.mean(np.array(nul) >= obs))
    gleich = float(np.mean(la == lb)) if len(gem) else 0.0
    kz = {"kuerzel_treffer": int(kz_t), "zeit_treffer": int(zt), "gefragt": len(roh), "benannt_minus_anonym_p": round(p, 4),
          "gleiches_urteil_benannt_anonym": round(gleich, 3)}
    if kz_t >= 2 or zt >= 6:
        return {"ergebnis": "STOP-KONTAMINATION (Asset oder Zeitraum erkannt) - P2b: nur noch vorwaerts", "kennzahlen": kz}
    if p < 0.05 and obs > 0:
        return {"ergebnis": "STOP-KONTAMINATION (benannt trennt besser als anonym) - P2b: nur noch vorwaerts", "kennzahlen": kz}
    return {"ergebnis": "WEITER (Kontaminationsprobe bestanden)", "kennzahlen": kz}


# ---------------------------------------------------------------------------- Regel-Arm
def regel_arm(d: pd.DataFrame) -> pd.Series:
    """Antizyklisch wie die Wette der REGEL0: Lage des Schlusses in der Spanne der letzten 20 Tageskerzen (dieselben Kerzen wie die
    Trader-Eingabe). Je Jahr: unterste 10 % -> stuetzt, oberste 45 % -> spricht dagegen (gleiche Quote wie die Kalibrierung)."""
    from datetime import datetime, timedelta, timezone
    import agent.regel0_llm as L
    lage = []
    for r in d.itertuples():
        k = L.tageskerzen(os.path.join(PROJ, "data"), r.symbol, L._t(r.signalstunde) + timedelta(hours=1))   # wie trader_eingabe (mit Zeitzone)
        if k is None:
            lage.append(np.nan); continue
        h, l, cl = k["h"][-20:], k["l"][-20:], k["c"][-1]
        lage.append((cl - l.min()) / (h.max() - l.min()) if h.max() > l.min() else 0.5)
    d = d.assign(lage=lage)
    lab = pd.Series(0, index=d.index)
    for j, g in d.groupby("jahr"):
        q10, q55 = g["lage"].quantile([0.10, 0.55])
        lab[g.index] = np.where(g["lage"] <= q10, 1, np.where(g["lage"] >= q55, -1, 0))
    return lab


# ---------------------------------------------------------------------------- Endbericht
def bericht(ablage: str) -> int:
    c = sqlite3.connect("file:%s?mode=ro" % ablage.replace("\\", "/"), uri=True)
    gest = c.execute("SELECT v FROM meta WHERE k='t_gestoppt'").fetchone()
    n_e = c.execute("SELECT COUNT(*) FROM eingabe WHERE eingabe IS NOT NULL").fetchone()[0]   # ohne Eingabe: kein Aufruf (wie im Betrieb)
    fertig = c.execute("SELECT COUNT(*) FROM (SELECT pos FROM stimme WHERE teil='T' GROUP BY pos HAVING COUNT(*)>=5)").fetchone()[0]
    if not gest and fertig < n_e:
        print("T ist nicht fertig (%d von %d) und nicht am Zwischenentscheid beendet - KEIN Bericht (kein Zwischenblick)." % (fertig, n_e))
        return 1
    d = urteile(c, "T")
    d = d[d["stimmen"] >= 5]
    print("N4 ENDBERICHT · Ablage %s · Fassung %s · T %d Anker%s" % (ablage, c.execute("SELECT v FROM meta WHERE k='fassung'").fetchone()[0],
                                                                    len(d), (" (beendet am " + gest[0] + ")") if gest else ""))
    print("Verteilung Trader:", d["urteil"].value_counts().to_dict())
    r1 = r1_je_jahr(d, PERM_ENDE, "tag")
    r2 = r1_je_jahr(d, PERM_ENDE, "woche")
    rng = _rng()
    print("\nR1 HAUPTREGEL (Tag) und R2 (Woche): Unterschied stuetzt - spricht dagegen im 24-h-Ertrag")
    for j in sorted(r1):
        a, b = r1[j], r2[j]
        print("  %d: n %d (stuetzt %d, dagegen %d) · Unterschied %+.2f Pp · R1 Band %+.2f, p %.3f %s · R2 Band %+.2f, p %.3f" % (
            j, a["n"], a["n_st"], a["n_dg"], 100 * a["diff"], 100 * a["band"], a["p"], "UEBER" if a["diff"] > a["band"] else "nicht ueber",
            100 * b["band"], b["p"]))
    print("\nR3 Rangkorrelation Stimmen-Saldo (Woche):")
    for j, g in d.groupby("jahr"):
        s0, p, band, _z = _perm(g["spot"].values, g["saldo"].values.astype(float), g["woche"].values, _spearman, PERM_ENDE, rng)
        print("  %d: rho %+.3f · Band %+.3f · p %.3f" % (j, s0, band, p))
    print("\nREGEL-ARM (antizyklisch, Lage in der 20-Tage-Spanne, gleiche Quote) und ZUFALL")
    rl = regel_arm(d)
    d = d.assign(lab_regel=rl.values)
    besser = True
    for j, g in d.groupby("jahr"):
        dr = _diff(g["spot"].values, g["lab_regel"].values)
        zf = [_diff(g["spot"].values, rng.permutation(g["lab"].values)) for _ in range(PERM_ENDE)]
        besser &= r1[int(j)]["diff"] > dr
        print("  %d: Regel %+.2f Pp · Trader %+.2f Pp · Zufall gleiche Quote Mittel %+.2f, 95. Perz. %+.2f" % (
            j, 100 * dr, 100 * r1[int(j)]["diff"], 100 * np.mean(zf), 100 * np.percentile(zf, 95)))
    print("\nRAUSCHBODEN (Anker 0-99)")
    t100 = urteile(c, "T", bis=100).set_index("pos")
    for teil, name in (("R_w", "Wiederholung A/A'"), ("R_v", "vertauschte Reihenfolge")):
        x = urteile(c, teil, bis=100).set_index("pos")
        g = t100.index.intersection(x.index)
        print("  %-24s gleiches Mehrheitsurteil %d von %d (%.0f %%)" % (name, int((t100.loc[g, "urteil"] == x.loc[g, "urteil"]).sum()), len(g),
                                                                    100 * float((t100.loc[g, "urteil"] == x.loc[g, "urteil"]).mean()) if len(g) else 0))
    k = c.execute("SELECT ergebnis, kennzahlen FROM entscheid WHERE name='ENTSCHEID_K'").fetchone()
    print("\nKONTAMINATION:", k[0] if k else "-", k[1] if k else "")
    for name, erg, kz in c.execute("SELECT name, ergebnis, kennzahlen FROM entscheid WHERE name LIKE 'ENTSCHEID_T%' ORDER BY name"):
        print("ZWISCHENENTSCHEID %s: %s %s" % (name, erg, kz))
    print("\nSIGNALBILANZ JE ASSET (Anker mit stuetzt / dagegen, Mittel 24 h):")
    sb = d.groupby("symbol").agg(n=("lab", "size"), st=("lab", lambda x: int((x == 1).sum())), dg=("lab", lambda x: int((x == -1).sum())),
                                 ertrag=("spot", "mean")).sort_values("n", ascending=False)
    print("  " + " · ".join("%s %d (%d/%d) %+.1f %%" % (s, r.n, r.st, r.dg, 100 * r.ertrag) for s, r in sb.head(25).iterrows()))
    traegt = all(r1[j]["diff"] > r1[j]["band"] for j in r1) and besser
    print("\nP2 TRADER (vorab): %s" % ("TRAEGT (beide Jahre ueber dem Band und staerker als die Regel) -> Bestaetigung P3" if traegt else
                                       "TRAEGT NICHT (kein Unterschied ueber ~4-5 Pp nachweisbar, §23.2) -> Anpassen nach §23.5 oder Auskunft"))
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ablage", default=os.path.join(PROJ, "data", "_n4", "n4_ablage.db"))
    sys.exit(bericht(ap.parse_args().ablage))
