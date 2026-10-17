"""Spot B4 - Abbau-Reihenfolge (P18, 13.10.2026; Voranalyse_Spot_Neubau_04_10.md §39.7, §42.1, §43, §48).

Nutzer 13.10.: *"Ja"* (B4 bauen; O40 als P18b nach eigener Pruefung, Spot §48.5).

DIE REGEL (wie gemessen - der Nachbau ``p18_voranalyse.B4`` gibt an 7.471 von 7.471 Ankern der Vormessung dasselbe Fuenftel, Teil 0;
die Klasse ``Wert`` hier ist DERSELBE Code):

    Stichtag   Monatserster t (Dollar-Tagesschluss); gerechnet ab dem 2., wenn alle Eingaenge den Schluss von t haben, spaetestens am 5.
    Universum  Binance-Spot (Betriebskopie messdaten.db, TRADING + BREAK, >= 400 Kerzen) mit Kurs an t und >= 30 T Umsatz in 90 T;
               PLUS die GEHALTENEN Coins ausserhalb Binance mit >= 400 Kerzen in der Produktion (Uebernahmeregel §42.1). Ohne Stablecoins
               (Median |Tagesrendite| < 0,2 %), Sonderwerte und Kern
    Klasse     Marktwert-Rang (Umlauf CoinGecko x Schluss): H = Rang <= 30 an t, t-1M, t-2M und >= 730 T Daten; M <= 100; S Rest; ohne
               Umlauf die Umsatz-Klasse. ⚠️ Fehlt der Umlauf eines VORMONATS (NB-Reihe erst ab 09/2026), gilt der Umlauf am Stichtag -
               dieselbe Ersatzregel wie in der Messung vor 21.09.2025 (Spot §48.6: mit ihr 0 Abweichungen, ohne sie H 24 -> 0)
    Wert       ohne F9: Mittel der Perzentile in der Zelle (Stichtag x Klasse) von F1 Tiefe unter dem Hoch (unten), F2 Tage seit dem
               Hoch (oben), F8 Alter = Tage seit dem ersten Kurs DER REIHE (oben); ein Merkmal zaehlt in Zellen mit >= 10 Coins; F1/F2
               ab 180 Kerzen. UNTERES FUENFTEL = Perzentil <= 0,2
    Handlung   "Wenn du abbaust: zuerst X" - Mail einmal als ERSTLISTE, danach nur fuer Coins, die NEU ins untere Fuenftel fallen (E-91)
    Beleg      §43 (E-101): 12 Monate danach im Mittel 12,5 Pp (Dollar) unter einem zufaelligen Coin derselben Klasse (ab 2024, Rang 0,000)

DATEN AM NB (ohne Handgriff am Desktop): Kurse/Umsatz aus der Betriebskopie (500 T); das Hoch, sein Datum und der erste Kurs VOR dem
Fenster aus dem STAMMSATZ (Tabelle ``abbau_stamm``) - einmal je Paar die ganze Reihe bei Binance (frei), danach fortgeschrieben
(Teil 1/G3: Stammsatz + Fenster = volle Geschichte, 0 Abweichungen). Coins ausserhalb Binance: ``price_history_ohlc`` der Produktion.
Umlauf: ``umlaufmenge_cg.db``. Alles NUR LESEND bis auf die eigene Ablage ``data/spot_betrieb.db``.

NICHT gemessen und daher nicht behauptet: die Reihenfolge INNERHALB des unteren Fuenftels (die Mail ordnet nach Wert in EUR, nicht nach
Guete). Kein Futures-Start (traegt nicht, §39.5), kein TVL (F9, D4 spaeter), keine Umschichtung des Erloeses (B-6).
"""
from __future__ import annotations

import csv
import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from agent import spot_mitnahme as SM

logger = logging.getLogger(__name__)

ABLAGE = SM.ABLAGE
KERN = SM.KERN
KOPIE = "messdaten.db"                   # Betriebskopie am NB (Binance-Spot, 500 T)
UMLAUF = "umlaufmenge_cg.db"
FENSTER_T = 420                          # Rechenfenster; Stammsatz bis t - FENSTER_T - 1 (G3: jede Schnittlaenge gleich)
MIN_KERZEN = 400                         # Uebernahmeregel = MESSgrenze (lade_messreihen.MIN_KERZEN)
STABIL = 0.002                           # Median |Tagesrendite| darunter = Stablecoin (s3_stufe1.stabil)
LETZTER_TAG = 5                          # bis zum 5. wird gewartet, dann gerechnet mit dem, was da ist
ZUORDNUNG_TOLERANZ = 0.03                # D5: Tagesschluss Produktion / Binance-Reihe im Median ausserhalb 0,97-1,03 = anderer Coin
# s3_stufe1.SONDER (Fiat, Gold, Wrapped, Stablecoins mit Namen, Kern) - dieselbe Liste wie in der Messung
SONDER = {"AEUR", "AUD", "EUR", "EURI", "GBP", "PAXG", "WBTC", "WBETH", "BNSOL", "BFUSD", "BUSD", "FDUSD", "PAX", "TUSD", "USD1", "USDC",
          "USDP", "USDSOLD", "XUSD", "BTC", "ETH", "SOL"}
BELEG = ("Gemessen ab 2024 (20 Monatsstichtage, Spot §43): Coins im unteren Fünftel lagen 12 Monate später im Mittel 12,5 Prozentpunkte "
         "(in Dollar) unter einem zufällig gewählten Coin derselben Klasse – in jeder Klasse (H −33,9 · M −16,8 · S −9,4) und in "
         "beiden Jahren (2024 −17,0 · 2025 −7,0); gegen Zufall Rang 0,000. Vorläufig ohne das TVL-Merkmal")
