"""P88 VORANALYSE L-1 (Asset-Filter Monatsebene) und L-2 (Hebel: andere Haltedauer je Asset-Gruppe) (25.10.2026).

    python -X utf8 Basisinfos/Rechenkern_02_10/p88_l1_l2_voranalyse.py

Nutzer 25.10.: *"ja L-1 Voranalyse starten ... auch L-2 wir brauchen auch fuer Hebel eine Loesung, diese kann nicht wie spot sein, auch auf
mein bestehendes Portfolio pruefen und eine andere Haltedauer pruefen, was eine neue RegelXY waere und ggf. fuer bestimmte Assets geeignet?"*

NUR MACHBARKEIT UND AUFLOESUNG - kein Ergebnis einer neuen Regel:
 L1-a  Bestand (NB-Diagnose 19.10., holdings_check) gegen Klasse, Marktwert-Rang und Fuenftel am letzten Stichtag
 L1-b  je Filter (Top 30, oberes Fuenftel, Top 30 & oberes Fuenftel, H & oberes Fuenftel): Coins je Stichtag, Wechsel der Mitglieder je Monat,
       Gebuehr des Wechsels (Fusion 0,25 % je Seite)
 L1-c  Aufloesung nach messnorm (Block max(15 T, 3 x H), >= 20 Bloecke): kleinster erkennbarer Unterschied 'Filter - Gruppe' und
       'Filter - BTC' bei 7 T und 30 T, ab 2024 und alle Jahre - aus der STREUUNG (zentrierter Block-Bootstrap), nicht aus dem Mittel
 L2-a  REGEL0-Einstiege 2024-26 (Referenz, Lauf A) je Asset-Gruppe; Kosten je Haltedauer (0,30 % + 0,18 % je Tag, §23.68)
 L2-b  Aufloesung je Gruppe und Haltedauer 24/72/168 h (Tagesbloecke nach messnorm), aus der Streuung
Nur lesend.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import messnorm  # noqa: E402
import p85_atlas_voranalyse as P85  # noqa: E402
import p86_a1_zerlegung as P86  # noqa: E402

MK = P85.MK
RNG = np.random.default_rng(88)
DIAG = r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json"
KERN = ("BTC", "ETH", "SOL")
NICHT_KRYPTO = {"EURCV", "3QSS", "CEBS", "DBPK", "EXH3", "ISOC", "OD7C", "OD7H", "OD7L", "OD7N", "PLTR", "VST", "VVMX", "X136", "VSN", "G2X", "ROL"}


def mde_aus_streuung(werte, block, n=2000):
    """2,5 x Standardabweichung des Mittels unter zirkulaerem Block-Bootstrap der ZENTRIERTEN Werte; None unter 20 Bloecken."""
    w = np.asarray(werte, float)
    w = w[np.isfinite(w)]
    if len(w) / block < 20:
        return None, len(w) / block
    w = w - w.mean()
    st = RNG.integers(0, len(w), (n, int(np.ceil(len(w) / block))))
    ix = ((st[:, :, None] + np.arange(block)) % len(w)).reshape(n, -1)[:, :len(w)]
    return 2.5 * float(w[ix].mean(axis=1).std()), len(w) / block


def filter_maske(D, f):
    top30 = D.rang <= 30
    f5 = D.f == 5
    return {"Top 30": top30, "oberes Fuenftel": f5, "Top 30 & oberes Fuenftel": top30 & f5, "H & oberes Fuenftel": (D.kl == "H") & f5}[f]


def main():
    print("P88 VORANALYSE L-1 / L-2 (Machbarkeit und Aufloesung)\n")
    T1 = P85.wert_tabelle(1)
    letzter = T1.t.max()
    rg = MK.rang_mw(pd.Timestamp(letzter))[1]
    # ── L1-a Bestand ─────────────────────────────────────────────────────────────────────────────────────────────────────
    d = json.load(open(DIAG, encoding="utf-8"))
    hb = [x for x in d["holdings_check"] if (x.get("quantity") or 0) + (x.get("staked_quantity") or 0) > 0]
    stand = max(x.get("updated_at") or "" for x in hb)[:10]
    krypto = sorted({x["symbol"] for x in hb} - NICHT_KRYPTO)
    L = T1[T1.t == letzter].set_index("sym")
    print("L1-a BESTAND (NB-Diagnose, Stand %s) gegen den Stichtag %s: %d Krypto-Werte" % (stand, letzter.date(), len(krypto)))
    zeilen = []
    for s in krypto:
        if s in KERN:
            zeilen.append((s, "Kern", "-", "-", "Kern (nicht in der Watchlist-Ordnung)"))
            continue
        if s not in L.index:
            zeilen.append((s, "-", "-", "-", "nicht im Universum am Stichtag (Binance-Spot, >= 400 Kerzen)"))
            continue
        r = rg.get(s, np.nan)
        p = L.p[s]
        f = int(np.ceil(p * 5)) if p == p else None
        flags = [n for n, ok in (("Top 30", r <= 30), ("oberes Fuenftel", f == 5), ("Top 30 & oberes Fuenftel", r <= 30 and f == 5)) if ok]
        zeilen.append((s, L.kl[s], "%.0f" % r if r == r else "kein Umlauf", str(f) if f else "-", ", ".join(flags) or "in keinem Filter"))
    for z in zeilen:
        print("    %-8s Klasse %-4s Rang %-10s Fuenftel %-2s -> %s" % z)
    ub = {k: sum(1 for z in zeilen if k in z[4]) for k in ("Top 30", "oberes Fuenftel", "Top 30 & oberes Fuenftel")}
    print("    Zusammen: Kern %d · in Top 30 %d · oberes Fuenftel %d · Top 30 & oberes Fuenftel %d · in keinem Filter %d · nicht im Universum %d\n" % (
        sum(1 for z in zeilen if z[1] == "Kern"), ub["Top 30"], ub["oberes Fuenftel"], ub["Top 30 & oberes Fuenftel"],
        sum(1 for z in zeilen if z[4] == "in keinem Filter"), sum(1 for z in zeilen if z[1] == "-")))
    # ── L1-b / L1-c Filter ───────────────────────────────────────────────────────────────────────────────────────────────
    for h in (7, 30):
        D = P86.anker(h, T1)
        block = int(np.ceil(messnorm._block(h) / 30.4))
        print("L1 Horizont %d T · Block nach messnorm %d Stichtag(e)" % (h, block))
        for fn in ("Top 30", "oberes Fuenftel", "Top 30 & oberes Fuenftel", "H & oberes Fuenftel"):
            m = filter_maske(D, fn)
            for ep in ("E3", "alle"):
                e = (D.ep == "E3") if ep == "E3" else (D.ep != "")
                X = D[m & e]
                n_je = X.groupby("t").size()
                mitgl = X.groupby("t").sym.apply(set).sort_index()
                wechsel = [len(b - a) / max(len(b), 1) for a, b in zip(mitgl.values[:-1], mitgl.values[1:])]
                gr = D[e & ((D.rang <= 30) if fn.startswith("Top 30") else (D.kl == "H") if fn.startswith("H ") else True)]
                g_t = gr.groupby("t").r.mean()
                f_t = X.groupby("t").r.mean()
                b_t = D[e].groupby("t").rb.first()
                ix = f_t.index.intersection(g_t.index)
                m1, nb1 = mde_aus_streuung((f_t[ix] - g_t[ix]).values, block)
                m2, nb2 = mde_aus_streuung((f_t[ix] - b_t[ix]).values, block)
                if h == 30:
                    print("    %-26s %-4s Coins/Stichtag %4.1f · Wechsel je Monat %3.0f %% (Gebuehr %.2f %% je Monat) · MDE Filter-Gruppe %s · Filter-BTC %s (%.0f Bloecke)" % (
                        fn, ep, n_je.mean(), 100 * np.mean(wechsel), 2 * 0.25 * np.mean(wechsel),
                        ("– (Filter = Gruppe)" if fn in ("Top 30",) else "%.1f Pp" % (100 * m1)) if m1 is not None else "KEIN BEFUND", "%.1f Pp" % (100 * m2) if m2 is not None else "KEIN BEFUND", nb1))
                else:
                    print("    %-26s %-4s Coins/Stichtag %4.1f · MDE Filter-Gruppe %s · Filter-BTC %s (%.0f Bloecke)" % (
                        fn, ep, n_je.mean(), ("– (Filter = Gruppe)" if fn in ("Top 30",) else "%.1f Pp" % (100 * m1)) if m1 is not None else "KEIN BEFUND", "%.1f Pp" % (100 * m2) if m2 is not None else "KEIN BEFUND", nb1))
        print()
    # ── L2 Hebel ─────────────────────────────────────────────────────────────────────────────────────────────────────────
    print("L2-a Kosten Bitpanda-Hebel je Haltedauer (0,30 % + 0,18 % je Tag, §23.68): " + " · ".join(
        "%s %.2f %%" % (n, 0.30 + 0.18 * t) for n, t in (("24 h", 1), ("72 h", 3), ("7 T", 7), ("30 T", 30))))
    K = P85.Kurse()
    for weg, pfad in (("Referenz", os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")),
                      ("Lauf A", os.path.join("data", "_hist", "einstiege_A.csv"))):
        E = P85.einstiege(pfad, T1, K)
        E["rang"] = [MK.rang_mw(pd.Timestamp(t))[1].get(s, np.nan) if t == t else np.nan for t, s in zip(E.t, E.symbol)] if False else np.nan
        rgs = {t: MK.rang_mw(pd.Timestamp(t))[1] for t in E.t.dropna().unique()}
        E["rang"] = [rgs[t].get(s, np.nan) if t in rgs else np.nan for t, s in zip(E.t, E.symbol)]
        E = E[E.zeit.dt.year >= 2024]
        gruppen = {"BTC": E.symbol == "BTC", "ETH": E.symbol == "ETH", "SOL": E.symbol == "SOL", "Kern BTC/ETH/SOL": E.symbol.isin(KERN),
                   "Top 30 & oberes Fuenftel": (E.rang <= 30) & (E.f == 5), "H & oberes Fuenftel": (E.kl == "H") & (E.f == 5),
                   "Top 30": E.rang <= 30, "oberes Fuenftel": E.f == 5, "alle": np.ones(len(E), bool)}
        print("L2 %s: Einstiege 2024-26 und kleinster erkennbarer mittlerer Ertrag (2,5 x Streuung, Tagesbloecke nach messnorm)" % weg)
        for gname, gm in gruppen.items():
            y = E[np.asarray(gm, bool)]
            teile = []
            for hn, hh in (("24 h", 1), ("7 T", 7), ("30 T", 30)):
                col = "z_" + hn
                z = y[["tag", col]].dropna()
                tage = pd.date_range("2024-01-01", "2026-08-31", freq="D")
                s_ = z.groupby("tag")[col].sum().reindex(tage).fillna(0).to_numpy()
                n_ = z.groupby("tag")[col].size().reindex(tage).fillna(0).to_numpy()
                blk = messnorm._block(hh)
                nb = len(tage) / blk
                if nb < 20 or n_.sum() < 20:
                    teile.append("%s KEIN BEFUND (%.0f Bloecke)" % (hn, nb))
                    continue
                st = RNG.integers(0, len(tage), (1000, int(np.ceil(len(tage) / blk))))
                ix = ((st[:, :, None] + np.arange(blk)) % len(tage)).reshape(1000, -1)[:, :len(tage)]
                mu = s_.sum() / n_.sum()
                sz = s_ - mu * n_                                    # zentriert: nur die Streuung, nicht das Mittel
                mm = sz[ix].sum(axis=1) / np.maximum(n_[ix].sum(axis=1), 1)
                teile.append("%s MDE %.2f Pp (%.0f Bl.)" % (hn, 100 * 2.5 * mm.std(), nb))
            print("    %-26s %5d Einstiege an %4d Tagen · %s" % (gname, len(y), y.tag.nunique(), " · ".join(teile)))
        print()
    import agent.season_ampel as SA
    Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    st = SA.geltend(SA.stufen(Z))
    s24 = st[(st.index >= "2024-01-01") & (st.index <= "2026-06-22")]
    print("L2 Auskunft Season-Ampel 2024-01..2026-06: " + " · ".join("%s %.0f %%" % (k, 100 * v) for k, v in s24.value_counts(normalize=True).items()))


if __name__ == "__main__":
    main()
