"""Spot G1-M1 (Voranalyse_Spot_Neubau_04_10.md §10.7, Commit 289a872): dein tatsaechliches Handeln aus dem Bitpanda-Buch.

    python Basisinfos/Spot_Voranalyse_04_10/g1_m1_eigenes_handeln.py

Nur lesend: Austauschordner bitpanda_transaktionen.json (Spot-Trades 13.09.2024-01.08.2026), data/tradinginfotool.db (Kraken EUR, mode=ro),
data/messdaten.db (USD, mode=ro), data/_spot/coinmetrics.db. Kein Netz, kein Schreiben ausser auf stdout.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - Tageskurs EUR je Asset: Kraken EUR; fehlt der Tag, messdaten USD / Wechselkurs; Wechselkurs = BTC Kraken EUR / BTC CoinMetrics USD
    am selben Tag, nach dem letzten Kraken-Tag fortgeschrieben (letzter Wert)
  - A3 (ii) Netto-DCA: Monatserste vom Monat des ersten Trades bis Juli 2026, je Termin Nettokapital / Zahl der Termine
  - Kosten: nur Tage mit Kraken-EUR-Schluss (kein Umrechnungsfehler im Kostenmass)
"""
import json
import os
import sqlite3
from collections import defaultdict

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)
QUELLE = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\bitpanda_transaktionen.json"
STICHTAG = pd.Timestamp(os.environ.get("G1M1_STICHTAG", "2026-08-01"))   # Umgebungsvariable nur fuer die Gegenprobe
STICHTAG_AUSKUNFT = pd.Timestamp("2026-09-20")    # Auskunft: Ende messdaten.db, Stichtagsabhaengigkeit (Baerenmarkt 08.2026)
STABLE = {"EURCV", "EURC", "USDC", "USDT", "DAI", "FDUSD", "TUSD", "BUSD", "PYUSD", "USDE", "EURI"}


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


# ---------------- Trades
d = json.load(open(QUELLE, encoding="utf-8"))
# KORREKTUR nach dem ersten Lauf (05.10., beim Pruefen gefunden): die Liste `trades` enthaelt auch die HEBEL-Eroeffnungen
# (BTC: 39 von 79 "Kaeufen" sind margin_trading.open). Massgeblich ist deshalb `transaktionen`: nur buy/sell OHNE margin-Markierung.
_sp = {t["unix_timestamp"]: t.get("is_savings", False) for t in d["trades"]}
tr = pd.DataFrame([{"symbol": t["cryptocoin_symbol"], "type": t["type"], "amount_fiat": float(t["trade_amount_fiat"]),
                    "amount_cryptocoin": float(t["trade_amount_cryptocoin"]), "price": float(t["trade_price"]),
                    "unix_timestamp": t["unix_timestamp"], "datum_utc": t["datum_utc"], "is_savings": bool(_sp.get(t["unix_timestamp"], False))}
                   for t in d["transaktionen"]
                   if t["type"] in ("buy", "sell") and set(t.get("tags") or []) <= {"advanced_trading.trade"}
                   and t.get("trade_fiat_id") == "1" and t.get("trade_amount_fiat") is not None])
tr["tag"] = pd.to_datetime(tr["datum_utc"])
MARGIN = sum(1 for t in d["transaktionen"] if any(str(g).startswith("margin_trading") for g in (t.get("tags") or [])))
# KORREKTUR 2 (05.10., beim Pruefen gefunden): Coins aus geschlossenen Hebelpositionen werden danach als NORMALE Verkaeufe gebucht
# (TAO -68, LINK -622, SUI -3495 netto aus Spot). Fuer Coins, die je gehebelt wurden, sind Verkaeufe und Restmengen daher NICHT belastbar.
MIT_HEBEL = {t["cryptocoin_symbol"] for t in d["transaktionen"] if any(str(g).startswith("margin_trading") for g in (t.get("tags") or []))}
tr["vz"] = np.where(tr["type"] == "buy", 1.0, -1.0)
tr = tr[~tr["symbol"].isin(STABLE)].copy()

# ---------------- Kurse
c = ro("data/tradinginfotool.db")
kr = pd.read_sql("SELECT symbol, date, close, high, low FROM price_history_ohlc WHERE currency='EUR'", c, parse_dates=["date"])
c.close()
KR = kr.pivot(index="date", columns="symbol", values="close").sort_index()
KM = kr.assign(m=(kr["high"] + kr["low"]) / 2).pivot(index="date", columns="symbol", values="m").sort_index()   # Gegenprobe Kosten
c = ro("data/messdaten.db")
md = pd.read_sql("SELECT symbol, date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date>='2024-06-01'",
                 c, parse_dates=["date"])
