"""Vorpruefung 'inhaltliche Bewertung' (Voranalyse_Spot §23, Nutzer 06.10.) - NUR Datenlage: wie viele Coins der Klassen H/M/S haben
Gebuehrendaten (DefiLlama, frei, ohne Schluessel) und ab wann? Kein Merkmalsschnitt, keine Wirkung.

    python Basisinfos/Spot_Voranalyse_04_10/nutzen_vorpruefung.py

Zuordnung Symbol -> Gebuehrenreihe: (1) Blockchains ueber /v2/chains (tokenSymbol), (2) Protokolle ueber /protocols (symbol) und die
Gebuehrenliste /overview/fees (slug bzw. defillamaId). Mehrdeutige Symbole (mehrere Protokolle mit demselben Kuerzel) werden ausgewiesen, nicht geraten.
Schreibt NUR nach data/_spot/gebuehren.db (Messdatei des Spot-Strangs): je zugeordnetem Symbol die Tagesgebuehren.
"""
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

ZIEL = os.path.join("data", "_spot", "gebuehren.db")


def hole(url):
    for _ in range(3):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.json()
        except Exception:                                    # noqa: BLE001
            pass
        time.sleep(2)
    return None


def main():
    chains = hole("https://api.llama.fi/v2/chains") or []
    prot = hole("https://api.llama.fi/protocols") or []
    fees = (hole("https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true") or {}).get("protocols", [])
    mit_fees = {str(x.get("defillamaId")): x for x in fees}
    mit_fees_slug = {x.get("slug"): x for x in fees if x.get("slug")}
    karte = {}                                                         # Symbol -> (Art, Schluessel fuer summary-Abfrage)
    for c in chains:
        s = (c.get("tokenSymbol") or "").upper()
        if s and c.get("name"):
            karte.setdefault(s, []).append(("chain", c["name"]))
    for p in prot:
        s = (p.get("symbol") or "").upper()
        if not s or s == "-":
            continue
        if str(p.get("id")) in mit_fees or p.get("slug") in mit_fees_slug:
            karte.setdefault(s, []).append(("protokoll", p.get("slug")))
    t = A.ENDE.replace(day=1)
    kl = A.klassen(t)[0]
    print("Vorpruefung inhaltliche Bewertung (§23) · Klassen zum %s · DefiLlama: %d Blockchains, %d Protokolle mit Gebuehren\n" % (t.date(), len(chains), len(fees)))
    zeilen, eindeutig = [], {}
    for k in ("H", "M", "S"):
        syms = [s for s, v in kl.items() if v == k]
        hat = [s for s in syms if s in karte]
        mehr = [s for s in hat if len({x[1] for x in karte[s]}) > 1]
        print("  %s  %3d Coins · mit Gebuehrenreihe %3d (%3.0f %%) · davon mehrdeutig %d" % (k, len(syms), len(hat), 100 * len(hat) / max(len(syms), 1), len(mehr)))
        for s in hat:
            ziele = {x for x in karte[s]}
            chain = [x for x in ziele if x[0] == "chain"]
            wahl = chain[0] if chain else (sorted(ziele)[0] if len(ziele) == 1 else None)
            if wahl:
                eindeutig[s] = wahl
            zeilen.append((k, s, wahl))
    # Historie holen und ablegen
    reihen = []
    for s, (art, key) in sorted(eindeutig.items()):
        url = ("https://api.llama.fi/summary/fees/%s?dataType=dailyFees" % key) if art == "protokoll" else \
              ("https://api.llama.fi/overview/fees/%s?excludeTotalDataChartBreakdown=true&dataType=dailyFees" % key)
        d = hole(url) or {}
        tc = d.get("totalDataChart") or []
        for ts, v in tc:
            reihen.append((s, art, key, pd.Timestamp(int(ts), unit="s").date().isoformat(), float(v)))
        time.sleep(0.3)
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    c = sqlite3.connect(ZIEL)
    c.execute("DROP TABLE IF EXISTS gebuehr")
    c.execute("CREATE TABLE gebuehr (symbol TEXT, art TEXT, quelle TEXT, datum TEXT, usd REAL, PRIMARY KEY (symbol, datum))")
    c.executemany("INSERT OR REPLACE INTO gebuehr VALUES (?,?,?,?,?)", reihen)
    c.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    c.execute("INSERT OR REPLACE INTO _herkunft VALUES ('quelle', 'DefiLlama dailyFees (frei), geladen %s')" % time.strftime("%Y-%m-%d %H:%M"))
    c.commit()
    g = pd.DataFrame(reihen, columns=["symbol", "art", "quelle", "datum", "usd"])
    g["datum"] = pd.to_datetime(g["datum"])
    print("\nGespeichert: %d Tageswerte fuer %d Symbole -> %s" % (len(g), g.symbol.nunique(), ZIEL))
    print("\nAbdeckung je Stichtag (Coins der Klasse mit Gebuehrenwerten in den 180 T davor):")
    erst = g.groupby("symbol").datum.min()
    for j in (2021, 2022, 2023, 2024, 2025, 2026):
        tj = pd.Timestamp("%d-01-01" % j)
        klj = A.klassen(tj)[0]
        z = []
        for k in ("H", "M", "S"):
            syms = [s for s, v in klj.items() if v == k]
            n = sum(1 for s in syms if s in erst.index and erst[s] <= tj - pd.Timedelta(days=180))
            z.append("%s %d/%d" % (k, n, len(syms)))
        print("  %d-01-01  %s" % (j, " · ".join(z)))
    print("\nBeispiele (aktuelle Klassen, Jahresgebuehren der letzten 365 T in Mio. USD):")
    letzt = g[g.datum > g.datum.max() - pd.Timedelta(days=365)].groupby("symbol").usd.sum() / 1e6
    for k in ("H", "M"):
        x = [(s, letzt.get(s, np.nan)) for s in [s for s, v in kl.items() if v == k] if s in letzt.index]
        print("  %s: %s" % (k, ", ".join("%s %.1f" % (s, v) for s, v in sorted(x, key=lambda z: -z[1])[:25])))
    print("\nMehrdeutig (nicht zugeordnet): %s" % ", ".join(sorted(s for k, s, w in zeilen if w is None)))


if __name__ == "__main__":
    main()
