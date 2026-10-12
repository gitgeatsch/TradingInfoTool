"""Voranalyse P15 (GUI-3 Bestand-Tab) + P16 (Spot B3 Upbit) - Fakten an der NB-Sicherung und am Upbit-Archiv. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p15p16_voranalyse.py <NB-Sicherung tradinginfotool.db>

  V1 Bestand nach Rolle (frei + gestakt > 0): Kern BTC/ETH/SOL, L (Krypto ohne Kern/Stablecoin), Cash-aequivalent, andere Klassen
  V2 offene Hebelpositionen (hebel_positions status offen)
  V3 Upbit heute: L-Bestaende OHNE KRW-Markt (freie Marktliste) = Kreis fuer B3; Kuerzel-Zuordnung (symbol_zuordnung, Faktor 1)
  V4 Regel der Messung (c2_messung: '신규 거래지원' und 'KRW', Kuerzel in Klammern vor dem Stichwort) auf dem Archiv data/_c2:
     Meldungen, Ereignisse, ab 2024, wie viele trafen einen HEUTIGEN Bestand
"""
import csv
import os
import re
import sqlite3
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config as C  # noqa: E402

NB = sys.argv[1]
c = sqlite3.connect("file:%s?mode=ro" % NB.replace("\\", "/"), uri=True)
wl = {a.symbol: a for a in C.get_watchlist()}
KERN = ("BTC", "ETH", "SOL")
rolle = {}
for s, q, st in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
    if (q or 0) + (st or 0) <= 0:
        continue
    a = wl.get(s)
    if a is None:
        r = "nicht in der Watchlist"
    elif getattr(a, "ist_cash_aequivalent", False):
        r = "Cash-aequivalent"
    elif a.assetklasse != "krypto":
        r = "andere Klasse (%s)" % a.assetklasse
    elif s in KERN:
        r = "Kern"
    else:
        r = "L"
    rolle.setdefault(r, []).append(s)
print("V1 Bestand nach Rolle (NB-Sicherung):")
for r, l in sorted(rolle.items()):
    print("   %-28s %2d  %s" % (r, len(l), ", ".join(sorted(l))))
spalten = [x[1] for x in c.execute("PRAGMA table_info(hebel_positions)")]
st_sp = "status" if "status" in spalten else None
hp = c.execute("SELECT symbol, %s FROM hebel_positions" % (st_sp or "'?'")).fetchall()
offen = [s for s, z in hp if str(z).lower() in ("offen", "open")]
print("\nV2 hebel_positions: %d Zeilen, offen %d: %s (Spalten: %s)" % (len(hp), len(offen), ", ".join(offen), ", ".join(spalten[:12])))

zu = {}
with open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        if r["faktor"] == "1":
            zu[r["bitpanda"]] = r["binance"]
m = requests.get("https://api.upbit.com/v1/market/all", timeout=30).json()
krw = {x["market"].split("-")[1] for x in m if x["market"].startswith("KRW-")}
L = sorted(rolle.get("L", []))
kreis = [s for s in L if zu.get(s, s) not in krw]
print("\nV3 Upbit: %d KRW-Maerkte · L-Bestaende %d · davon OHNE KRW-Markt (Kreis B3) %d: %s · Zuordnung abweichend: %s" % (
    len(krw), len(L), len(kreis), ", ".join(kreis), {s: zu[s] for s in L if s in zu}))

a = sqlite3.connect("file:data/_c2/ankuendigungen.db?mode=ro", uri=True)
ev = []
for titel, utc in a.execute("SELECT titel, utc FROM upbit"):
    if "신규 거래지원" in titel and "KRW" in titel:
        for s in re.findall(r"\(([A-Z0-9]{2,15})\)", titel.split("신규 거래지원")[0]):
            ev.append((utc, s))
n_alle = a.execute("SELECT COUNT(*), MIN(utc), MAX(utc) FROM upbit").fetchone()
ab24 = [e for e in ev if e[0] >= "2024-01-01"]
gehalten_upbit = {zu.get(s, s) for s in L}          # KORREKTUR 1. Lauf: vorher gegen ALLE Zuordnungsnamen (ZK erschien, nicht gehalten)
heute = sorted({(u[:10], s) for u, s in ab24 if s in gehalten_upbit})
print("\nV4 Upbit-Archiv: %d Meldungen %s bis %s · KRW-Listings (Regel der Messung) %d, ab 2024 %d · davon heutige L-Bestaende: %s" % (
    n_alle[0], n_alle[1][:10], n_alle[2][:10], len(ev), len(ab24), heute))
