"""Gegenprobe P66 (19.10.2026) - zweite Wege, dazu die POSITIVKONTROLLE der Kontaminationsprobe. 6 LLM-Abfragen.

    python Basisinfos/Rechenkern_02_10/p66_gegenprobe.py

G1 Kontamination mit erzwungener Schaetzung (kein 'unbekannt' erlaubt) an 3 KONTROLLtagen 2023/24 (muss das Modell kennen) und 3 Testtagen
   2025-26. Die Probe taugt nur, wenn sie an den Kontrolltagen Wissen zeigt (Fehler < 10 %). Vergleichsmassstab je Testtag: der letzte
   Kurs, den ein Modell mit Stichtag Ende 2024 kennen koennte (BTC am 2024-12-31) - liegt die Schaetzung nicht naeher am echten Kurs als
   dieser Massstab, zeigt sie kein Wissen ueber 2025-26.
G2 Absturztage auf zweitem Weg (groupby auf den Rohzeilen von p65_einstiege.csv, eigener Code) - dieselben 16 Tage?
G3 Meldungen 24 h vor dem Einstieg: an 300 zufaelligen Einstiegen per searchsorted statt Maske - gleiche Zahl wie p66_einstiege.csv?
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
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P66 GEGENPROBE\n")
from dotenv import dotenv_values  # noqa: E402
from api.gemini import GeminiClient  # noqa: E402
gc = GeminiClient(dotenv_values(".env").get("GEMINI_API_KEY"))
cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
btc = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
cm.close()
anker = float(btc.asof(pd.Timestamp("2024-12-31")))
erg = {}
for art, d in (("Kontrolle", "2023-06-15"), ("Kontrolle", "2024-03-14"), ("Kontrolle", "2024-11-11"),
               ("Test", "2025-04-07"), ("Test", "2025-10-10"), ("Test", "2026-06-04")):
    frage = ("Schaetze den Bitcoin-Schlusskurs in USD am %s (UTC). Du MUSST eine Zahl nennen, auch wenn du unsicher bist. "
             "Antworte nur als JSON {\"btc_usd\": Zahl}." % d)
    try:
        a = gc.chat([{"role": "user", "content": frage}], model="gemini-3.5-flash-lite", temperature=0.0)
        g = float(json.loads(re.search(r"\{.*\}", a, re.S).group(0))["btc_usd"])
    except Exception as exc:  # noqa: BLE001
        g = None
        print("   %s: keine Zahl (%s)" % (d, str(exc)[:80]))
    echt = float(btc.asof(pd.Timestamp(d)))
    f = abs(g / echt - 1) if g else None
    fa = abs(anker / echt - 1)
    erg[d] = (art, g, echt, f, fa)
    print("   %-9s %s  echt %8.0f · Schaetzung %-9s · Fehler %-7s · Massstab Ende-2024-Kurs %.0f (Fehler %.1f %%)" % (
        art, d, echt, ("%.0f" % g) if g else "-", ("%.1f %%" % (100 * f)) if f is not None else "-", anker, 100 * fa))
ko = [v for v in erg.values() if v[0] == "Kontrolle" and v[3] is not None]
pruefe("G1a Positivkontrolle: Probe erkennt Wissen an den Kontrolltagen 2023/24 (Fehler < 10 %, mind. 2 von 3)", sum(v[3] < 0.10 for v in ko) >= 2,
       " · ".join("%.1f %%" % (100 * v[3]) for v in ko))
te = [v for v in erg.values() if v[0] == "Test" and v[3] is not None]
pruefe("G1b Testtage 2025-26: Schaetzung NICHT besser als der Ende-2024-Massstab (an allen 3)", len(te) == 3 and all(v[3] >= v[4] - 0.02 for v in te),
       " · ".join("Modell %.1f %% / Massstab %.1f %%" % (100 * v[3], 100 * v[4]) for v in te))
E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
tage = {}
for z, t in zip(E.zeit, E.tief):
    k = z.date()
    a, b = tage.get(k, (0, 0))
    tage[k] = (a + 1, b + int(t <= -0.10))
ab = sorted(k for k, (n, b) in tage.items() if n >= 5 and b / n >= 0.25)
pruefe("G2 Absturztage auf zweitem Weg: 16, erster 2025-03-06, letzter 2026-06-04", len(ab) == 16 and str(ab[0]) == "2025-03-06" and str(ab[-1]) == "2026-06-04",
       "%d Tage" % len(ab))
c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True)
M = pd.read_sql("SELECT titel, pub_utc, aufnahme_ts FROM meldung WHERE pub_utc IS NOT NULL", c, parse_dates=["pub_utc"])
c.close()
M["zeit"] = np.minimum(M.pub_utc.values, pd.to_datetime(M.aufnahme_ts.str[:14], format="%Y%m%d%H%M%S").values)
M["schl"] = M.titel.fillna("").str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
M = M.sort_values("zeit").drop_duplicates("schl")
M = M[M.zeit >= "2024-12-01"]
zs = np.sort(M.zeit.to_numpy())
P = pd.read_csv(os.path.join("data", "_lc", "p66_einstiege.csv"), sep=";", parse_dates=["zeit"]).sample(300, random_state=3)
gleich = sum(int(np.searchsorted(zs, np.datetime64(z), "left") - np.searchsorted(zs, np.datetime64(z) - np.timedelta64(24, "h"), "left")) == int(n)
             for z, n in zip(P.zeit, P.n24))
pruefe("G3 Meldungen 24 h davor per searchsorted gleich (300 Einstiege)", gleich == 300, "%d von 300" % gleich)
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
