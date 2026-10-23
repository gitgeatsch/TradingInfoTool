"""P73 ATLAS T3 (Messplan_Indikator_Atlas_23_10.md, vorab ec7ce185): lange Historie traditioneller Maerkte - beschreibend.

    python Basisinfos/Rechenkern_02_10/p73_atlas_t3_lang.py

Daten FRED (API, kostenfrei): NASDAQCOM (1971, taeglich), M2SL (1959, monatlich), USREC (1854), T10Y2Y (1976), T10Y3M (1982), FEDFUNDS (1954),
SAHMREALTIME (1959). Zwischenablage data/_ra/p73_fred.csv.
(a) Dauer Nasdaq-Bullenmaerkte (Baer = >= -20 % vom Hoch) und M2-Ausweitungen (M2 J/J > 0)
(b) Anteil Bullenmarkt-Monate mit / ohne M2-Ausweitung
(c) Nasdaq in und um NBER-Rezessionen
(d) Vorlauf der Zinskurve: Inversion -> Rezessionsbeginn
(e) Reifegrad heute: laufender Bullenmarkt und laufende Ausweitung als Perzentil
"""
import os
import sys
import time

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ABLAGE = os.path.join("data", "_ra", "p73_fred.csv")
REIHEN = ("NASDAQCOM", "M2SL", "USREC", "T10Y2Y", "T10Y3M", "FEDFUNDS", "SAHMREALTIME", "CPIAUCSL")


def lade():
    if os.path.exists(ABLAGE):
        d = pd.read_csv(ABLAGE, parse_dates=["datum"])
        return {s: g.set_index("datum").wert for s, g in d.groupby("reihe")}
    import requests
    from dotenv import dotenv_values
    key = dotenv_values(".env").get("FRED_API_KEY")
    zeilen = []
    for s in REIHEN:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=90,
                         params={"series_id": s, "api_key": key, "file_type": "json", "observation_start": "1850-01-01"})
        for o in r.json()["observations"]:
            if o["value"] not in (".", ""):
                zeilen.append((s, o["date"], float(o["value"])))
        time.sleep(0.3)
    d = pd.DataFrame(zeilen, columns=["reihe", "datum", "wert"])
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    d.to_csv(ABLAGE, index=False)
    d["datum"] = pd.to_datetime(d.datum)
    return {s: g.set_index("datum").wert for s, g in d.groupby("reihe")}


def baer_phasen(p, grenze=0.20):
    """Hoch -> Tief mit Rueckgang >= grenze; Bullenmarkt = Tief -> naechstes Hoch, das einen Baeren einleitet (oder laufend)."""
    ath, ath_t, phasen = p.iloc[0], p.index[0], []
    tief, tief_t, im_baer = None, None, False
    for t, v in p.items():
        if not im_baer:
            if v > ath:
                ath, ath_t = v, t
            elif v <= ath * (1 - grenze):
                im_baer, tief, tief_t = True, v, t
        else:
            if v < tief:
                tief, tief_t = v, t
            if v >= ath:                                    # neues Hoch beendet den Baeren
                phasen.append((ath_t, tief_t, tief / ath - 1))
                im_baer, ath, ath_t = False, v, t
    offen = (ath_t, tief_t, tief / ath - 1) if im_baer else None
    return phasen, offen


def strecken(maske):
    """-> Liste (start, ende, wert) der zusammenhaengenden Strecken einer bool-Serie."""
    out, start, w = [], maske.index[0], maske.iloc[0]
    for t, v in maske.items():
        if v != w:
            out.append((start, t, w))
            start, w = t, v
    out.append((start, maske.index[-1], w))
    return out


