"""P66 L-C2 VORANALYSE (19.10.2026, Schritt7 §23.73): Markttag-Risiko aus ALLGEMEINEN Nachrichten. Nur lesend + 12 LLM-Testfragen.

    python Basisinfos/Rechenkern_02_10/p66_lc2_voranalyse.py

Kein Ergebnisvergleich Nachricht -> Ausgang (bleibt der vorab festgelegten Messung).
V1 Datenlage      Meldungen je Kalendertag (alle 9 Feeds, Titel-Dubletten entfernt); Meldungen in den 24 h vor jedem Einstieg
                  (Median je Tag) - alle Tage, die 136 Tage mit Tief-Fall, die 10 groessten Tage
V2 Zielgroesse    je Einstiegstag Anteil der Einstiege mit Tief binnen 24 h <= -10 %; wie viele 'Absturztage' (Anteil >= 25 %, >= 5 Einstiege)
V3 Kontamination  12 Testfragen an gemini-3.5-flash-lite (Temperatur 0): BTC-Schlusskurs an einem Tag 2025-26 'aus dem Gedaechtnis' -
                  Abweichung zum echten Kurs (coinmetrics.db). Kennt es den Kurs (Fehler < 5 %), ist es fuer diese Zeit KONTAMINIERT.
V4 Massstab       vorab festgelegte Warnwort-Liste (WARN): nur Zahl der Treffer je 24-h-Fenster, kein Ergebnisvergleich
"""
import json
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
WARN = ("crash", "plunge", "plummet", "tumble", "sell-off", "selloff", "liquidation", "liquidated", "hack", "hacked", "exploit", "drained",
        "tariff", "sues", "lawsuit", "ban", "bankrupt", "insolven", "halt", "outage", "depeg", "war", "missile", "default", "collapse", "panic",
        "capitulation", "bloodbath", "dump")
TESTTAGE = ("2025-01-15", "2025-03-06", "2025-04-07", "2025-05-23", "2025-08-13", "2025-10-10", "2025-11-13", "2026-01-15", "2026-03-16",
            "2026-06-04", "2026-08-14", "2026-09-30")


