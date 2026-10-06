"""Erster Wurf Watchlist (Voranalyse_Spot_Neubau_04_10.md §21, vorab Commits 417b423 und e2b887c) - B1 Ausschluss, B2 Bestaetigung/Laenge, B5 Ausstieg.

    python Basisinfos/Spot_Voranalyse_04_10/wl_messung.py

Nur lesend (mode=ro); der Bitpanda-Ticker wird oeffentlich gelesen (nur Auskunft). V0 = oberstes Fuenftel der Kombination F1 unten, F2 oben,
F8 oben, F9 oben (§19.6). Zelle = (Stichtag, Klasse).

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - B1/B2 Statistik je Zelle: (Anteil R2 - Anteil L) der behaltenen Liste minus derselbe Wert von V0; Stichtag = nach Zellgroesse gewichtet;
    Epoche = Mittel der Stichtage. Nullwelt: gleich viele zufaellig aus V0 behalten. Zellen, in denen die Regel nichts aendert, zaehlen mit 0
  - Bestaetigung (V1/V2): Mitgliedschaft im Vormonat aus der Monatsrechnung ALLER Coins (auch ohne Ausgang); Klasse jeweils des Monats
  - K5/K10: die besten k nach Gesamtwert in der Zelle (nur M und S); hat V0 in der Zelle <= k Coins, aendert sich nichts
  - B5: Kurs ab Schluss t+1, hoechstens 365 T; X1/X2 wie a2_messung.ausstieg (x2/x3, Nachlauf 0,65, Notbremse 0,5); X7 prueft an den
    Monatsersten t+1M..t+11M, Verkauf am Folgetag zum Schluss; Korb = Mittel der Ertraege nach Kosten je Stichtag (alle Klassen)
  - B5 Zufallswelt gleicher Haltedauer: die Haltedauern (Tage bis zum letzten Verkauf; bei Teilverkaeufen der gewichtete Mittelwert) der Regel
    werden innerhalb der Epoche zufaellig auf die Einstiege verteilt, Verkauf dann ganz an diesem Tag
"""
import math
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402

A = M.A
K, IDX, POS, ENDE = M.K, M.IDX, M.POS, M.ENDE
RNG = np.random.default_rng(20261013)
NZ = 200
KO, KB = A.KO_COIN, A.KO_BTC
WAHL = [("F1", "unten"), ("F2", "oben"), ("F8", "oben"), ("F9", "oben")]


def wert(Z, F, wahl=WAHL, ersatz=None):
    F = dict(F, **(ersatz or {}))
    P = np.vstack([M.pct_in_zelle(Z, F[k]) if s == "oben" else 1 - M.pct_in_zelle(Z, F[k]) for k, s in wahl])
    with np.errstate(all="ignore"):
        return np.where(np.isnan(P).all(axis=0), np.nan, np.nanmean(P, axis=0))


class Leicht:
    """Zellen ohne Ausgang (fuer die Monatsrechnung aller Coins)."""
    def __init__(self, D):
        self.D = D
        self.gruppen = [(t, k, np.array(ix)) for (t, k), ix in D.groupby(["t", "kl"]).groups.items()]


def monatsrang():
    zeilen = []
    for t in pd.date_range("2019-01-01", ENDE, freq="MS"):
        if t not in POS:
            continue
        for s, k in A.klassen(t)[0].items():
            if not np.isnan(K[s].values[POS[t]]):
                zeilen.append(dict(t=t, sym=s, kl=k))
    Dall = pd.DataFrame(zeilen)
    F = M.merkmale(Dall)
    Zl = Leicht(Dall)
    w = wert(Zl, F)
    p = M.pct_in_zelle(Zl, w)
    Dall["wert"], Dall["p"] = w, p
    return Dall.set_index(["t", "sym"])


