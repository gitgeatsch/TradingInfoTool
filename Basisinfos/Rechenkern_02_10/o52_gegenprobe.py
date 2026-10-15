"""O52 GEGENPROBE (15.10.2026): agent/termin_fakt gegen ALLE echten Termine 2023-2026 und gegen FRED live - anderer Weg als der Pruefstand.

    python Basisinfos/Rechenkern_02_10/o52_gegenprobe.py > Basisinfos/Rechenkern_02_10/o52_gegenprobe.txt

  G1  jeder Termin aus data/_termine/termine.json (CPI/NFP, Sondertermine ausgenommen wie p59) und der Fed-Liste: ein Trade mit Einstieg
      1 h VOR dem Termin nennt genau diesen Termin mit der Ortszeit, die pandas unabhaengig rechnet; Einstieg 3 h NACH dem Termin nennt
      ihn nicht. FRED wird dabei aus der Datei gestellt (Tag >= heute, wie release/dates mit realtime_start)
  G2  die feste FOMC-Liste 2026 im Code = die Liste der Vorpruefung p59 (dort vom Fed-Kalender abgeschrieben)
  G3  FRED LIVE (nur lesend, frei): naechster CPI- und Arbeitsmarkt-Termin ab heute = der naechste Tag in termine.json
"""
import io
import json
import os
import sys
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd  # noqa: E402

import config  # noqa: E402
import agent.termin_fakt as TF  # noqa: E402
from agent.cycles import FOMC_MEETING_DATES_2026  # noqa: E402

with redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")):
    import p59_termin_vorpruefung as V  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


T = json.load(open(os.path.join("data", "_termine", "termine.json"), encoding="utf-8"))
TAGE = {a: sorted(date.fromisoformat(z["tag"]) for z in T[a] if z["tag"] not in V.AUS[a]) for a in ("cpi", "nfp")}
echt = TF._fred_naechster
TF._fred_naechster = lambda art, heute, k: (next((t for t in TAGE[art] if t >= heute), None), True)

fehl, n = [], 0
# FOMC nur, soweit die feste Liste im Code reicht (2026/2027) - 2023-2025 fehlen dort mit Absicht (der Betrieb schaut nur nach vorn)
liste = [(a, t) for a in ("cpi", "nfp") for t in TAGE[a]] + [("fomc", date.fromisoformat(d)) for d in V.FOMC if d >= "2026"]
for art, tag in liste:
    t_ny = pd.Timestamp("%s %s" % (tag, TF.UHR[art])).tz_localize("America/New_York")
    t_utc = t_ny.tz_convert("UTC").to_pydatetime()
    soll = "%s %s Uhr" % (TF.NAME[art], t_ny.tz_convert("Europe/Vienna").strftime("%d.%m. %H:%M"))
    vor = TF.zeile(t_utc - timedelta(hours=1), t_utc + timedelta(hours=23), "x")
    nach = TF.zeile(t_utc + timedelta(hours=3), t_utc + timedelta(hours=27), "x")
    n += 1
    if soll not in vor or soll in nach:
        fehl.append((art, str(tag), vor[:80], nach[:80]))
pruefe("G1", not fehl, "%d Termine (CPI %d, Arbeitsmarkt %d, FOMC ab 2026 %d) · Abweichungen %d%s" % (
    n, len(TAGE["cpi"]), len(TAGE["nfp"]), sum(d >= "2026" for d in V.FOMC), len(fehl), (" · " + str(fehl[:3])) if fehl else ""))

code26 = sorted(e.isoformat() for _, e in FOMC_MEETING_DATES_2026)
p59_26 = sorted(d for d in V.FOMC if d.startswith("2026"))
pruefe("G2", code26 == p59_26, "Code %d · p59 %d · gleich %s" % (len(code26), len(p59_26), code26 == p59_26))

TF._fred_naechster = echt
config.load_env()
key = os.environ.get("FRED_API_KEY") or ""
heute = date.today()
live = {}
for art in ("cpi", "nfp"):
    TF._SPEICHER.clear()
    live[art] = TF._fred_naechster(art, heute, key)
soll = {a: next((t for t in TAGE[a] if t >= heute), None) for a in ("cpi", "nfp")}
pruefe("G3", all(live[a][1] and live[a][0] == soll[a] for a in live),
       "FRED live ab %s: CPI %s (Datei %s) · Arbeitsmarkt %s (Datei %s)" % (heute, live["cpi"][0], soll["cpi"], live["nfp"][0], soll["nfp"]))
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
