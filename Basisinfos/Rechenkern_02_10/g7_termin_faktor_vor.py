r"""G7 P-1 (S8) — der Terminfaktor, gemessen NUR mit Daten VOR dem Rückspielzeitraum (Gegenprüfung 05.11.2026, Befund P-1).

Die S8-Eingabe nennt "BTC bewegt sich in den 2 h ab dem Termin im Mittel 2,3x so stark …, gemessen 2023-2026 an 127 Terminen"
(termin_fakt, p59 F1). Diese Messung schließt Dez. 2025 – Okt. 2026 ein -> Vorgriff im Rückspiel. Hier:
  (1) REPRODUKTION (R-R11) der p59-F1-Werte mit derselben Rechnung auf derselben Basis,
  (2) dieselbe Rechnung mit Terminen, Ersatztagen und Kursen ausschließlich VOR dem Stichtag 2025-12-01.
Rechnung wie p59 F1: mittlere |log-Rendite| BTC von der Stunde vor dem Termin bis 2 h danach, gegen dieselbe UTC-Uhrzeit an
Werktagen ohne Termin (±1 Tag), Ersatzpool ±400 Tage; dazu 24 h (FAKTOR_24H). Nur lesend.

    python Basisinfos/Rechenkern_02_10/g7_termin_faktor_vor.py   -> g7_termin_faktor_vor.txt
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
B0 = datetime(2020, 1, 1)
NY, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")
AUS = {"cpi": {"2024-02-09"}, "nfp": {"2024-01-10", "2024-08-21"}}
STICHTAG = datetime(2025, 12, 1)
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def stunde(tag, uhr):
    t = datetime.fromisoformat("%s %s" % (tag, uhr)).replace(tzinfo=NY).astimezone(UTC).replace(tzinfo=None)
    return int((t - B0).total_seconds() // 3600)


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("p59fomc", os.path.join(HIER, "p59_termin_vorpruefung.py"))
    src = open(spec.origin, encoding="utf-8").read()             # die FOMC-Liste von p59 wörtlich übernehmen (ohne den Lauf)
    fomc = eval(src[src.index("FOMC = [") + 7: src.index("]", src.index("FOMC = [")) + 1])  # noqa: S307 - eigene Datei, nur Liste
    T = json.load(open(os.path.join(PROJ, "data", "_termine", "termine.json"), encoding="utf-8"))
    TERM = {"cpi": [stunde(z["tag"], "08:30") for z in T["cpi"] if z["tag"] not in AUS["cpi"]],
            "nfp": [stunde(z["tag"], "08:30") for z in T["nfp"] if z["tag"] not in AUS["nfp"]],
            "fomc": [stunde(d, "14:00") for d in fomc]}
    alle_tage = {(B0 + timedelta(hours=h)).date() for v in TERM.values() for h in v}
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(PROJ, "data", "stundenkurse.db").replace("\\", "/"), uri=True)
    k = pd.read_sql("select stunde, close from stundenkurse where symbol='BTC' order by stunde", c)
    k["h"] = ((pd.to_datetime(k.stunde) - pd.Timestamp(B0)).dt.total_seconds() // 3600).astype(int)
    close = pd.Series(k.close.values, index=k.h.values)

    def rechne(grenze_h, rng, ende_alt=None):
        H0 = int(close.index.min())
        H1 = int(close.index.max()) if grenze_h is None else min(int(close.index.max()), grenze_h - 1)
        if ende_alt is not None:
            H1 = min(H1, ende_alt)
        lc = np.log(close.reindex(range(H0, H1 + 1)).values)

        def bew(h, n):
            i = h - H0
            return np.nan if i - 1 < 0 or i + n - 1 >= len(lc) else abs(lc[i + n - 1] - lc[i - 1])

        def ersatz(h, n):
            tag0 = B0 + timedelta(hours=h)
            kand = [h + 24 * d for d in range(-400, 401) if d and (tag0 + timedelta(days=d)).weekday() < 5
                    and not any(((tag0 + timedelta(days=d)).date() + timedelta(days=x)) in alle_tage for x in (-1, 0, 1))]
            return rng.choice(np.array(kand), size=n, replace=True)

        aus = {}
        for art in ("cpi", "nfp", "fomc"):
            for n_h, name in ((2, "2h"), (24, "24h")):
                hs = [h for h in TERM[art] if H0 < h < H1 - n_h]
                echt = np.nanmean([bew(h, n_h) for h in hs])
                pool = [[bew(x, n_h) for x in ersatz(h, 400) if H0 < x < H1 - n_h][:300] for h in hs]
                ohne = np.nanmean([np.nanmean(q) for q in pool])
                aus[(art, name)] = (len(hs), echt / ohne)
        return aus, (B0 + timedelta(hours=H0)), (B0 + timedelta(hours=H1))

    p("G7 P-1 · TERMINFAKTOR VOR DEM RÜCKSPIEL · %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    ende_p59 = stunde("2026-09-24", "11:00")                     # p59 lief bis 2026-09-24 15:00 UTC
    voll, a, b = rechne(None, np.random.default_rng(59), ende_alt=ende_p59 + 4)
    p("(1) REPRODUKTION p59 F1 (BTC %s bis %s): %s" % (a, b, " · ".join(
        "%s %s n %d %.2f×" % (art, nm, n, f) for (art, nm), (n, f) in voll.items() if nm == "2h")))
    p("    Soll laut termin_fakt: cpi 1,83 · nfp 1,49 · fomc 2,28 (2 h)")
    g = int((STICHTAG - B0).total_seconds() // 3600)
    vor, a, b = rechne(g, np.random.default_rng(59))
    p("(2) NUR VOR %s (BTC %s bis %s, Ersatztage ebenfalls davor):" % (STICHTAG.date(), a, b))
    for (art, nm), (n, f) in vor.items():
        p("    %-4s %-3s n %2d · Faktor %.2f×" % (art, nm, n, f))
    n_alle = sum(n for (art, nm), (n, f) in vor.items() if nm == "2h")
    f24 = np.mean([f for (art, nm), (n, f) in vor.items() if nm == "24h"])
    p("ERGEBNIS für die Rückspiel-Eingabe: FAKTOR_2H = {%s} · FAKTOR_24H ≈ %.2f (Mittel der drei Arten) · %d Termine" % (
        ", ".join('"%s": %.2f' % (art, vor[(art, "2h")][1]) for art in ("cpi", "nfp", "fomc")), f24, n_alle))
    open(os.path.join(HIER, "g7_termin_faktor_vor.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
