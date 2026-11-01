# -*- coding: utf-8 -*-
"""FÜTTERUNG — Probe der SATZFORM (Ü1) an einem echten Stichtag (Nutzer 31.10.2026: „weiter mit dem Fütterungskonzept für Weg a“).

Zeigt, was eine Sicht (Ebene 2) als Eingabe bekäme: je Zustand EIN Satz mit Wert, Einordnung gegen die eigene Geschichte,
Veränderung, Stand und Kennzeichen. Nur lesend auf ``data/_sichten/sichten.db`` (mode=ro), NIE die Produktions-DB.

    python -X utf8 Basisinfos/Rechenkern_02_10/fuetterung_satzform_probe.py [--stichtag 2026-10-29] [--jahre 5]

⚠️ KEIN VORGRIFF: am Stichtag T gilt je Beobachtung der Jahrgang mit ``bekannt_ab <= T`` und ``bis >= T`` (bzw. offen); das Fenster
der Einordnung ist das, was man AM Stichtag über die Vergangenheit weiß.
⚠️ Das ist eine PROBE der Form, kein Betriebscode und keine Messung.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ABLAGE = os.path.join(PROJ, "data", "_sichten", "sichten.db")
AUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuetterung_satzform_probe.txt")

# Einheit "anteil" = Bruch, wird in % angezeigt (Basis, Prämie); FRED-Zinsen kommen schon in %.
# Die LESART sagt, was HÖHER heißt - beschreibend, nie wertend (Ü2: kein "bullish"/"überhitzt").
# Maß je Zustand: "niveau" (Zinsen, Aufschläge, Schwankung, Ton, Prämie) · "abstand200" (Preise: Abstand zum 200-T-Schnitt)
#                 · "jahr" (Mengen: Veränderung gegen Vorjahr)
ZUSTAENDE = [
    ("S1", "basis_quartal", "BTC", "Basis Quartalsfuture BTC", "niveau", "anteil", "höher = Terminkäufer zahlen mehr Aufschlag"),
    ("S1", "basis_quartal", "ETH", "Basis Quartalsfuture ETH", "niveau", "anteil", "höher = Terminkäufer zahlen mehr Aufschlag"),
    ("S1", "coinbase_praemie", "BTC", "Coinbase-Prämie BTC", "niveau", "anteil", "höher = US-Käufer zahlen mehr als der Rest der Welt"),
    ("S1", "coinbase_praemie", "ETH", "Coinbase-Prämie ETH", "niveau", "anteil", "höher = US-Käufer zahlen mehr als der Rest der Welt"),
    ("S1", "gdelt_ton", "krypto", "Nachrichtenton Krypto (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S2", "fred", "NETTO", "Netto-Liquidität Fed (Bilanz − TGA − RRP)", "jahr", "Mrd. USD", "höher = mehr Zentralbankgeld im Umlauf als vor einem Jahr"),
    ("S2", "fred", "M2SL", "Geldmenge M2", "jahr", "Mrd. USD", "höher = Geldmenge wächst schneller"),
    ("S2", "fred", "DFII10", "Realzins 10 J", "niveau", "%", "höher = teureres Geld nach Inflation"),
    ("S2", "fred", "DGS2", "Rendite 2 J", "niveau", "%", "höher = Markt erwartet höhere Leitzinsen"),
    ("S2", "fred", "T10Y2Y", "Zinskurve 10 J − 2 J", "niveau", "Pp", "höher = steilere Kurve"),
    ("S2", "gdelt_ton", "fed", "Nachrichtenton Fed (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S3", "yfinance", "^GSPC", "S&P 500", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "^NDX", "Nasdaq 100", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "SOXX", "Halbleiter (SOXX)", "abstand200", "", "höher = weiter über dem eigenen Schnitt"),
    ("S3", "yfinance", "^VIX", "VIX", "niveau", "", "höher = Aktienmarkt erwartet größere Schwankung"),
    ("S3", "yfinance", "^MOVE", "MOVE (Anleihe-Schwankung)", "niveau", "", "höher = Anleihemarkt erwartet größere Schwankung"),
    # 01.11.: BAA10Y statt Hochzins-Aufschlag BAMLH0A0HYM2 - den führt FRED (ICE-Lizenz) nur ab 10/2023, im Rückspiel ab Dez. 2025
    # wären das 2,1 J und ein wachsendes Fenster (SF7). BAA10Y liegt mit Jahrgängen ab 2018 vor und misst dieselbe Art Aufschlag.
    ("S3", "fred", "BAA10Y", "Kreditaufschlag Baa − 10 J", "niveau", "Pp", "höher = Kreditgeber verlangen mehr für Risiko"),
    ("S3", "fred", "NFCI", "Finanzlage NFCI", "niveau", "", "höher = straffere Finanzierungsbedingungen"),
    ("S3", "gdelt_ton", "aktien", "Nachrichtenton Aktienmarkt (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
    ("S4", "yfinance", "DX-Y.NYB", "Dollar-Index DXY", "abstand200", "", "höher = Dollar stärker als im eigenen Schnitt"),
    ("S4", "yfinance", "GC=F", "Gold", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S4", "yfinance", "BZ=F", "Öl Brent", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S4", "yfinance", "HG=F", "Kupfer", "abstand200", "USD", "höher = weiter über dem eigenen Schnitt"),
    ("S7", "gdelt_ton", "konflikt", "Nachrichtenton Krieg/Sanktionen/Zölle (GDELT)", "niveau", "", "höher = freundlicherer Ton"),
]


def stand_am(df: pd.DataFrame, T: str) -> pd.Series:
    """Je Beobachtungstag der am Stichtag gültige Jahrgang."""
    tag = T[:10]
    g = df[(df.bekannt_ab <= T) & (df.bis.isna() | (df.bis >= tag))]
    g = g.sort_values("bekannt_ab").groupby("datum").last()
    return g.wert.sort_index()


def klasse(p: float) -> str:
    return ("sehr tief" if p <= 5 else "tief" if p <= 20 else "normal" if p < 80 else "hoch" if p < 95 else "sehr hoch")


def satz(sicht, name, mass, einheit, lesart, s: pd.Series, T: str, jahre: int) -> tuple[str, bool, float]:
    s.index = pd.to_datetime(s.index)
    t = pd.Timestamp(T[:10])
    s = s[s.index < t]
    if mass == "abstand200":
        m = s.rolling(200, min_periods=150).mean()
        x = (s / m - 1) * 100
    elif mass == "jahr":
        v = s.reindex(pd.date_range(s.index.min(), s.index.max())).ffill()
        x = (v / v.shift(365) - 1) * 100
        x = x[x.index.isin(s.index)]
    else:
        x = s * (100 if einheit == "anteil" else 1)
    x = x.dropna()
    fenster = x[x.index >= t - pd.DateOffset(years=jahre)]
    jetzt, datum = x.iloc[-1], x.index[-1].strftime("%Y-%m-%d")
    p = (fenster < jetzt).mean() * 100 + (fenster == jetzt).mean() * 50
    ab = fenster.index.min()
    j = (t - ab).days / 365.25
    v20 = x[x.index <= x.index[-1] - pd.Timedelta(days=28)]
    rich = "" if v20.empty else " · vor 4 Wochen %+.2f" % v20.iloc[-1]
    if mass == "abstand200":
        wert = "%s %.2f%s, %+.1f %% zum 200-T-Schnitt" % (name, s.iloc[-1], (" " + einheit) if einheit else "", jetzt)
    elif mass == "jahr":
        wert = "%s %.0f %s, %+.1f %% gegen Vorjahr" % (name, s.iloc[-1], einheit, jetzt)
    else:
        wert = ("%s %.3g %s" % (name, jetzt, "%" if einheit == "anteil" else einheit)).rstrip()
    knapp = " ⚠ Fenster nur %.1f J" % j if j < jahre - 0.2 else ""
    abst = fenster.index.to_series().diff().dt.days.dropna()
    if len(abst) and abst.max() > max(10, 5 * abst.median()):   # 01.11.: ein Loch im Fenster ist so schlimm wie ein kurzes Fenster
        knapp += " ⚠ Lücke %d T ab %s" % (abst.max(), (abst.idxmax() - pd.Timedelta(days=int(abst.max()))).strftime("%Y-%m-%d"))
    zeile = "[%s] %s · Rang P%.0f der letzten %.1f J (ab %s) = %s (%s)%s · Stand %s%s · Fakt" % (
        sicht, wert, p, j, ab.strftime("%Y-%m"), klasse(p), lesart, rich, datum, knapp)
    return zeile, klasse(p) != "normal", (0.0 if "Lücke" in knapp else j)   # ein Loch zählt wie ein kurzes Fenster


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--stichtag", default="2026-10-29")
    a.add_argument("--jahre", type=int, default=5)
    o = a.parse_args()
    T = o.stichtag + "T00:00:00+00:00"
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE, uri=True)
    df = pd.read_sql("SELECT quelle, symbol, datum, wert, bekannt_ab, bis FROM reihe", c)
    c.close()

    def reihe(q, sym):
        if sym == "NETTO":   # WALCL und WTREGEN in Mio. USD, RRPONTSYD in Mrd. USD
            w, g, r = (stand_am(df[(df.quelle == "fred") & (df.symbol == k)], T) for k in ("WALCL", "WTREGEN", "RRPONTSYD"))
            tage = pd.date_range(min(w.index.min(), g.index.min()), T[:10])
            f = lambda s: s.set_axis(pd.to_datetime(s.index)).reindex(tage).ffill()
            n = (f(w) / 1000 - f(g) / 1000 - f(r).fillna(0)).dropna()
            n = n[n.index.isin(pd.to_datetime(w.index))]
            return n.set_axis(n.index.strftime("%Y-%m-%d"))
        return stand_am(df[(df.quelle == q) & (df.symbol == sym)], T)

    zeilen, auff, kurz = [], 0, 0
    aus = ["FÜTTERUNG — PROBE DER SATZFORM (Ü1) · Stichtag %s · Einordnung %d J · nur lesend %s" % (T, o.jahre, ABLAGE), ""]
    for sicht, q, sym, name, mass, einheit, lesart in ZUSTAENDE:
        z, a_, j = satz(sicht, name, mass, einheit, lesart, reihe(q, sym).copy(), T, o.jahre)
        zeilen.append((sicht, z, a_))
        auff += a_
        kurz += j < o.jahre - 0.2
    for sicht in ("S1", "S2", "S3", "S4", "S7"):
        aus.append("── %s ──" % sicht)
        aus += ["  " + ("● " if a_ else "  ") + z for s_, z, a_ in zeilen if s_ == sicht]
    aus += ["", "● = auffällig (Rang ≤ P20 oder ≥ P80) · %d von %d Zuständen auffällig · %d mit kürzerem Fenster als %d J" % (
        auff, len(zeilen), kurz, o.jahre),
        "Zeichen gesamt: %d (≈ %d Token bei 3,5–4 Zeichen je Token)" % (sum(len(z) for _, z, _ in zeilen),
                                                                       sum(len(z) for _, z, _ in zeilen) / 3.75)]
    text = "\n".join(aus)
    print(text)
    with open(AUS, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
