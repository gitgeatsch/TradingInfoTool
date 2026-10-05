"""Gegenprobe G1-M1 (python Basisinfos/Spot_Voranalyse_04_10/g1_m1_gegenprobe.py): unabhaengiger Code direkt auf dem JSON - Filter, A1 BTC, PME fuer 4 Coins."""
import json, os, sqlite3, datetime as dt
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
d = json.load(open(r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\bitpanda_transaktionen.json", encoding="utf-8"))
spot = [t for t in d["transaktionen"] if t["type"] in ("buy", "sell") and not any("margin" in g for g in (t.get("tags") or []))
        and t.get("trade_fiat_id") == "1" and t.get("trade_amount_fiat") is not None]
print("Spot-Buchungen (alle, mit Stablecoins):", len(spot))
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
eur = {}
for s, d_, cl in c.execute("SELECT symbol, date, close FROM price_history_ohlc WHERE currency='EUR'"):
    eur[(s, d_[:10])] = cl
# A1 BTC: EUR-gewichteter Kaufpreis gegen harmonisches Mittel der Tagesschluesse im Kaufzeitraum (nur Kraken-Tage)
k = [t for t in spot if t["cryptocoin_symbol"] == "BTC" and t["type"] == "buy"]
a, b = min(t["datum_utc"] for t in k), max(t["datum_utc"] for t in k)
tage = [d_ for (s, d_) in eur if s == "BTC" and a <= d_ <= b]
harm = len(tage) / sum(1 / eur[("BTC", d_)] for d_ in tage)
kp = sum(float(t["trade_amount_fiat"]) for t in k) / sum(float(t["trade_amount_cryptocoin"]) for t in k)
print("A1 BTC: Kaufpreis %.0f / taeglich gleich %.0f = %.3f (n %d Kaeufe, %d Tage)" % (kp, harm, kp / harm, len(k), len(tage)))
# PME fuer einzelne Coins mit Kraken-EUR bis zum letzten gemeinsamen Kraken-Tag
ende = "2026-07-13"
for sym in ("XLM", "KAS", "APT", "INJ"):
    tt = [t for t in spot if t["cryptocoin_symbol"] == sym and t["datum_utc"] <= ende]
    geld = menge = btc = 0.0
    for t in tt:
        v = 1 if t["type"] == "buy" else -1
        f = float(t["trade_amount_fiat"]); m = float(t["trade_amount_cryptocoin"])
        geld -= v * f; menge += v * m; btc += v * f / eur[("BTC", t["datum_utc"])]
    e_c = geld + menge * eur[(sym, ende)]; e_b = geld + btc * eur[("BTC", ende)]
    print("PME %s bis %s: Ergebnis %+.0f EUR, BTC-Spiegel %+.0f EUR, Vorteil %+.0f EUR (%d Buchungen)" % (sym, ende, e_c, e_b, e_c - e_b, len(tt)))
import subprocess, sys
env = dict(os.environ, G1M1_STICHTAG=ende, G1M1_ZEIGE="XLM,KAS,APT,INJ", PYTHONIOENCODING="utf-8")
out = subprocess.run([sys.executable, "Basisinfos/Spot_Voranalyse_04_10/g1_m1_eigenes_handeln.py"], capture_output=True, text=True, encoding="utf-8", env=env).stdout
print("Hauptskript mit Stichtag %s:" % ende)
for l in out.splitlines():
    if "ZEIGE" in l:
        print(l)