ZUORDNUNG_DATEI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Basisinfos", "symbol_zuordnung.csv")


# ══ die Regel - DERSELBE Code wie p18_voranalyse.B4 (Teil 0 bitgleich) ════════════════════════════════════════════════════════
class Wert:
    """Fuenftel des Watchlist-Werts ohne F9 je Zelle Stichtag x Marktwert-Klasse. ``stamm``: {Symbol: (hoch, pos_hoch, erst, n, schnitt)}
    mit Positionen im Index von K (Stammsatz bis einschliesslich ``schnitt``); ``erst`` ueberschreibt den ersten Kurs (Fensterbetrieb)."""

    def __init__(self, K, U, ausschluss, umlauf, stamm=None, erst=None):
        univ = [s for s in K.columns if s not in ausschluss]
        self.X = K[univ]
        self.U90 = U.reindex(columns=univ).rolling(90, min_periods=30).mean().shift(1)
        self.ERST = self.X.apply(lambda x: x.first_valid_index())
        if erst:
            for s, e in erst.items():
                if s in self.ERST.index and e is not None:
                    self.ERST[s] = pd.Timestamp(e)
        self.umlauf = umlauf
        self.stamm = stamm
        self.pos = {t: i for i, t in enumerate(self.X.index)}
        self._r = {}

    def _rang_umsatz(self, m):
        if m not in self._r:
            da = self.X.columns[self.X.loc[m].notna().values] if m in self.pos else []
            self._r[m] = self.U90.loc[m, da].dropna().rank(ascending=False) if m in self.pos else pd.Series(dtype=float)
        return self._r[m]

    def klassen_umsatz(self, m):
        r, r1, r2 = self._rang_umsatz(m), self._rang_umsatz(m - pd.DateOffset(months=1)), self._rang_umsatz(m - pd.DateOffset(months=2))
        out = {}
        for s, x in r.items():
            if x <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (m - self.ERST[s]).days >= 730:
                out[s] = "H"
            else:
                out[s] = "M" if x <= 100 else "S"
        return out

    def _rang_mw(self, m):
        kl = self.klassen_umsatz(m)
        mw = {s: self.umlauf(s, m) * self.X.at[m, s] for s in kl}
        mw = {s: v for s, v in mw.items() if v == v and v > 0}
        return kl, pd.Series(mw, dtype=float).rank(ascending=False)

    def klassen(self, m):
        kl, r = self._rang_mw(m)
        r1 = self._rang_mw(m - pd.DateOffset(months=1))[1] if (m - pd.DateOffset(months=1)) in self.pos else pd.Series(dtype=float)
        r2 = self._rang_mw(m - pd.DateOffset(months=2))[1] if (m - pd.DateOffset(months=2)) in self.pos else pd.Series(dtype=float)
        out = {}
        for s, k_ums in kl.items():
            if s not in r.index:
                out[s] = k_ums
            elif r[s] <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (m - self.ERST[s]).days >= 730:
                out[s] = "H"
            else:
                out[s] = "M" if r[s] <= 100 else "S"
        return out

    def merkmale(self, m, s):
        i = self.pos[m]
        x = self.X[s].values[: i + 1]
        if self.stamm is None or s not in self.stamm:
            ok = ~np.isnan(x)
            n = int(ok.sum())
            hoch = np.nanmax(x) if ok.any() else np.nan
            idx = np.where(ok & (x == np.fmax.accumulate(np.where(ok, x, -np.inf))))[0]
            tage = i - idx[-1] if len(idx) else np.nan
            erst = self.ERST[s]
        else:
            hoch0, i_hoch0, erst, n0, schnitt = self.stamm[s]
            w = x[schnitt + 1:]
            okw = ~np.isnan(w)
            n = n0 + int(okw.sum())
            cm = np.fmax.accumulate(np.r_[hoch0 if hoch0 == hoch0 else -np.inf, np.where(okw, w, -np.inf)])[1:]
            gl = np.where(okw & (w == cm))[0]
            hoch = cm[-1]
            tage = i - (schnitt + 1 + gl[-1]) if len(gl) else i - i_hoch0
            erst = self.ERST[s]
        if np.isnan(x[-1]):
            return np.nan, np.nan, np.nan
        f1 = x[-1] / hoch - 1 if n >= 180 else np.nan
        f2 = float(tage) if n >= 180 else np.nan
        return f1, f2, float((m - erst).days)

    def fuenftel(self, m, nur=None):
        """-> DataFrame sym, kl, F1, F2, F8, wert, p, q (q = Fuenftel 1..5; 1 = unten)."""
        kl = self.klassen(m)
        if nur is not None:
            kl = {s: k for s, k in kl.items() if s in nur}
        z = pd.DataFrame([(s, k) + self.merkmale(m, s) for s, k in kl.items()], columns=["sym", "kl", "F1", "F2", "F8"])
        z["wert"] = np.nan
        z["p"] = np.nan
        for _, g in z.groupby("kl"):
            P = []
            for f, seite in (("F1", "unten"), ("F2", "oben"), ("F8", "oben")):
                v = g[f]
                pc = pd.Series(np.nan, index=g.index)
                if v.notna().sum() >= 10:
                    pc[v.notna()] = v[v.notna()].rank(pct=True)
                P.append(1 - pc if seite == "unten" else pc)
            P = pd.concat(P, axis=1)
            with np.errstate(all="ignore"):
                w = P.mean(axis=1, skipna=True)
            z.loc[g.index, "wert"] = w
            ok = w.notna()
            if ok.sum() >= 10:
                z.loc[g.index[ok.values], "p"] = w[ok].rank(pct=True).values
        z["q"] = np.where(z.p.isna(), np.nan, np.clip(np.ceil(z.p * 5), 1, 5))
        return z


