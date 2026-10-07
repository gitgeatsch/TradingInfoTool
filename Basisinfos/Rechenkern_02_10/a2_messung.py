"""A2 Teil 2 (Voranalyse_Schritt7 §23.15, E-76..E-79): trennen NEUE Informationen INNERHALB der REGEL0-Einstiege? Nur lesend, keine Aufrufe.

    python Basisinfos/Rechenkern_02_10/a2_messung.py

AUSLEGUNG, vor dem ersten Lauf festgelegt (07.10.2026):
  Mengen      data/_vergleich/kern48jbz_einstiege_{bestand,unverzerrt_1,unverzerrt_2,unverzerrt_3}.csv (REGEL0-Form; stunde = Signalstunde,
              Stunden seit 2020-01-01; t_u/t_d = Stunden bis +5 % / -5 %, 999 = nicht erreicht) - dieselben Mengen wie die Kern-Befunde
  Zielgroesse Chance A24 = t_u <= 24 und t_u < t_d (wie messe_losfahren.py:88); Spiegel B24 = t_d <= 24 und t_d <= t_u;
              Auskunft: 24-h-Ertrag = Schluss (t+25) / Schluss (t+1) - 1
  Merkmale    nur aus Kerzen bis einschliesslich der Signalstunde t (Schluss bekannt):
              a_praemie    Markpreis-Schluss t / Kurs-Schluss t - 1
              b_kapitul    Umsatz der 6 h bis t / Median der 6-h-Umsaetze der 30 Tage davor
              c_docht      (Schluss t - Tief t) / (Hoch t - Tief t)
              d_fall6, d_fall24   Ertrag 6 h bzw. 24 h bis t in Einheiten der eigenen Tagesspanne (Mittel der 14 Tagesspannen davor)
              e_btc24, e_btc168   BTC-Ertrag 24 h bzw. 168 h bis t
              f_oi24       OI-Wert t / OI-Wert t-24 - 1 · f_ls Konten-Long/Short t · f_taker Taker-Verhaeltnis t · f_funding Tageswert des VORTAGS
              g_kauf6      Kaeufer-Volumen / Volumen der 6 h bis t
  Wahl        Menge bestand, Einstiege 2024: Drittelkanten aus 2024; Unterschied Chance oberes - unteres Drittel; Nullwelt 500 Vertauschungen
              des Merkmals INNERHALB des Tages; Wahl, wenn |Unterschied| ueber dem 90. Perzentil der |Null|; Richtung = Vorzeichen
  Bestaetigung je Menge 2025-01..2026-08, Kanten aus 2024, gewaehlte Richtung: (1) Unterschied ueber dem 95. Perzentil der Null (einseitig),
              (2) RICHTUNG statt Bewegung: Richtung x (Unterschied Chance - Unterschied Spiegel) > 0
  Traegt      Wahl bestanden UND Bestaetigung in >= 3 von 4 Mengen
  Auskunft    24-h-Ertrag je Drittel, Weglassprobe ohne die 5 Assets mit den meisten Einstiegen im gewaehlten Drittel, Abdeckung je Merkmal
"""
import os
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(WURZEL, "data")
B0 = datetime(2020, 1, 1)
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
RNG = np.random.default_rng(20261008)
NZ = 500
MERKMALE = ("a_praemie", "b_kapitul", "c_docht", "d_fall6", "d_fall24", "e_btc24", "e_btc168", "f_oi24", "f_ls", "f_taker", "f_funding", "g_kauf6")


def con(name):
    return sqlite3.connect("file:%s?mode=ro" % os.path.join(D, name), uri=True)


def reihe(conns, tab, sym, spalten):
    # ALLE Quellen zusammen (20 Symbole liegen in Basis UND eingestellt_historie - je Zeitraum eine andere Datei), erste Quelle gewinnt
    teile = []
    for c in conns:
        d = pd.read_sql("SELECT stunde, %s FROM %s WHERE symbol=?" % (spalten, tab), c, params=(sym,))
        if len(d):
            d.index = pd.to_datetime(d.pop("stunde"))
            teile.append(d)
    if not teile:
        return None
    d = pd.concat(teile)
    return d[~d.index.duplicated()].sort_index()


