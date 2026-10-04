"""V-2 der Spot-Voranalyse (Plan O23, E-54): Kaufen die Spot-Signale in den Verlust nach, oder an einem Boden?

Nur lesend. Eingaben:
  argv[1]  Kopie der NB-Datenbank (Tabelle signals) - wird nur mit mode=ro geoeffnet
  data/stundenkurse_alle.db, data/stundenkurse.db (Desktop, mode=ro), Basisinfos/symbol_zuordnung.csv

Gemessen je Spot-Kaufsignal (KAUFEN, NACHKAUFEN, ERÖFFNEN; Krypto; erstes Signal je Symbol, Aktion und UTC-Tag):
  Einstieg = Schlusskurs der Folgestunde (wie REGEL0).
  r_h      = Kurs nach h Stunden / Einstieg - 1, h = 24, 168, 336, 672
  ueber_h  = r_h minus Median aller Stundenkurs-Assets im selben Fenster (tagestreuer Marktbezug)
  lage     = Lage des Einstiegs im Bereich [Tief, Hoch] der 7 Tage davor UND danach (0 = am Boden, 1 = am Gipfel).
             Bezug: dieselbe Groesse fuer ALLE Stunden derselben Assets im selben Zeitraum (Zufallseinstieg).
⚠️ Zeitraum nur Juli bis Oktober 2026 (aeltere Spot-Signale gibt es nicht) - EIN Regime, Auskunft, kein Urteil.
"""
import csv
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
NB = sys.argv[1]
H = (24, 168, 336, 672)
AB = "2026-05-01 00:00"


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


zu = {}
with open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8") as f:
    for z in csv.DictReader(f, delimiter=";"):
        zu[z["bitpanda"]] = (z["binance"], z["markt"], float(z["faktor"] or 1))

kurse = {}
for datei in ("data/stundenkurse.db", "data/stundenkurse_alle.db"):
    c = ro(datei)
    for sym, st, lo, hi, cl in c.execute("select symbol, stunde, low, high, close from stundenkurse where stunde >= ?", (AB,)):
        kurse.setdefault(sym, {}).setdefault(st, (lo, hi, cl))
    c.close()
idx = pd.date_range(AB, max(max(v) for v in kurse.values()), freq="h").strftime("%Y-%m-%d %H:%M")
CL = pd.DataFrame({s: pd.Series({k: v[2] for k, v in d.items()}) for s, d in kurse.items()}).reindex(idx)
LO = pd.DataFrame({s: pd.Series({k: v[0] for k, v in d.items()}) for s, d in kurse.items()}).reindex(idx)
HI = pd.DataFrame({s: pd.Series({k: v[1] for k, v in d.items()}) for s, d in kurse.items()}).reindex(idx)
markt = {h: (CL.shift(-h) / CL - 1).median(axis=1) for h in H}
# Lage im 15-Tage-Fenster (7 Tage davor, 7 danach) - fuer jede Stunde jedes Assets
tief = LO.rolling(337, center=True, min_periods=337).min()
hoch = HI.rolling(337, center=True, min_periods=337).max()
LAGE = (CL - tief) / (hoch - tief)

c = ro(NB)
_sig_syms = sorted(set(zu.get(r[0], (r[0],))[0] for r in c.execute(
    "select distinct symbol from signals where coalesce(instrument,'spot')='spot' and coalesce(gruppe,'krypto')='krypto'")) & set(CL.columns))
# ⚠️ der faire Bezug: dieselben Watchlist-Assets zur selben Stunde (Zeitpunkt UND Auswahl der Watchlist herausgerechnet)
markt_wl = {h: (CL[_sig_syms].shift(-h) / CL[_sig_syms] - 1).median(axis=1) for h in H}
roh = c.execute("""select symbol, created_at, action from signals
                   where action in ('KAUFEN','NACHKAUFEN','ERÖFFNEN') and coalesce(instrument,'spot') = 'spot'
                     and coalesce(gruppe,'krypto') = 'krypto' order by created_at""").fetchall()
c.close()
gesehen, zeilen, ohne = set(), [], {}
for sym, ts, akt in roh:
    k = (sym, akt, ts[:10])
    if k in gesehen:
        continue
    gesehen.add(k)
    b, m, fak = zu.get(sym, (sym, "spot", 1.0))
    if m == "gesperrt" or b not in CL.columns:
        ohne[sym] = ohne.get(sym, 0) + 1
        continue
    st = pd.Timestamp(ts[:13] + ":00").tz_localize(None) + pd.Timedelta(hours=1)
    s = st.strftime("%Y-%m-%d %H:%M")
    if s not in CL.index or pd.isna(CL.at[s, b]):
        ohne[sym] = ohne.get(sym, 0) + 1
        continue
    i = CL.index.get_loc(s)
    e = CL.iat[i, CL.columns.get_loc(b)]
    z = {"symbol": sym, "aktion": akt, "monat": ts[:7], "lage": LAGE.at[s, b], "woche": st.strftime("%G-%V")}
    for h in H:
        if i + h < len(CL) and not pd.isna(CL.iat[i + h, CL.columns.get_loc(b)]):
            r = CL.iat[i + h, CL.columns.get_loc(b)] / e - 1
            z["r%d" % h] = r
            z["u%d" % h] = r - markt[h].iat[i]
            z["w%d" % h] = r - markt_wl[h].iat[i]
    lo7 = LO[b].iloc[i + 1:i + 169]
    if len(lo7.dropna()) > 100:
        z["mae168"] = lo7.min() / e - 1
    zeilen.append(z)
