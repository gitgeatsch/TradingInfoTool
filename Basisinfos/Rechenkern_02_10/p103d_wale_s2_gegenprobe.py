# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — GEGENPROBE der Voranalyse (31.10.2026), jeweils auf einem ZWEITEN Weg:

    1  Spotmarkt und Dateigrößen: S3-Verzeichnis des Archivs (ListBucket) statt HEAD je Datei
    2  Abdeckung: eigene Schleife je Einstieg mit dem Spotbeginn aus dem S3-Verzeichnis statt der Pandas-Maske
    3  Ertragsweg der Einstiege: Nachbildung der Referenzzahl aus F-1 (p71/Voranalyse_REGEL0_Marktfilter §5:
       unverzerrt 1, 2025-26, alle Handel netto -0,184 % je Handel bei 0,48 % Kosten)
    4  Tagesprofil: D(0..24) mit dem Ertragsweg von Fassung 4 (B.ertrag) statt des eigenen Fensters

    python -X utf8 Basisinfos/Rechenkern_02_10/p103d_wale_s2_gegenprobe.py
"""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p103_wale_s2_voranalyse as V  # noqa: E402
import p103b_wale_s2_aufloesung as A  # noqa: E402
import p103c_wale_s2_tagesprofil as G  # noqa: E402
import p102_wale_basis as B  # noqa: E402

LISTE = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/aggTrades/{p}/"
AUS = []


def zeige(s=""):
    print(s, flush=True)
    AUS.append(s)


def verzeichnis(p):
    r = requests.get(LISTE.format(p=p), headers=V.H, timeout=60)
    r.raise_for_status()
    assert "<IsTruncated>false</IsTruncated>" in r.text, p
    return {m: int(g) for m, g in re.findall(r"aggTrades-(\d{4}-\d{2})\.zip</Key>.*?<Size>(\d+)</Size>", r.text)}


def main():
    zeige("GEGENPROBE VORANALYSE G16 STUFE 2 (Gerät %s, %s)" % (os.environ.get("COMPUTERNAME", "?"), datetime.now().isoformat(timespec="seconds")))
    E = V.einstiege()
    alle = sorted(set().union(*[set(e.symbol) for e in E.values()]))
    T = V.spot_tabelle(alle)
    MASKE, paar, *_ = V.abdeckung(E, T)
    ok_alle = True

    # ── 1 ──
    paare = sorted({p for s in alle for p in V.kandidaten(s)})
    with ThreadPoolExecutor(8) as ex:
        L = dict(zip(paare, ex.map(verzeichnis, paare)))
    bereich = {"%04d-%02d" % jm for jm in V.monate()}
    abw = 0
    for _, z in T.iterrows():
        soll = L[z.paar].get(z.monat, -1)
        if (soll > 0) != (z.bytes > 0) or (soll > 0 and soll != z.bytes):
            abw += 1
    mit_spot = {s for s in alle if any(set(L[p]) & bereich for p in V.kandidaten(s))}
    noetig = [s for s in mit_spot if s not in V.GELADEN]
    gb = sum(b for s in noetig for m, b in L[s + "USDT"].items() if m in bereich) / 1e9
    zeige("\n1 S3-Verzeichnis: %d Paare · Abweichungen zu HEAD (Existenz oder Größe) %d von %d Zeilen · mit Spotmarkt %d (Voranalyse %d) · "
          "Download %.1f GB" % (len(paare), abw, len(T), len(mit_spot), len(paar), gb))
    ok_alle &= abw == 0 and len(mit_spot) == len(paar)

    # ── 2 ──
    beginn = {}
    for s in mit_spot:
        ms = sorted(m for m in L[s + "USDT"] if m in bereich)
        beginn[s] = (max(pd.Timestamp(V.START), pd.Timestamp(ms[0] + "-01")), pd.Timestamp(ms[-1] + "-01") + pd.offsets.MonthEnd(0))
    for m, e in E.items():
        n = 0
        for s, z in zip(e.symbol, e.ein):
            if s in beginn:
                vt = z.normalize() - pd.Timedelta(days=1)
                n += (vt - beginn[s][0]).days >= V.VORLAUF and vt <= beginn[s][1]
        zeige("2 Abdeckung %-13s eigene Schleife %5d · Voranalyse %5d · %s" % (m, n, MASKE[m].sum(), "✔" if n == MASKE[m].sum() else "✖"))
        ok_alle &= n == MASKE[m].sum()

    # ── 3 ──
    e = E["unverzerrt_1"]
    e = e[(e.zeit >= "2025-01-01")].copy()
    y = A.ertraege(e)
    netto = np.nanmean(np.expm1(y)) - 0.0048
    zeige("3 Ertragsweg: unverzerrt 1, 2025-26, %d von %d Handel mit Kurs · netto %.3f %% je Handel (Referenz F-1 -0,184 %%) %s" % (
        np.isfinite(y).sum(), len(e), 100 * netto, "✔" if abs(100 * netto + 0.184) < 0.0015 else "✖"))
    ok_alle &= abs(100 * netto + 0.184) < 0.0015

    # ── 4 ──
    B.fassung4()
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    S = B.SYMBOLE
    con = B.ro()
    px = {s: B.kurse(con, s) for s in S}
    con.close()
    lab = [aus[s]["markt"]["spot"][B.Q_HAUPT][3][w] for s in S]
    tgw = [d for d, m in zip(tg, w) if m]
    d_b = B.differenz_gepoolt(lab, [aus[s]["y"][(1, 0)][w] for s in S])
    d_g = B.differenz_gepoolt(lab, [G.fenster(px[s], tgw, 0, 24) for s in S])
    d_b6 = B.differenz_gepoolt(lab, [aus[s]["y"][(1, 6)][w] for s in S])
    d_g6 = B.differenz_gepoolt(lab, [G.fenster(px[s], tgw, 6, 30) for s in S])
    zeige("4 Tagesprofil: D(0..24) B.ertrag %.6f · eigenes Fenster %.6f · D(6..30) %.6f / %.6f · %s" % (
        d_b, d_g, d_b6, d_g6, "✔" if abs(d_b - d_g) < 1e-12 and abs(d_b6 - d_g6) < 1e-12 else "✖"))
    ok_alle &= abs(d_b - d_g) < 1e-12 and abs(d_b6 - d_g6) < 1e-12

    zeige("\nGEGENPROBE %s" % ("BESTANDEN" if ok_alle else "NICHT BESTANDEN"))
    with open(os.path.join(HIER, "p103d_wale_s2_gegenprobe.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