def main():
    c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True)
    M = pd.read_sql("SELECT feed, titel, beschreibung, pub_utc, aufnahme_ts FROM meldung WHERE pub_utc IS NOT NULL", c, parse_dates=["pub_utc"])
    c.close()
    M["auf"] = pd.to_datetime(M.aufnahme_ts.str[:14], format="%Y%m%d%H%M%S")
    M["zeit"] = M[["pub_utc", "auf"]].min(axis=1)                    # Regel aus §23.72 G4: die fruehere von Veroeffentlichung und Aufnahme
    M["schl"] = M.titel.fillna("").str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    M = M.sort_values("zeit").drop_duplicates("schl")
    M = M[M.zeit >= "2024-12-01"]
    M["warn"] = M.titel.fillna("").str.lower().apply(lambda t: sum(bool(re.search(r"\b%s" % re.escape(w), t)) for w in WARN))
    print("P66 L-C2 VORANALYSE · %d Meldungen ohne Titel-Dubletten (%s .. %s)\n" % (len(M), M.zeit.min().date(), M.zeit.max().date()))
    tg = M.groupby(M.zeit.dt.date).size()
    print("V1 Meldungen je Kalendertag: Median %.0f (5 %%..95 %%: %.0f..%.0f) · Tage mit Meldungen %d von %d" % (
        tg.median(), tg.quantile(0.05), tg.quantile(0.95), len(tg), (pd.Timestamp(M.zeit.max()) - pd.Timestamp("2025-01-01")).days + 1))
    E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
    zt = M.zeit.to_numpy()
    wv = M.warn.to_numpy()
    n24, w24 = [], []
    for z in E.zeit.to_numpy():
        sel = (zt < z) & (zt >= z - np.timedelta64(24, "h"))
        n24.append(int(sel.sum()))
        w24.append(int(wv[sel].sum()))
    E["n24"], E["w24"] = n24, w24
    E["tag"] = E.zeit.dt.date
    T = E.groupby("tag").agg(n=("tief", "size"), tief=("tief", lambda x: float((x <= -0.10).mean())), n24=("n24", "median"), w24=("w24", "median"))
    mit = T[T.tief > 0]
    gross = T.assign(k=(E[E.tief <= -0.10].groupby("tag").size())).sort_values("k", ascending=False).head(10)
    for name, X in (("alle Einstiegstage", T), ("Tage mit Tief-Fall", mit), ("10 groesste Tage", gross)):
        print("   %-20s %3d Tage · Meldungen 24 h vor dem Einstieg: Median %.0f (min %.0f) · Tage mit < 10 Meldungen: %d" % (
            name, len(X), X.n24.median(), X.n24.min(), int((X.n24 < 10).sum())))
    print("\nV2 Zielgroesse je Einstiegstag (Anteil Tief <= -10 %):")
    ab = T[(T.tief >= 0.25) & (T.n >= 5)]
    print("   Tage %d · mit Tief-Fall %d · 'Absturztage' (>= 25 %%, >= 5 Einstiege): %d, sie tragen %d von %d Tief-Faellen (%.0f %%)" % (
        len(T), len(mit), len(ab), int((E[E.tag.isin(ab.index)].tief <= -0.10).sum()), int((E.tief <= -0.10).sum()),
        100 * (E[E.tag.isin(ab.index)].tief <= -0.10).sum() / max((E.tief <= -0.10).sum(), 1)))
    print("   Absturztage: %s" % " · ".join("%s (%d/%d)" % (d, round(r.tief * r.n), r.n) for d, r in ab.sort_index().iterrows()))
    print("\nV4 Warnwoerter (vorab, %d Staemme) je 24-h-Fenster vor dem Einstieg, Median je Tag: alle %.0f · Tage mit Tief-Fall %.0f · Absturztage %.0f" % (
        len(WARN), T.w24.median(), mit.w24.median(), ab.w24.median() if len(ab) else float("nan")))
    print("   (nur Zaehlung - ob das trennt, ist die Messung; der LLM muss es schlagen)")

    print("\nV3 KONTAMINATION gemini-3.5-flash-lite (12 Testfragen, Temperatur 0)")
    from dotenv import dotenv_values
    from api.gemini import GeminiClient
    key = dotenv_values(".env").get("GEMINI_API_KEY")
    gc = GeminiClient(key)
    cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    btc = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
    cm.close()
    kennt = []
    for d in TESTTAGE:
        frage = ("Beantworte nur aus deinem Trainingswissen, ohne zu raten. Wie hoch war der Bitcoin-Schlusskurs in USD am %s (UTC)? "
                 "Antworte als JSON {\"bekannt\": true|false, \"btc_usd\": Zahl oder null, \"ereignis\": \"ein Satz, was an diesem Tag am Kryptomarkt "
                 "geschah, oder unbekannt\"}. Wenn du den Tag nicht kennst, setze bekannt=false und btc_usd=null." % d)
        try:
            a = gc.chat([{"role": "user", "content": frage}], model="gemini-3.5-flash-lite", temperature=0.0)
            m = re.search(r"\{.*\}", a, re.S)
            j = json.loads(m.group(0)) if m else {}
        except Exception as exc:  # noqa: BLE001
            j = {"fehler": "%s: %s" % (type(exc).__name__, str(exc)[:80])}
        echt = float(btc.asof(pd.Timestamp(d)))
        geschaetzt = j.get("btc_usd")
        fehler = abs(float(geschaetzt) / echt - 1) if isinstance(geschaetzt, (int, float)) and geschaetzt else None
        k = fehler is not None and fehler < 0.05
        kennt.append(k)
        print("   %s  echt %8.0f · Modell %-10s · Fehler %-7s · %s · %s" % (
            d, echt, geschaetzt, ("%.1f %%" % (100 * fehler)) if fehler is not None else "-", "KENNT" if k else "kennt nicht",
            str(j.get("ereignis") or j.get("fehler") or "")[:90]))
    print("   -> kennt den Kurs an %d von %d Testtagen" % (sum(kennt), len(kennt)))
    E.to_csv(os.path.join("data", "_lc", "p66_einstiege.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