def main():
    D = lade()
    nq = D["NASDAQCOM"]
    m2 = D["M2SL"]
    print("P73 ATLAS T3 · Nasdaq %s..%s · M2 %s..%s\n" % (nq.index[0].date(), nq.index[-1].date(), m2.index[0].date(), m2.index[-1].date()))
    phasen, offen = baer_phasen(nq)
    print("(a) Nasdaq-Baerenmaerkte (>= -20 %% vom Hoch): %d abgeschlossen%s" % (len(phasen), ", 1 laufend" if offen else ""))
    for h, t, r in phasen:
        print("    %s -> %s  %.0f %%  (%.1f Mon.)" % (h.date(), t.date(), 100 * r, (t - h).days / 30.44))
    bull = []
    tiefs = [nq.index[0]] + [t for _, t, _ in phasen]
    hochs = [h for h, _, _ in phasen] + ([offen[0]] if offen else [nq.index[-1]])
    for a, b in zip(tiefs, hochs[1:] + ([] if offen else [])):
        pass
    bull = [(tiefs[i], hochs[i + 1] if i + 1 < len(hochs) else nq.index[-1]) for i in range(len(tiefs))]
    dauern = np.array([(b - a).days / 30.44 for a, b in bull[1:]])        # ohne den Anfangs-Stumpf 1971
    laufend = None
    if not offen:
        laufend = (nq.index[-1] - tiefs[-1]).days / 30.44
    print("    Bullenmaerkte (Tief -> Hoch vor dem naechsten Baeren), ohne Anfang 1971: n %d · Median %.0f Mon. · Spanne %.0f..%.0f Mon."
          % (len(dauern), np.median(dauern), dauern.min(), dauern.max()))
    if laufend is not None:
        print("    LAUFENDER Bullenmarkt seit %s: %.0f Monate = Perzentil %.0f der abgeschlossenen" % (tiefs[-1].date(), laufend, 100 * np.mean(dauern < laufend)))
    else:
        print("    laufender Baer seit %s (Tief bisher %s, %.0f %%)" % (offen[0].date(), offen[1].date(), 100 * offen[2]))
    m2y = (m2 / m2.shift(12) - 1).dropna()
    st = [(a, b, w) for a, b, w in strecken(m2y > 0)]
    aus = np.array([(b - a).days / 30.44 for a, b, w in st[:-1] if w])
    print("\n(a) M2-Ausweitungen (J/J > 0) 1960-2026: %d abgeschlossene Strecken · Median %.0f Mon. · Spanne %.0f..%.0f Mon. · Schrumpfungen: %d Strecken"
          % (len(aus), np.median(aus), aus.min(), aus.max(), sum(1 for *_, w in st if not w)))
    for a, b, w in st:
        if not w:
            print("    M2-SCHRUMPFUNG %s .. %s (%.0f Mon.)" % (a.date(), b.date(), (b - a).days / 30.44))
    a_, b_, w_ = st[-1]
    print("    laufend seit %s: %s seit %.0f Monaten (Stand M2 %s, J/J %+.1f %%)" % (a_.date(), "Ausweitung" if w_ else "Schrumpfung",
                                                                              (b_ - a_).days / 30.44, m2.index[-1].date(), 100 * m2y.iloc[-1]))
    nqm = nq.resample("ME").last()
    baer_m = pd.Series(False, index=nqm.index)
    for h, t, r in phasen + ([offen] if offen else []):
        baer_m[(baer_m.index >= h) & (baer_m.index <= t)] = True
    m2a = (m2y > 0).reindex(nqm.index, method="ffill")
    ok = m2a.notna()
    bm, ma = ~baer_m[ok], m2a[ok].astype(bool)
    print("\n(b) Monate 1971-2026: Bullenmarkt-Anteil bei M2-Ausweitung %.0f %% (n %d) · bei M2-Schrumpfung %.0f %% (n %d)"
          % (100 * bm[ma].mean(), ma.sum(), 100 * bm[~ma].mean(), (~ma).sum()))
    if "CPIAUCSL" in D:
        real = (m2 / D["CPIAUCSL"].reindex(m2.index)).dropna()
        ry = (real / real.shift(12) - 1).dropna()
        rst = strecken(ry > 0)
        print("\n(b2) AUSKUNFT reales M2 (M2 / Verbraucherpreise, J/J > 0): %d Strecken seit %s; Schrumpfungen:" % (len(rst), ry.index[0].date()))
        for a, b, w in rst:
            if not w:
                print("    reales M2 SCHRUMPFT %s .. %s (%.0f Mon.)" % (a.date(), b.date(), (b - a).days / 30.44))
        ra = (ry > 0).reindex(nqm.index, method="ffill")
        ok2 = ra.notna()
        bm2, ra2 = ~baer_m[ok2], ra[ok2].astype(bool)
        print("    Bullenmarkt-Anteil der Monate: reales M2 waechst %.0f %% (n %d) · schrumpft %.0f %% (n %d)"
              % (100 * bm2[ra2].mean(), ra2.sum(), 100 * bm2[~ra2].mean(), (~ra2).sum()))
        print("    laufend: reales M2 J/J %+.1f %% (Stand %s)" % (100 * ry.iloc[-1], ry.index[-1].date()))
    print("    Auskunft: seit dem Tief des letzten grossen Baeren (2022-12-28) laeuft der Nasdaq %.0f Monate ohne -30 %%-Rueckgang"
          % ((nq.index[-1] - pd.Timestamp("2022-12-28")).days / 30.44))
    rec = D["USREC"]
    rs = [(a, b) for a, b, w in strecken(rec > 0) if w and a.year >= 1971]
    print("\n(c) NBER-Rezessionen seit 1971: %d" % len(rs))
    for a, b in rs:
        v = nq[a - pd.Timedelta(days=183):b + pd.Timedelta(days=183)]
        vor = nq[:a].iloc[-1]
        print("    %s .. %s · Nasdaq vom Beginn bis Tief binnen +-6 Mon. %.0f %% · Hoch der 12 Mon. davor bis Tief %.0f %%"
              % (a.date(), b.date(), 100 * (v.min() / vor - 1), 100 * (v.min() / nq[a - pd.Timedelta(days=365):a].max() - 1)))
    for kurve in ("T10Y2Y", "T10Y3M"):
        k = D[kurve].resample("ME").mean()
        inv = [(a, b) for a, b, w in strecken(k < 0) if w]
        print("\n(d) Inversion %s (Monatsmittel < 0) seit %s: %d Strecken" % (kurve, k.index[0].date(), len(inv)))
        for a, b in inv:
            nach = [r for r in rs if r[0] >= a]
            if nach:
                print("    Inversion ab %s (%.0f Mon.) -> Rezession ab %s nach %.0f Mon." % (a.date(), (b - a).days / 30.44, nach[0][0].date(), (nach[0][0] - a).days / 30.44))
            else:
                print("    Inversion ab %s (%.0f Mon.) -> keine Rezession bisher" % (a.date(), (b - a).days / 30.44))
    sahm = D["SAHMREALTIME"]
    print("\n(e) Reifegrad heute: Sahm-Regel %.2f (Stand %s; >= 0,50 gilt als Rezessionssignal) · Fed Funds %.2f %% (Stand %s)"
          % (sahm.iloc[-1], sahm.index[-1].date(), D["FEDFUNDS"].iloc[-1], D["FEDFUNDS"].index[-1].date()))


if __name__ == "__main__":
    main()