# ══ Stammsatz (D3) ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def stamm_aus(tage: list, schluesse: list, bis: date) -> dict:
    """Stammsatz aus einer Reihe [(Tag, Schluss)] bis einschliesslich ``bis``: Hoch, Tag des Hochs (letzter Gleichstand, wie die
    Messung ``X == cummax``), erster Tag, Kerzenzahl, Median |Tagesrendite| (ueber die GANZE Reihe, Stablecoin-Pruefung)."""
    d = pd.Series(schluesse, index=pd.to_datetime(tage), dtype=float).sort_index()
    d = d[~d.index.duplicated(keep="last")].asfreq("D")         # je Tag EIN Schluss (wie die Messung: pivot je Tag)
    r = d.pct_change(fill_method=None)
    med = float(r.abs().median()) if r.notna().any() else None
    vor = d[: pd.Timestamp(bis)]
    ok = vor.notna()
    if not ok.any():
        return {"hoch": None, "tag_hoch": None, "erst": d.first_valid_index().date().isoformat() if d.notna().any() else None, "n": 0,
                "stand": bis.isoformat(), "median_absret": med}
    cm = vor.cummax()
    gl = vor.index[(ok & (vor == cm)).values]
    return {"hoch": float(cm.iloc[-1]), "tag_hoch": gl[-1].date().isoformat(), "erst": d.first_valid_index().date().isoformat(),
            "n": int(ok.sum()), "stand": bis.isoformat(), "median_absret": med}


def fortschreiben(st: dict, tage: list, schluesse: list, bis: date) -> dict:
    """Stammsatz von ``st['stand']`` bis ``bis`` weiterschreiben mit den Kerzen dazwischen (aus der Betriebskopie)."""
    neu = dict(st, stand=bis.isoformat())
    for t, k in sorted(zip(tage, schluesse)):
        if not (st["stand"] < t <= bis.isoformat()) or k is None or k != k:
            continue
        neu["n"] += 1
        if neu["hoch"] is None or k >= neu["hoch"]:
            neu["hoch"], neu["tag_hoch"] = float(k), t
    return neu


def hole_binance_reihe(symbol: str, http=None) -> list:
    """Ganze Tagesreihe eines USDT-Paars bei Binance (frei) -> [(Tag, Schluss)]. ``http`` (Pruefstand): Ersatz fuer den Abruf."""
    if http is not None:
        return http(symbol)
    import requests

    import lade_messreihen as LM
    s = requests.Session()
    roh = LM.hole_alles(s, symbol + "USDT")
    return [(datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc).date().isoformat(), float(k[4])) for k in roh]


# ══ Ablage ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def oeffne(ordner: str) -> sqlite3.Connection:
    c = SM.oeffne(ordner)                    # legt auch die gemeinsame Tabelle protokoll an
    c.execute("CREATE TABLE IF NOT EXISTS abbau_stamm (symbol TEXT PRIMARY KEY, hoch REAL, tag_hoch TEXT, erst TEXT, n INTEGER, stand TEXT, "
              "median_absret REAL, quelle TEXT, geholt_am TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS abbau_lauf (stichtag TEXT PRIMARY KEY, am TEXT, status TEXT, art TEXT, universum INTEGER, "
              "zellen TEXT, unten TEXT, neu TEXT, fehlend TEXT, mail_am TEXT, fehler TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS abbau_fuenftel (stichtag TEXT, symbol TEXT, reihe TEXT, klasse TEXT, f1 REAL, f2 REAL, f8 REAL, "
              "perzentil REAL, fuenftel INTEGER, grund TEXT, menge REAL, PRIMARY KEY (stichtag, symbol))")
    c.commit()
    return c


