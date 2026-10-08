"""MESSUNG C2 - Boersen-Ankuendigungen als Ausloeser (Spot §38.2, vorab Commit 28e6cb0) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/c2_messung.py

C2-a Binance Futures-Start · C2-b Upbit-Listing (KRW) · C2-c Binance Spot-Listing (Auskunft). Einstieg Schluss der Stunde, die 4 h nach
der Meldung beginnt; Ausstieg nach 168 h; gegen BTC brutto; Korb je Monat; Bonferroni 0,975; Nullwelt zufaellige Coins derselben Klasse
zur selben Stunde (200); Spiegel (+/-15 % in 7 T); Mindestzahl; Selbsttest; Kosten getrennt. Urteil ab 2024, 2023 Auskunft.
"""
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402

RNG = np.random.default_rng(20261038)
T0 = pd.Timestamp("2023-01-01")
KOSTEN = {"H": 0.0072, "M": 0.0176, "S": 0.064, "U": 0.064}
SCHWELLE = 0.975
VERZUG, HALTE = 4, 168
KERN = ("BTC", "ETH", "SOL")
WORT = {"USD", "USDⓈ", "M", "MARGINED", "BUSD", "COIN", "MULTIPLE", "TRADFI", "AND", "PERPETUAL", "CONTRACT", "CONTRACTS", "QUARTERLY", "UP", "TO",
        "WITH", "LEVERAGE", "THE", "OF", "FOR", "ON", "IN", "X", "PRE", "MARKET", "BINANCE", "FUTURES", "WILL", "LAUNCH"}
MARKT = {"KRW", "BTC", "USDT"}


def ohne_vorsatz(s):
    return re.sub(r"^(1000000|1000|1M)(?=[A-Z])", "", s)


def ereignisse():
    c = sqlite3.connect("file:data/_c2/ankuendigungen.db?mode=ro", uri=True)
    z = []
    for titel, ms in c.execute("select titel, release_ms from binance"):
        t = pd.Timestamp(datetime.fromtimestamp(ms / 1000, timezone.utc).replace(tzinfo=None))
        if re.search(r"Futures Will Launch", titel, re.I) and "Perpetual" in titel and "Multiple" not in titel:
            teil = titel.split("Launch", 1)[1].split("Perpetual")[0]
            for tok in re.findall(r"\b[A-Z0-9]{2,15}\b", teil.replace("USDⓈ-M", " ").replace("-Margined", " ")):
                if tok in WORT:
                    continue
                s = ohne_vorsatz(re.sub(r"(USDT|USDC|BUSD)$", "", tok))
                if s and s not in WORT and not s.isdigit():
                    z.append(("C2-a Futures-Start", s, t, titel))
        m = re.match(r"Binance Will List .*?\(([A-Z0-9]{2,15})\)", titel)
        if m:
            z.append(("C2-c Spot-Listing", ohne_vorsatz(m.group(1)), t, titel))
    for titel, utc in c.execute("select titel, utc from upbit"):
        if "신규 거래지원" in titel and "KRW" in titel:
            t = pd.Timestamp(utc)
            for s in re.findall(r"\(([A-Z0-9]{2,15})\)", titel.split("신규 거래지원")[0]):
                if s not in MARKT:
                    z.append(("C2-b Upbit-Listing", s, t, titel))
    E = pd.DataFrame(z, columns=["art", "sym", "zeit", "titel"]).sort_values("zeit")
    E = E[E.zeit >= T0]
    # je Art und Coin nur die ERSTE Meldung binnen 30 T (Folgemeldungen: Startzeit, Verschiebung)
    keep, letzte = [], {}
    for r in E.itertuples():
        k = (r.art, r.sym)
        if k in letzte and (r.zeit - letzte[k]).days < 30:
            continue
        letzte[k] = r.zeit
        keep.append(r.Index)
    return E.loc[keep].reset_index(drop=True)


def stundenreihen(syms):
    n = int((pd.Timestamp(M.ENDE) + pd.Timedelta(days=15) - T0) / pd.Timedelta(hours=1)) + 1
    P = {}
    for db in ("data/stundenkurse.db", "data/stundenkurse_alle.db"):
        c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        for s in syms:
            if s in P:
                continue
            rows = c.execute("select stunde, close from stundenkurse where symbol=? and stunde >= '2023-01-01'", (s,)).fetchall()
            if not rows:
                continue
            a = np.full(n, np.nan, dtype=np.float64)
            for st, cl in rows:
                h = int((pd.Timestamp(st) - T0) / pd.Timedelta(hours=1))
                if 0 <= h < n and cl:
                    a[h] = cl
            P[s] = a
    return P


def letzter(a, h0, h1):
    w = a[h0:h1 + 1]
    ok = np.where(~np.isnan(w))[0]
    return a[h0 + ok[-1]] if len(ok) else np.nan


def ex(P, s, he, hx):
    if s not in P or np.isnan(P[s][he]) or np.isnan(P["BTC"][he]) or np.isnan(P["BTC"][hx]):
        return np.nan
    return (letzter(P[s], he, hx) / P[s][he]) / (P["BTC"][hx] / P["BTC"][he]) - 1


