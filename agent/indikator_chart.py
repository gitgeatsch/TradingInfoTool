"""Wochen- und Tageschart mit RSI und MACD fuer die Signalmails (O45, 11.10.2026).

Nutzer 10.10.: *"in allen Signalmails - Spot und Hebel - nur wenn wir die Daten haben, fuer die Assets MACD und RSI im Wochenchart
mitliefern"*; 11.10.: *"das sollen schon Charts sein und nicht nur ... Durchschnittswerte"*, Auswahl **Woche + Tag**.

Je Ebene ein Bild: Kerzen (abgeschlossene Wochen bzw. Tage), RSI 14 mit 30/70, MACD 12/26/9 mit Histogramm. Es ist KONTEXT in der
Mail (Regel 4, E-91) - kein Ausloeser: es aendert weder Signal noch Stufe noch Versand, und scheitert es, geht die Mail ohne Bild.

DATEN: die stuendlichen Binance-Kurse der REGEL0 (`stundenkurse.db`, dann `stundenkurse_alle.db`, nur lesend `mode=ro`) - am NB
stuendlich vom Nachlader fortgeschrieben, ab 2023. Keine weitere Quelle, kein Netz.

⚠️ ABGESCHLOSSEN NACH DER UHR, NICHT NACH DER POSITION (Gegenprobe 11.10.): eine Kerze zaehlt nur, wenn ihr Zeitraum vorbei ist
UND mindestens 90 % der Stunden vorliegen. Die erste Fassung liess pauschal die letzte Kerze weg - endete die Reihe frueh (aeltere
Datei), fiel damit eine VOLLSTAENDIGE Woche weg.

⚠️ WOCHENGRENZE: Montag 00:00 bis Montag 00:00 UTC (wie Binance) - ``resample("W-MON", closed="left", label="left")``. Die
pandas-Vorgabe "W-SUN" schneidet mit closed="right" und haette die Sonntagsstunden in die FOLGEwoche gelegt.

WAEHRUNG: ``fx`` (EUR je Binance-Einheit) rechnet in Euro um - REGEL0 nimmt ``r["eur_je_usd"]`` (Bitpanda-Ticker / Binance-Kurs,
damit ist auch der Faktor bei 1000CAT erfasst). Ohne ``fx`` bleibt es USDT und sagt das im Titel. RSI ist skalenfrei, MACD
skaliert linear - der Verlauf aendert sich durch die Umrechnung nicht.
"""
from __future__ import annotations

import io
import os
import sqlite3
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZUORDNUNG = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db")
EBENEN = {
    "W": {"regel": "W-MON", "stunden": 168, "zeigen": 104, "name": "Wochenchart", "einheit": "Wochen"},
    "D": {"regel": "D", "stunden": 24, "zeigen": 180, "name": "Tageschart", "einheit": "Tage"},
}
MIN_ANTEIL = 0.9          # Kerze nur mit >= 90 % der Stunden
MACD_MIN, RSI_MIN = 35, 15  # wie indicators/calculations.macd/rsi


def _ro(pfad: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=5)