def _zuordnung() -> dict:
    """Bitpanda-Kuerzel -> (Binance-Spot-Kuerzel, Faktor) aus Basisinfos/symbol_zuordnung.csv (CAT -> 1000CAT, Faktor 1000)."""
    aus = {}
    try:
        with open(ZUORDNUNG_DATEI, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                if r.get("markt") == "spot":
                    aus[r["bitpanda"]] = (r["binance"], float(r.get("faktor") or 1))
    except OSError:
        pass
    return aus


def _universum_ablegen(c, conn_prod, t: str, z: pd.DataFrame, gehalten: set) -> int:
    """P19 A3: je Coin des Universums Klasse, Perzentil und Fuenftel am Stichtag, dazu Bitpanda-Kuerzel und -Handelbarkeit (Katalog der
    Produktion, nur lesend) und ob gehalten (O41: markiert, nicht bevorzugt). ``z``: Ergebnis von ``Wert.fuenftel`` (Index = Reihe)."""
    c.execute("CREATE TABLE IF NOT EXISTS abbau_universum (stichtag TEXT, reihe TEXT, bitpanda TEXT, klasse TEXT, perzentil REAL, "
              "fuenftel INTEGER, handelbar INTEGER, gehalten INTEGER, PRIMARY KEY (stichtag, reihe))")
    bp_von = {bn: bp for bp, (bn, _f) in _zuordnung().items()}
    kat = {str(s).upper() for s in pd.read_sql("SELECT symbol FROM bitpanda_katalog WHERE gruppe IN ('coin','token') AND symbol IS NOT NULL",
                                                conn_prod).symbol}
    c.execute("DELETE FROM abbau_universum WHERE stichtag=?", (t,))
    n = 0
    for s, r in z.iterrows():
        if r.q != r.q:
            continue
        bp = bp_von.get(s, s)
        c.execute("INSERT INTO abbau_universum VALUES (?,?,?,?,?,?,?,?)", (t, s, bp, r.kl, float(r.p), int(r.q), int(bp.upper() in kat),
                                                                         int(s in gehalten)))
        n += 1
    return n


def kandidaten(ordner: str, je_klasse: int = 10) -> dict | None:
    """P19 A3: Einstiegs-Kandidaten = oberes Fuenftel des Watchlist-Werts am letzten Stichtag, bei Bitpanda handelbar; H alle, M und S die
    besten ``je_klasse`` nach Perzentil. Belegstufe: ORDNET den Fortbestand (Spot §25.6/§39.9), ein Einstieg je Asset ist NICHT belegt
    (E-102). -> {'stichtag', 'liste': {Klasse: [(Bitpanda, Perzentil, gehalten)]}, 'kurz': {Klasse: [Text]}, 'anzahl'} oder None"""
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return None
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='abbau_universum'").fetchone():
            return None
        t = c.execute("SELECT MAX(stichtag) FROM abbau_universum").fetchone()[0]
        if not t:
            return None
        rows = c.execute("SELECT bitpanda, klasse, perzentil, gehalten FROM abbau_universum WHERE stichtag=? AND fuenftel=5 AND handelbar=1 "
                         "ORDER BY perzentil DESC, bitpanda", (t,)).fetchall()
        alle = c.execute("SELECT COUNT(*) FROM abbau_universum WHERE stichtag=? AND fuenftel=5", (t,)).fetchone()[0]
    finally:
        c.close()
    liste = {}
    for bp, kl, pz, geh in rows:
        liste.setdefault(kl, []).append((bp, pz, bool(geh)))
    liste = {kl: (v if kl == "H" else v[:je_klasse]) for kl, v in liste.items()}
    kurz = {kl: ["%s%s" % (bp, " (gehalten)" if geh else "") for bp, _p, geh in v] for kl, v in liste.items()}
    return {"stichtag": t, "liste": liste, "kurz": kurz, "anzahl": len(rows), "oben_gesamt": alle}


def _prod_reihe(conn_prod, symbol: str) -> pd.Series:
    d = pd.read_sql("SELECT date, close, volume FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND close IS NOT NULL "
                    "AND COALESCE(quelle, '') != 'rekonstruiert' ORDER BY date", conn_prod, params=(symbol,))
    if d.empty:
        return pd.DataFrame(columns=["close", "umsatz"])
    d["date"] = pd.to_datetime(d.date.str[:10])
    d = d.drop_duplicates("date", keep="last").set_index("date")
    return pd.DataFrame({"close": d.close.astype(float), "umsatz": d.close.astype(float) * d.volume.astype(float)})


# ══ ein Lauf ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def stichtag(heute: date) -> date:
    return heute.replace(day=1)


def lauf(conn_prod, ordner: str, watchlist: list, heute: date | None = None, http=None, mit_tabelle: bool = False) -> dict:
    """Rechnet den Stichtag des laufenden Monats (einmal; danach nur noch die Mail-Lage). Schreibt nur in die Ablage.
    -> {'stichtag', 'status' (fertig|wartet|frueh|schon), 'art' (erstliste|neu), 'unten': [...], 'neu': [...], 'fehlend': [...], ...}"""
    heute = heute or datetime.now(timezone.utc).date()
    t = stichtag(heute)
    jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    erg = {"stichtag": t.isoformat(), "status": None, "art": None, "unten": [], "neu": [], "fehlend": [], "kreis": 0, "universum": 0,
           "geholt": 0, "fehler": None}
    c = oeffne(ordner)
    try:
        r = c.execute("SELECT status, art, unten, neu, fehlend, mail_am FROM abbau_lauf WHERE stichtag=?", (t.isoformat(),)).fetchone()
        if r and r[0] == "fertig":
            erg.update(status="schon", art=r[1], unten=json.loads(r[2] or "[]"), neu=json.loads(r[3] or "[]"),
                       fehlend=json.loads(r[4] or "[]"), mail_am=r[5])
            return erg
        if heute.day < 2:
            erg["status"] = "frueh"
            return erg
        bestand = SM.kreis(conn_prod, watchlist)
        erg["kreis"] = len(bestand)
        z_map = _zuordnung()
        # ---- Betriebskopie lesen (Fenster)
        ab = t - timedelta(days=FENSTER_T)
        kp = os.path.join(ordner, KOPIE)
        kc = sqlite3.connect("file:%s?mode=ro" % kp.replace("\\", "/"), uri=True, timeout=10)
        try:
            d = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' "
                            "AND date >= ? AND date <= ?", kc, params=(ab.isoformat(), t.isoformat()))
            spanne = {r[0]: (r[1][:10], r[2][:10]) for r in kc.execute("SELECT symbol, MIN(date), MAX(date) FROM price_history_ohlc WHERE "
                                                                      "assetklasse='krypto' AND currency='USD' GROUP BY symbol")}
        finally:
            kc.close()
        d["date"] = pd.to_datetime(d.date.str[:10])
        idx = pd.date_range(ab, t, freq="D")
        K = d.pivot_table(index="date", columns="symbol", values="close", aggfunc="last").reindex(idx)
        U = (d.assign(u=d.close * d.volume).pivot_table(index="date", columns="symbol", values="u", aggfunc="last").reindex(idx))
        mit_t = int(K.loc[pd.Timestamp(t)].notna().sum()) if len(K.columns) else 0
        # ---- gehaltene Coins: im Binance-Universum (mit Zuordnungspruefung D5) oder ausserhalb (Produktionsreihe >= 400 Kerzen)
        reihe_von, grund = {}, {}
        prod_cols = {}
        for s in bestand:
            b, f = z_map.get(s, (s, 1.0))
            pr = _prod_reihe(conn_prod, s)
            if b in K.columns and K[b].notna().any():
                gm = pd.concat([pr.close * f, K[b]], axis=1, join="inner").dropna().iloc[-60:] if len(pr) else pd.DataFrame()
                if len(gm) >= 20 and abs(float((gm.iloc[:, 0] / gm.iloc[:, 1]).median()) - 1) > ZUORDNUNG_TOLERANZ:
                    grund[s] = "Zuordnung unsicher (%s bei Binance ist ein anderer Kurs)" % b
                    continue
                reihe_von[s] = b
                continue
            pr = pr[pr.index <= pd.Timestamp(t)]
            if len(pr) < MIN_KERZEN:
                grund[s] = "zu jung (%d Tage Daten, Regel ab %d)" % (len(pr), MIN_KERZEN)
                continue
            if pd.Timestamp(t) not in pr.index:
                erg["fehlend"].append(s)
            prod_cols[s] = pr
            reihe_von[s] = s
        # ---- Vollstaendigkeit: Betriebskopie hat den Schluss von t, und jede Produktionsreihe auch
        if (mit_t < 100 or erg["fehlend"]) and heute.day < LETZTER_TAG:
            c.execute("INSERT OR REPLACE INTO abbau_lauf (stichtag, am, status, fehlend) VALUES (?,?,?,?)",
                      (t.isoformat(), jt, "wartet", json.dumps(erg["fehlend"] + ([] if mit_t >= 100 else ["Betriebskopie (%d Reihen an t)" % mit_t]))))
            c.commit()
            erg["status"] = "wartet"
            return erg
        for s, pr in prod_cols.items():
            K[s] = pr.close.reindex(idx)
            U[s] = pr.umsatz.reindex(idx)
        # ---- Stammsatz je Coin mit Kurs an t, t-1M oder t-2M (die Klassen der Vormonate brauchen den ersten Kurs)
        schnitt = ab - timedelta(days=1)
        live = set()
        for m in (pd.Timestamp(t), pd.Timestamp(t) - pd.DateOffset(months=1), pd.Timestamp(t) - pd.DateOffset(months=2)):
            if m in K.index:
                live |= set(K.columns[K.loc[m].notna().values])
        stamm_db = {r[0]: dict(zip(("symbol", "hoch", "tag_hoch", "erst", "n", "stand", "median_absret"), r))
                    for r in c.execute("SELECT symbol, hoch, tag_hoch, erst, n, stand, median_absret FROM abbau_stamm")}
        stamm, erst, median = {}, {}, {}
        stamm_fehlt = []
        for s in sorted(live):
            if s in prod_cols:
                pr = prod_cols[s]
                st = stamm_aus([x.date().isoformat() for x in pr.index], list(pr.close), schnitt)
                quelle = "produktion"
            else:
                k_erst, k_letzt = spanne.get(s, ("", ""))
                # GEKUERZT erkennt man an der Spanne: die Betriebskopie behaelt je Reihe die letzten 500 T. Eine Spanne ab 495 T kann
                # gekuerzt sein -> Stammsatz noetig (gespeichert oder von Binance); darunter traegt die Kopie die ganze Reihe
                getrimmt = bool(k_erst) and (date.fromisoformat(k_letzt) - date.fromisoformat(k_erst)).days >= 495
                if not getrimmt:
                    # die Kopie traegt die GANZE Reihe (juenger als 500 T) - aber auch die Kerzen VOR dem Rechenfenster gehoeren in den
                    # Stammsatz, also die ganze Reihe aus der Kopie lesen, nicht nur das Fenster
                    kc = sqlite3.connect("file:%s?mode=ro" % kp.replace("\\", "/"), uri=True, timeout=10)
                    try:
                        reihe = [(a[:10], b) for a, b in kc.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND "
                                                                     "assetklasse='krypto' AND currency='USD' AND date <= ? ORDER BY date", (s, t.isoformat()))]
                    finally:
                        kc.close()
                    st = stamm_aus([a for a, _ in reihe] or [t.isoformat()], [b for _, b in reihe] or [np.nan], schnitt)
                    st["erst"] = k_erst or st["erst"]
                    quelle = "kopie"
                else:
                    alt = stamm_db.get(s)
                    if alt and alt["stand"] and alt["stand"] >= (date.fromisoformat(k_erst) - timedelta(days=1)).isoformat():
                        if alt["stand"] < schnitt.isoformat():
                            # die Kerzen zwischen altem Stand und Schnitt liegen in der Betriebskopie (Stand ist juenger als 500 T)
                            kc = sqlite3.connect("file:%s?mode=ro" % kp.replace("\\", "/"), uri=True, timeout=10)
                            try:
                                zw = kc.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' AND currency='USD' "
                                                "AND date > ? AND date <= ?", (s, alt["stand"], schnitt.isoformat())).fetchall()
                            finally:
                                kc.close()
                            st = fortschreiben(alt, [z[0][:10] for z in zw], [z[1] for z in zw], schnitt)
                        else:
                            st = alt
                        quelle = "fortgeschrieben"
                    else:
                        try:
                            ganz = hole_binance_reihe(s, http)
                        except Exception as exc:                 # noqa: BLE001
                            grund_s = "Stammsatz nicht abrufbar (%s)" % type(exc).__name__
                            c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, s, "abbau stamm", grund_s))
                            stamm_fehlt.append(s)
                            continue
                        st = stamm_aus([a for a, _ in ganz], [b for _, b in ganz], schnitt)
                        erg["geholt"] += 1
                        quelle = "binance"
                c.execute("INSERT OR REPLACE INTO abbau_stamm VALUES (?,?,?,?,?,?,?,?,?)",
                          (s, st["hoch"], st["tag_hoch"], st["erst"], st["n"], st["stand"], st["median_absret"], quelle, jt))
            median[s] = st.get("median_absret")
            erst[s] = st.get("erst")
            pos_hoch = (pd.Timestamp(st["tag_hoch"]) - pd.Timestamp(ab)).days if st.get("tag_hoch") else -1
            stamm[s] = (st["hoch"] if st["hoch"] is not None else np.nan, pos_hoch, pd.Timestamp(st["erst"]) if st["erst"] else None,
                        int(st["n"] or 0), -1)
        # Fehlt ein Stammsatz (Binance nicht erreichbar), fehlt der Coin im Universum und verschiebt die Zellen der anderen - bis zum
        # 5. wird deshalb gewartet (die schon geholten Stammsaetze bleiben gespeichert, morgen fehlt nur der Rest)
        if stamm_fehlt and heute.day < LETZTER_TAG:
            c.execute("INSERT OR REPLACE INTO abbau_lauf (stichtag, am, status, fehlend) VALUES (?,?,?,?)",
                      (t.isoformat(), jt, "wartet", json.dumps(["Stammsatz " + x for x in stamm_fehlt])))
            c.commit()
            erg.update(status="wartet", fehlend=["Stammsatz " + x for x in stamm_fehlt])
            return erg
        # Stablecoins: Median |Tagesrendite| der GANZEN Reihe (aus dem Stammsatz; fuer junge Reihen aus der Kopie)
        ausschluss = set(SONDER) | {s for s, v in median.items() if v is not None and v < STABIL} | set(K.columns) - live - set(prod_cols)
        cgh = _umlauf(ordner)

        def umlauf(s, m):
            r = cgh.get(s)
            if r is None:
                return np.nan
            h = _asof(r, m)
            if h is None:
                h = _asof(r, pd.Timestamp(t))       # ⚠️ Ersatzregel §48.6: Vormonat ohne Umlauf -> Umlauf am Stichtag
            return h if h is not None else np.nan
        W = Wert(K, U, ausschluss | (set(K.columns) - set(stamm)), umlauf, stamm=stamm, erst=erst)
        z = W.fuenftel(pd.Timestamp(t)).set_index("sym")
        if mit_tabelle:                                      # Pruefstand: das ganze Universum, nicht nur der Bestand
            erg["_tabelle"] = z.reset_index()
        # P22 (15.10.2026): Verwaesserung 90 T als FAKT fuer dasselbe Universum und dieselben Klassen - eigene Tabellen, die Regel B4
        # oben bleibt unberuehrt; scheitert nie (ohne Verwaesserung laeuft B4 wie vorher)
        try:
            from agent import verwaesserung as VW
            from agent import umlauf_zusatz as UZ           # P22b: Zusatz-Coins NUR fuer die Verwaesserung, nie fuer die Klassen
            erg["verw"] = VW.speichere(c, t.isoformat(), z.reset_index(), {**UZ.reihen(ordner), **cgh})
        except Exception as exc:                             # noqa: BLE001
            erg["verw"] = None
            c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, "-", "verwaesserung fehler", ("%s: %s" % (type(exc).__name__, exc))[:300]))
        # P19 A3 (17.10.2026, Spot §49.3): das GANZE Universum je Stichtag - daraus die Einstiegs-Kandidaten (oberes Fuenftel); eigene
        # Tabelle, die Regel B4 oben bleibt unberuehrt; scheitert nie (ohne Ablage laeuft B4 wie vorher)
        try:
            erg["kandidaten_abgelegt"] = _universum_ablegen(c, conn_prod, t.isoformat(), z, set(reihe_von.values()))
        except Exception as exc:                             # noqa: BLE001
            erg["kandidaten_abgelegt"] = None
            c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, "-", "universum fehler", ("%s: %s" % (type(exc).__name__, exc))[:300]))
        erg["universum"] = int(z.q.notna().sum())
        zellen = {k: int((z.kl == k).sum()) for k in ("H", "M", "S")}
        # ---- je gehaltenem Coin
        vorher = {r[0]: r[1] for r in c.execute("SELECT symbol, fuenftel FROM abbau_fuenftel WHERE stichtag = (SELECT MAX(stichtag) "
                                                  "FROM abbau_lauf WHERE status='fertig' AND stichtag < ?)", (t.isoformat(),))}
        erstlauf = c.execute("SELECT COUNT(*) FROM abbau_lauf WHERE status='fertig' AND stichtag < ?", (t.isoformat(),)).fetchone()[0] == 0
        for s in sorted(bestand):
            b = reihe_von.get(s)
            if b is not None and b in z.index and z.q[b] == z.q[b]:
                q = int(z.q[b])
                c.execute("INSERT OR REPLACE INTO abbau_fuenftel VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                    t.isoformat(), s, b, z.kl[b], _f(z.F1[b]), _f(z.F2[b]), _f(z.F8[b]), float(z.p[b]), q, None, bestand[s]))
                if q == 1:
                    erg["unten"].append(s)
                    if erstlauf or vorher.get(s) != 1:
                        erg["neu"].append(s)
            else:
                g = grund.get(s) or ("ohne Kurs am Stichtag" if b in erg["fehlend"] else
                                     "nicht im Universum (keine Klasse oder < 10 Coins mit Wert)" if b is not None else "keine Reihe")
                c.execute("INSERT OR REPLACE INTO abbau_fuenftel VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                    t.isoformat(), s, b, None, None, None, None, None, None, g, bestand[s]))
        erg["art"] = "erstliste" if erstlauf else "neu"
        c.execute("INSERT OR REPLACE INTO abbau_lauf (stichtag, am, status, art, universum, zellen, unten, neu, fehlend) VALUES (?,?,?,?,?,?,?,?,?)",
                  (t.isoformat(), jt, "fertig", erg["art"], erg["universum"], json.dumps(zellen), json.dumps(erg["unten"]),
                   json.dumps(erg["neu"]), json.dumps(erg["fehlend"])))
        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, "-", "abbau %s" % erg["art"], "Stichtag %s · Universum %d (H %d, M %d, S %d) · "
                  "unten %s · neu %s%s" % (t, erg["universum"], zellen["H"], zellen["M"], zellen["S"], ",".join(erg["unten"]) or "-",
                                          ",".join(erg["neu"]) or "-", (" · ohne Kurs: " + ",".join(erg["fehlend"])) if erg["fehlend"] else "")))
        c.commit()
        erg["status"] = "fertig"
        erg["zellen"] = zellen
    except Exception as exc:                                     # noqa: BLE001
        logger.exception("Spot-Abbau: Rechnung fuer %s fehlgeschlagen", t)
        erg["status"], erg["fehler"] = "fehler", "%s: %s" % (type(exc).__name__, exc)
        try:
            c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, "-", "abbau fehler", erg["fehler"][:300]))
            c.commit()
        except sqlite3.Error:
            pass
    finally:
        c.close()
    return erg