def pfad(P, s, he, hx):
    a = P[s][he:hx + 1] / P[s][he]
    b = P["BTC"][he:hx + 1] / P["BTC"][he]
    r = a / b
    return np.nanmax(r) >= 1.15, np.nanmin(r) <= 1 / 1.15


def klasse_am(t, s):
    m = t.to_period("M").to_timestamp()
    if m not in M.POS:
        return "U"
    return MK.klassen_mw(m)[0].get(s, "U")


def boot(vals, n=2000):
    vals = np.asarray(vals)
    if len(vals) < 2:
        return float("nan")
    bs = [np.concatenate([vals[k:k + 3] for k in RNG.integers(0, max(len(vals) - 2, 1), size=int(np.ceil(len(vals) / 3)))])[:len(vals)].mean() for _ in range(n)]
    return float(np.mean(np.array(bs) > 0))


def aufbauen(E, P, verzug=VERZUG, halte=HALTE):
    z = []
    for r in E.itertuples():
        h_rel = int((r.zeit - T0) / pd.Timedelta(hours=1))
        he = h_rel + verzug
        hx = he + halte
        if r.sym in KERN or r.sym not in P or hx >= len(P["BTC"]):
            continue
        a = P[r.sym]
        if np.isnan(a[he]) or (r.art != "C2-c Spot-Listing" and np.isnan(np.nanmin(a[max(he - 90 * 24, 0):he - 89 * 24]) if he - 90 * 24 >= 0 else True)):
            continue
        e = ex(P, r.sym, he, hx)
        if np.isnan(e):
            continue
        l, ab = pfad(P, r.sym, he, hx)
        vor = a[h_rel - 1] if h_rel >= 1 else np.nan
        verp = (a[he] / vor) / (P["BTC"][he] / P["BTC"][h_rel - 1]) - 1 if vor == vor and vor and not np.isnan(P["BTC"][h_rel - 1]) else np.nan
        z.append(dict(art=r.art, sym=r.sym, zeit=r.zeit, he=he, hx=hx, ex=e, lauf=l, absturz=ab, verpasst=verp, kl=klasse_am(r.zeit, r.sym)))
    return pd.DataFrame(z)


def kandidaten(D, P):
    out = {}
    for r in D.itertuples():
        m = r.zeit.to_period("M").to_timestamp()
        kl = MK.klassen_mw(m)[0] if m in M.POS else {}
        k = r.kl if r.kl != "U" else "S"
        out[r.Index] = [s for s, kk in kl.items() if kk == k and s != r.sym and s in P and s not in KERN
                        and not np.isnan(P[s][r.he]) and not np.isnan(P[s][r.hx])]
    return out


def urteil(D, P, kand, nz=200):
    D = D.copy()
    D["mon"] = D.zeit.dt.to_period("M")
    jk = D.groupby("mon").ex.mean().sort_index()
    b = boot(jk.values)
    vor = {i: np.array([ex(P, s, D.at[i, "he"], D.at[i, "hx"]) for s in kand[i]]) for i in D.index}
    nl = []
    for _ in range(nz):
        w = {}
        for i in D.index:
            v = vor[i]
            if len(v):
                w.setdefault(D.at[i, "mon"], []).append(RNG.choice(v))
        nl.append(np.mean([np.mean(x) for x in w.values()]))
    nl = np.array(nl)
    rang = float(np.mean(nl < jk.mean()))
    la_n = np.mean([np.mean([pfad(P, s, D.at[i, "he"], D.at[i, "hx"])[0] for s in kand[i]]) for i in D.index if kand[i]])
    ab_n = np.mean([np.mean([pfad(P, s, D.at[i, "he"], D.at[i, "hx"])[1] for s in kand[i]]) for i in D.index if kand[i]])
    sp = (D.lauf.mean() / max(D.absturz.mean(), 1e-9)) / (la_n / max(ab_n, 1e-9))
    genug = len(D) >= 20 and D.mon.nunique() >= 6
    if not genug:
        u = "NICHT ENTSCHEIDBAR"
    elif jk.mean() > 0 and b >= SCHWELLE and rang >= SCHWELLE and sp > 1:
        u = "TRAEGT"
    elif jk.mean() < 0 and b <= 1 - SCHWELLE:
        u = "SCHADET"
    else:
        u = "TRAEGT NICHT"
    return u, jk, b, rang, sp, nl, la_n, ab_n


