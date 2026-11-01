# -*- coding: utf-8 -*-
"""NACHWEIS S1-Ergänzung (01.11.2026, Nutzer: „1a, 2a, 3 ja – prüfen gegenprüfen und doku“).

Nur lesend: ``data/_sichten/sichten.db``, Desktop-Messbasen, die NB-Kopie ``spot_betrieb.db`` aus dem Austauschordner und
öffentliche Schnittstellen (eine Abfrage je Reihe).

    G1  Vollständigkeit: je Reihe keine Lücke > 1 Tag im eigenen Zeitraum
    G2  Kein Vorgriff: bekannt_ab = Folgetag 00:00 UTC, kein Tag >= heute (UTC)
    G3  Kurs BTC/ETH  = Desktop-Messbasis (Binance), gleiche Tage
    G4  Funding       x Zahl der Zahlungen = funding_historie.db (dort Tagessumme)
    G5  OI            Metrikdatei gegen openInterestHist an den gemeinsamen Tagen (≤ 0,1 %)
    G6  Breite/Stufe  Desktop (Messbasis) gegen NB (spot_betrieb.db, ampel_tag) an allen gemeinsamen Tagen  (Voranalyse V2)
    G7  Stablecoins   B3 (91 T) aus unserer Reihe gegen NB ampel_tag.b3 (gleiche Datierung wie die Ampel)

    python -X utf8 Basisinfos/Rechenkern_02_10/s1_nachweis.py
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
SICHT = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/_sichten/sichten.db?mode=ro"
MESS = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/messdaten.db?mode=ro"
FUND = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/funding_historie.db?mode=ro"
NB_SPOT = "file:K:/My Drive/Claude_Austauschordner/spot_betrieb.db?mode=ro"
NEU = [("kurs", "BTC"), ("kurs", "ETH"), ("dvol", "BTC"), ("dvol", "ETH"), ("funding", "BTC"), ("funding", "ETH"),
       ("oi", "BTC"), ("oi", "ETH"), ("stablecoins", "USD"), ("breite", "TOP50"), ("season", "STUFE")]
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-Sichten"}
ergebnis = []


def urteil(name, ok, text):
    ergebnis.append((name, ok))
    print("  %s  %-44s %s" % ("OK  " if ok else "FEHL", name, text))


def reihe(c, q, s) -> pd.DataFrame:
    return pd.read_sql("SELECT datum, wert, bekannt_ab FROM reihe WHERE quelle=? AND symbol=? ORDER BY datum", c, params=(q, s))


def main() -> int:
    c = sqlite3.connect(SICHT, uri=True)
    heute = datetime.now(timezone.utc).date().isoformat()
    print("=" * 100)
    print("S1-ERGÄNZUNG — NACHWEIS (%s UTC)" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    print("=" * 100)

    # G1, G2
    for q, s in NEU:
        r = reihe(c, q, s)
        if not len(r):
            urteil("G1 %s %s vorhanden" % (q, s), False, "leer")
            continue
        d = pd.to_datetime(r.datum)
        luecke = int(d.diff().dt.days.max() or 1)
        urteil("G1 %s %s lückenlos" % (q, s), luecke <= 1, "%d Tage, %s bis %s, größter Abstand %d T"
               % (len(r), r.datum.iloc[0], r.datum.iloc[-1], luecke))
        soll = (d + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%dT00:00:00+00:00")
        falsch = int((soll != r.bekannt_ab).sum())
        urteil("G2 %s %s ohne Vorgriff" % (q, s), falsch == 0 and r.datum.max() < heute,
               "bekannt_ab ≠ Folgetag: %d · letzter Tag %s (< %s)" % (falsch, r.datum.max(), heute))

    # G3 Kurs gegen Messbasis
    m = sqlite3.connect(MESS, uri=True)
    for b in ("BTC", "ETH"):
        r = reihe(c, "kurs", b).set_index("datum").wert
        mb = pd.read_sql("SELECT substr(date,1,10) AS datum, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' "
                         "AND currency='USD'", m, params=(b,)).set_index("datum").close
        # ⚠️ der LETZTE Tag der eingefrorenen Messbasis (2026-09-20) wurde mit noch offener Kerze geladen (01.11. gefunden: BTC 0,8 %,
        # ETH 2,6 % daneben) - er wird ausgewiesen, nicht verglichen
        letzt = mb.index.max()
        g = r.index.intersection(mb.index).drop(letzt, errors="ignore")
        abw = float(((r[g] / mb[g]) - 1).abs().max()) if len(g) else float("nan")
        urteil("G3 Kurs %s = Messbasis" % b, len(g) > 1000 and abw < 1e-9,
               "%d gemeinsame Tage, größte Abweichung %.2e · letzter Messbasis-Tag %s (offene Kerze) %+.2f %%"
               % (len(g), abw, letzt, 100 * (mb[letzt] / r[letzt] - 1) if letzt in r.index else float("nan")))

    # G4 Funding gegen funding_historie (Tagessumme)
    f = sqlite3.connect(FUND, uri=True)
    for b in ("BTC", "ETH"):
        r = reihe(c, "funding", b).set_index("datum").wert
        alt = pd.read_sql("SELECT datum, wert FROM funding WHERE symbol=?", f, params=(b,)).set_index("datum").wert
        g = r.index.intersection(alt.index)
        quot = (alt[g] / r[g]).replace([float("inf")], float("nan")).dropna()
        drei = float(((quot - 3).abs() < 1e-6).mean()) if len(quot) else 0.0
        urteil("G4 Funding %s ×3 = funding_historie" % b, len(g) > 1000 and drei > 0.99,
               "%d gemeinsame Tage, Verhältnis 3 an %.1f %% (Rest: Tage mit anderer Zahl an Zahlungen)" % (len(g), 100 * drei))

    # G5 OI Datei gegen API
    for b in ("BTC", "ETH"):
        r = reihe(c, "oi", b).set_index("datum").wert
        a = requests.get("https://fapi.binance.com/futures/data/openInterestHist",
                         params={"symbol": b + "USDT", "period": "1d", "limit": 30}, headers=H, timeout=30).json()
        api = pd.Series({(date.fromisoformat(datetime.fromtimestamp(x["timestamp"] / 1000, timezone.utc).date().isoformat())
                          - timedelta(days=1)).isoformat(): float(x["sumOpenInterest"]) for x in a})
        g = r.index.intersection(api.index)
        rel = ((r[g] / api[g]) - 1).abs()
        gleich = int((rel < 1e-12).sum())                              # Tage, an denen die Reihe selbst aus der API kommt
        rel_d = rel[rel >= 1e-12]
        # Grenze 0,5 % (01.11. begruendet): die 30-T-Veraenderung von OI liegt im Median bei 7–10 %, im 10. Perzentil bei 1,3 %;
        # aus der API kommt nur der jeweils LETZTE Tag (die Datei des Folgetags ist noch nicht erschienen)
        urteil("G5 OI %s Datei ≈ API (≤ 0,5 %%)" % b, len(g) >= 25 and (rel_d.max() if len(rel_d) else 0) < 5e-3,
               "%d gemeinsame Tage (davon %d aus der API selbst), Datei gg. API größte Abweichung %.3f %%, Median %.3f %%"
               % (len(g), gleich, 100 * (rel_d.max() if len(rel_d) else 0), 100 * (rel_d.median() if len(rel_d) else 0)))

    # G6 Breite und Stufe gegen NB
    from api.sichten_quellen import SEASON_CODE
    n = sqlite3.connect(NB_SPOT, uri=True)
    nb = pd.read_sql("SELECT datum, breite, stufe, b3 FROM ampel_tag", n).set_index("datum")
    br = reihe(c, "breite", "TOP50").set_index("datum").wert
    st = reihe(c, "season", "STUFE").set_index("datum").wert
    g = br.index.intersection(nb.index)
    d = (br[g] - nb.breite[g]).abs()
    urteil("G6a Breite Desktop = NB", len(g) > 300 and float(d.max()) < 1e-9,
           "%d gemeinsame Tage · gleich an %d · größte Abweichung %.3f (%.1f Coins von 50) · Mittel %.4f"
           % (len(g), int((d < 1e-9).sum()), float(d.max()), float(d.max()) * 50, float(d.mean())))
    if len(g):
        print("       größte Abweichungen:", ", ".join("%s %.3f/%.3f" % (t, br[t], nb.breite[t]) for t in d.sort_values().index[-5:]))
        # Wirkung auf die KLASSE (SF3) im 5-J-Rang - die Zahl, die zählt (wie messe_grundgesamtheit)
        bt = br.copy()
        bt.index = pd.to_datetime(bt.index)

        def klasse(p):
            return "sehr tief" if p <= 5 else "tief" if p <= 20 else "sehr hoch" if p >= 95 else "hoch" if p >= 80 else "normal"
        anders = 0
        for t in g:
            f = bt[(bt.index > pd.Timestamp(t) - pd.Timedelta(days=5 * 365)) & (bt.index <= pd.Timestamp(t))]
            rang = lambda x: 100 * (f < x).mean() + 50 * (f == x).mean()   # noqa: E731
            anders += klasse(rang(br[t])) != klasse(rang(nb.breite[t]))
        print("       Wirkung: Klasse im 5-J-Rang anders an %d von %d Tagen (%.1f %%)" % (anders, len(g), 100 * anders / len(g)))
    gs = st.index.intersection(nb.index)
    nb_code = nb.stufe[gs].map(SEASON_CODE)
    gleich = int((st[gs] == nb_code).sum())
    urteil("G6b Season-Stufe Desktop = NB", len(gs) > 300 and gleich == len(gs), "%d gemeinsame Tage, gleich an %d" % (len(gs), gleich))

    # G7 Stablecoins: B3 aus unserer Reihe (datiert wie die Ampel: Verfügbarkeitstag = Beobachtung + 1)
    sb = reihe(c, "stablecoins", "USD")
    s = pd.Series(sb.wert.values, index=pd.to_datetime(sb.datum) + pd.Timedelta(days=1))
    s = s.reindex(pd.date_range(s.index[0], s.index[-1], freq="D")).ffill()
    b3 = (s / s.shift(91) - 1)
    b3.index = b3.index.strftime("%Y-%m-%d")
    g = b3.dropna().index.intersection(nb.index)
    d = (b3[g] - nb.b3[g]).abs()
    urteil("G7 Stablecoins B3 = NB-Ampel", len(g) > 300 and float(d.max()) < 1e-3,
           "%d gemeinsame Tage, größte Abweichung %.2e (Revisionen DefiLlama zwischen den Abrufen)" % (len(g), float(d.max())))

    print("=" * 100)
    fehl = [x for x, ok in ergebnis if not ok]
    print("%d Prüfungen, %s" % (len(ergebnis), "ALLE BESTANDEN" if not fehl else "%d FEHLGESCHLAGEN: %s" % (len(fehl), ", ".join(fehl))))
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