def _f(x):
    return None if x is None or x != x else float(x)


def _asof(r: pd.Series, m) -> float | None:
    x = r[:m]
    if len(x) and (m - x.index[-1]).days <= 7 and x.iloc[-1] > 0:
        return float(x.iloc[-1])
    return None


def _umlauf(ordner: str) -> dict:
    p = os.path.join(ordner, UMLAUF)
    if not os.path.exists(p):
        return {}
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        d = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", c)
    finally:
        c.close()
    d["datum"] = pd.to_datetime(d.datum.str[:10])
    return {s: g.set_index("datum")["wert"].sort_index() for s, g in d.groupby("symbol")}


def faellig(ordner: str, t: str) -> dict | None:
    """Mail-Lage des Stichtags: {'art', 'liste'} wenn fertig, nicht gemailt und etwas zu melden ist - sonst None."""
    c = oeffne(ordner)
    try:
        r = c.execute("SELECT status, art, neu, mail_am FROM abbau_lauf WHERE stichtag=?", (t,)).fetchone()
        if not r or r[0] != "fertig" or r[3]:
            return None
        neu = json.loads(r[2] or "[]")
        if not neu:
            return None
        zeilen = {x[0]: x for x in c.execute("SELECT symbol, reihe, klasse, f1, f2, f8, perzentil, fuenftel, grund, menge FROM abbau_fuenftel "
                                             "WHERE stichtag=?", (t,))}
        return {"stichtag": t, "art": r[1], "liste": [zeilen[s] for s in neu if s in zeilen]}
    finally:
        c.close()