# ---------------------------------------------------------------- B1 / B2
def vergleich(Z, behalte, V0):
    """Saldo-Differenz (behaltene Liste minus V0) je Epoche mit Nullwelt 'gleich viele zufaellig aus V0'."""
    out = {}
    for ep in ("E2", "E3"):
        dv, dn, nul, ent, n_v0 = {}, {}, {}, 0, 0
        r2k = lk = r2v = lv = 0.0; nk = nv = 0
        for t, k, ix in Z.gruppen:
            if Z.ep[t] != ep:
                continue
            q = ix[V0[ix]]
            if len(q) == 0:
                continue
            kb = q[behalte[q]]
            n = len(ix)
            n_v0 += len(q); ent += len(q) - len(kb)
            r2v += Z.r2[q].sum(); lv += Z.l[q].sum(); nv += len(q)
            if len(kb):
                r2k += Z.r2[kb].sum(); lk += Z.l[kb].sum(); nk += len(kb)
            v = (Z.a[kb].mean() - Z.a[q].mean()) if 0 < len(kb) < len(q) else 0.0
            dv[t] = dv.get(t, 0) + v * n; dn[t] = dn.get(t, 0) + n
            if 0 < len(kb) < len(q):
                zz = RNG.random((NZ, len(q))).argsort(axis=1)[:, :len(kb)]
                nv_ = Z.a[q][zz].mean(axis=1) - Z.a[q].mean()
            else:
                nv_ = np.zeros(NZ)
            nul.setdefault(t, []).append(nv_ * n)
        tage = sorted(dn)
        echt = np.mean([dv[t] / dn[t] for t in tage])
        nw = np.mean([np.sum(nul[t], axis=0) / dn[t] for t in tage], axis=0)
        out[ep] = dict(diff=echt, rang=float(np.mean(nw < echt)), entfernt=ent / max(n_v0, 1), r2k=r2k / max(nk, 1), lk=lk / max(nk, 1),
                       r2v=r2v / max(nv, 1), lv=lv / max(nv, 1), je_monat=nk / len(tage))
    return out


def traegt(o):
    return all(o[e]["diff"] > 0 and o[e]["rang"] >= 0.95 for e in ("E2", "E3"))


def zeige(name, o):
    print("  %-44s %s  ->  %s" % (name, " | ".join("%s %+5.1f Pp Rang %.2f · entfernt %3.0f %% · bleiben %4.1f je Monat · verdoppelt %4.1f %% (V0 %4.1f) · Absturz/eing. %4.1f %% (V0 %4.1f)" % (
        e, 100 * o[e]["diff"], o[e]["rang"], 100 * o[e]["entfernt"], o[e]["je_monat"], 100 * o[e]["r2k"], 100 * o[e]["r2v"], 100 * o[e]["lk"], 100 * o[e]["lv"])
        for e in ("E2", "E3")), "TRAEGT" if traegt(o) else "traegt nicht"))


# ---------------------------------------------------------------- B5
def ertrag(v, b, vk):
    c = sum(a * v[t] / v[0] * (1 - KO) for t, a in vk) / (1 + KO) - 1
    bb = sum(a * b[t] / b[0] * (1 - KB) for t, a in vk) / (1 + KB) - 1
    dauer = sum(a * t for t, a in vk)
    return c, bb, dauer


def ausstiege(t, s, RANG):
    i0 = POS[t] + 1
    v, b = A.pfad(s, i0, 365)
    if v is None or len(v) < 2:
        return None
    n = len(v) - 1
    out = {"X0": [(n, 1.0)], "X1": A.ausstieg(v, "X1"), "X2": A.ausstieg(v, "X2")}
    for name, grenze in (("X7a", 0.5), ("X7b", 0.8)):
        tag = n
        for m in range(1, 12):
            tm = t + pd.DateOffset(months=m)
            if tm not in POS or POS[tm] + 1 - i0 > n:
                break
            try:
                p = RANG.at[(tm, s), "p"]
            except KeyError:
                p = np.nan
            if not np.isnan(p) and p <= grenze:
                tag = POS[tm] + 1 - i0; break
        out[name] = [(min(tag, n), 1.0)]
    zm = int(RNG.integers(1, 13))
    out["Zufall"] = [(min(int(round(zm * 30.4)), n), 1.0)]
    return v, b, out


def b5(D, V0, RANG):
    zeilen = []
    for j in np.where(V0)[0]:
        t, s = D.t[j], D.sym[j]
        r = ausstiege(t, s, RANG)
        if r is None:
            continue
        v, b, out = r
        for name, vk in out.items():
            c, bb, dauer = ertrag(v, b, vk)
            zeilen.append(dict(t=t, sym=s, ep=D.ep[j], kl=D.kl[j], regel=name, r=c, rb=bb, dauer=dauer, real2=max(v[x] / v[0] for x, _ in vk) >= 2,
                               real_l=min(v[x] / v[0] for x, _ in vk) <= 0.3))
        zeilen[-1]["_pfad"] = (v, b)
    return pd.DataFrame(zeilen)


