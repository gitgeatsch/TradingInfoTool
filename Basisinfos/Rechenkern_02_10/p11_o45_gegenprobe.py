"""Buendel P11 + O45 (11.10.2026) - GEGENPROBE mit eigener Rechnung, nicht ueber die geprueften Funktionen.

    python Basisinfos/Rechenkern_02_10/p11_o45_gegenprobe.py <Pruefverzeichnis mit Kopie tradinginfotool.db>

  G1 P11: Wallet je Symbol und Kredit mit EINEM eigenen JOIN (Katalog x Saldo x Positionen) gegen hebel_wallet_abgleich.pruefe
  G2 O45 Wochen: Kerzen ueber die ISO-Kalenderwoche (Montag-Beginn) per Hand gruppiert, vollstaendig = 168 Stunden und vorbei,
     gegen indikator_chart.kerzen (pandas resample) - Open, High, Low, Close und Anzahl je Woche
  G3 O45 Tage: dasselbe ueber das UTC-Datum (24 Stunden)
  G4 O45 RSI 14 und MACD 12/26/9 der letzten Kerze: eigene Wilder- und EMA-Rechnung in reinem Python gegen indikator_chart.werte
"""
import os
import sqlite3
import sys
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import agent.hebel_wallet_abgleich as HW  # noqa: E402
import agent.indikator_chart as IC  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


# ---- G1 ----
c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "tradinginfotool.db").replace("\\", "/"), uri=True)
eigen = {s: (w, p) for s, w, p in c.execute(
    "SELECT k.symbol, SUM(w.saldo), (SELECT SUM(positionsmenge) FROM hebel_positions h WHERE h.symbol=k.symbol AND h.geschlossen_am IS NULL) "
    "FROM bitpanda_wallet_saldo w JOIN bitpanda_katalog k ON k.asset_id=w.asset_id WHERE w.wallet_owner='margin-trading' "
    "GROUP BY k.symbol HAVING ABS(SUM(w.saldo)) > 1e-8 OR (SELECT COUNT(*) FROM hebel_positions h WHERE h.symbol=k.symbol "
    "AND h.geschlossen_am IS NULL) > 0")}
kredit = (c.execute("SELECT SUM(saldo) FROM bitpanda_wallet_saldo WHERE wallet_owner='margin-trading-credit'").fetchone()[0],
          c.execute("SELECT SUM(kreditbetrag_eur) FROM hebel_positions WHERE geschlossen_am IS NULL").fetchone()[0])
e = HW.pruefe(c)
c.close()
fn = {z["symbol"]: (z["wallet"], z["position"]) for z in e["zeilen"]}
pruefe("G1", fn == {s: (w, p or 0.0) for s, (w, p) in eigen.items()} and abs(kredit[0] - e["kredit"]["wallet"]) < 1e-9
       and abs(kredit[1] - e["kredit"]["positionen"]) < 1e-9, "eigen %s Kredit %s · Funktion %s Kredit %s/%s" % (
           eigen, kredit, fn, e["kredit"]["wallet"], e["kredit"]["positionen"]))

# ---- G2/G3 ----
jetzt = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)
roh = IC.stunden("data", "ETH")


def hand(roh, schluessel, stunden):
    g = OrderedDict()
    for t, o, h, l, cl in roh:
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        g.setdefault(schluessel(dt), []).append((o, h, l, cl))
    aus = []
    for beginn, x in g.items():
        if beginn + timedelta(hours=stunden) <= jetzt and len(x) >= 0.9 * stunden:
            aus.append((beginn, x[0][0], max(y[1] for y in x), min(y[2] for y in x), x[-1][3], len(x)))
    return aus


woche = hand(roh, lambda dt: (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0), 168)
tag = hand(roh, lambda dt: dt.replace(hour=0, minute=0), 24)
for k_, ebene, ref in (("G2", "W", woche), ("G3", "D", tag)):
    kz = IC.kerzen(roh, ebene, jetzt)
    f = [(i.to_pydatetime(), r.o, r.h, r.l, r.c, int(r.n)) for i, r in kz.iterrows()]
    pruefe(k_, f == ref, "%s: %d Kerzen hand / %d Funktion, letzte %s / %s" % (ebene, len(ref), len(f), ref[-1][0] if ref else None,
                                                                             f[-1][0] if f else None))

# ---- G4 ----
cl = [x[4] for x in woche]


def ema(xs, n):
    a, out = 2 / (n + 1), []
    for i, x in enumerate(xs):
        out.append(x if i == 0 else a * x + (1 - a) * out[-1])
    return out


def wilder_rsi(xs, n=14):
    d = [xs[i] - xs[i - 1] for i in range(1, len(xs))]
    g = [max(v, 0) for v in d]
    v_ = [max(-v, 0) for v in d]
    ag, av = sum(g[:n]) / n, sum(v_[:n]) / n
    for i in range(n, len(d)):
        ag, av = (ag * (n - 1) + g[i]) / n, (av * (n - 1) + v_[i]) / n
    return 100 - 100 / (1 + ag / av) if av else 100.0


mline = [a - b for a, b in zip(ema(cl, 12), ema(cl, 26))]
sig = ema(mline, 9)
w = IC.werte(IC.kerzen(roh, "W", jetzt))
r_f, m_f, s_f = float(w["rsi"][-1]), float(w["macd"]["macd"][-1]), float(w["macd"]["signal"][-1])
r_e = wilder_rsi(cl)
pruefe("G4", abs(r_f - r_e) < 0.01 and (m_f > s_f) == (mline[-1] > sig[-1]) and abs(m_f - mline[-1]) <= 0.01 * max(1, abs(mline[-1])),
       "RSI Funktion %.3f / eigen %.3f · MACD %.3f / %.3f · Signal %.3f / %.3f (EMA-Start unterschiedlich gewaehlt, Richtung gleich)" % (
           r_f, r_e, m_f, mline[-1], s_f, sig[-1]))
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