def vermerke_mail(ordner: str, t: str) -> None:
    c = oeffne(ordner)
    try:
        jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        c.execute("UPDATE abbau_lauf SET mail_am=? WHERE stichtag=?", (jt, t))
        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, "-", "abbau gemailt", "Stichtag %s" % t))
        c.commit()
    finally:
        c.close()


# ══ die Mail (E-91: Coin · was tun · wann · warum) ════════════════════════════════════════════════════════════════════════════
def mail(fall: dict, werte_eur: dict, ausserhalb_binance: set, verw: dict | None = None, makro_text: str | None = None,
         ampel_text: str | None = None) -> tuple:
    """``werte_eur``: {Symbol: Wert in EUR (frei + gestakt)}; Reihenfolge nach Wert - die Guete INNERHALB des Fuenftels ist nicht gemessen.
    ``verw`` (P22): {Symbol: (log-Wachstum 90 T, Fuenftel)} am Stichtag - Faktenzeile je Coin, kein Teil der Regel."""
    liste = sorted(fall["liste"], key=lambda r: -(werte_eur.get(r[0]) or 0))
    namen = ", ".join(r[0] for r in liste)
    b = "Spot: Abbau-Reihenfolge – zuerst %s" % namen
    z = ["1  WAS ZU TUN IST",
         ("  Wenn du Spot-Bestände abbaust, verkaufe zuerst: %s." % namen),
         "  Kein Termin: Es ist eine Reihenfolge für den nächsten Abbau, kein Verkaufssignal für heute.",
         ("  Das ist die Erstliste: alle gehaltenen Coins, die am %s im unteren Fünftel stehen." % _de(fall["stichtag"])
          if fall["art"] == "erstliste" else
          "  Neu im unteren Fünftel seit dem letzten Monatsstichtag (%s)." % _de(fall["stichtag"])),
         "", "2  WARUM",
         "  Am Monatsersten wird jeder Coin in seiner Klasse (H/M/S nach Marktwert) nach drei Merkmalen eingeordnet: wie tief er unter "
         "seinem Allzeithoch steht, wie lange das Hoch zurückliegt und wie lange es Daten gibt. Diese Coins stehen im unteren Fünftel.",
         "  " + BELEG + ".",
         "  Nicht gemessen ist, welcher Coin INNERHALB des Fünftels schlechter ist – die Liste ist nach deinem Wert in Euro geordnet, "
         "nicht nach Güte.",
         "", "3  JE COIN (Fakten am Stichtag)"]
    for r in liste:
        s, reihe, kl, f1, f2, f8, p, q, _g, menge = r
        z.append("  %s%s: Klasse %s · %s unter dem Allzeithoch · Hoch vor %s Tagen · Daten seit %s Tagen · Perzentil %s · Wert %s EUR · "
                 "Kosten je Seite %s %%%s" % (
                     s, (" (Binance %s)" % reihe) if reihe and reihe != s else "", kl, ("%.0f %%" % (-100 * f1)) if f1 is not None else "?",
                     "%d" % f2 if f2 is not None else "?", "%d" % f8 if f8 is not None else "?", ("%.2f" % p).replace(".", ","),
                     _eur(werte_eur.get(s)), ("%.2f" % SM.KOSTEN_JE_SEITE.get(kl, 0)).replace(".", ","),
                     " · außerhalb Binance: eingeordnet, nicht gemessen" if s in ausserhalb_binance else ""))
        if verw is not None:
            from agent import verwaesserung as VW
            z.append("     " + VW.text_stichtag(*tuple(verw.get(s) or (None, None))[:3]))
    z += ["", "4  KONTEXT (keine Handlung)",
          "  Mitnahme ×3 (B1) und Upbit-Listing (B3) gelten weiter; kommt dort eine Mail, hat sie Vorrang (sie hat einen Termin).",
          *(["  " + __import__("agent.verwaesserung", fromlist=["MESSLAGE"]).MESSLAGE + "."] if verw is not None else []),
          *(["  Makro " + makro_text + "."] if makro_text else []),               # O54 (15.10.2026): Fakt, Gewichtung beim Nutzer
          *(["  Season-Ampel " + ampel_text + "."] if ampel_text else []),        # P19 (17.10.2026): Fakt, loest nichts aus
          "  Der Erlös: Wohin er geht, ist nicht gemessen – in der Messung lag er still (Dollar).",
          "", "5  TECHNIK", "  Spot B4 · Stichtag %s · Wert ohne TVL (F1, F2, F8) · Fünftel je Klasse · Spot §43/§48." % fall["stichtag"]]
    return b, "\n".join(z)