def b5_auswertung(B, PF):
    x0 = B[B.regel == "X0"].set_index(["t", "sym"])
    print("\nB5 FUEHRUNG UND AUSSTIEG (Korb je Stichtag, nach Kosten; gepaart gegen X0; Zufallswelt gleicher Haltedauer)")
    for regel in ("X0", "X1", "X2", "X7a", "X7b", "Zufall"):
        x = B[B.regel == regel].set_index(["t", "sym"])
        ok = True; teile = []
        for ep in ("E2", "E3"):
            xe = x[x.ep == ep]
            d = (xe.r - x0.loc[xe.index].r)
            je_t = d.groupby(level=0).mean()
            tage = je_t.index.sort_values()
            vals = je_t.loc[tage].values
            bs = []
            for _ in range(1000):
                st = RNG.integers(0, max(len(vals) - 2, 1), size=math.ceil(len(vals) / 3))
                bs.append(np.concatenate([vals[k:k + 3] for k in st])[:len(vals)].mean())
            boot = float(np.mean(np.array(bs) > 0))
            # Zufallswelt gleicher Haltedauer
            dauern = xe.dauer.values
            nul = []
            for _ in range(NZ):
                perm = RNG.permutation(dauern)
                rr = []
                for (t, s), dd in zip(xe.index, perm):
                    v, b = PF[(t, s)]
                    tt = int(min(round(dd), len(v) - 1))
                    rr.append(((t, s), ertrag(v, b, [(tt, 1.0)])[0]))
                z = pd.Series(dict(rr))
                nul.append((z - x0.loc[z.index].r).groupby(level=0).mean().mean())
            rang = float(np.mean(np.array(nul) < je_t.mean())) if regel != "X0" else float("nan")
            korb = xe.r.groupby(level=0).mean().mean(); korb_b = xe.rb.groupby(level=0).mean().mean()
            e_ok = je_t.mean() > 0 and je_t.median() > 0 and boot >= 0.95 and rang >= 0.95
            ok &= e_ok
            teile.append("%s Korb %+5.1f %% (BTC %+5.1f %%) · gg. X0 Mittel %+5.1f / Median %+5.1f Pp · Bootstrap %.2f · gleiche Dauer Rang %s · Halten %3.0f T · realisiert >=x2 %3.0f %% · <=-70 %% %3.0f %%" % (
                ep, 100 * korb, 100 * korb_b, 100 * je_t.mean(), 100 * je_t.median(), boot, "%.2f" % rang if regel != "X0" else "-", xe.dauer.mean(),
                100 * xe.real2.mean(), 100 * xe.real_l.mean()))
        print("  %-7s %s  ->  %s" % (regel, "\n          ".join(teile), "TRAEGT" if (ok and regel not in ("X0",)) else "traegt nicht" if regel != "X0" else "Bezug"))