c.close()
MD = md.pivot(index="date", columns="symbol", values="close").sort_index()
c = ro("data/_spot/coinmetrics.db")
cm = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND tag>='2024-06-01'", c, parse_dates=["tag"]).set_index("tag")["PriceUSD"]
c.close()
tage = pd.date_range("2024-07-01", "2026-10-04")
fx = (KR["BTC"].reindex(tage) / cm.reindex(tage)).ffill()          # EUR je USD
fx_letzter_kraken = KR["BTC"].dropna().index.max()


def eur_reihe(sym):
    k = KR[sym].reindex(tage) if sym in KR else pd.Series(np.nan, index=tage)
    u = MD[sym].reindex(tage) if sym in MD else pd.Series(np.nan, index=tage)
    if sym == "BTC":
        u = cm.reindex(tage)
    return k.fillna(u * fx)


print("Spot G1-M1 - dein Handeln aus dem Bitpanda-Buch (Voranalyse_Spot §10.7), Trades %s bis %s, Stichtag %s" % (
    tr["tag"].min().date(), tr["tag"].max().date(), STICHTAG.date()))
print("Spot-Kaeufe/-Verkaeufe ohne Stablecoins: %d (Hebel-Buchungen ausgeschlossen: %d) · Kraken-EUR bis %s, danach CoinMetrics/messdaten x Wechselkurs" % (
    len(tr), MARGIN, fx_letzter_kraken.date()))
_H = {h["symbol"]: (h["quantity"] or 0) + (h["staked_quantity"] or 0) for h in d["holdings_schnappschuss"]}
_q = tr.assign(m=tr["amount_cryptocoin"] * tr["vz"]).groupby("symbol")["m"].sum()
print("Mengenabgleich (Auskunft): aus Spot-Trades gegen Bestand 01.08. (Bestand enthaelt Staking-Belohnungen und Boni ohne Geldfluss): " + " · ".join(
    "%s %.4g/%.4g" % (s_, _q.get(s_, 0), _H.get(s_, 0)) for s_ in ("BTC", "ETH", "SOL", "TAO", "LINK", "SUI")))
print("negative Spot-Mengen (mehr verkauft als gekauft, z. B. Boni verkauft): %d Coins" % int((_q < -1e-9).sum()))
print()

# ---------------- Teil A
print("=" * 30, "TEIL A - Kernwerte", "=" * 30)
for sym in ("BTC", "ETH", "SOL"):
    t = tr[tr["symbol"] == sym].sort_values("unix_timestamp")
    if t.empty:
        continue
    p = eur_reihe(sym)
    k, v = t[t["type"] == "buy"], t[t["type"] == "sell"]
    print("%s: %d Kaeufe (%.0f EUR), %d Verkaeufe (%.0f EUR), Sparplan-Kaeufe %d" % (
        sym, len(k), k["amount_fiat"].sum(), len(v), v["amount_fiat"].sum(), int(k["is_savings"].sum())))
    if sym in MIT_HEBEL:
        print("  ⚠️ %s wurde auch GEHEBELT: A2 und A3 enthalten Verkaeufe aus Hebel-Schliessungen - nur A1 (Kaufqualitaet) ist belastbar" % sym)
    # A1 Kaufqualitaet
    zr = p[k["tag"].min():k["tag"].max()].dropna()
    dca_preis = len(zr) / (1 / zr).sum()                                 # harmonisches Mittel = Preis bei taeglich gleichem Betrag
    kauf_preis = k["amount_fiat"].sum() / k["amount_cryptocoin"].sum()
    null = []
    pv = zr.values
    for _ in range(1000):
        tg = RNG.integers(0, len(pv), len(k))
        null.append(k["amount_fiat"].sum() / (k["amount_fiat"].values / pv[tg]).sum())
    rang = float(np.mean(np.array(null) <= kauf_preis))
    print("  A1 Kaufqualitaet: dein Durchschnitt %.0f EUR gegen taeglich gleich %.0f EUR -> %.3f (unter 1 = billiger) · Nullwelt (Zufallstage): "
          "Median %.3f, Rang %.2f (klein = besser als Zufall)" % (kauf_preis, dca_preis, kauf_preis / dca_preis, np.median(null) / dca_preis, rang))
    # A2 Verkaufsqualitaet
    if len(v):
        zv = p[v["tag"].min():v["tag"].max()].dropna()
        vk_preis = v["amount_fiat"].sum() / v["amount_cryptocoin"].sum()
        menge_v = v["amount_cryptocoin"].sum()
        print("  A2 Verkaufsqualitaet: dein Durchschnitt %.0f EUR gegen Mittel %.0f EUR -> %.3f (ueber 1 = teurer verkauft) · "
              "die verkaufte Menge waere am Stichtag %.0f EUR wert, erloest %.0f EUR (%+.0f EUR durch das Verkaufen)" % (
                  vk_preis, zv.mean(), vk_preis / zv.mean(), menge_v * p[STICHTAG], v["amount_fiat"].sum(),
                  v["amount_fiat"].sum() - menge_v * p[STICHTAG]))
    # A3 Ergebnis und Gegenwelten
    menge = k["amount_cryptocoin"].sum() - v["amount_cryptocoin"].sum()
    erg = v["amount_fiat"].sum() + menge * p[STICHTAG] - k["amount_fiat"].sum()
    erg_halten = k["amount_cryptocoin"].sum() * p[STICHTAG] - k["amount_fiat"].sum()
    netto = k["amount_fiat"].sum() - v["amount_fiat"].sum()
    termine = pd.date_range(t["tag"].min().to_period("M").to_timestamp(), STICHTAG, freq="MS")
    termine = [x for x in termine if x <= STICHTAG]
    if netto > 0:
        je = netto / len(termine)
        erg_dca = sum(je / p[x] for x in termine) * p[STICHTAG] - netto
        dca_txt = "%+.0f EUR auf %.0f EUR Netto (%+.1f %%)" % (erg_dca, netto, 100 * erg_dca / netto)
    else:
        dca_txt = "entfaellt (Netto <= 0: mehr verkauft als gekauft)"
    print("  A3 Ergebnis: tatsaechlich %+.0f EUR (Restmenge %.6f, %.0f EUR) · (i) dieselben Kaeufe nie verkauft %+.0f EUR · "
          "(ii) regelmaessig Netto %s" % (erg, menge, menge * p[STICHTAG], erg_halten, dca_txt))
