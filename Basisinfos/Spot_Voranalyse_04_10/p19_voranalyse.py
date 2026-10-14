"""P19 VORANALYSE Season-Ampel C1 (+ D1 Nachlader, A3 Kandidatenliste) - Spot §49, 14.10.2026. Nur lesend; Abrufe FRED/DefiLlama (frei).

    python Basisinfos/Spot_Voranalyse_04_10/p19_voranalyse.py <Prod-Sicherung tradinginfotool.db>

  Teil 0  dieselbe Regel: der Nachbau (Klasse Ampel, spaeter agent/season_ampel.py) gibt aus den Spalten B1/B2/B3 der Kalibrierung
          (data/_spot/am_kalibrierung.csv, §36.4) denselben Stand X von 3 - und die Stufen nach §36.5 mit ihren Season-Anteilen
  Teil 1  Breite: der eigene Rechenweg (Top 50 nach Umsatz 30 T, Anteil mit 90-T-Ertrag > BTC) gegen s1_messung.baue - bitgleich?
          Dann am NB-Universum (Betriebskopie = ohne die 10 Uebernahmen): Abweichung und Wirkung auf die Schwelle 0,6
  Teil 2  Daten frisch abgerufen (wie die Messung: fredgraph.csv M2SL +35 T, DefiLlama stablecoincharts/all peggedUSD +1 T, Netto-
          Liquiditaet WALCL - WTREGEN - RRP): gegen die Kalibrierung auf den gemeinsamen Tagen (Revisionen)
  Teil 3  Ampel HEUTE (BTC aus der Produktion bis gestern, Breite bis zum Ende der Messbasis)
  Teil 4  Kandidatenliste A3: oberes Fuenftel des Watchlist-Werts (wie B4, ohne F9) am letzten Stichtag, bei Bitpanda handelbar
"""
import io
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

PROD = os.path.abspath(sys.argv[1])
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))

SCHWELLE = {"B1": 0.20, "B2": 0.05, "B3": 0.10}
BREITE_HEISS = 0.6
ENDE_T = 90
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]


# ══ der Nachbau (spaeter agent/season_ampel.py) ═════════════════════════════════════════════════════════════════════════
def stand(b1, b2, b3):
    return int(b1 > SCHWELLE["B1"]) + int(b2 > SCHWELLE["B2"]) + int(b3 > SCHWELLE["B3"])


def muster(b1, b2, b3):
    return (b1 > SCHWELLE["B1"], b2 > SCHWELLE["B2"], b3 > SCHWELLE["B3"])


def stufe(b1, b2, b3, breite, dreivon3_in_ende_t: bool) -> str:
    """§36.5 - aus dem Muster der drei Bedingungen; 'Ende' = 3/3 war in den letzten ENDE_T Tagen an und ist es nicht mehr."""
    m = muster(b1, b2, b3)
    if all(m):
        return "Ueberhitzung" if (breite == breite and breite >= BREITE_HEISS) else "Season-Klima"
    if dreivon3_in_ende_t:
        return "Ende"
    if m == (False, True, True):
        return "Vorlauf"
    if m == (True, True, False):
        return "ungewohnt"
    return "kalt"


def stufen(T):
    an3 = ((T.B1 > SCHWELLE["B1"]) & (T.B2 > SCHWELLE["B2"]) & (T.B3 > SCHWELLE["B3"])).astype(int)
    vorher = an3.shift(1).rolling(ENDE_T, min_periods=1).max().fillna(0) > 0
    return pd.Series([stufe(a, b, c, br, v) for a, b, c, br, v in zip(T.B1, T.B2, T.B3, T.Breite, vorher)], index=T.index)


def breite(K, U, alts, B, tage):
    """Anteil der Top 50 (Umsatz-Mittel der 30 T bis zum Monatsersten) mit 90-T-Ertrag > BTC, nur Coins mit beiden Kursen, >= 20."""
    aus = pd.Series(np.nan, index=tage)
    tops = {}
    for t in tage:
        m = t.replace(day=1)
        if m not in tops:
            vol = U.loc[m - pd.Timedelta(days=30):m, [a for a in alts if a in U.columns]].mean().dropna()
            tops[m] = vol.sort_values(ascending=False).index[:50]
        top = tops[m]
        a90 = (K.loc[t, top] / K.loc[t - pd.Timedelta(days=90), top]).dropna()
        if len(a90) >= 20:
            aus[t] = float((a90 > B[t] / B[t - pd.Timedelta(days=90)]).mean())
    return aus


def fred(s, verzug):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=90)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d.datum) + pd.Timedelta(days=verzug)
    return pd.to_numeric(d.set_index("datum")[s], errors="coerce").dropna()


def stablecoins():
    j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=90).json()
    return pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0)
                      for x in j}).sort_index()


def taeglich(r, idx):
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


