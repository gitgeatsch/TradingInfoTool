"""E-1 Messung (Voranalyse_Schritt7 §23.23): Laufen REGEL0-Einstiege NACH einer Binance-Ankuendigung (Delisting, Monitoring) anders?
Nur lesend, keine Aufrufe. Ereignisse aus data/_e1/binance_ankuendigungen.db (e1_lade_binance.py).

    python Basisinfos/Rechenkern_02_10/e1_messung.py

VORAB FESTGELEGT (07.10.2026, vor dem ersten Lauf):
  Mengen      kern48jbz_einstiege_{bestand, unverzerrt_1..3} (wie A2/Kern), Einstiege 2024-01 bis 2026-08 (Messfokus ab 2024)
  Zielgroesse HAUPT: 24-h-Ertrag (Schluss t+25 / Schluss t+1 - 1; die Wette, wie N4/N5). Richtungsprobe: Chance A24 (+5 % vor -5 % in 24 h)
              und Spiegel B24 (-5 % zuerst). Auskunft: grosser Verlust L10 = 24-h-Ertrag <= -10 %
  Ereignis    Ankuendigung VOR dem Ende der Signalstunde (release <= t + 1 h, kein Vorgriff), je Asset, im Fenster davor:
                token_delist 30 T · futures_delist 30 T · monitoring 180 T (endet frueher mit einer 'monitoring_ende'-Meldung)
                paar_entfernt 14 T · margin 30 T
              HAUPT-Merkmal SCHWER = token_delist ODER futures_delist ODER monitoring. Die anderen Arten nur Auskunft
  Test        je Menge Unterschied mit - ohne; Nullwelt = Vertauschen des Merkmals INNERHALB des Tages (1.000), ZWEISEITIG 5 %
  Traegt      SCHWER: |Unterschied 24 h| ueber dem 95. Perzentil der |Null| in >= 3 von 4 Mengen, gleiches Vorzeichen, je Menge >= 30
              Einstiege mit Ereignis, UND Richtung: Chance und Spiegel zeigen gegeneinander (sign(dA) != sign(dB) oder dA - dB mit dem
              Vorzeichen des Ertrags) - sonst ist es nur Bewegung
  Auskunft    je Jahr (2024 / 2025-26), Weglassprobe ohne das Asset mit den meisten Ereignis-Einstiegen, SIGNALBILANZ je Asset
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
FENSTER = {"token_delist": 30, "futures_delist": 30, "monitoring": 180, "paar_entfernt": 14, "margin": 30}
NZ = 1000
RNG = np.random.default_rng(20261008)


def con(name):
    return sqlite3.connect("file:%s?mode=ro" % os.path.join(D, name).replace("\\", "/"), uri=True)


def ereignisse() -> pd.DataFrame:
    c = con(os.path.join("_e1", "binance_ankuendigungen.db"))
    e = pd.read_sql("SELECT symbol, art, release_ms FROM ereignis", c)
    c.close()
    e["zeit"] = pd.to_datetime(e.release_ms, unit="ms")
    return e


def schliesse(sym, C) -> pd.Series:
    teile = []
    for k in ("sk", "ska", "eh"):
        d = pd.read_sql("SELECT stunde, close FROM stundenkurse WHERE symbol=?", C[k], params=(sym,))
        if len(d):
            teile.append(d)
    if not teile:
        return pd.Series(dtype=float)
    d = pd.concat(teile).drop_duplicates("stunde")
    return pd.Series(d.close.values, index=pd.to_datetime(d.stunde)).sort_index()


def flags(E: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """Je Einstieg und Art: gab es eine Ankuendigung in (ende - Fenster, ende], ende = Signalstunde + 1 h? Monitoring endet mit 'monitoring_ende'."""
    out = {a: np.zeros(len(E), dtype=bool) for a in FENSTER}
    # KORREKTUR 08.10.2026 (Gegenprobe O29, e1_betrieb_gegenprobe.py): 'monitoring_ende' hat keine Zuordnung - das Kuerzel steht nur im
    # TITEL. Die erste Fassung suchte es in den Zuordnungen, das Ende griff NIE (67 Einstiege zu viel als Monitoring). Die Vorabregel
    # ("endet frueher mit einer monitoring_ende-Meldung") bleibt; korrigiert ist nur ihre Umsetzung - wie im Betrieb ueber den Titel.
    import re as _re
    _c = con(os.path.join("_e1", "binance_ankuendigungen.db"))
    _t = pd.read_sql("SELECT titel, release_ms FROM meldung WHERE art='monitoring_ende'", _c)
    _c.close()
    _z = [(pd.to_datetime(ms, unit="ms"), t) for t, ms in zip(_t.titel, _t.release_ms)]
    _sy = {s for s in E.symbol.unique()}
    ende_m = pd.DataFrame([(s, z) for z, t in _z for s in _sy if _re.search(r"(?<![A-Z0-9])%s(?![A-Z0-9])" % _re.escape(s), t or "")],
                          columns=["symbol", "zeit"])
    g = {k: v for k, v in ev.groupby("symbol")}
    for i, (s, t) in enumerate(zip(E.symbol.values, E.zeit.values)):
        if s not in g:
            continue
        x = g[s]
        t_ende = pd.Timestamp(t) + pd.Timedelta(hours=1)
        for a, w in FENSTER.items():
            y = x[(x.art == a) & (x.zeit <= t_ende) & (x.zeit > t_ende - pd.Timedelta(days=w))]
            if a == "monitoring" and len(y):
                letzte = y.zeit.max()
                beendet = ende_m[(ende_m.symbol == s) & (ende_m.zeit > letzte) & (ende_m.zeit <= t_ende)]
                out[a][i] = beendet.empty
            else:
                out[a][i] = len(y) > 0
    F = pd.DataFrame(out, index=E.index)
    F["SCHWER"] = F.token_delist | F.futures_delist | F.monitoring
    return F


def lade_menge(m, C, cache) -> pd.DataFrame:
    E = pd.read_csv(os.path.join(D, "_vergleich", "kern48jbz_einstiege_%s.csv" % m), sep=";")
    E["zeit"] = [B0 + timedelta(hours=int(h)) for h in E.stunde]
    E = E[(E.zeit >= datetime(2024, 1, 1)) & (E.zeit < datetime(2026, 9, 1))].reset_index(drop=True)
    E["tag"] = E.zeit.dt.strftime("%Y-%m-%d")
    E["A24"] = ((E.t_u <= 24) & (E.t_u < E.t_d)).astype(float)
    E["B24"] = ((E.t_d <= 24) & (E.t_d <= E.t_u)).astype(float)
    er = np.full(len(E), np.nan)
    for sym, idx in E.groupby("symbol").groups.items():
        if sym not in cache:
            cache[sym] = schliesse(sym, C)
        k = cache[sym]
        if k.empty:
            continue
        for i in idx:
            t = E.at[i, "zeit"]
            a, b = k.get(t + timedelta(hours=1)), k.get(t + timedelta(hours=25))
            if a and b and np.isfinite(a) and np.isfinite(b):
                er[i] = b / a - 1.0
    E["ertrag24"] = er
    E["L10"] = (E.ertrag24 <= -0.10).astype(float)
    return E


def diff(x, f):
    f = np.asarray(f, dtype=bool)
    if f.sum() < 2 or (~f).sum() < 2:
        return np.nan, np.nan, np.nan, np.nan
    v = lambda c: np.nanmean(x[c].values[f]) - np.nanmean(x[c].values[~f])   # noqa: E731
    return v("ertrag24"), v("A24"), v("B24"), v("L10")


def null(x, f, nz=NZ):
    f = np.asarray(f, dtype=bool)
    tc = pd.factorize(x.tag.values)[0]
    nach = np.argsort(tc, kind="stable")
    w = np.empty(nz)
    for i in range(nz):
        g = np.empty_like(f)
        g[nach] = f[np.lexsort((RNG.random(len(f)), tc))]
        w[i] = diff(x, g)[0]
    return w


def main():
    C = {k: con(f) for k, f in (("sk", "stundenkurse.db"), ("ska", "stundenkurse_alle.db"), ("eh", "eingestellt_historie.db"))}
    ev = ereignisse()
    print("E-1 MESSUNG (Schritt7 §23.23) · Ereignisse %s" % ev.groupby("art").size().to_dict())
    cache, M = {}, {}
    for m in MENGEN:
        X = lade_menge(m, C, cache)
        M[m] = pd.concat([X, flags(X, ev)], axis=1)
    print("Einstiege 2024-01..2026-08: %s\n" % ", ".join("%s %d" % (m, len(x)) for m, x in M.items()))
    urteil = {}
    for a in ["SCHWER"] + list(FENSTER):
        print("%s%s" % (a, "  (HAUPT)" if a == "SCHWER" else "  (Auskunft)"))
        treffer, zeichen = 0, []
        for m, x in M.items():
            f = x[a].values
            n_mit = int(f.sum())
            dE, dA, dB, dL = diff(x, f)
            if n_mit < 2:
                print("   %-13s mit Ereignis %d - zu wenige" % (m, n_mit)); continue
            nul = null(x, f)
            p95 = np.nanpercentile(np.abs(nul), 95)
            p2 = float(np.mean(np.abs(nul) >= abs(dE)))
            richtung = (np.sign(dA) != np.sign(dB)) or (np.sign(dA - dB) == np.sign(dE))
            ok = n_mit >= 30 and abs(dE) > p95 and richtung
            treffer += ok
            zeichen.append(np.sign(dE))
            mj = {j: (int(x[(x.jahr == j) | ((j == 2025) & (x.jahr == 2026))][a].sum())) for j in (2024, 2025)}
            j24 = diff(x[x.jahr == 2024], x[x.jahr == 2024][a].values)[0]
            j25 = diff(x[x.jahr >= 2025], x[x.jahr >= 2025][a].values)[0]
            top = x[f].symbol.value_counts()
            xw = x[x.symbol != top.index[0]] if len(top) else x
            dW = diff(xw, xw[a].values)[0]
            print("   %-13s mit %4d (Assets %3d) · 24 h %+.2f %% (|Null| P95 %.2f, p2 %.3f) · Chance %+.3f · Spiegel %+.3f · L10 %+.3f · "
                  "2024 %+.2f %% / 2025-26 %+.2f %% · ohne %s %+.2f %% · %s" % (
                      m, n_mit, x[f].symbol.nunique(), 100 * dE, 100 * p95, p2, dA, dB, dL, 100 * j24 if np.isfinite(j24) else np.nan,
                      100 * j25 if np.isfinite(j25) else np.nan, top.index[0] if len(top) else "-", 100 * dW if np.isfinite(dW) else np.nan,
                      "TRAEGT" if ok else ("Richtung nein" if not richtung else ("zu wenige" if n_mit < 30 else "nicht ueber"))))
        gleich = len(set(zeichen)) == 1
        urteil[a] = "TRAEGT (%d/4)" % treffer if (treffer >= 3 and gleich) else "traegt nicht (%d/4)" % treffer
        print("   -> %s\n" % urteil[a])
    print("SIGNALBILANZ (Menge unverzerrt_1): Einstiege mit SCHWER je Asset - Mittel 24 h, Anteil L10")
    x = M["unverzerrt_1"]
    sb = x[x.SCHWER].groupby("symbol").agg(n=("ertrag24", "size"), e=("ertrag24", "mean"), l=("L10", "mean")).sort_values("n", ascending=False)
    print("   " + " · ".join("%s %d (%+.1f %%, L10 %.0f %%)" % (s, r.n, 100 * r.e, 100 * r.l) for s, r in sb.head(30).iterrows()))
    print("\nGESAMT (vorab: HAUPT = SCHWER, >= 3 von 4 Mengen, gleiches Vorzeichen, Richtung, >= 30 Ereignis-Einstiege):")
    for a, u in urteil.items():
        print("   %-15s %s" % (a, u))
    pd.concat([x.assign(menge=m) for m, x in M.items()])[["menge", "symbol", "stunde", "jahr", "ertrag24", "A24", "B24", "L10", "SCHWER"] + list(FENSTER)].to_csv(
        os.path.join(D, "_e1", "e1_einstiege.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