def _eur(x) -> str:
    return "?" if x is None else ("%.0f" % x)


def _de(s: str) -> str:
    return date.fromisoformat(s[:10]).strftime("%d.%m.%Y")


# ══ Lesen fuer Statusseite, Teilexport, Bestand-Tab ═══════════════════════════════════════════════════════════════════════════
def stand(ordner: str) -> dict:
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return {"ablage": False}
    c = SM._ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='abbau_lauf'").fetchone():
            return {"ablage": True, "laeufe": 0}
        l = c.execute("SELECT stichtag, am, status, art, universum, zellen, unten, neu, fehlend, mail_am, fehler FROM abbau_lauf "
                      "ORDER BY stichtag DESC LIMIT 1").fetchone()
        n = c.execute("SELECT COUNT(*) FROM abbau_lauf").fetchone()[0]
        st = c.execute("SELECT COUNT(*), SUM(quelle='binance') FROM abbau_stamm").fetchone()
        letzte = [tuple(r) for r in c.execute("SELECT am, symbol, art, text FROM protokoll WHERE art LIKE 'abbau%' ORDER BY rowid DESC LIMIT 4")]
        verw = []
        if l and c.execute("SELECT 1 FROM sqlite_master WHERE name='verw_universum'").fetchone():
            from agent import verwaesserung as VW               # P22: Bestandscoins im staerksten Verwaesserungs-Fuenftel
            reihen = {r[0]: r[1] for r in c.execute("SELECT symbol, reihe FROM abbau_fuenftel WHERE stichtag=? AND reihe IS NOT NULL", (l[0],))}
            verw = VW.stand_bestand(ordner, reihen)
        rhy = []
        if l:
            try:                                                 # P22c: naechste Freigaben (Rhythmus der Vergangenheit) im Bestand
                from agent import verwaesserung as VW
                reihen_b = {r[0]: r[1] for r in c.execute("SELECT symbol, reihe FROM abbau_fuenftel WHERE stichtag=? AND reihe IS NOT NULL", (l[0],))}
                rhy = VW.rhythmus_bestand(ordner, reihen_b)
            except Exception:                                    # noqa: BLE001
                rhy = []
        return {"ablage": True, "laeufe": n, "letzter": tuple(l) if l else None, "stamm": st[0] or 0, "stamm_binance": st[1] or 0, "letzte": letzte,
                "verw_staerkstes": verw, "verw_rhythmus": rhy}
    finally:
        c.close()


