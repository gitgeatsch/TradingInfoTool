"""M-A MESSUNG Fassung 1 (Spot §60.5, Messplan vorab c18e23f2): Trendallokation BTC <-> EURCV nach R2 (10-Monats-Schnitt).

    python Basisinfos/Spot_Voranalyse_04_10/ma_messung.py

AUSLEGUNG, VOR DEM ERSTEN LAUF FESTGELEGT (im Plan nicht genau bestimmt):
- Der ZUSTAND wird auf dem BTC-Kurs in EUR berechnet (Plan: "gerechnet wird in EUR"); der Zustand auf USD laeuft als Auskunft mit.
- Monatsschluss = Tagesschluss am letzten Kalendertag (CoinMetrics ist lueckenlos). Das 10-Monats-Mittel enthaelt den laufenden Monat (Faber).
- Ausfuehrung zum Schluss des Folgetags (1. des Folgemonats); Teil A beginnt 2011-05-01 (erster Zustand 2011-04-30), Teil B am 2017-01-01.
- EUR-USD: EZB-Referenzkurs (EXR D.USD.EUR.SP00.A, 14:15 MEZ), gespeichert in data/_spot/ma_eurusd_ezb.csv; fehlende Tage mit dem Vortag.
  ABWEICHUNG VOM PLAN VOR DEM LAUF (21.10.2026): FRED (DEXUSEU) war beim ersten Abruf in Wartung (HTML "Site Maintenance" statt JSON);
  die EZB-Reihe ist ebenso amtlich und kostenfrei. Kein Ergebnis war vorher angesehen.
- BAERENPHASEN aus dem EUR-Kurs, Zickzack symmetrisch in Log: Hoch -> Tief bei mind. -50 %, das Tief gilt als bestaetigt, wenn der Kurs danach
  um mind. +100 % steigt (ln 2 = -ln 0,5). Unbestaetigt = laufend, zaehlt nicht fuer S4.
- vermieden je Phase = 1 - (Regel-Verm. Tief/Hoch - 1) / (Kurs Tief/Hoch - 1). Ausstiegs-Verspaetung = erster Ausstieg ab dem Hoch
  (war die Regel am Hoch schon draussen: 0 T); Wiedereinstieg = erster Einstieg nach dem Tief.
- Fehlausstieg = eine Draussen-Strecke, an deren Ende der Kurs HOEHER lag als beim Ausstieg.
- Umkehr-Probe: Rendite je Haltemonat (Ausfuehrungstag bis naechster Ausfuehrungstag), Mittel ueber die Monate DRAUSSEN.
- Nullwelt: Zustandsreihe des Teils zirkulaer verschoben um k = 12 .. n-12 Monate (alle). Rang = Anteil der Verschiebungen, die SCHLECHTER sind.
- Kosten (Anwendungszeile): die halbe Runde (0,28 / 0,405 %) je Kauf oder Verkauf, auch der erste Kauf; Halten zahlt den ersten Kauf.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

FX_DATEI = os.path.join("data", "_spot", "ma_eurusd_ezb.csv")
TEILE = {"A": ("2011-05-01", "2016-12-31"), "B": ("2017-01-01", "2026-09-30")}
KOSTEN = (0.0056, 0.0081)


def kurse(asset="btc"):
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    P = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset=? AND PriceUSD IS NOT NULL", c, params=(asset,), parse_dates=["tag"])
    c.close()
    return P.set_index("tag").PriceUSD.asfreq("D").ffill()


def eurusd():
    if not os.path.exists(FX_DATEI):
        import io
        import requests
        r = requests.get("https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A", timeout=90,
                         params={"format": "csvdata", "startPeriod": "2009-01-01"})
        r.raise_for_status()
        d = pd.read_csv(io.StringIO(r.text))[["TIME_PERIOD", "OBS_VALUE"]].dropna()
        d.columns = ["tag", "eurusd"]
        d.to_csv(FX_DATEI, index=False)
    return pd.read_csv(FX_DATEI, parse_dates=["tag"]).set_index("tag").eurusd


def in_eur(usd):
    F = eurusd()
    return (usd / F.reindex(F.index.union(usd.index)).ffill().reindex(usd.index)).dropna()


def zustand_r2(px):
    M = px.resample("ME").last()
    return (M > M.rolling(10).mean()).where(M.rolling(10).count() == 10).dropna().astype(bool)


def zustand_r3(px):
    M = px.resample("ME").last()
    return (M / M.shift(12) - 1 > 0).where(M.shift(12).notna()).dropna().astype(bool)


def zustand_r1(px):
    """Tagesregel: Zustand am Tagesschluss, Ausfuehrung am Folgetag - als 'Monatsreihe' mit Tagesindex."""
    return (px > px.rolling(200).mean()).where(px.rolling(200).count() == 200).dropna().astype(bool)


def lauf(px, Z, s, e, kosten=0.0):
    """Z: Zustand je Entscheidungstag (Index = Tag der Entscheidung). Ausfuehrung am Folgetag zum Schluss. -> (Vermoegen, Position, Haltewerte)."""
    exe = pd.Series(Z.values, index=Z.index + pd.Timedelta(days=1))
    tage = px.loc[s:e].index
    pos = exe.reindex(exe.index.union(tage)).ffill().reindex(tage)
    if pd.isna(pos.iloc[0]):
        raise ValueError("kein Zustand am Start %s" % s)
    pos = pos.astype(bool)
    p = px.loc[s:e]
    r = p.pct_change().fillna(0.0).values
    v = np.empty(len(p))
    v[0] = 1.0 * (1 - kosten / 2) if pos.iloc[0] else 1.0
    for i in range(1, len(p)):
        v[i] = v[i - 1] * (1 + (r[i] if pos.iloc[i - 1] else 0.0))
        if pos.iloc[i] != pos.iloc[i - 1]:
            v[i] *= 1 - kosten / 2
    V = pd.Series(v, index=p.index)
    H = p / p.iloc[0] * (1 - kosten / 2)
    return V, pos, H


def rueckgang(V):
    return float((V / V.cummax() - 1).min())


def kennzahlen(px, Z, s, e):
    V, pos, H = lauf(px, Z, s, e)
    w = int(pos.ne(pos.shift()).iloc[1:].sum())
    return {"end_halten": V.iloc[-1] / H.iloc[-1], "rg_regel": rueckgang(V), "rg_halten": rueckgang(H), "wechsel": w,
            "draussen": float(1 - pos.mean()), "V": V, "pos": pos, "H": H}


def phasen(px):
    """Zickzack -50 % / +100 % auf Tagesschluessen. -> Liste (hoch_tag, tief_tag, bestaetigt)."""
    aus, hoch_t, hoch_p, tief_t, tief_p, richtung = [], px.index[0], px.iloc[0], None, None, "auf"
    for t, p in px.items():
        if richtung == "auf":
            if p > hoch_p:
                hoch_t, hoch_p = t, p
            elif p <= hoch_p * 0.5:
                richtung, tief_t, tief_p = "ab", t, p
        else:
            if p < tief_p:
                tief_t, tief_p = t, p
            elif p >= tief_p * 2.0:
                aus.append((hoch_t, tief_t, True))
                richtung, hoch_t, hoch_p = "auf", t, p
    if richtung == "ab":
        aus.append((hoch_t, tief_t, False))
    return aus


def je_phase(px, V, pos, h, t):
    if h < V.index[0] or t > V.index[-1]:
        return None
    dk = px[t] / px[h] - 1
    dv = V[t] / V[h] - 1
    seg = pos.loc[h:]
    if not pos[h]:
        aus_tage, aus_pct = 0, 0.0
    else:
        a = seg[~seg]
        aus_tage, aus_pct = (int((a.index[0] - h).days), px[a.index[0]] / px[h] - 1) if len(a) else (None, None)
    nach = pos.loc[t:]
    ein = nach[nach]
    ein_tage, ein_pct = (int((ein.index[0] - t).days), px[ein.index[0]] / px[t] - 1) if len(ein) else (None, None)
    return {"kurs": dk, "regel": dv, "vermieden": 1 - dv / dk, "aus_tage": aus_tage, "aus_pct": aus_pct, "ein_tage": ein_tage, "ein_pct": ein_pct}


def fehlausstiege(px, pos):
    n = f = 0
    i = 1
    while i < len(pos):
        if pos.iloc[i - 1] and not pos.iloc[i]:
            j = i
            while j < len(pos) and not pos.iloc[j]:
                j += 1
            if j < len(pos):
                n += 1
                f += int(px.iloc[j] > px.iloc[i])
            i = j
        i += 1
    return n, f


def umkehr(px, Z, s, e):
    exe = pd.Series(Z.values, index=Z.index + pd.Timedelta(days=1)).loc[s:e]
    tage = list(exe.index) + [pd.Timestamp(e)]
    r_aus, r_drin = [], []
    for a, b, z in zip(tage[:-1], tage[1:], exe.values):
        rr = px[b] / px[a] - 1
        (r_drin if z else r_aus).append(rr)
    return (np.mean(r_aus) if r_aus else float("nan"), len(r_aus), np.mean(r_drin) if r_drin else float("nan"), len(r_drin))


def nullwelt(px, Z, s, e):
    """Zirkulaere Verschiebung der Monatszustaende des Teils (Entscheidungstage vom Vormonat des Starts bis zum letzten Monat vor e)."""
    z = Z.loc[pd.Timestamp(s) - pd.Timedelta(days=1):pd.Timestamp(e) - pd.Timedelta(days=1)]
    n = len(z)
    k0 = kennzahlen(px, z, s, e)
    eh, rg = [], []
    for k in range(12, n - 11):
        zk = pd.Series(np.roll(z.values, k), index=z.index)
        kk = kennzahlen(px, zk, s, e)
        eh.append(kk["end_halten"])
        rg.append(kk["rg_regel"])
    eh, rg = np.array(eh), np.array(rg)
    return {"n": len(eh), "rang_end": float(np.mean(eh < k0["end_halten"])), "rang_rg": float(np.mean(rg < k0["rg_regel"])),
            "null_end_median": float(np.median(eh)), "null_rg_median": float(np.median(rg))}


def bericht_teil(name, px, Z, s, e, ph, mit_null=True):
    k = kennzahlen(px, Z, s, e)
    print("  Teil %s %s bis %s: Endvermoegen / Halten %.3f · groesster Rueckgang Regel %.1f %% gegen Halten %.1f %% · Wechsel %d · draussen %.0f %%"
          % (name, s, e, k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"], k["wechsel"], 100 * k["draussen"]))
    nw = None
    if mit_null:
        nw = nullwelt(px, Z, s, e)
        print("    Nullwelt (%d Verschiebungen): Rang Endvermoegen %.2f (Median Null %.3f) · Rang Rueckgang %.2f (Median Null %.1f %%)"
              % (nw["n"], nw["rang_end"], nw["null_end_median"], nw["rang_rg"], 100 * nw["null_rg_median"]))
    u = umkehr(px, Z, s, e)
    print("    Umkehr: Haltemonat-Rendite draussen %+.1f %% (n %d) · drin %+.1f %% (n %d)" % (100 * u[0], u[1], 100 * u[2], u[3]))
    nf = fehlausstiege(px, k["pos"])
    print("    Ausstiege mit Wiedereinstieg %d, davon Fehlausstiege (Wiedereinstieg teurer) %d" % nf)
    zeilen = []
    for h, t, best in ph:
        if pd.Timestamp(s) <= h and t <= pd.Timestamp(e):
            r = je_phase(px, k["V"], k["pos"], h, t)
            if r:
                zeilen.append((h, t, best, r))
                print("    Phase %s -> %s%s: Kurs %.0f %% · Regel %.0f %% · vermieden %.0f %% · Ausstieg %s T nach dem Hoch (%s) · Wiedereinstieg %s T nach dem Tief (%s)"
                      % (h.date(), t.date(), "" if best else " (LAUFEND)", 100 * r["kurs"], 100 * r["regel"], 100 * r["vermieden"],
                         r["aus_tage"], "%+.0f %%" % (100 * r["aus_pct"]) if r["aus_pct"] is not None else "-",
                         r["ein_tage"], "%+.0f %%" % (100 * r["ein_pct"]) if r["ein_pct"] is not None else "-"))
    return k, nw, u, zeilen


def main():
    usd = kurse("btc")
    px = in_eur(usd)
    print("M-A MESSUNG Fassung 1 · BTC in EUR %s bis %s, %d Tage · EUR-USD bis %s" % (px.index[0].date(), px.index[-1].date(), len(px),
                                                                                     eurusd().index[-1].date()))
    Z = zustand_r2(px)
    ph = phasen(px)
    print("\nBaerenphasen (Zickzack -50 %/+100 %, EUR):")
    for h, t, b in ph:
        print("  %s -> %s  %.0f %%%s" % (h.date(), t.date(), 100 * (px[t] / px[h] - 1), "" if b else "  LAUFEND"))
    print("\nHAUPTREGEL R2 (10-Monats-Schnitt, Zustand in EUR)")
    erg = {}
    for name, (s, e) in TEILE.items():
        erg[name] = bericht_teil(name, px, Z, s, e, ph)
    # Urteil
    S1 = all(erg[n][2][0] < 0 for n in TEILE)
    S2 = all(erg[n][0]["rg_regel"] > erg[n][0]["rg_halten"] and erg[n][1]["rang_rg"] >= 0.90 for n in TEILE)
    S3 = all(erg[n][1]["rang_end"] >= 0.90 for n in TEILE)
    abg = [z for n in TEILE for z in erg[n][3] if z[2]]
    S4 = len(abg) > 0 and all(z[3]["vermieden"] > 0 for z in abg)
    umg = any(erg[n][1]["rang_rg"] <= 0.10 or erg[n][1]["rang_end"] <= 0.10 for n in TEILE)
    print("\nURTEIL nach §60.5: S1 Umkehr %s · S2 Rueckgang %s · S3 Endvermoegen %s · S4 jede abgeschlossene Phase vermieden %s (%d Phasen) · umgekehrt %s"
          % tuple(["ja" if x else "nein" for x in (S1, S2, S3)] + ["ja" if S4 else "nein", len(abg), "JA" if umg else "nein"]))
    if umg:
        folge = "wie 'traegt nicht', mit WORAN"
    elif S1 and S2 and S3 and S4:
        folge = "KANDIDAT (Handlung in der Spot-Mail nach Abstimmung)"
    elif S1 and S2 and S4:
        folge = "SENKT DAS RISIKO, KOSTET ERTRAG (Fakt-Zeile, Nutzerentscheidung)"
    elif not (S1 and S4):
        folge = "M-A TRAEGT NICHT"
    else:
        folge = "teilweise (S1 und S4 ja, S2 nein) - WORAN"
    print("FOLGE: %s" % folge)

    print("\nANWENDUNG netto (Bitpanda BTC je Runde 0,56 / 0,81 %):")
    for name, (s, e) in TEILE.items():
        for c in KOSTEN:
            V, pos, H = lauf(px, Z, s, e, c)
            print("  Teil %s, Kosten %.2f %%: Endvermoegen / Halten %.3f" % (name, 100 * c, V.iloc[-1] / H.iloc[-1]))

    print("\nAUSKUNFT")
    print(" ab 2024 (R2):")
    bericht_teil("ab2024", px, Z, "2024-01-01", "2026-09-30", ph, mit_null=False)
    print(" Zustand aus USD (R2), Bewertung in EUR:")
    Zu = zustand_r2(usd)
    for name, (s, e) in TEILE.items():
        k = kennzahlen(px, Zu, s, e)
        print("  Teil %s: Endverm./Halten %.3f · Rueckgang %.1f gegen %.1f %% · Wechsel %d" % (name, k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"], k["wechsel"]))
    print(" Rechnung ganz in USD (R2 auf USD):")
    for name, (s, e) in TEILE.items():
        k = kennzahlen(usd, Zu, s, e)
        print("  Teil %s: Endverm./Halten %.3f · Rueckgang %.1f gegen %.1f %%" % (name, k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"]))
    for lab, Zx in (("R1 200-Tage", zustand_r1(px)), ("R3 12-Monats-Momentum", zustand_r3(px))):
        print(" %s:" % lab)
        for name, (s, e) in TEILE.items():
            if Zx.index[0] + pd.Timedelta(days=1) > pd.Timestamp(s):
                s = str((Zx.index[0] + pd.Timedelta(days=1)).date())
            k = kennzahlen(px, Zx, s, e)
            print("  Teil %s (ab %s): Endverm./Halten %.3f · Rueckgang %.1f gegen %.1f %% · Wechsel %d" % (name, s, k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"], k["wechsel"]))
    print(" ETH mit R2 (EUR, ab 2016-06):")
    pe = in_eur(kurse("eth"))
    Ze = zustand_r2(pe)
    k = kennzahlen(pe, Ze, "2016-06-01", "2026-09-30")
    print("  Endverm./Halten %.3f · Rueckgang %.1f gegen %.1f %% · Wechsel %d · draussen %.0f %%" % (k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"], k["wechsel"], 100 * k["draussen"]))
    for h, t, b in phasen(pe):
        r = je_phase(pe, k["V"], k["pos"], h, t)
        if r:
            print("  Phase %s -> %s%s: Kurs %.0f %% · Regel %.0f %% · vermieden %.0f %%" % (h.date(), t.date(), "" if b else " (LAUFEND)", 100 * r["kurs"], 100 * r["regel"], 100 * r["vermieden"]))
    print(" Starts je 01.01. bis 2026-09-30 (R2, BTC EUR):")
    kl = 0
    jahre = list(range(2012, 2027))
    for j in jahre:
        k = kennzahlen(px, Z, "%d-01-01" % j, "2026-09-30")
        kl += int(k["rg_regel"] > k["rg_halten"])
        print("  %d: Endverm./Halten %.3f · Rueckgang %.1f gegen %.1f %%" % (j, k["end_halten"], 100 * k["rg_regel"], 100 * k["rg_halten"]))
    print("  kleinerer Rueckgang in %d von %d Starts" % (kl, len(jahre)))


if __name__ == "__main__":
    main()
