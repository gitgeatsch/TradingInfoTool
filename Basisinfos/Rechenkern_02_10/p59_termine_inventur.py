"""P59 INVENTUR: Makro-Termine mit Uhrzeit fuer die Termin-Fenster-Vorpruefung (15.10.2026).

    python Basisinfos/Rechenkern_02_10/p59_termine_inventur.py

Holt aus FRED (frei, Schluessel aus .env, wird NIE ausgegeben) die vergangenen Veroeffentlichungstage:
    CPI                    release_id 10   08:30 New York
    Arbeitsmarkt (NFP)     release_id 50   08:30 New York
    FOMC-Erklaerung        release_id 101  14:00 New York  (Pruefung: deckt sich das mit agent/cycles 2026?)
und die Tagesreihe DGS2 (2-jaehrige US-Rendite) als Ersatz fuer die Ueberraschung.

Schreibt NUR nach data/_termine/ (nicht versioniert). Keine Produktions-DB.
"""
import json
import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
sys.stdout.reconfigure(encoding="utf-8")

import config  # noqa: E402

config.load_env()
KEY = os.environ.get("FRED_API_KEY")
assert KEY, "FRED_API_KEY fehlt in .env"
NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
ZIEL = os.path.join("data", "_termine")
os.makedirs(ZIEL, exist_ok=True)
VON, BIS = "2023-01-01", "2026-12-31"
ART = {"cpi": (10, "08:30"), "nfp": (50, "08:30"), "fomc": (101, "14:00")}


def tage(release_id):
    r = requests.get("https://api.stlouisfed.org/fred/release/dates",
                     params={"release_id": release_id, "api_key": KEY, "file_type": "json", "realtime_start": VON,
                             "realtime_end": BIS, "include_release_dates_with_no_data": "true", "limit": 1000,
                             "sort_order": "asc"}, timeout=30)
    r.raise_for_status()
    return [d["date"] for d in r.json().get("release_dates", [])]


aus = {}
for art, (rid, uhr) in ART.items():
    t = tage(rid)
    zeilen = []
    for d in t:
        lok = datetime.fromisoformat("%s %s" % (d, uhr)).replace(tzinfo=NY)
        zeilen.append({"tag": d, "utc": lok.astimezone(UTC).strftime("%Y-%m-%d %H:%M")})
    aus[art] = zeilen
    je_jahr = {}
    for z in zeilen:
        je_jahr[z["tag"][:4]] = je_jahr.get(z["tag"][:4], 0) + 1
    print("%-5s release_id %3d · %d Termine · je Jahr %s · erster %s · letzter %s"
          % (art, rid, len(zeilen), je_jahr, zeilen[0]["tag"] if zeilen else "-", zeilen[-1]["tag"] if zeilen else "-"))

# Gegenprobe FOMC gegen die statische Fed-Liste 2026 (zweiter Tag = Erklaerung)
from agent.cycles import FOMC_MEETING_DATES_2026  # noqa: E402

fed = {e.isoformat() for _, e in FOMC_MEETING_DATES_2026}
fred26 = {z["tag"] for z in aus["fomc"] if z["tag"].startswith("2026")}
print("\nGegenprobe FOMC 2026: Fed-Liste %d · FRED %d · gemeinsam %d · nur Fed %s · nur FRED %s"
      % (len(fed), len(fred26), len(fed & fred26), sorted(fed - fred26), sorted(fred26 - fed)))

r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                 params={"series_id": "DGS2", "api_key": KEY, "file_type": "json", "observation_start": VON}, timeout=30)
r.raise_for_status()
dgs2 = [(o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] not in (".", "")]
print("DGS2: %d Tageswerte %s bis %s" % (len(dgs2), dgs2[0][0], dgs2[-1][0]))
aus["dgs2"] = dgs2
with open(os.path.join(ZIEL, "termine.json"), "w", encoding="utf-8") as f:
    json.dump(aus, f, ensure_ascii=False, indent=1)
print("geschrieben: %s (Stand %s)" % (os.path.join(ZIEL, "termine.json"), date.today()))
