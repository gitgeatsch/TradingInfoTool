"""P61 / O21 Stufe 1 - VORPRUEFUNG der laufenden Ergebnismessung der REGEL0-Signale (17.10.2026). Nur lesend; Binance-Kerzen frei.

    python Basisinfos/Rechenkern_02_10/p61_o21_vorpruefung.py <Kopie regel0_signale.db> <Wegwerf-Kopie tradinginfotool.db>

  Teil 0  R-R11 der MESS-DEFINITION: die Referenz kern48jbz_einstiege_bestand.csv traegt je Einstieg t_u / t_d (Stunden bis +5 % bzw.
          -5 %, gemessen an Hoch/Tief der Folgestunden gegen den SCHLUSS der Einstiegsstunde; 'stunde' = Einstiegsstunde = Signal + 1).
          Mit E2.ergebnisse auf den Reihen von stundenkurse.db nachgerechnet - bitgleich? (so misst spaeter auch der Betrieb)
  Teil 1  AUSSAGEKRAFT: 24-h-Ertrag und Trefferbilanz Q der Referenz 2025-01..2026-08; Streuung, Tagesklumpung, und wie viele
          BETRIEBSTAGE es braucht, bis das Mittel auf +-0,2 Pp (95 %) steht bzw. von 0 und von 0,48 % (Kosten) unterscheidbar ist
  Teil 2  BETRIEB 03.-14.10.: die Signale der NB-Kopie, Ausgang aus Binance-Stundenkerzen (Markt und Paar wie im Signal); Abgleich
          Signalkurs gegen Schluss der Einstiegsstunde; Mittel, Q, je Hebel-Schalter und Stufe, Tagesblock-Intervall; gegen die Referenz
  Teil 3  ECHTE TRADES: Lebenszyklen aus dem Hebel-Buch (Wegwerf-Kopie der NB-Sicherung) ab 03.10., je Trade das REGEL0-Signal
          desselben Assets (Eroeffnung 1-26 h nach der Signalstunde), Brutto-Ergebnis (ohne Gebuehr/Finanzierung) und Haltedauer
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import messe_e2_beitraege as E2  # noqa: E402
import agent.regel0_nachlader as NL  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
KOPIE, PROD = sys.argv[1], sys.argv[2]
B0 = datetime(2020, 1, 1)
KOSTEN = 0.0048
rng = np.random.default_rng(61)


def h_txt(h):
    return (B0 + timedelta(hours=int(h))).strftime("%Y-%m-%d %H:%M")


def q_von(tu, td):
    return np.where((tu <= 24) & (tu < td), 1, np.where((td <= 24) & (td <= tu), -1, 0))


def tagesblock(werte, tage, n_boot=2000):
    d = pd.DataFrame({"w": werte, "t": tage}).dropna()
    g = d.groupby("t").w.agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    T = len(g)
    if T < 2:
        return np.nan, np.nan
    ix = rng.integers(0, T, (n_boot, T))
    m = s[ix].sum(1) / n[ix].sum(1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


# ══ Teil 0 + 1: Referenz ════════════════════════════════════════════════════════════════════════════════════════════════════
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
reihen = {}
for datei in ("stundenkurse.db", "stundenkurse_alle.db"):           # wie regel0_llm._reihe_stunden: die erste Datei gewinnt
    c = sqlite3.connect("file:data/%s?mode=ro" % datei, uri=True)
    for sym in sorted(E.symbol.unique()):
        if sym in reihen:
            continue
        rows = c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
        if rows:
            reihen[sym] = rows
    c.close()
tu_n, td_n, e24 = [], [], []
for r in E.itertuples():
    rows = reihen.get(r.symbol)
    if rows is None:
        tu_n.append(np.nan); td_n.append(np.nan); e24.append(np.nan)
        continue
    if not hasattr(q_von, "_cache"):
        q_von._cache = {}
    if r.symbol not in q_von._cache:
        st = np.array([int((datetime.strptime(x[0], "%Y-%m-%d %H:%M") - B0).total_seconds() // 3600) for x in rows])
        h = np.array([x[1] for x in rows], float)
        lo = np.array([x[2] for x in rows], float)
        cc = np.array([x[3] for x in rows], float)
        t, _m, _v = E2.ergebnisse(h, lo, cc, 72, (("u5", 1.05, True), ("d5", 0.95, False)))
        q_von._cache[r.symbol] = (st, t["u5"], t["d5"], cc)
    st, tu, td, cc = q_von._cache[r.symbol]
    i = np.searchsorted(st, r.stunde)
    if i < len(st) and st[i] == r.stunde:
        tu_n.append(tu[i]); td_n.append(td[i])
        e24.append(cc[i + 24] / cc[i] - 1 if i + 24 < len(st) and st[i + 24] == r.stunde + 24 else np.nan)
    else:
        tu_n.append(np.nan); td_n.append(np.nan); e24.append(np.nan)
E["tu_n"], E["td_n"], E["e24"] = tu_n, td_n, e24
tu_ref = pd.to_numeric(E.t_u, errors="coerce")
td_ref = pd.to_numeric(E.t_d, errors="coerce")
gl = ((E.tu_n == tu_ref) | (E.tu_n.isna() & tu_ref.isna())) & ((E.td_n == td_ref) | (E.td_n.isna() & td_ref.isna()))
print("P61 / O21 VORPRUEFUNG - laufende Ergebnismessung der REGEL0-Signale\n")
print("TEIL 0 R-R11 Mess-Definition: t_u/t_d aus den REGEL0-Stundenkursen mit E2.ergebnisse gegen die Referenz: %d von %d Einstiegen gleich%s" % (
    int(gl.sum()), len(E), "  ✔ BITGLEICH" if gl.all() else "  ⛔ ABWEICHUNG (z. B. %s)" % E[~gl].head(5)[["symbol", "stunde", "t_u", "tu_n", "t_d", "td_n"]].values.tolist()))
print("   ohne Reihe am Desktop: %s" % (sorted(set(E.symbol) - set(reihen)) or "-"))
E["q"] = q_von(E.tu_n.fillna(999).to_numpy(), E.td_n.fillna(999).to_numpy())
E["tag"] = E.stunde // 24
R = E[(E.jahr >= 2025)].copy()
lo_, hi_ = tagesblock(R.e24, R.tag)
print("\nTEIL 1 AUSSAGEKRAFT (Referenz bestand 2025-01..2026-08: %d Einstiege an %d Tagen, %.1f je Tag)" % (len(R), R.tag.nunique(), len(R) / R.tag.nunique()))
print("   24-h-Ertrag: Mittel %+.3f %%, Streuung %.2f %% je Einstieg · Tagesblock-95 %%: [%+.3f, %+.3f] %% · Trefferbilanz Q %+.3f" % (
    100 * R.e24.mean(), 100 * R.e24.std(), 100 * lo_, 100 * hi_, R.q.mean()))
naiv = 1.96 * R.e24.std() / np.sqrt(R.e24.notna().sum())
print("   Klumpung: Tagesblock-Halbbreite %.2f Pp gegen %.2f Pp bei unabhaengigen Einstiegen -> Faktor %.0f auf die Varianz, also "
      "effektiv etwa %.1f unabhaengige Beobachtung(en) je Tag (alle Einstiege eines Tages sehen denselben Markt)" % (
          100 * (hi_ - lo_) / 2, 100 * naiv, ((hi_ - lo_) / 2 / naiv) ** 2, (len(R) / R.tag.nunique()) / ((hi_ - lo_) / 2 / naiv) ** 2))
print("   Halbe Breite des 95-%%-Intervalls des Mittels nach N Betriebstagen (Tage aus der Referenz gezogen, gleiche Klumpung):")
tage = R.tag.unique()
g = R.groupby("tag").e24.agg(["sum", "count"])
for N in (14, 30, 60, 90, 180, 365):
    ix = rng.integers(0, len(g), (2000, N))
    m = g["sum"].to_numpy()[ix].sum(1) / g["count"].to_numpy()[ix].sum(1)
    hb = (np.percentile(m, 97.5) - np.percentile(m, 2.5)) / 2
    print("     %4d Tage: +-%.2f Pp%s" % (N, 100 * hb, "  <- Mittel von 0 trennbar (wenn es wie 2025-26 ist)" if hb < abs(R.e24.mean()) else ""))

# ══ Teil 2: Betrieb Oktober ═════════════════════════════════════════════════════════════════════════════════════════════════
k = sqlite3.connect("file:%s?mode=ro" % KOPIE.replace("\\", "/"), uri=True)
S = pd.read_sql("SELECT symbol, signalstunde, einstieg, ausstieg, stufe, hebel_schalter, bitpanda, kurs, kurs_markt, paar, faktor, mail_signal_am, "
                "zusatz FROM signal ORDER BY signalstunde", k)
k.close()
jetzt_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
kerzen, fehler = {}, []
t0 = time.time()
ZW = os.path.join(os.path.dirname(os.path.abspath(PROD)), "o21_kerzen.json")             # Zwischenspeicher im Wegwerf-Ordner
if os.path.exists(ZW):
    kerzen = {tuple(k_.split("|")): v for k_, v in json.load(open(ZW, encoding="utf-8")).items()}
for (sym, markt, paar), _g in S.groupby([S.symbol, S.kurs_markt.fillna("spot"), S.paar.fillna(S.symbol + "USDT")]):
    if (sym, markt, paar) in kerzen:
        continue
    url = NL.FUT[1] if markt == "futures" else NL.SPOT[1]
    try:
        k_ = NL._hole(url, paar, NL._ms("2026-10-02 00:00"), jetzt_ms)
        kerzen[(sym, markt, paar)] = {NL._stunde(int(x[0])): (float(x[2]), float(x[3]), float(x[4])) for x in k_}
    except Exception as ex:                                                   # noqa: BLE001
        fehler.append("%s %s %s: %s" % (sym, markt, paar, type(ex).__name__))
json.dump({"|".join(k_): v for k_, v in kerzen.items()}, open(ZW, "w", encoding="utf-8"))
erg = []
for r in S.itertuples():
    key = (r.symbol, r.kurs_markt or "spot", r.paar or r.symbol + "USDT")
    kz = kerzen.get(key) or {}
    e = datetime.strptime(r.einstieg, "%Y-%m-%d %H:%M")
    h = [kz.get((e + timedelta(hours=s)).strftime("%Y-%m-%d %H:%M")) for s in range(0, 73)]
    if h[0] is None or any(x is None for x in h[1:25]):
        erg.append(dict(e24=np.nan, q=np.nan, vollst=False))
        continue
    cc = h[0][2]
    tu = next((s for s in range(1, 73) if h[s] is not None and h[s][0] >= 1.05 * cc), 999)
    td = next((s for s in range(1, 73) if h[s] is not None and h[s][1] <= 0.95 * cc), 999)
    sh = kz.get(r.signalstunde)
    erg.append(dict(e24=h[24][2] / cc - 1, q=int(q_von(np.array([tu]), np.array([td]))[0]), vollst=True, cc=cc,
                    kursdiff=(r.kurs / (cc * (r.faktor or 1.0)) - 1) if r.kurs else np.nan,
                    kursdiff_sig=(r.kurs / (sh[2] * (r.faktor or 1.0)) - 1) if (r.kurs and sh) else np.nan))
X = pd.concat([S.reset_index(drop=True), pd.DataFrame(erg)], axis=1)
X["tag"] = X.signalstunde.str[:10]
V = X[X.vollst == True]                                                         # noqa: E712
lo_, hi_ = tagesblock(V.e24, V.tag)
print("\nTEIL 2 BETRIEB %s bis %s: %d Signale (%d Assets), Kerzen geholt %d Reihen in %.0f s, Fehler %d%s" % (
    S.signalstunde.min(), S.signalstunde.max(), len(S), S.symbol.nunique(), len(kerzen), time.time() - t0, len(fehler),
    (" (%s)" % "; ".join(fehler[:4])) if fehler else ""))
print("   mit vollem 24-h-Ausgang: %d an %d Tagen · Signalkurs gegen Schluss der Einstiegsstunde: Median %+.3f %%, |Abw.| > 1 %% bei %d von %d · "
      "gegen Schluss der SIGNALstunde: Median %+.3f %%, |Abw.| > 1 %% bei %d von %d"
      % (len(V), V.tag.nunique(), 100 * V.kursdiff.median(), int((V.kursdiff.abs() > 0.01).sum()), int(V.kursdiff.notna().sum()),
         100 * V.kursdiff_sig.median(), int((V.kursdiff_sig.abs() > 0.01).sum()), int(V.kursdiff_sig.notna().sum())))
print("   24-h-Ertrag: Mittel %+.3f %% · Tagesblock-95 %% [%+.3f, %+.3f] %% · Q %+.3f · Anteil +5 %% zuerst %.1f %%, -5 %% zuerst %.1f %%" % (
    100 * V.e24.mean(), 100 * lo_, 100 * hi_, V.q.mean(), 100 * (V.q == 1).mean(), 100 * (V.q == -1).mean()))
print("   Referenz 2025-26 zum Vergleich: Mittel %+.3f %%, Q %+.3f" % (100 * R.e24.mean(), R.q.mean()))
for name, sel in (("Hebel-Schalter an", V.hebel_schalter == 1), ("Schalter aus/ohne", V.hebel_schalter != 1),
                  ("Stufe 5", V.stufe == 5), ("Stufe 3", V.stufe == 3), ("Stufe 2", V.stufe == 2), ("Zusatz-Assets", V.zusatz == 1),
                  ("ohne 09./10.10.", ~V.tag.isin(["2026-10-09", "2026-10-10"]))):
    s_ = V[sel]
    print("     %-18s n %3d · Tage %2d · Mittel %+.3f %% · Q %+.3f" % (name, len(s_), s_.tag.nunique(), 100 * s_.e24.mean(), s_.q.mean()))
print("   je Tag: " + " · ".join("%s %d %+.2f%%" % (t_[5:], len(g_), 100 * g_.e24.mean()) for t_, g_ in V.groupby("tag")))

# ══ Teil 3: echte Trades ════════════════════════════════════════════════════════════════════════════════════════════════════
import importer.hebel_buch as HB  # noqa: E402
cp = sqlite3.connect(PROD)
Z = [z for z in HB.lebenszyklen(cp) if str(z["auf"]) >= "2026-10-03"]
vg = pd.read_sql("SELECT zeit, typ, asset_id, zugang, abgang, kurs FROM hebel_buch_vorgang", cp)
kat = dict(cp.execute("SELECT asset_id, symbol FROM bitpanda_katalog").fetchall())
cp.close()
vg["symbol"] = vg.asset_id.map(kat)
print("\nTEIL 3 ECHTE TRADES ab 03.10. (Hebel-Buch der NB-Sicherung): %d Lebenszyklen" % len(Z))
print("   ⚠️ Das Ergebnis eines echten Trades steht NICHT direkt in den Vorgaengen: Bitpanda bucht Eigenkapital, Kredit, Teilverkauf "
      "(nur der Kreditanteil) und Uebertrag ins Spot-Wallet als eigene Transaktionen - hier nur Signalbezug, Verzug und Haltedauer")
for z in Z:
    auf = datetime.fromisoformat(str(z["auf"]).replace("Z", "")[:19])
    kand = X[(X.bitpanda.where(X.bitpanda.notna(), X.symbol).str.upper() == z["symbol"].upper())]
    kand = kand[[1 <= (auf - datetime.strptime(s_, "%Y-%m-%d %H:%M")).total_seconds() / 3600 <= 26 for s_ in kand.signalstunde]]
    sg = kand.iloc[-1] if len(kand) else None
    dauer = ((datetime.fromisoformat(str(z["zu"]).replace("Z", "")[:19]) - auf).total_seconds() / 3600) if z.get("zu") else np.nan
    verzug = ((auf - datetime.strptime(sg.einstieg, "%Y-%m-%d %H:%M")).total_seconds() / 3600) if sg is not None else np.nan
    print("   %-6s auf %s UTC · zu %s · Haltedauer %s (Regel 24 h) · %s" % (
        z["symbol"], str(z["auf"])[:16], str(z.get("zu"))[:16] if z.get("zu") else "offen", "%.0f h" % dauer if dauer == dauer else "offen",
        ("REGEL0-Signal %s, Stufe %s, Schalter %s, Eroeffnung %.1f h nach dem gemessenen Einstieg; 24-h-Ertrag des Signals %+.2f %%" % (
            sg.signalstunde, int(sg.stufe), int(sg.hebel_schalter) if sg.hebel_schalter == sg.hebel_schalter else "-", verzug, 100 * sg.e24))
        if sg is not None else "KEIN REGEL0-Signal in den 26 h davor (eigene Entscheidung)"))