def main():
    E = ereignisse()
    alle_syms = set(E.sym) | {"BTC"}
    for m in pd.date_range("2023-01-01", M.ENDE, freq="MS"):
        if m in M.POS:
            alle_syms |= set(MK.klassen_mw(m)[0])
    P = stundenreihen(sorted(alle_syms))
    print("MESSUNG C2 (§38.2) · Kurse bis %s · Meldungen ab 2023: %s · Stundenreihen %d\n" % (
        M.ENDE.date(), " · ".join("%s %d" % (a, n) for a, n in E.art.value_counts().items()), len(P)))
    D = aufbauen(E, P)
    D.to_csv(os.path.join("data", "_spot", "c2_ereignisse.csv"), sep=";", index=False)
    for art in ("C2-a Futures-Start", "C2-b Upbit-Listing"):
        Du = D[(D.art == art) & (D.zeit >= "2024-01-01")].reset_index(drop=True)
        Dw = D[(D.art == art) & (D.zeit < "2024-01-01")]
        kand = kandidaten(Du, P)
        u, jk, b, rang, sp, nl, la_n, ab_n = urteil(Du, P, kand)
        kosten = Du.kl.map(KOSTEN).mean()
        print("%s ab 2024: Ereignisse %d an %d Monaten (%d Coins; Klassen %s) · Korb %+.2f Pp gegen BTC in 7 T (Median der Monate %+.2f) · Bootstrap %.3f · "
              "Rang gegen Nullwelt %.3f (Nullwelt %+.2f Pp) · Spiegel %.2f (Lauf %.0f %% / Absturz %.0f %%, Nullwelt %.0f / %.0f %%)  ->  %s" % (
                  art, len(Du), Du.zeit.dt.to_period("M").nunique(), Du.sym.nunique(), dict(Du.kl.value_counts()), 100 * jk.mean(), 100 * jk.median(), b, rang,
                  100 * nl.mean(), sp, 100 * Du.lauf.mean(), 100 * Du.absturz.mean(), 100 * la_n, 100 * ab_n, u))
        print("   verpasst (Meldung bis +4 h) Median %+.1f %% / Mittel %+.1f %% · nach Kosten (Mittel %.2f %%): Korb %+.2f Pp -> %s · 2023 (Auskunft, ab 09/2023): n %d, Mittel %+.1f %%" % (
            100 * Du.verpasst.median(), 100 * Du.verpasst.mean(), 100 * kosten, 100 * (jk.mean() - kosten), "LOHNT" if jk.mean() - kosten > 0 else "lohnt nicht",
            len(Dw), 100 * Dw.ex.mean() if len(Dw) else float("nan")))
        fehl = 0
        for _ in range(100):
            Z = Du.copy()
            ks = {}
            for i in Z.index:
                if kand[i]:
                    s = RNG.choice(kand[i])
                    Z.at[i, "sym"] = s
                    Z.at[i, "ex"] = ex(P, s, Z.at[i, "he"], Z.at[i, "hx"])
                    Z.at[i, "lauf"], Z.at[i, "absturz"] = pfad(P, s, Z.at[i, "he"], Z.at[i, "hx"])
                    ks[i] = [x for x in kand[i] if x != s] + [Du.at[i, "sym"]]
                else:
                    ks[i] = []
            fehl += urteil(Z, P, ks, nz=40)[0] == "TRAEGT"
        G = Du[Du.ex >= 0.05].reset_index(drop=True)
        ug = urteil(G, P, kandidaten(G, P), nz=40)[0] if len(G) >= 20 else "zu wenige"
        print("   SELBSTTEST (a) Zufalls-Ereignis 100 Welten: Fehlalarm %d %% -> %s · (b) gepflanzt (nur Ereignisse >= +5 %%, n %d): %s" % (
            fehl, "bestanden" if fehl <= 2.5 else "NICHT bestanden", len(G), "erkannt" if ug == "TRAEGT" else "NICHT erkannt (%s)" % ug))
        teile = []
        for v, h in ((1, 168), (24, 168), (4, 24), (4, 72), (4, 720)):
            Dx = aufbauen(E[E.art == art], P, verzug=v, halte=h)
            Dx = Dx[Dx.zeit >= "2024-01-01"]
            Dx["mon"] = Dx.zeit.dt.to_period("M")
            teile.append("+%d h / %d T: %+.1f Pp (n %d)" % (v, h // 24, 100 * Dx.groupby("mon").ex.mean().mean(), len(Dx)))
        print("   AUSKUNFT (nach dem Urteil): %s" % " · ".join(teile))
        print("   je Klasse: %s · je Jahr: %s" % (
            " · ".join("%s %+.1f Pp (n %d)" % (k, 100 * g.ex.mean(), len(g)) for k, g in Du.groupby("kl")),
            " · ".join("%d %+.1f Pp (n %d)" % (j, 100 * g.ex.mean(), len(g)) for j, g in Du.groupby(Du.zeit.dt.year))))
    Dc = D[(D.art == "C2-c Spot-Listing") & (D.zeit >= "2024-01-01")]
    print("\nC2-c Binance Spot-Listing (Auskunft, Kauf 4 h nach der Meldung, nur wo schon ein Binance-Kurs lag): n %d · Mittel %+.1f %% · Median %+.1f %% gegen BTC in 7 T" % (
        len(Dc), 100 * Dc.ex.mean() if len(Dc) else float("nan"), 100 * Dc.ex.median() if len(Dc) else float("nan")))


if __name__ == "__main__":
    main()