print()

# ---------------- Teil B PME gegen BTC
print("=" * 30, "TEIL B - Altcoin-Spot gegen BTC (PME, jeder Geldfluss in BTC gespiegelt)", "=" * 30)
btc = eur_reihe("BTC")
zeilen, ohne = [], defaultdict(float)
for sym, t in tr[~tr["symbol"].isin({"BTC"})].groupby("symbol"):
    p = eur_reihe(sym)
    if p.notna().sum() == 0:
        ohne[sym] = t["amount_fiat"].sum()
        continue
    fl = t["vz"] * t["amount_fiat"]                                      # + Kauf, - Verkauf (Geld hinein)
    menge = (t["vz"] * t["amount_cryptocoin"]).sum()
    end_p = p[STICHTAG] if pd.notna(p.get(STICHTAG)) else np.nan
    notbew = False
    if np.isnan(end_p):
        end_p = t.sort_values("unix_timestamp")["price"].iloc[-1]
        notbew = True
    erg = -fl.sum() + menge * end_p
    btc_menge = (fl / btc.reindex(t["tag"]).values).sum()
    erg_btc = -fl.sum() + btc_menge * btc[STICHTAG]
    zeilen.append((sym, t["amount_fiat"][t["type"] == "buy"].sum(), erg, erg_btc, erg - erg_btc, notbew, abs(menge * end_p) < 1, sym in MIT_HEBEL, menge))
alle_z = pd.DataFrame(zeilen, columns=["sym", "kauf_eur", "erg", "erg_btc", "vorteil", "notbew", "geschlossen", "hebel", "menge"]).sort_values("vorteil")
hz = alle_z[alle_z["hebel"]]
print("AUSKUNFT, nicht belastbar - Coins MIT Hebel (%d, Spot-Kaeufe %.0f EUR): Vorteil gegen BTC %+.0f EUR, davon %d mit negativer Spot-Menge" % (
    len(hz), hz["kauf_eur"].sum(), hz["vorteil"].sum(), int((hz["menge"] < -1e-9).sum())))
z = alle_z[~alle_z["hebel"]]
print("BELASTBAR - Coins NUR Spot (nie gehebelt): %d, davon negative Spot-Menge (Boni/Belohnungen verkauft) %d" % (len(z), int((z["menge"] < -1e-9).sum())))
print("Coins mit Kurs: %d (Kaeufe %.0f EUR) · ohne Kursreihe, nur gezaehlt: %d (Umsatz %.0f EUR) · Notbewertung mit letztem Tradepreis: %d" % (
    len(z), z["kauf_eur"].sum(), len(ohne), sum(ohne.values()), int(z["notbew"].sum())))
