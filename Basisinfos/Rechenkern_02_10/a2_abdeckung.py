"""A2 Schritt 0 (Voranalyse_Schritt7 §23.15, E-75): Datenquellen- und ABDECKUNGSPRUEFUNG je Kandidat auf den REGEL0-Einstiegen - nur lesend.

    python Basisinfos/Rechenkern_02_10/a2_abdeckung.py

Einstiege: data/_vergleich/kern48jbz_einstiege_bestand.csv (Referenz der Testwoche, REGEL0-Form, Menge 'bestand'; stunde = Stunden seit
2020-01-01). Je Kandidat: Anteil der Einstiege, fuer die der Wert zur Signalstunde (bzw. davor) vorliegt - je Jahr 2024 / 2025 / 2026.
  N-a Markpreis-Praemie   markpreis_historie + markpreis_alle (Markpreis) und stundenkurse + stundenkurse_alle zur Signalstunde
  N-b..N-d Kapitulation, Docht, Fallgeschwindigkeit   stundenkurse_alle: 24 Stunden bis zur Signalstunde lueckenlos
  N-e BTC-Umfeld           stundenkurse_alle BTC, 168 h davor
  N-f OI / Long-Short / Taker   terminmarkt_historie (stuendlich) zur Signalstunde; Funding (Tageswert!) nur Vortag (TAGESwert an
                                STUNDENanker waere Vorgriff)
  N-g Kaeuferanteil        richtung_historie.fluss zur Signalstunde
"""
import os
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(WURZEL, "data")
B0 = datetime(2020, 1, 1)


def stunden(db, tab, spalte="stunde", wo=""):
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, db), uri=True)
    d = pd.read_sql("SELECT symbol, %s AS s FROM %s %s" % (spalte, tab, wo), c)
    return set(zip(d.symbol, d.s))


def main():
    E = pd.read_csv(os.path.join(D, "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    E["zeit"] = [B0 + timedelta(hours=int(h)) for h in E.stunde]
    E["txt"] = E.zeit.dt.strftime("%Y-%m-%d %H:%M")
    print("A2 Schritt 0 - Abdeckung je Kandidat auf %d REGEL0-Einstiegen (%s) · Assets %d" % (
        len(E), ", ".join("%s %d" % (j, (E.jahr == j).sum()) for j in sorted(E.jahr.unique())), E.symbol.nunique()))
    # KORREKTUR 07.10. (erster Lauf): die 116 Basis-Assets liegen in stundenkurse.db / markpreis_historie.db, die *_alle-Dateien tragen
    # nur die ZUSAETZLICHEN Assets (O11) - beide zusammen
    sk = stunden("stundenkurse.db", "stundenkurse") | stunden("stundenkurse_alle.db", "stundenkurse")
    mk = stunden("markpreis_historie.db", "markpreis") | stunden("markpreis_alle.db", "markpreis")
    tm = stunden("terminmarkt_historie.db", "terminmarkt")
    rf = stunden("richtung_historie.db", "fluss")
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "funding_historie.db"), uri=True)
    fu = set(map(tuple, pd.read_sql("SELECT symbol, datum FROM funding", c).values))
    btc = {s for (sy, s) in sk if sy == "BTC"}

    def voll24(sy, t):
        return all((sy, (t - timedelta(hours=k)).strftime("%Y-%m-%d %H:%M")) in sk for k in range(0, 24))
    kand = {
        "N-a Markpreis-Praemie": lambda r: (r.symbol, r.txt) in mk and (r.symbol, r.txt) in sk,
        "N-b/c/d Kapitulation, Docht, Fall (24 h luecklos)": lambda r: voll24(r.symbol, r.zeit),
        "N-e BTC-Umfeld (168 h davor)": lambda r: r.txt in btc and (r.zeit - timedelta(hours=168)).strftime("%Y-%m-%d %H:%M") in btc,
        "N-f OI / Long-Short / Taker (stuendlich)": lambda r: (r.symbol, r.txt) in tm,
        "N-f Funding (Vortag)": lambda r: (r.symbol, (r.zeit - timedelta(days=1)).strftime("%Y-%m-%d")) in fu,
        "N-g Kaeuferanteil (fluss)": lambda r: (r.symbol, r.txt) in rf,
    }
    print("\n  %-50s %s" % ("Kandidat", " · ".join("%s" % j for j in sorted(E.jahr.unique()))))
    for name, f in kand.items():
        ok = [bool(f(r)) for r in E.itertuples()]
        E["_ok"] = ok
        print("  %-50s %s · Assets mit Wert %d/%d" % (name, " · ".join("%5.1f %%" % (100 * E[E.jahr == j]._ok.mean()) for j in sorted(E.jahr.unique())),
                                                    E[E._ok].symbol.nunique(), E.symbol.nunique()))
    print("\n  Am NB im Betrieb (Teilexport 07.10.): markpreis_alle 396/411 laufend, stundenkurse_alle 533/537 laufend; terminmarkt/funding nur "
          "Symbolliste, Prod open_interest_snapshot 40 Symbole (15 min); richtung_historie fehlt")


if __name__ == "__main__":
    main()