def main():
    Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    # ---- Teil 0
    st = np.array([stand(a, b, c) for a, b, c in zip(Z.B1, Z.B2, Z.B3)])
    print("P19 VORANALYSE Season-Ampel · Kalibrierung %s bis %s (%d Tage)\n" % (Z.index[0].date(), Z.index[-1].date(), len(Z)))
    print("TEIL 0 Stand X von 3 aus B1/B2/B3: %d von %d Tagen gleich der Kalibrierung (%s)" % (
        int((st == Z.stand.values).sum()), len(Z), "BITGLEICH" if (st == Z.stand.values).all() else "ABWEICHUNG"))
    Z["stufe"] = stufen(Z)
    basis = Z.season.mean()
    print("   Stufen nach §36.5 (Ende = 3/3 in den letzten %d T an, jetzt nicht) - Beschreibung, ein Zyklus:" % ENDE_T)
    for s_, g in Z.groupby("stufe"):
        print("     %-13s Tage %4d (%4.1f %%) · Season-Tage %5.1f %% (Basis %.1f %%) · Jahre %s" % (
            s_, len(g), 100 * len(g) / len(Z), 100 * g.season.mean(), 100 * basis, ",".join(sorted({str(d.year) for d in g.index}))))
    w = Z.stufe != Z.stufe.shift(1)
    print("   Stufenwechsel: %d in %d Tagen (= Ereignis-Mails, wenn jede Stufe mit Handlung mailte: %d)" % (
        int(w.sum()) - 1, len(Z), int((w & Z.stufe.isin(["Vorlauf", "Season-Klima", "Ueberhitzung", "Ende"])).sum())))
    print("   Wechsel ab 2023: %s" % " · ".join("%s %s" % (d.date(), s_) for d, s_ in Z.stufe[w & (Z.index >= "2023-01-01")].items()))

    # ---- Teil 1 Breite
    import s1_messung as S1
    s1 = S1.baue()
    K, U, alts, Bi = s1["K"], s1["U"], s1["alts"], s1["K"]["BTC"]
    tage = [t for t in s1["idx"] if t >= pd.Timestamp("2025-01-01")]
    b_eigen = breite(K, U, alts, Bi, tage)
    b_s1 = s1["breite"].reindex(tage)
    gl = ((b_eigen == b_s1) | (b_eigen.isna() & b_s1.isna())).mean()
    print("\nTEIL 1 Breite eigener Rechenweg gegen s1_messung (ab 2025, %d Tage): gleich an %.1f %% der Tage (%s)" % (
        len(tage), 100 * gl, "BITGLEICH" if gl == 1 else "ABWEICHUNG, groesste %.4f" % float((b_eigen - b_s1).abs().max())))
    alts_nb = [a for a in alts if a not in UEBERNOMMEN]
    b_nb = breite(K, U, alts_nb, Bi, tage)
    d = (b_nb - b_eigen).dropna()
    kreuz = ((b_nb >= BREITE_HEISS) != (b_eigen >= BREITE_HEISS)) & b_nb.notna() & b_eigen.notna()
    print("   NB-Universum (ohne die 10 Uebernahmen): mittlere Abweichung %+.3f, groesste %.3f · Tage mit anderer Seite der Schwelle 0,6: %d von %d" % (
        d.mean(), d.abs().max(), int(kreuz.sum()), int(d.size)))

    # ---- Teil 2 frische Daten
    m2 = fred("M2SL", 35)
    stb = stablecoins()
    wl = pd.concat([fred("WALCL", 2), fred("WTREGEN", 2), fred("RRPONTSYD", 1).resample("W-WED").last()], axis=1, sort=True).ffill().dropna()
    netto = (wl["WALCL"] - wl["WTREGEN"] - wl["RRPONTSYD"] * 1000) / 1e6
    idx = pd.date_range("2019-01-01", pd.Timestamp.today().normalize(), freq="D")
    B2 = taeglich(m2 / m2.shift(12) - 1, idx)
    st_t = taeglich(stb, idx)
    B3 = st_t / st_t.shift(91) - 1
    gem = Z.index[(Z.index <= idx[-1])]
    d2 = (B2.reindex(gem) - Z.B2).abs()
    d3 = (B3.reindex(gem) - Z.B3).abs()
    st_neu = np.array([stand(a, b, c) for a, b, c in zip(Z.B1, B2.reindex(gem), B3.reindex(gem))])
    print("\nTEIL 2 frisch abgerufen gegen die Kalibrierung (%d gemeinsame Tage): B2 M2 groesste Abweichung %.4f (Tage > 0,001: %d) · "
          "B3 Stablecoins groesste %.4f (Tage > 0,001: %d) · Stand anders an %d Tagen" % (
              len(gem), d2.max(), int((d2 > 0.001).sum()), d3.max(), int((d3 > 0.001).sum()), int((st_neu != Z.stand.values).sum())))
    print("   letzte Werte: M2SL %s (%s, inkl. 35 T Verzug) · Stablecoins %s (%.1f Mrd USD) · Netto-Liquiditaet %s" % (
        m2.index[-1].date(), "%.1f" % m2.iloc[-1], stb.index[-1].date(), stb.iloc[-1] / 1e9, netto.index[-1].date()))

    # ---- Teil 3 Ampel heute
    c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
    btc = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol='BTC' AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert' "
                      "ORDER BY date", c)
    btc["date"] = pd.to_datetime(btc.date.str[:10])
    btc = btc.drop_duplicates("date", keep="last").set_index("date").close
    fg = pd.read_sql("SELECT date, fear_greed_value FROM macro_snapshot WHERE fear_greed_value IS NOT NULL", c)
    c.close()
    fg["date"] = pd.to_datetime(fg.date.str[:10])
    fg = fg.groupby("date").fear_greed_value.mean()
    heute = btc.index[-1]
    b1 = btc / btc.shift(91, freq="D").reindex(btc.index) - 1
    nt = taeglich(netto, idx)
    print("\nTEIL 3 AMPEL HEUTE (BTC-Schluss bis %s aus der Produktion):" % heute.date())
    for tag in (heute, heute - pd.Timedelta(days=30), heute - pd.Timedelta(days=90)):
        a, b_, c3 = b1.get(tag, np.nan), B2.get(tag, np.nan), B3.get(tag, np.nan)
        br = b_nb.get(tag, b_nb.dropna().iloc[-1] if tag > b_nb.dropna().index[-1] else np.nan)
        vorher = any(stand(b1.get(x, np.nan), B2.get(x, np.nan), B3.get(x, np.nan)) == 3 for x in pd.date_range(tag - pd.Timedelta(days=ENDE_T), tag - pd.Timedelta(days=1)))
        print("   %s  B1 BTC 91T %+6.1f %% %s · B2 M2 J/J %+5.1f %% %s · B3 Stablecoins 91T %+5.1f %% %s · Stand %d von 3 · Breite %.2f%s · Stufe %s · "
              "Netto-Liq 13W %+.1f %% · F&G %s" % (
                  tag.date(), 100 * a, "an" if a > SCHWELLE["B1"] else "aus", 100 * b_, "an" if b_ > SCHWELLE["B2"] else "aus", 100 * c3,
                  "an" if c3 > SCHWELLE["B3"] else "aus", stand(a, b_, c3), br, "" if tag <= b_nb.dropna().index[-1] else " (Stand %s)" % b_nb.dropna().index[-1].date(),
                  stufe(a, b_, c3, br, vorher), 100 * (nt.get(tag, np.nan) / nt.get(tag - pd.Timedelta(days=91), np.nan) - 1),
                  "%.0f" % fg.get(tag) if tag in fg.index else "-"))

    # ---- Teil 4 Kandidatenliste
    import p18_voranalyse as P18
    MK = P18.MK
    G = P18.G
    Kp, Up = G["K"], G["U"]
    aus = set(G["SONDER"]) | {s for s in Kp.columns if s not in G["UNIV"]} | set(UEBERNOMMEN)
    t = pd.Timestamp("2026-09-01")
    z = P18.B4(Kp, Up, aus, P18.cgh_nur).fuenftel(t)
    c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
    kat = {r[0].upper() for r in c.execute("SELECT symbol FROM bitpanda_katalog WHERE gruppe IN ('coin','token') AND symbol IS NOT NULL")}
    gehalten = {r[0] for r in c.execute("SELECT symbol FROM holdings WHERE COALESCE(quantity,0) + COALESCE(staked_quantity,0) > 0")}
    c.close()
    zu = pd.read_csv("Basisinfos/symbol_zuordnung.csv", sep=";")
    bp_von = {r.binance: r.bitpanda for r in zu.itertuples() if r.markt == "spot"}
    oben = z[z.q == 5].copy()
    oben["bitpanda"] = [bp_von.get(s, s) in kat for s in oben.sym]
    print("\nTEIL 4 KANDIDATENLISTE A3 am %s: oberes Fuenftel %d Coins (H %d · M %d · S %d), davon bei Bitpanda handelbar %d (H %d · M %d · S %d); "
          "davon schon gehalten: %s" % (
              t.date(), len(oben), (oben.kl == "H").sum(), (oben.kl == "M").sum(), (oben.kl == "S").sum(), int(oben.bitpanda.sum()),
              int((oben.bitpanda & (oben.kl == "H")).sum()), int((oben.bitpanda & (oben.kl == "M")).sum()), int((oben.bitpanda & (oben.kl == "S")).sum()),
              ", ".join(sorted(bp_von.get(s, s) for s in oben.sym if bp_von.get(s, s) in gehalten)) or "-"))
    for kl in ("H", "M", "S"):
        x = oben[(oben.kl == kl) & oben.bitpanda].sort_values("p", ascending=False)
        print("   %s: %s" % (kl, ", ".join("%s %.2f" % (bp_von.get(s, s), p) for s, p in list(zip(x.sym, x.p))[:12]) or "-"))


if __name__ == "__main__":
    main()