print("SUMME: Ergebnis Altcoins %+.0f EUR · dasselbe Geld zur selben Zeit in BTC %+.0f EUR · VORTEIL gegen BTC %+.0f EUR" % (
    z["erg"].sum(), z["erg_btc"].sum(), z["vorteil"].sum()))
# Auskunft Stichtagsabhaengigkeit: dieselben Restmengen am 20.09.2026 bewertet (Ende messdaten; Kaeufe/Verkaeufe nach dem 01.08. unbekannt)
_aus = 0.0
for r_ in z.itertuples():
    p_ = eur_reihe(r_.sym)
    if pd.notna(p_.get(STICHTAG_AUSKUNFT)) and pd.notna(p_.get(STICHTAG)):
        _aus += r_.menge * (p_[STICHTAG_AUSKUNFT] - p_[STICHTAG])
_btc_m = sum(((t_["vz"] * t_["amount_fiat"]) / btc.reindex(t_["tag"]).values).sum() for s_, t_ in tr[tr["symbol"].isin(set(z["sym"]))].groupby("symbol"))
_aus_btc = _btc_m * (btc[STICHTAG_AUSKUNFT] - btc[STICHTAG])
print("AUSKUNFT Stichtag %s (Restmengen unveraendert angenommen): Vorteil gegen BTC %+.0f EUR (am %s %+.0f EUR)" % (
    STICHTAG_AUSKUNFT.date(), z["vorteil"].sum() + _aus - _aus_btc, STICHTAG.date(), z["vorteil"].sum()))
print("Coins vor BTC: %d von %d (%.0f %%) · nach Kaufvolumen gewichtet vor BTC: %.0f %%" % (
    (z["vorteil"] > 0).sum(), len(z), 100 * (z["vorteil"] > 0).mean(), 100 * z.loc[z["vorteil"] > 0, "kauf_eur"].sum() / z["kauf_eur"].sum()))
for _s in [x for x in os.environ.get("G1M1_ZEIGE", "").split(",") if x]:
    _r = alle_z[alle_z["sym"] == _s].iloc[0]
    print("  ZEIGE %s: Ergebnis %+.0f, BTC-Spiegel %+.0f, Vorteil %+.0f" % (_s, _r.erg, _r.erg_btc, _r.vorteil))
print("  die 10 groessten Nachteile:  " + " · ".join("%s %+.0f" % (r.sym, r.vorteil) for r in z.head(10).itertuples()))
print("  die 10 groessten Vorteile:   " + " · ".join("%s %+.0f" % (r.sym, r.vorteil) for r in z.tail(10)[::-1].itertuples()))
print("  ohne Kursreihe (Umsatz EUR): " + ", ".join("%s %.0f" % (s, v) for s, v in sorted(ohne.items(), key=lambda x: -x[1])[:15]))
print()

# ---------------- Kosten M-1
print("=" * 30, "KOSTEN (M-1): Tradepreis / Kraken-Tagesschluss - 1", "=" * 30)
kz = []
for r in tr.itertuples():
    if r.symbol in KR and r.tag in KR.index and pd.notna(KR.at[r.tag, r.symbol]):
        kz.append((r.symbol, r.type, r.price / KR.at[r.tag, r.symbol] - 1, r.amount_fiat, r.price / KM.at[r.tag, r.symbol] - 1))
kz = pd.DataFrame(kz, columns=["sym", "typ", "abw", "eur", "abw_mitte"])
for name, sel in (("BTC", kz["sym"] == "BTC"), ("ETH", kz["sym"] == "ETH"), ("alle Kraken-EUR-Werte", kz["sym"].notna())):
    a, b = kz[sel & (kz["typ"] == "buy")]["abw"], kz[sel & (kz["typ"] == "sell")]["abw"]
    if len(a) and len(b):
        print("  %-22s Kauf: Median %+.2f %% (Quartile %+.2f/%+.2f, n %d) · Verkauf: Median %+.2f %% (%+.2f/%+.2f, n %d) -> "
              "Hin und zurueck etwa %.2f %%" % (name, 100 * a.median(), 100 * a.quantile(.25), 100 * a.quantile(.75), len(a),
                                               100 * b.median(), 100 * b.quantile(.25), 100 * b.quantile(.75), len(b),
                                               100 * (a.median() - b.median())))
        am, bm = kz[sel & (kz["typ"] == "buy")]["abw_mitte"], kz[sel & (kz["typ"] == "sell")]["abw_mitte"]
        print("  %-22s Gegenprobe gegen die Tagesmitte (Hoch+Tief)/2: Kauf %+.2f %%, Verkauf %+.2f %% -> Hin und zurueck etwa %.2f %%" % (
            "", 100 * am.median(), 100 * bm.median(), 100 * (am.median() - bm.median())))