def main():
    D = M.paare(365).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    w = wert(Z, F)
    p = M.pct_in_zelle(Z, w)
    V0 = p > 0.8
    print("Erster Wurf Watchlist (§21) · %d Coin-Anker · V0 = oberstes Fuenftel der Kombination · %d Mitglieder\n" % (len(D), V0.sum()))
    RANG = monatsrang()
    print("Monatsrechnung aller Coins: %d Zeilen, %s bis %s" % (len(RANG), RANG.index.get_level_values(0).min().date(), RANG.index.get_level_values(0).max().date()))

    # ---- B1
    print("\nB1 ASSETLISTE - Ausschlussregeln (Liste nach Ausschluss minus V0; Nullwelt gleich viele zufaellig entfernt)")
    sprung = (M.ret.abs() > 4) | (M.ret < -0.8)
    sprung_bis = sprung.cumsum() > 0
    u90 = np.array([M.U90.at[t, s] if s in M.U90.columns else np.nan for t, s in zip(D.t, D.sym)])
    u_dez = np.zeros(len(D), bool)
    for _, _, ix in Z.gruppen:
        x = u90[ix]
        if np.isfinite(x).sum() >= 10:
            u_dez[ix] = x <= np.nanpercentile(x, 10)
    regeln = {
        "XA Restwert (Kurs <= 1 % des Allzeithochs)": ~(F["F1"] <= -0.99),
        "XB Umsatzschwund (90 T < 20 % von 365 T)": ~(F["F7"] < 0.2),
        "XC Mindestumsatz (unterstes Zehntel der Klasse)": ~u_dez,
        "XD Datenfehler (Tagessprung > Faktor 5 bis t)": ~np.array([bool(sprung_bis.at[t, s]) for t, s in zip(D.t, D.sym)]),
    }
    for name, keep in regeln.items():
        zeige(name, vergleich(Z, keep, V0))
    alle = np.logical_and.reduce(list(regeln.values()))
    zeige("Auskunft: alle vier zusammen", vergleich(Z, alle, V0))
    # Auskunft Allzeithoch ab Tag 31
    X = M.X
    cm2 = X.where(M.NGESCH > 30).cummax()
    ar2 = pd.DataFrame(np.where(X.notna() & (X == cm2), np.arange(len(X))[:, None], np.nan), index=X.index, columns=X.columns).ffill()
    f1b, f2b = F["F1"].copy(), F["F2"].copy()
    for j, (t, s) in enumerate(zip(D.t, D.sym)):
        if not np.isnan(F["F1"][j]):
            i, k = POS[t], X.columns.get_loc(s)
            f1b[j] = X.iat[i, k] / cm2.iat[i, k] - 1 if cm2.iat[i, k] > 0 else np.nan
            f2b[j] = i - ar2.iat[i, k]
    pb = M.pct_in_zelle(Z, wert(Z, F, ersatz={"F1": f1b, "F2": f2b}))
    for e in ("E2", "E3"):
        o0 = M.bewerte(Z, w, "oben", null=False, ep_liste=(e,))[e]
        ob = M.bewerte(Z, np.where(np.isnan(pb), np.nan, pb), "oben", null=False, ep_liste=(e,))[e]
        print("  Auskunft Allzeithoch ab dem 31. Tag, %s: Saldo gg. Klasse %+5.1f Pp (V0 %+5.1f) · Ueberschneidung mit V0 %3.0f %%" % (
            e, 100 * ob["saldo"], 100 * o0["saldo"], 100 * np.mean(V0[(pb > 0.8) & (D.ep.values == e)])))
    try:
        import requests
        bp = set(requests.get("https://api.bitpanda.com/v1/ticker", timeout=30).json().keys())
        letzt = RANG.index.get_level_values(0).max()
        heute = RANG.loc[letzt]
        mit = heute[heute.p > 0.8]
        print("  Auskunft Bitpanda (heute, Ticker): von %d Coins der aktuellen Liste (%s) sind %d bei Bitpanda gelistet" % (len(mit), letzt.date(), sum(s in bp for s in mit.index)))
    except Exception as ex:                                       # noqa: BLE001
        print("  Auskunft Bitpanda nicht abrufbar: %s" % ex)

    # ---- B2
    print("\nB2 WATCHLIST - Bestaetigung und Laenge (Liste minus V0; Nullwelt gleich viele zufaellig aus V0)")
    def im(t, s, versatz):
        tm = t - pd.DateOffset(months=versatz)
        try:
            return RANG.at[(tm, s), "p"] > 0.8
        except KeyError:
            return False
    v1 = np.array([im(t, s, 1) for t, s in zip(D.t, D.sym)])
    v2 = v1 & np.array([im(t, s, 2) for t, s in zip(D.t, D.sym)])
    zeige("V1 bestaetigt (auch im Vormonat)", vergleich(Z, v1, V0))
    zeige("V2 bestaetigt (auch t-1 und t-2)", vergleich(Z, v2, V0))
    for k in (5, 10):
        keep = np.zeros(len(D), bool)
        for _, kl, ix in Z.gruppen:
            q = ix[V0[ix]]
            if kl == "H" or len(q) <= k:
                keep[q] = True; continue
            keep[q[np.argsort(-w[q])[:k]]] = True
        zeige("K%d nur die besten %d je Klasse (M, S)" % (k, k), vergleich(Z, keep, V0))

    # ---- B5
    B = b5(D, V0, RANG)
    PF = {}
    for j in np.where(V0)[0]:
        t, s = D.t[j], D.sym[j]
        v, b = A.pfad(s, POS[t] + 1, 365)
        if v is not None and len(v) >= 2:
            PF[(t, s)] = (v, b)
    B = B.drop(columns=["_pfad"], errors="ignore")
    b5_auswertung(B, PF)


if __name__ == "__main__":
    main()
