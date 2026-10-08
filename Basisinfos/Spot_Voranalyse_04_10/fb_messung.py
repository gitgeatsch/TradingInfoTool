"""MESSUNG Teil B - Fuehrung und Ausstieg je Rolle (Voranalyse_Spot_Neubau_04_10.md §31.3, vorab Commit 0517a30) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/fb_messung.py

Nach §31.3, mit EINER Korrektur vor der Messung (§31.5):
  Rolle L Haupt-Nullwelt = zufaellige L-Positionen DESSELBEN Starttags, gleiche Zahl wie ausgeloest, Verkaufstag aus der Ausloese-Verteilung
  der Stufe. Die vorab beschriebene Form 'gleicher Coin, zufaelliger Tag' ist trivial zu schlagen (der Ausloesetag liegt per Bauart auf
  erhoehtem Kurs) und laeuft nur als Auskunft mit.

  Teil 0 (R-R11)  Lagebild L5 (X2 180 T, ab 2024, Median gegen BTC: Ausbrecher +39,2 %, alle -23,9 %) mit der Marke dieser Messung;
                  B5 X2 (+31,8 / -4,0 %) mit wl_messung.b5 -> Abweichung > 1 Pp bricht ab
  Rolle L         L-Kandidaten (oberstes Fuenftel), monatliche Starttage, 365 T; Regel: 50 % am Tag nach dem ersten Erreichen des Ziels,
                  Rest bis Fensterende; d = Regel - Halten = 0,5 x (Kurs Verkaufstag - Kurs Ende) / Kurs Start (0 ohne Ausloesung)
  Rolle K         Stellvertreter-Einstieg (Coin/BTC >= 1,3 x 30-T-Tief, 30 T Sperre), Kauf Folgetag, 180 T; Nachlauf-Stufen;
                  d = Regel - Halten 180 T; Nullwelt gleicher Coin, Ausstieg an zufaelligem Tag aus der Haltedauer-Verteilung
  Wahl 2023       groesster Korb mit Rang >= 0,90 gegen die Nullwelt; Gleichstand +-1 Pp -> die einfachere (Reihenfolge der Liste)
  Urteil ab 2024  Korb > 0, Block-Bootstrap (Bloecke zu 3) >= 0,95, Rang >= 0,95, >= 20 ausgeloeste Faelle an >= 6 Stichtagen/Monaten;
                  zweiseitig: Korb < 0 und Bootstrap <= 0,05 -> SCHADET
  Selbsttest      (a) Zufalls-Kriterium 100 Welten, Fehlalarm <= 5 %; (b) gepflanzt: Verkauf am wahren Hoch -> muss tragen
  Auskunft        erst NACH dem Urteil: Dosis-Wirkung aller Stufen ab 2024, je Klasse, Jahre, Weglassprobe, netto, gegen BTC
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import a2_messung as A2     # noqa: E402
import as_messung as M      # noqa: E402
import ein_vorpruefung as EV  # noqa: E402
import mk_messung as MK     # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
RNG = np.random.default_rng(20261008)
NZ = 200
KO, KB = 0.0125, 0.004
L_STUFEN = ["Z1 x1,5", "Z1 x2", "Z1 x3", "Z3 +50 %", "Z3 +100 %", "Z4 1 s", "Z4 2 s", "Z4 3 s"]
K_STUFEN = ["w 15 %", "w 20 %", "w 25 %", "w 30 %", "w 35 %", "w 45 %", "k 1", "k 1,5", "k 2", "k 3", "Teil 1/2 bei +50 %"]


# ---------------------------------------------------------------- Werkzeuge
def marke(v, i0, w, max_t, bremse=0.5):
    """Nachlauf w vom Hoch seit Kauf, Notbremse bremse x Kauf, Verkauf am Folgetag; -> (Index Verkauf, Grund). Wie ein_vorpruefung.ausstieg."""
    k0, hoch = v[i0], v[i0]
    ende = min(i0 + max_t, len(v) - 1)
    j = i0
    while j < ende:
        j += 1
        if np.isnan(v[j]):
            return j - 1, "eingestellt"
        hoch = max(hoch, v[j])
        if v[j] < max((1 - w) * hoch, bremse * k0) and j + 1 <= len(v) - 1 and not np.isnan(v[j + 1]):
            return j + 1, "marke"
    if j - i0 < max_t:
        return None, "offen"
    return j, "ende"


def ende_halten(v, i0, max_t):
    ende = min(i0 + max_t, len(v) - 1)
    if ende - i0 < max_t:
        return None
    w = v[i0:ende + 1]
    ok = ~np.isnan(w)
    return i0 + (len(w) - 1 if ok.all() else int(np.argmin(ok)) - 1)


def boot(vals, n=2000):
    vals = np.asarray(vals)
    if len(vals) < 2:
        return float("nan")
    bs = []
    for _ in range(n):
        st = RNG.integers(0, max(len(vals) - 2, 1), size=int(np.ceil(len(vals) / 3)))
        bs.append(np.concatenate([vals[k:k + 3] for k in st])[:len(vals)].mean())
    return float(np.mean(np.array(bs) > 0))


def korb(df, spalte, gruppe):
    return df.groupby(gruppe)[spalte].mean()


# ---------------------------------------------------------------- Teil 0
def teil0():
    la = pd.read_csv(os.path.join("data", "_spot", "lage_e3_anker.csv"), sep=";", parse_dates=["t"])
    la = la[la.t >= "2024-01-01"]
    neu = []
    for r in la.itertuples():
        v = K[r.sym].values
        i0 = POS[r.t] + 1
        j, _ = marke(v, i0, 0.35, 180)
        neu.append(np.nan if j is None else (v[j] / v[i0]) / (BTCV[j] / BTCV[i0]) - 1)
    la["neu"] = neu
    aus, alle = la[la.hoch >= 1].neu.median(), la.neu.median()
    print("TEIL 0 (R-R11)\n  Lagebild L5 mit der Marke dieser Messung: Ausbrecher Median %+.1f %% (Soll +39,2) · alle %+.1f %% (Soll -23,9) · Abweichung zu x2-Spalte %d" % (
        100 * aus, 100 * alle, int((la.neu - la.x2).abs().gt(1e-9).sum())))
    Dw = M.paare(365).reset_index(drop=True)
    Zw = M.Zellen(Dw)
    V0 = M.pct_in_zelle(Zw, W.wert(Zw, M.merkmale(Dw))) > 0.8
    B = W.b5(Dw, V0, W.monatsrang())
    b2 = B[B.regel == "X2"]
    k0 = {e: b2[b2.ep == e].groupby("t").r.mean().mean() for e in ("E2", "E3")}
    gleich = sum(marke(K[r.sym].values, POS[r.t] + 1, 0.35, 365)[0] - (POS[r.t] + 1) == A2.ausstieg(A2.pfad(r.sym, POS[r.t] + 1, 365)[0], "X2")[0][0]
                 for r in b2.itertuples())
    print("  B5 X2 mit wl_messung.b5: E2 %+.1f %% · E3 %+.1f %% (Soll +31,8 / -4,0) · Ausstiegstag gleich an %d von %d" % (100 * k0["E2"], 100 * k0["E3"], gleich, len(b2)))
    ok = abs(100 * aus - 39.2) <= 1 and abs(100 * alle + 23.9) <= 1 and abs(100 * k0["E2"] - 31.8) <= 1 and abs(100 * k0["E3"] + 4.0) <= 1 and gleich == len(b2)
    return ok


# ---------------------------------------------------------------- Rolle L
def l_anker():
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    D["fuenftel"] = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D))) > 0.8
    D = D[(D.t >= "2023-01-01") & D.fuenftel & (D.sym != "BTC")].reset_index(drop=True)
    pf = []
    for r in D.itertuples():
        i = POS[r.t]
        v = K[r.sym].values
        p0 = v[i]
        x = v[i + 1:i + 1 + 365]
        b = BTCV[i + 1:i + 1 + 365] / BTCV[i]
        ok = ~np.isnan(x)
        if not ok.all():
            x, b = x[:np.argmin(ok)], b[:np.argmin(ok)]
        lr = np.diff(np.log(v[i - 90:i + 1]))
        sig = np.nanstd(lr) * np.sqrt(90)
        pf.append(dict(t=r.t, sym=r.sym, kl=r.kl, ep="W" if r.t.year == 2023 else "U", x=x / p0, b=b, sig=sig))
    return pf


def l_regel(a, stufe):
    x, b = a["x"], a["b"]
    if stufe.startswith("Z1"):
        hit = np.where(x >= {"Z1 x1,5": 1.5, "Z1 x2": 2, "Z1 x3": 3}[stufe])[0]
    elif stufe.startswith("Z3"):
        hit = np.where(x / b >= {"Z3 +50 %": 1.5, "Z3 +100 %": 2}[stufe])[0]
    else:
        hit = np.where(x >= np.exp({"Z4 1 s": 1, "Z4 2 s": 2, "Z4 3 s": 3}[stufe] * a["sig"]))[0]
    if not len(hit) or hit[0] + 1 >= len(x):
        return None
    return int(hit[0]) + 1                                      # Verkaufstag = Folgetag (Index in x)


def l_auswerten(pf, stufe, verkauf=None):
    """-> DataFrame je Anker: d, ausgeloest, Verkaufstag; verkauf: optionale Funktion(a) -> Tag (Selbsttest)."""
    z = []
    for a in pf:
        j = verkauf(a) if verkauf else l_regel(a, stufe)
        e = a["x"][-1]
        d = 0.5 * (a["x"][j] - e) if j is not None else 0.0
        rb = a["b"][-1]
        regel = (0.5 * a["x"][j] + 0.5 * e) if j is not None else e
        z.append(dict(t=a["t"], sym=a["sym"], kl=a["kl"], ep=a["ep"], d=d, aus=j is not None, tag=j if j is not None else -1,
                      gg_btc=regel / rb - 1, halten_btc=e / rb - 1, halten=e - 1, regel=regel - 1))
    return pd.DataFrame(z)


def l_null(pf, df, nz=NZ, gleicher_coin=False):
    """Haupt: zufaellige Positionen desselben Starttags (gleiche Zahl), Tag aus der Ausloese-Verteilung. Auskunft: gleicher Coin, zufaelliger Tag."""
    tage = df[df.aus].tag.values
    if not len(tage):
        return np.full(nz, np.nan)
    je_t = {}
    for k, a in enumerate(pf):
        je_t.setdefault(a["t"], []).append(k)
    n_aus = df[df.aus].groupby("t").size().to_dict()
    aus_idx = {t: list(df.index[(df.t == t) & df.aus]) for t in n_aus}
    out = []
    for _ in range(nz):
        m = []
        for t, ks in je_t.items():
            n = n_aus.get(t, 0)
            dd = np.zeros(len(ks))
            if n:
                wahl = aus_idx[t] if gleicher_coin else list(RNG.choice(ks, size=n, replace=False))
                for k in wahl:
                    x = pf[k]["x"]
                    tau = min(int(RNG.choice(tage)), len(x) - 1)
                    dd[ks.index(k)] = 0.5 * (x[tau] - x[-1])
            m.append(dd.mean())
        out.append(np.mean(m))
    return np.array(out)


# ---------------------------------------------------------------- Rolle K
def k_anker():
    out = []
    ende = len(IDX) - 1 - 181
    i_start = POS[pd.Timestamp("2023-01-01")]
    mon_kl = {}
    for t in pd.date_range("2023-01-01", M.ENDE, freq="MS"):
        if t in POS:
            mon_kl[t] = MK.klassen_mw(t)[0]
    for s in K.columns:
        if s in ("BTC", "ETH", "SOL"):
            continue
        v = K[s].values
        rel = v / BTCV
        sperre = -1
        for i in range(i_start, ende):
            if i <= sperre or not np.isfinite(rel[i]):
                continue
            mt = IDX[i].to_period("M").to_timestamp()
            kl = mon_kl.get(mt, {}).get(s)
            if kl is None:
                continue
            tief = np.nanmin(rel[i - 30:i + 1])
            if np.isfinite(tief) and tief > 0 and rel[i] >= 1.3 * tief:
                i0 = i + 1
                he = ende_halten(v, i0, 180)
                if he is None or np.isnan(v[i0]):
                    continue
                lr = np.diff(np.log(v[i - 30:i + 1]))
                out.append(dict(t=IDX[i], mon=mt, sym=s, kl=kl, ep="W" if IDX[i].year == 2023 else "U", i0=i0, he=he,
                                sig=np.nanstd(lr) * np.sqrt(30)))
                sperre = i + 30
    return out


def k_regel(a, stufe):
    v = K[a["sym"]].values
    i0 = a["i0"]
    if stufe.startswith("w"):
        j, _ = marke(v, i0, int(stufe.split()[1]) / 100, 180)
        return [(1.0, j)]
    if stufe.startswith("k"):
        w = min(0.9, float(stufe.split()[1].replace(",", ".")) * a["sig"])
        j, _ = marke(v, i0, w, 180)
        return [(1.0, j)]
    hit = np.where(v[i0 + 1:a["he"] + 1] >= 1.5 * v[i0])[0]                       # Teilverkauf
    j2, _ = marke(v, i0, 0.35, 180)
    if len(hit) and i0 + 1 + hit[0] + 1 <= a["he"] and (j2 is None or i0 + 1 + hit[0] + 1 <= j2):
        return [(0.5, i0 + 1 + int(hit[0]) + 1), (0.5, j2)]
    return [(1.0, j2)]


def k_wert(a, teile):
    v = K[a["sym"]].values
    i0 = a["i0"]
    return sum(f * v[j] / v[i0] for f, j in teile), sum(f * BTCV[j] / BTCV[i0] for f, j in teile)


def k_auswerten(ka, stufe, ausstieg=None):
    z = []
    for a in ka:
        teile = ausstieg(a) if ausstieg else k_regel(a, stufe)
        if any(j is None for _, j in teile):
            continue
        v = K[a["sym"]].values
        regel, rb = k_wert(a, teile)
        halten = v[a["he"]] / v[a["i0"]]
        dauer = max(j for _, j in teile) - a["i0"]
        z.append(dict(t=a["t"], mon=a["mon"], sym=a["sym"], kl=a["kl"], ep=a["ep"], d=regel - halten, dauer=dauer,
                      regel=regel - 1, halten=halten - 1, gg_btc=regel / rb - 1,
                      netto=(regel * (1 - KO) / (1 + KO)) - (halten * (1 - KO) / (1 + KO))))
    return pd.DataFrame(z)


def k_null(ka, df, nz=NZ):
    dauern = df.dauer.values
    pos = {(a["t"], a["sym"]): a for a in ka}
    zeilen = [pos[(r.t, r.sym)] for r in df.itertuples()]
    mon = df.mon.values
    out = []
    for _ in range(nz):
        dd = []
        for a in zeilen:
            v = K[a["sym"]].values
            j = min(a["i0"] + int(RNG.choice(dauern)), a["he"])
            dd.append(v[j] / v[a["i0"]] - v[a["he"]] / v[a["i0"]])
        out.append(pd.Series(dd).groupby(mon).mean().mean())
    return np.array(out)


# ---------------------------------------------------------------- Urteil
def wahl(erg):
    """erg: {stufe: (korb, rang)} in Listenreihenfolge -> gewaehlte Stufe oder None."""
    gueltig = [(s, k) for s, (k, r) in erg.items() if r >= 0.90 and np.isfinite(k)]
    if not gueltig:
        return None
    best = max(k for _, k in gueltig)
    return next(s for s, k in gueltig if k >= best - 0.01)


def urteil(je, null, n_faelle, n_stich):
    k = je.mean()
    b = boot(je.sort_index().values)
    rang = float(np.mean(null < k))
    if n_faelle < 20 or n_stich < 6:
        return "NICHT ENTSCHEIDBAR", k, b, rang
    if k > 0 and b >= 0.95 and rang >= 0.95:
        return "TRAEGT", k, b, rang
    if k < 0 and b <= 0.05:
        return "SCHADET", k, b, rang
    return "TRAEGT NICHT", k, b, rang


def main():
    print("MESSUNG Teil B (§31.3) · Kurse bis %s\n" % M.ENDE.date())
    if not teil0():
        print("REPRODUKTION FEHLGESCHLAGEN - Abbruch"); return

    # ------------------------------------------------ Rolle L
    pf = l_anker()
    pW = [a for a in pf if a["ep"] == "W"]
    pU = [a for a in pf if a["ep"] == "U"]
    print("\nROLLE L - Teilmitnahme 50 %% (L-Kandidaten: 2023 %d an %d Starttagen · ab 2024 %d an %d)" % (
        len(pW), len({a["t"] for a in pW}), len(pU), len({a["t"] for a in pU})))
    erg = {}
    print("  WAHL 2023 (Korb = Mittel ueber Starttage von d = Regel - Halten; Rang gegen Haupt-Nullwelt):")
    for s in L_STUFEN:
        df = l_auswerten(pW, s)
        je = korb(df, "d", "t")
        null = l_null(pW, df)
        erg[s] = (je.mean(), float(np.mean(null < je.mean())))
        print("    %-10s ausgeloest %3.0f %% · Korb %+6.2f Pp · Rang %.2f" % (s, 100 * df.aus.mean(), 100 * je.mean(), erg[s][1]))
    gew = wahl(erg)
    print("  -> GEWAEHLT (vorab-Regel): %s" % (gew or "keine Stufe mit Rang >= 0,90 -> L ohne Mitnahme-Regel"))
    l_urteil = None
    if gew:
        df = l_auswerten(pU, gew)
        je = korb(df, "d", "t")
        null = l_null(pU, df)
        l_urteil = urteil(je, null, int(df.aus.sum()), df[df.aus].t.nunique())
        nullc = l_null(pU, df, nz=100, gleicher_coin=True)
        print("  URTEIL ab 2024 %s: ausgeloest %d an %d Starttagen · Korb %+.2f Pp · Bootstrap %.2f · Rang %.2f  ->  %s" % (
            gew, int(df.aus.sum()), df[df.aus].t.nunique(), 100 * l_urteil[1], l_urteil[2], l_urteil[3], l_urteil[0]))
        print("    Auskunft Nullwelt 'gleicher Coin, zufaelliger Tag' (trivial): Rang %.2f" % np.mean(nullc < l_urteil[1]))
        # Selbsttest
        fehl = 0
        for _ in range(100):
            zt = l_auswerten(pU, gew, verkauf=lambda a: (int(RNG.integers(1, len(a["x"]))) if RNG.random() < df.aus.mean() and len(a["x"]) > 1 else None))
            jz = korb(zt, "d", "t")
            nz_ = l_null(pU, zt, nz=50)
            fehl += (jz.mean() > 0 and boot(jz.sort_index().values, 300) >= 0.95 and np.mean(nz_ < jz.mean()) >= 0.95)
        pg = l_auswerten(pU, gew, verkauf=lambda a: int(np.argmax(a["x"])) if len(a["x"]) > 1 else None)
        jg = korb(pg, "d", "t")
        ng = l_null(pU, pg, nz=50)
        print("  SELBSTTEST (a) Zufalls-Kriterium 100 Welten: Fehlalarm %d %% -> %s · (b) gepflanzt (Verkauf am Hoch): Korb %+.1f Pp, Rang %.2f -> %s" % (
            fehl, "bestanden" if fehl <= 5 else "NICHT bestanden", 100 * jg.mean(), np.mean(ng < jg.mean()), "erkannt" if (jg.mean() > 0 and np.mean(ng < jg.mean()) >= 0.95) else "NICHT erkannt"))
        print("  AUSKUNFT (nach dem Urteil) %s ab 2024: je Klasse %s · je Jahr %s" % (gew, " · ".join("%s %+.1f Pp" % (k, 100 * korb(g, "d", "t").mean()) for k, g in df.groupby("kl")),
              " · ".join("%d %+.1f Pp" % (j, 100 * korb(g, "d", "t").mean()) for j, g in df.groupby(df.t.dt.year))))
        top = df.sort_values("d", ascending=False).sym.head(5).tolist()
        print("    Weglassprobe ohne %s: Korb %+.2f Pp · gegen BTC Median: Regel %+.1f %% / Halten %+.1f %%" % (
            ",".join(top), 100 * korb(df[~df.sym.isin(top)], "d", "t").mean(), 100 * df.gg_btc.median(), 100 * df.halten_btc.median()))
        df.to_csv(os.path.join("data", "_spot", "fb_messung_l.csv"), sep=";", index=False)
    print("  DOSIS ab 2024 (alle Stufen, Auskunft, nach dem Urteil): %s" % " · ".join(
        "%s %+.1f" % (s, 100 * korb(l_auswerten(pU, s), "d", "t").mean()) for s in L_STUFEN))

    # ------------------------------------------------ Rolle K
    ka = k_anker()
    kW = [a for a in ka if a["ep"] == "W"]
    kU = [a for a in ka if a["ep"] == "U"]
    print("\nROLLE K - Nachlauf (Stellvertreter-Einstieg: 2023 %d in %d Monaten · ab 2024 %d in %d)" % (
        len(kW), len({a["mon"] for a in kW}), len(kU), len({a["mon"] for a in kU})))
    erg = {}
    print("  WAHL 2023 (Korb = Mittel ueber Monate von d = Regel - Halten 180 T):")
    for s in K_STUFEN:
        df = k_auswerten(kW, s)
        je = korb(df, "d", "mon")
        null = k_null(kW, df)
        erg[s] = (je.mean(), float(np.mean(null < je.mean())))
        print("    %-18s n %4d · Korb %+6.2f Pp · Haltedauer Median %3d T · Rang %.2f" % (s, len(df), 100 * je.mean(), int(df.dauer.median()), erg[s][1]))
    gew = wahl(erg)
    print("  -> GEWAEHLT (vorab-Regel): %s" % (gew or "keine"))
    if gew:
        df = k_auswerten(kU, gew)
        je = korb(df, "d", "mon")
        null = k_null(kU, df)
        u = urteil(je, null, len(df), df.mon.nunique())
        print("  URTEIL ab 2024 %s: n %d in %d Monaten · Korb %+.2f Pp · Bootstrap %.2f · Rang %.2f  ->  %s" % (gew, len(df), df.mon.nunique(), 100 * u[1], u[2], u[3], u[0]))
        fehl = 0
        dauern = df.dauer.values
        for _ in range(100):
            zt = k_auswerten(kU, gew, ausstieg=lambda a: [(1.0, min(a["i0"] + int(RNG.choice(dauern)), a["he"]))])
            jz = korb(zt, "d", "mon")
            nz_ = k_null(kU, zt, nz=30)
            fehl += (jz.mean() > 0 and boot(jz.sort_index().values, 300) >= 0.95 and np.mean(nz_ < jz.mean()) >= 0.95)
        pg = k_auswerten(kU, gew, ausstieg=lambda a: [(1.0, a["i0"] + int(np.nanargmax(K[a["sym"]].values[a["i0"]:a["he"] + 1])))])
        jg = korb(pg, "d", "mon")
        ng = k_null(kU, pg, nz=30)
        print("  SELBSTTEST (a) Zufalls-Ausstieg 100 Welten: Fehlalarm %d %% -> %s · (b) gepflanzt (Ausstieg am Hoch): Korb %+.1f Pp, Rang %.2f -> %s" % (
            fehl, "bestanden" if fehl <= 5 else "NICHT bestanden", 100 * jg.mean(), np.mean(ng < jg.mean()), "erkannt" if (jg.mean() > 0 and np.mean(ng < jg.mean()) >= 0.95) else "NICHT erkannt"))
        print("  AUSKUNFT (nach dem Urteil) %s ab 2024: je Klasse %s · je Jahr %s · netto %+.1f Pp · Regel gegen BTC Median %+.1f %% / Halten %+.1f %% (absolut)" % (
            gew, " · ".join("%s %+.1f" % (k, 100 * korb(g, "d", "mon").mean()) for k, g in df.groupby("kl")),
            " · ".join("%d %+.1f" % (j, 100 * korb(g, "d", "mon").mean()) for j, g in df.groupby(df.t.dt.year)),
            100 * korb(df, "netto", "mon").mean(), 100 * df.gg_btc.median(), 100 * df.halten.median()))
        top = df.sort_values("d", ascending=False).sym.head(5).tolist()
        print("    Weglassprobe ohne %s: Korb %+.2f Pp" % (",".join(top), 100 * korb(df[~df.sym.isin(top)], "d", "mon").mean()))
        df.to_csv(os.path.join("data", "_spot", "fb_messung_k.csv"), sep=";", index=False)
    print("  DOSIS ab 2024 (alle Stufen, Auskunft, nach dem Urteil): %s" % " · ".join(
        "%s %+.1f" % (s, 100 * korb(k_auswerten(kU, s), "d", "mon").mean()) for s in K_STUFEN))


if __name__ == "__main__":
    main()