def merkmale_je_symbol(sym, ts, C):
    k = reihe([C["sk"], C["ska"], C["eh"]], "stundenkurse", sym, "open, high, low, close, volumen")
    out = {t: {m: np.nan for m in MERKMALE} | {"ertrag24": np.nan} for t in ts}
    if k is None:
        return out
    k = k.asfreq("h")
    mk = reihe([C["mh"], C["ma"]], "markpreis", sym, "close")
    tm = reihe([C["tm"], C["eh"]], "terminmarkt", sym, "oi_wert, konten_verh, taker_verh")
    fl = reihe([C["rf"], C["eh"]], "fluss", sym, "volumen, kauf_volumen")
    fu = pd.concat([pd.read_sql("SELECT datum, wert FROM funding WHERE symbol=?", C[q], params=(sym,)) for q in ("fu", "eh")])
    fu = fu.drop_duplicates("datum").set_index("datum")["wert"]
    tag_spanne = (k.high.rolling(24).max() - k.low.rolling(24).min()) / k.close
    for t in ts:
        if t not in k.index or np.isnan(k.close.get(t, np.nan)):
            continue
        o = out[t]
        z = k.loc[:t]
        c_t = z.close.iloc[-1]
        sp = [tag_spanne.get(t - timedelta(hours=24 * i), np.nan) for i in range(1, 15)]
        atr = np.nanmean(sp) if np.isfinite(sp).sum() >= 10 else np.nan
        if mk is not None and t in mk.index:
            o["a_praemie"] = mk.close.get(t) / c_t - 1
        v6 = z.volumen.iloc[-6:].sum()
        hist = z.volumen.iloc[-726:-6]
        if len(hist) >= 600:
            m6 = hist.rolling(6).sum().iloc[5::6].median()
            o["b_kapitul"] = v6 / m6 if m6 and m6 > 0 else np.nan
        h, l_ = z.high.iloc[-1], z.low.iloc[-1]
        o["c_docht"] = (c_t - l_) / (h - l_) if h > l_ else np.nan
        for n_, m in ((6, "d_fall6"), (24, "d_fall24")):
            if len(z) > n_ and atr and np.isfinite(atr) and atr > 0:
                o[m] = (c_t / z.close.iloc[-1 - n_] - 1) / atr
        b = C["btc"]
        if t in b.index:
            for n_, m in ((24, "e_btc24"), (168, "e_btc168")):
                t0 = t - timedelta(hours=n_)
                if t0 in b.index:
                    o[m] = b.close[t] / b.close[t0] - 1
        if tm is not None and t in tm.index:
            o["f_ls"], o["f_taker"] = tm.konten_verh.get(t), tm.taker_verh.get(t)
            t0 = t - timedelta(hours=24)
            if t0 in tm.index and tm.oi_wert.get(t0):
                o["f_oi24"] = tm.oi_wert.get(t) / tm.oi_wert.get(t0) - 1
        vt = (t - timedelta(days=1)).strftime("%Y-%m-%d")
        if vt in fu.index:
            o["f_funding"] = float(fu[vt])
        if fl is not None:
            w = fl.loc[t - timedelta(hours=5):t]
            if len(w) >= 6 and w.volumen.sum() > 0:
                o["g_kauf6"] = w.kauf_volumen.sum() / w.volumen.sum()
        e1, e25 = t + timedelta(hours=1), t + timedelta(hours=25)
        if e1 in k.index and e25 in k.index and np.isfinite(k.close.get(e1, np.nan)) and np.isfinite(k.close.get(e25, np.nan)):
            o["ertrag24"] = k.close[e25] / k.close[e1] - 1
    return out


def lade_menge(m, C, cache):
    E = pd.read_csv(os.path.join(D, "_vergleich", "kern48jbz_einstiege_%s.csv" % m), sep=";")
    E["zeit"] = [B0 + timedelta(hours=int(h)) for h in E.stunde]
    E["tag"] = E.zeit.dt.strftime("%Y-%m-%d")
    E["A24"] = ((E.t_u <= 24) & (E.t_u < E.t_d)).astype(float)
    E["B24"] = ((E.t_d <= 24) & (E.t_d <= E.t_u)).astype(float)
    zeilen = []
    for sym, g in E.groupby("symbol"):
        fehlt = [t for t in g.zeit if (sym, t) not in cache]
        if fehlt:
            for t, o in merkmale_je_symbol(sym, fehlt, C).items():
                cache[(sym, t)] = o
        zeilen += [cache[(sym, t)] for t in g.zeit]
    F = pd.DataFrame(zeilen, index=E.index)
    return pd.concat([E, F], axis=1)


def diff(x, f, k):
    f = np.asarray(f, dtype=float)
    o, u = f > k[1], f <= k[0]
    if o.sum() < 30 or u.sum() < 30:
        return np.nan, np.nan, np.nan
    A, B, E = x.A24.values, x.B24.values, x.ertrag24.values
    return A[o].mean() - A[u].mean(), B[o].mean() - B[u].mean(), np.nanmean(E[o]) - np.nanmean(E[u])