def verw_am_stichtag(ordner: str, t: str, liste: list) -> dict:
    """P22: {Bestandsymbol: (log-Wachstum 90 T, Fuenftel)} fuer die Zeilen ``liste`` (abbau_fuenftel: symbol, reihe, ...) am Stichtag."""
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return {}
    c = SM._ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='verw_universum'").fetchone():
            return {}
        w = {r[0]: (r[1], r[2]) for r in c.execute("SELECT symbol, verw90, fuenftel FROM verw_universum WHERE stichtag=?", (t,))}
    finally:
        c.close()
    aus = {r[0]: w.get(r[1] or r[0], (None, None)) for r in liste}
    try:                                                     # P22c: Freigabe-Rhythmus (Vergangenheit) je Coin dazu
        from agent import verwaesserung as VW
        reihen = VW.alle_reihen(ordner)[0]                   # P22b: mit Zusatz-Coins
        heute = datetime.now(timezone.utc).date()
        aus = {r[0]: tuple(aus[r[0]]) + (VW.rhythmus_text(VW.rhythmus(reihen.get(r[1] or r[0]), heute)),) for r in liste}
    except Exception:                                        # noqa: BLE001
        pass
    return aus


def letzte_fuenftel(ordner: str) -> dict:
    """{Symbol: (Stichtag, Fuenftel oder None, Klasse, Grund)} des juengsten fertigen Stichtags - fuer die Spalte B4 im Bestand-Tab."""
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return {}
    c = SM._ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='abbau_lauf'").fetchone():
            return {}
        t = c.execute("SELECT MAX(stichtag) FROM abbau_lauf WHERE status='fertig'").fetchone()[0]
        if not t:
            return {}
        return {r[0]: (t, r[1], r[2], r[3]) for r in c.execute("SELECT symbol, fuenftel, klasse, grund FROM abbau_fuenftel WHERE stichtag=?", (t,))}
    finally:
        c.close()