D = pd.DataFrame(zeilen)

print("V-2 Spot-Kaufsignale gegen den weiteren Kursverlauf (NB-Kopie %s, Kurse bis %s)" % (os.path.basename(NB), CL.index[-1]))
print("Signale roh %d -> je Symbol/Aktion/Tag %d, mit Kursen %d; ohne Kurse: %s" % (len(roh), len(gesehen), len(D), dict(sorted(ohne.items(), key=lambda x: -x[1])[:12])))
print()


def block(T, titel):
    print("== %s (n = %d, %d Symbole)" % (titel, len(T), T["symbol"].nunique()))
    for h in H:
        if "r%d" % h not in T or T["r%d" % h].notna().sum() < 10:
            continue
        r, u = T["r%d" % h].dropna(), T["u%d" % h].dropna()
        print("  %4d h  n=%4d  Median %+6.2f %%  Mittel %+6.2f %%  im Minus %3.0f %%  | gegen Markt: Median %+6.2f %%, schlechter %3.0f %%"
              % (h, len(r), 100 * r.median(), 100 * r.mean(), 100 * (r < 0).mean(), 100 * u.median(), 100 * (u < 0).mean()))
    for h in (168, 336):
        if "w%d" % h in T and T["w%d" % h].notna().sum() >= 10:
            w = T["w%d" % h].dropna()
            # unabhaengige Faelle: Symbol-Wochen (dieselbe Woche desselben Assets zaehlt einmal, Mittel ihrer Signale)
            kl = T.dropna(subset=["w%d" % h]).groupby(["symbol", "woche"])["w%d" % h].mean()
            se = kl.std(ddof=1) / np.sqrt(len(kl))
            print("  %4d h  gegen DIESELBEN Watchlist-Assets: Median %+6.2f %%, schlechter %3.0f %% | Symbol-Wochen %d, Mittel %+6.2f %% +- %.2f (2 SE %s)"
                  % (h, 100 * w.median(), 100 * (w < 0).mean(), len(kl), 100 * kl.mean(), 100 * se,
                     "ueber null" if kl.mean() - 2 * se > 0 else ("unter null" if kl.mean() + 2 * se < 0 else "schliesst null ein")))
    if "mae168" in T:
        m = T["mae168"].dropna()
        print("  in den 7 Tagen danach: tiefer als der Einstieg %3.0f %%, mindestens 5 %% tiefer %3.0f %%, 10 %% tiefer %3.0f %% (n=%d)"
              % (100 * (m < 0).mean(), 100 * (m < -0.05).mean(), 100 * (m < -0.10).mean(), len(m)))
    lg = T["lage"].dropna()
    if len(lg) >= 10:
        print("  Lage im 15-Tage-Bereich (0 Boden, 1 Gipfel): Median %.2f, im unteren Fuenftel %3.0f %% (n=%d)"
              % (lg.median(), 100 * (lg < 0.2).mean(), len(lg)))


block(D, "ALLE Spot-Kaufsignale")
for a in sorted(D["aktion"].unique()):
    block(D[D["aktion"] == a], a)
for mo in sorted(D["monat"].unique()):
    block(D[D["monat"] == mo], "Monat " + mo)
# Bezug fuer die Lage: alle Stunden der Signal-Assets im Signalzeitraum
syms = sorted(set(zu.get(s, (s,))[0] for s in D["symbol"]) & set(CL.columns))
von = min(r[1] for r in roh)[:13].replace("T", " ") + ":00"
bez = LAGE.loc[von:, syms].stack().dropna()
print()
print("BEZUG Zufallseinstieg: Lage aller Stunden derselben %d Assets seit %s: Median %.2f, im unteren Fuenftel %3.0f %% (n=%d)"
      % (len(syms), von, bez.median(), 100 * (bez < 0.2).mean(), len(bez)))
for h in H:
    rr = (CL.shift(-h) / CL - 1).loc[von:, syms].stack().dropna()
    if len(rr):
        print("BEZUG %4d h: Median %+6.2f %%, im Minus %3.0f %%" % (h, 100 * rr.median(), 100 * (rr < 0).mean()))