def null(x, m, k, nz=NZ):
    # Vertauschung des Merkmals INNERHALB des Tages, vektorisiert: beide Ordnungen nach Tag sortiert, innerhalb des Tages zufaellig
    f = x[m].values.astype(float)
    tc = pd.factorize(x.tag.values)[0]
    nach_tag = np.argsort(tc, kind="stable")
    w = np.empty(nz)
    for i in range(nz):
        perm = np.lexsort((RNG.random(len(f)), tc))
        g = np.empty_like(f)
        g[nach_tag] = f[perm]
        w[i] = diff(x, g, k)[0]
    return w


def main():
    C = {n: con(f) for n, f in (("sk", "stundenkurse.db"), ("ska", "stundenkurse_alle.db"), ("eh", "eingestellt_historie.db"),
                                ("mh", "markpreis_historie.db"), ("ma", "markpreis_alle.db"), ("tm", "terminmarkt_historie.db"),
                                ("rf", "richtung_historie.db"), ("fu", "funding_historie.db"))}
    b = reihe([C["sk"], C["ska"]], "stundenkurse", "BTC", "close")
    C["btc"] = b
    cache = {}
    M = {m: lade_menge(m, C, cache) for m in MENGEN}
    print("A2 Teil 2 (Schritt7 §23.15) · REGEL0-Einstiege je Menge: %s" % ", ".join("%s %d" % (m, len(x)) for m, x in M.items()))
    print("Abdeckung je Merkmal (Anteil mit Wert, bestand 2024 / 2025-26): " + " · ".join(
        "%s %.0f/%.0f %%" % (f, 100 * M["bestand"][M["bestand"].jahr == 2024][f].notna().mean(), 100 * M["bestand"][M["bestand"].jahr >= 2025][f].notna().mean())
        for f in MERKMALE))
    print("Grundrate Chance A24 / Spiegel B24 (bestand): 2024 %.3f / %.3f · 2025-26 %.3f / %.3f\n" % (
        M["bestand"][M["bestand"].jahr == 2024].A24.mean(), M["bestand"][M["bestand"].jahr == 2024].B24.mean(),
        M["bestand"][M["bestand"].jahr >= 2025].A24.mean(), M["bestand"][M["bestand"].jahr >= 2025].B24.mean()))
    gesamt = []
    for f in MERKMALE:
        w = M["bestand"][(M["bestand"].jahr == 2024) & M["bestand"][f].notna()]
        if len(w) < 200:
            print("%-10s Wahl: zu wenige Werte (%d)" % (f, len(w))); gesamt.append((f, "zu wenige")); continue
        k = w[f].quantile([1 / 3, 2 / 3]).values
        dA, dB, dE = diff(w, w[f], k)
        nul = null(w, f, k)
        p90 = np.nanpercentile(np.abs(nul), 90)
        richtung = 1 if dA > 0 else -1
        wahl = abs(dA) > p90
        zeile = "%-10s WAHL 2024: Chance oben-unten %+.3f (|Null| P90 %.3f) Spiegel %+.3f Ertrag %+.2f %% -> %s%s" % (
            f, dA, p90, dB, 100 * dE, "gewaehlt" if wahl else "nicht gewaehlt", (" Richtung %s" % ("OBEN" if richtung > 0 else "UNTEN")) if wahl else "")
        print(zeile)
        bes = 0
        for m in MENGEN:
            x = M[m][(M[m].jahr >= 2025) & M[m][f].notna()]
            dA2, dB2, dE2 = diff(x, x[f], k)
            if np.isnan(dA2):
                print("      %-13s zu wenige" % m); continue
            nul2 = null(x, f, k, nz=300) * richtung
            p95 = np.nanpercentile(nul2, 95)
            ok1 = richtung * dA2 > p95
            ok2 = richtung * (dA2 - dB2) > 0
            o_ = x[(x[f] > k[1]) if richtung > 0 else (x[f] <= k[0])]
            top5 = o_.symbol.value_counts().index[:5].tolist()
            xw = x[~x.symbol.isin(top5)]
            dW = diff(xw, xw[f], k)[0]
            bes += bool(wahl and ok1 and ok2)
            print("      %-13s 2025-26 n %5d: Chance %+.3f (Null P95 %+.3f) %s · Spiegel %+.3f · Richtung %s · Ertrag %+.2f %% · ohne Top-5 %+.3f" % (
                m, len(x), richtung * dA2, p95, "ueber" if ok1 else "nicht ueber", richtung * dB2, "ja" if ok2 else "nein", 100 * richtung * dE2,
                richtung * dW if np.isfinite(dW) else np.nan))
        urteil = "TRAEGT" if (wahl and bes >= 3) else ("nicht gewaehlt" if not wahl else "traegt nicht (%d/4)" % bes)
        gesamt.append((f, urteil))
        print("      -> %s\n" % urteil)
    print("GESAMT (vorab: Wahl 2024 und Bestaetigung >= 3 von 4 Mengen):")
    for f, u in gesamt:
        print("  %-10s %s" % (f, u))


if __name__ == "__main__":
    main()