def stunden(ordner: str, symbol: str) -> list:
    """Alle Stunden (stunde, open, high, low, close) eines Binance-Symbols - erste Datei, die es fuehrt (wie regel0_chart.reihe)."""
    for f in DATEIEN:
        p = os.path.join(ordner, f)
        if not os.path.exists(p):
            continue
        c = _ro(p)
        try:
            r = c.execute("SELECT stunde, open, high, low, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (symbol,)).fetchall()
        finally:
            c.close()
        if r:
            return r
    return []


def kerzen(roh: list, ebene: str, jetzt: datetime | None = None):
    """Abgeschlossene Kerzen der Ebene als DataFrame (Index = Beginn, Spalten o/h/l/c, n = Stunden). Leer, wenn nichts da ist."""
    import pandas as pd

    jetzt = jetzt or datetime.now(timezone.utc)
    e = EBENEN[ebene]
    if not roh:
        return pd.DataFrame(columns=["o", "h", "l", "c", "n"])
    df = pd.DataFrame(roh, columns=["t", "o", "h", "l", "c"])
    df.index = pd.to_datetime(df["t"], utc=True)
    if ebene == "W":
        g = df.resample(e["regel"], closed="left", label="left")
    else:
        g = df.resample(e["regel"])
    k = g.agg({"o": "first", "h": "max", "l": "min", "c": "last"})
    k["n"] = g["c"].count()
    ende = k.index + pd.Timedelta(hours=e["stunden"])
    voll = (ende <= pd.Timestamp(jetzt)) & (k["n"] >= MIN_ANTEIL * e["stunden"])
    return k[voll].dropna(subset=["o", "h", "l", "c"])


def werte(k) -> dict:
    """RSI 14 und MACD 12/26/9 ueber ALLE abgeschlossenen Kerzen (der Verlauf vor dem gezeigten Fenster zaehlt mit)."""
    import numpy as np
    from indicators.calculations import macd, rsi

    cl = k["c"].values.astype(float)
    m, r = macd(cl), rsi(cl)
    aus = {"n": len(cl), "rsi": r.value if r.available else None, "macd": None}
    if m.available:
        aus["macd"] = {x: np.asarray(m.value[x]) for x in ("macd", "signal", "histogram")}
    return aus


def bild(ordner: str, symbol: str, ebene: str, name: str | None = None, fx: float | None = None,
         jetzt: datetime | None = None, roh: list | None = None) -> bytes | None:
    """PNG-Bytes (Kerzen + RSI + MACD) oder None, wenn es keine abgeschlossene Kerze gibt. ``name``: Bitpanda-Name fuer den Titel."""
    e = EBENEN[ebene]
    k = kerzen(roh if roh is not None else stunden(ordner, symbol), ebene, jetzt)
    if k.empty:
        return None
    if fx:
        k = k.copy()
        for s in ("o", "h", "l", "c"):
            k[s] = k[s] * float(fx)
    w = werte(k)
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = min(e["zeigen"], len(k))
    kz = k.iloc[-n:]
    x = np.arange(n)
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 7.2), dpi=100, sharex=True, gridspec_kw={"height_ratios": [3, 1.2, 1.4]})
    try:
        for i, (o, h, l, c) in enumerate(zip(kz["o"], kz["h"], kz["l"], kz["c"])):
            farbe = "#2e7d32" if c >= o else "#c62828"
            a1.vlines(i, l, h, color=farbe, linewidth=0.8)
            a1.add_patch(plt.Rectangle((i - 0.35, min(o, c)), 0.7, abs(c - o) or (h - l) * 0.01 or abs(c) * 1e-4, color=farbe))
        a1.set_title("%s – %s (Binance, %s), letzte %d %s bis %s" % (
            name or symbol, e["name"], "in EUR umgerechnet" if fx else "USDT", n, e["einheit"],
            (kz.index[-1] + timedelta(hours=e["stunden"] - 1)).strftime("%d.%m.%Y")), fontsize=10, loc="left")
        a1.grid(alpha=0.25)
        if w["rsi"] is not None:
            rv = np.asarray(w["rsi"])[-n:]
            a2.plot(x, rv, color="#6a1b9a", linewidth=1.3)
            a2.text(n - 1, rv[-1], "  %.1f" % rv[-1], va="center", fontsize=9)
        else:
            a2.text(0.5, 0.5, "RSI: zu kurz (%d %s, braucht %d)" % (w["n"], e["einheit"], RSI_MIN), ha="center", va="center",
                    transform=a2.transAxes, color="#777")
        for y in (70, 30):
            a2.axhline(y, color="#999", ls="--", lw=0.8)
        a2.set_ylim(0, 100)
        a2.set_ylabel("RSI 14")
        a2.grid(alpha=0.25)
        if w["macd"] is not None:
            mm, ss, hh = (w["macd"][s_][-n:] for s_ in ("macd", "signal", "histogram"))
            a3.bar(x, hh, color=["#2e7d32" if v >= 0 else "#c62828" for v in np.nan_to_num(hh)], width=0.7, alpha=0.6)
            a3.plot(x, mm, color="#1f4e79", lw=1.2, label="MACD 12/26")
            a3.plot(x, ss, color="#e65100", lw=1.0, label="Signal 9")
            a3.legend(fontsize=8, loc="upper left")
        else:
            a3.text(0.5, 0.5, "MACD: zu kurz (%d %s, braucht %d)" % (w["n"], e["einheit"], MACD_MIN), ha="center", va="center",
                    transform=a3.transAxes, color="#777")
        a3.axhline(0, color="#999", lw=0.6)
        a3.set_ylabel("MACD")
        a3.grid(alpha=0.25)
        schritt = max(1, n // 8)
        ticks = list(range(0, n, schritt))
        a3.set_xticks(ticks)
        a3.set_xticklabels([kz.index[i].strftime("%m/%y" if ebene == "W" else "%d.%m.") for i in ticks])
        fig.tight_layout()
        puf = io.BytesIO()
        fig.savefig(puf, format="png")
        return puf.getvalue()
    finally:
        plt.close(fig)


def bilder(ordner: str, symbol: str, name: str | None = None, fx: float | None = None, jetzt: datetime | None = None,
           praefix: str = "chart", roh: list | None = None) -> list:
    """Woche + Tag als Bildliste fuer ``send_notification_email(inline_images=...)``. Ein Lesezugriff fuer beide Ebenen."""
    roh = roh if roh is not None else stunden(ordner, symbol)
    aus = []
    for ebene in ("W", "D"):
        png = bild(ordner, symbol, ebene, name, fx, jetzt, roh)
        if png:
            aus.append({"png": png, "alt": "%s %s" % (name or symbol, EBENEN[ebene]["name"]),
                        "filename": "%s_%s_%s.png" % (praefix, symbol, "woche" if ebene == "W" else "tag")})
    return aus


def zuordnung(pfad: str | None = None) -> dict:
    """Bitpanda-Symbol -> (Binance-Symbol oder None bei Sperre). Ohne Eintrag gilt das gleiche Kuerzel (Basisinfos/symbol_zuordnung.csv)."""
    import csv

    pfad = pfad or ZUORDNUNG
    zu = {}
    if os.path.exists(pfad):
        for r in csv.DictReader(open(pfad, encoding="utf-8"), delimiter=";"):
            zu[r["bitpanda"]] = None if r["markt"] == "gesperrt" else r["binance"]
    return zu


def bilder_hebel(ordner: str, bitpanda_symbol: str, kurs_eur: float | None = None, jetzt: datetime | None = None) -> list:
    """Fuer die H15-Fuehrungsmail: Bitpanda-Symbol -> Binance, EUR ueber den H15-Kurs (kurs_eur / letzter Binance-Schluss)."""
    b = zuordnung().get(bitpanda_symbol, bitpanda_symbol)
    if not b:
        return []
    roh = stunden(ordner, b)
    fx = (float(kurs_eur) / float(roh[-1][4])) if (kurs_eur and roh and roh[-1][4]) else None
    return bilder(ordner, b, bitpanda_symbol, fx, jetzt, "hebel", roh)
