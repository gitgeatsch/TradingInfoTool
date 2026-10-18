"""Spot C1 - Season-Ampel als FAKT (P19, 17.10.2026; Voranalyse_Spot_Neubau_04_10.md §36, §49.1-§49.5).

Nutzer 14.10.: *"Ja passt vorerst"* (Bauumfang §49.3) · 16.10.: *"ok weiter mit P19 - hast du alles geprueft und gegengeprueft?"*

DIE REGEL (wie kalibriert, §36.3-§36.5; der Nachbau ``p19_voranalyse`` gibt an 2.639 von 2.639 Tagen denselben Stand, Teil 0 - die
Funktionen ``stand``/``muster``/``stufe``/``stufen``/``breite``/``taeglich`` hier sind DERSELBE Code):

    B1  BTC 91 T > +20 %            Betriebskopie messdaten.db (Binance, dieselbe Quelle wie die Messung; G3)
    B2  M2 J/J > +5 %               FRED M2SL, Datum + 35 T Verzug (ueber ``makro_lage.hole_reihe``, derselbe Abruf wie O54)
    B3  Stablecoins 91 T > +10 %    DefiLlama stablecoincharts/all peggedUSD, Datum + 1 T; bei JEDEM Lauf die GANZE Reihe (§49.5: Revision)
    Stand    Zahl der erfuellten Bedingungen (0-3)
    Stufe    aus dem Muster: 3/3 -> Season-Klima, mit Breite >= 0,6 Ueberhitzung; 3/3 in den letzten 90 T und jetzt nicht -> Ende;
             nur B2+B3 -> Vorlauf; nur B1+B2 -> ungewohnt; sonst kalt
    Haltezeit eine neue Stufe GILT erst am 7. Tag in Folge (Lauflaengen-Form wie p19_gegenprobe G2: 18 Wechsel auf der Kalibrierung)
    Breite   Anteil der Top 50 (Umsatz 30 T bis zum Monatsersten, ohne BTC und Stablecoins) mit 90-T-Ertrag > BTC, >= 20 Coins
    Kontext  Netto-Liquiditaet 13 W (WALCL - WTREGEN - RRP), Fear & Greed - nur Anzeige

⚠️ GEPRUEFT AN ZWEI ZYKLEN (E-124, 18.10.2026, Spot §59): kalibriert 2020/21, Holdout 2017/18 traegt (Season-Klima 76 % Season-Wochen,
kalt 0 %, Ruhe im Absturz 2018); sie trennt Season-Phase und Baerenmarkt, den BEGINN erkennt sie nicht genau vorab (2016/17: 19 T danach).
Anzeige: Statusseite, Reiter Markt (Krypto), Zeile in B1/B3/B4. MAIL bei einem Wechsel der geltenden Stufe in eine Stufe mit Handlung,
Schalter ``season_ampel_aktiv`` (seit E-124 an; ein Wechsel aus der Zeit mit Schalter aus wird nicht nachgeholt).

⚠️ REVISIONEN (§49.5): DefiLlama aendert die Vergangenheit. Die Tageswerte werden je Lauf ganz neu gerechnet; ein Wechsel zaehlt nur
gegen die zuletzt GEMELDETE Stufe (``ampel_meldung``), nie gegen eine neu gerechnete Vergangenheit. Die groesste Aenderung von B3
gegen den vorigen Lauf steht im Lauf (``revision_b3``).

Schreibt NUR ``data/spot_betrieb.db`` (ampel_tag, ampel_lauf, ampel_meldung); liest Betriebskopie, ``abbau_stamm`` und die Produktion
(Fear & Greed, Bestand) nur. Scheitert nie nach aussen: ohne neuen Stand bleibt der alte, mit Vermerk.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ABLAGE = "spot_betrieb.db"
KOPIE = "messdaten.db"
SCHWELLE = {"B1": 0.20, "B2": 0.05, "B3": 0.10}
BREITE_HEISS = 0.6
ENDE_T = 90
HALTE_T = 7
STABIL = 0.002                       # Median |Tagesrendite| darunter = Stablecoin (wie spot_abbau / s1_messung)
VERALTET_TAGE = 3
FRED = ("M2SL", "WALCL", "WTREGEN", "RRPONTSYD")
DEFILLAMA = "https://stablecoins.llama.fi/stablecoincharts/all"
HANDLUNG = {
    "Vorlauf": "L-Kandidaten bereit, erste kleine Tranche möglich",
    "Season-Klima": "L aufbauen in Tranchen",
    "Ueberhitzung": "kein Neuaufbau",
    "Ende": "kein Neuaufbau",
}
NAME = {"kalt": "kalt", "ungewohnt": "ungewohnt", "Vorlauf": "Vorlauf", "Season-Klima": "Season-Klima", "Ueberhitzung": "Überhitzung",
        "Ende": "Ende"}
BEDEUTUNG = {
    "kalt": "keine Season-Lage",
    "ungewohnt": "BTC läuft, das Geld fehlt – seit 2019 nie da gewesen, fachlich kein Season-Vorlauf",
    "Vorlauf": "das Geld ist da, BTC noch nicht",
    "Season-Klima": "alle drei Bedingungen erfüllt",
    "Ueberhitzung": "alle drei erfüllt und die Breite ist hoch",
    "Ende": "alle drei waren in den letzten 90 Tagen erfüllt, jetzt nicht mehr",
}
VORBEHALT = "geprüft an zwei Zyklen (2017/18, 2020/21) – trennt Season-Phase und Bärenmarkt, erkennt den Beginn nicht genau vorab"


# ══ die Regel (DERSELBE Code wie p19_voranalyse; R-R11 im Pruefstand) ════════════════════════════════════════════════════════
def stand(b1, b2, b3):
    return int(b1 > SCHWELLE["B1"]) + int(b2 > SCHWELLE["B2"]) + int(b3 > SCHWELLE["B3"])


def muster(b1, b2, b3):
    return (b1 > SCHWELLE["B1"], b2 > SCHWELLE["B2"], b3 > SCHWELLE["B3"])


def stufe(b1, b2, b3, breite, dreivon3_in_ende_t: bool) -> str:
    """§36.5 - aus dem Muster der drei Bedingungen; 'Ende' = 3/3 war in den letzten ENDE_T Tagen an und ist es nicht mehr."""
    m = muster(b1, b2, b3)
    if all(m):
        return "Ueberhitzung" if (breite == breite and breite >= BREITE_HEISS) else "Season-Klima"
    if dreivon3_in_ende_t:
        return "Ende"
    if m == (False, True, True):
        return "Vorlauf"
    if m == (True, True, False):
        return "ungewohnt"
    return "kalt"


def stufen(T):
    an3 = ((T.B1 > SCHWELLE["B1"]) & (T.B2 > SCHWELLE["B2"]) & (T.B3 > SCHWELLE["B3"])).astype(int)
    vorher = an3.shift(1).rolling(ENDE_T, min_periods=1).max().fillna(0) > 0
    return pd.Series([stufe(a, b, c, br, v) for a, b, c, br, v in zip(T.B1, T.B2, T.B3, T.Breite, vorher)], index=T.index)


def geltend(s: pd.Series, halte: int = HALTE_T) -> pd.Series:
    """Haltezeit: eine neue Stufe gilt am ``halte``-ten Tag in Folge (Lauflaengen-Form wie p19_gegenprobe G2)."""
    if not len(s):
        return s
    lauf = (s != s.shift(1)).cumsum()
    pos = s.groupby(lauf).cumcount() + 1
    akt, aus = s.iloc[0], []
    for st, ps in zip(s, pos):
        if st != akt and ps >= halte:
            akt = st
        aus.append(akt)
    return pd.Series(aus, index=s.index)


def breite(K, U, alts, B, tage):
    """Anteil der Top 50 (Umsatz-Mittel der 30 T bis zum Monatsersten) mit 90-T-Ertrag > BTC, nur Coins mit beiden Kursen, >= 20."""
    aus = pd.Series(np.nan, index=tage)
    tops = {}
    for t in tage:
        m = t.replace(day=1)
        if m not in tops:
            vol = U.loc[m - pd.Timedelta(days=30):m, [a for a in alts if a in U.columns]].mean().dropna()
            tops[m] = vol.sort_values(ascending=False).index[:50]
        top = tops[m]
        a90 = (K.loc[t, top] / K.loc[t - pd.Timedelta(days=90), top]).dropna()
        if len(a90) >= 20:
            aus[t] = float((a90 > B[t] / B[t - pd.Timedelta(days=90)]).mean())
    return aus


def taeglich(r, idx):
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


# ══ Daten ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _ro(pfad: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=10)


def kopie(ordner: str, bis: date):
    """(K, U) Tagesschluss und Dollar-Umsatz aus der Betriebskopie (alle Krypto-USD-Reihen, TRADING + BREAK), bis einschliesslich ``bis``."""
    c = _ro(os.path.join(ordner, KOPIE))
    try:
        d = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' "
                        "AND date <= ?", c, params=(bis.isoformat() + " 23:59",))
    finally:
        c.close()
    d["date"] = pd.to_datetime(d.date.str[:10])
    K = d.pivot_table(index="date", columns="symbol", values="close", aggfunc="last").sort_index().asfreq("D")
    U = d.assign(u=d.close * d.volume).pivot_table(index="date", columns="symbol", values="u", aggfunc="last").sort_index().asfreq("D")
    return K, U


def stabile(ordner: str, K: pd.DataFrame) -> set:
    """Stablecoins: Median |Tagesrendite| < 0,2 % - aus dem B4-Stammsatz (ganze Reihe), sonst ueber das Fenster der Kopie."""
    med = {}
    p = os.path.join(ordner, ABLAGE)
    if os.path.exists(p):
        c = _ro(p)
        try:
            if c.execute("SELECT 1 FROM sqlite_master WHERE name='abbau_stamm'").fetchone():
                med = {r[0]: r[1] for r in c.execute("SELECT symbol, median_absret FROM abbau_stamm WHERE median_absret IS NOT NULL")}
        finally:
            c.close()
    ret = K.pct_change(fill_method=None).abs().median()
    return {s for s in K.columns if (med.get(s) if s in med else ret.get(s, np.nan)) < STABIL}


def fred_reihen(fred_key: str, heute: date, http=None) -> dict:
    from agent import makro_lage as ML
    start = (heute - timedelta(days=4 * 365)).isoformat()
    return {sid: ML.hole_reihe(sid, fred_key, start, http) for sid in FRED}


def stablecoins(http=None) -> pd.Series:
    import requests
    j = (http or requests).get(DEFILLAMA, timeout=90).json()
    return pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0)
                      for x in j}).sort_index()


def fear_greed(conn_prod) -> pd.Series:
    if conn_prod is None:
        return pd.Series(dtype=float)
    fg = pd.read_sql("SELECT date, fear_greed_value FROM macro_snapshot WHERE fear_greed_value IS NOT NULL", conn_prod)
    if not len(fg):
        return pd.Series(dtype=float)
    fg["date"] = pd.to_datetime(fg.date.str[:10])
    return fg.groupby("date").fear_greed_value.mean()


def rechne(K, U, stabil: set, fred: dict, stb: pd.Series, fg: pd.Series, bis: date) -> pd.DataFrame:
    """Die Tageswerte ab dem ersten Tag, an dem B1 und die Breite rechenbar sind, bis ``bis``."""
    idx = pd.date_range("2019-01-01", pd.Timestamp(bis), freq="D")
    B = K["BTC"].reindex(idx)
    m2 = fred["M2SL"]
    B2 = taeglich(m2 / m2.shift(12) - 1, idx)
    st_t = taeglich(stb, idx)
    B3 = st_t / st_t.shift(91) - 1
    B1 = B / B.shift(91) - 1
    wl = pd.concat([fred["WALCL"], fred["WTREGEN"], fred["RRPONTSYD"].resample("W-WED").last()], axis=1, sort=True).ffill().dropna()
    wl.columns = ["WALCL", "WTREGEN", "RRPONTSYD"]
    netto = taeglich((wl["WALCL"] - wl["WTREGEN"] - wl["RRPONTSYD"] * 1000) / 1e6, idx)
    alts = [s for s in K.columns if s not in stabil and s != "BTC"]
    erst = K.index[0] + pd.Timedelta(days=120)                           # 90 T Ertrag + 30 T Umsatz vor dem Monatsersten
    tage = [t for t in idx if t >= erst and B1.get(t) == B1.get(t)]
    Kd = K.reindex(pd.date_range(K.index[0], pd.Timestamp(bis), freq="D"))
    Ud = U.reindex(Kd.index)
    br = breite(Kd, Ud, alts, Kd["BTC"], tage) if tage else pd.Series(dtype=float)
    T = pd.DataFrame({"B1": B1.reindex(tage), "B2": B2.reindex(tage), "B3": B3.reindex(tage), "Breite": br.reindex(tage),
                      "netto13": (netto / netto.shift(91) - 1).reindex(tage), "fg": fg.reindex(tage)}, index=pd.DatetimeIndex(tage))
    T = T.dropna(subset=["B1", "B2", "B3"])
    T["stand"] = [stand(a, b, c) for a, b, c in zip(T.B1, T.B2, T.B3)]
    T["stufe_roh"] = stufen(T)
    T["stufe"] = geltend(T.stufe_roh)
    return T


# ══ Ablage ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def oeffne(ordner: str) -> sqlite3.Connection:
    c = sqlite3.connect(os.path.join(ordner, ABLAGE), timeout=10)
    c.execute("CREATE TABLE IF NOT EXISTS ampel_tag (datum TEXT PRIMARY KEY, b1 REAL, b2 REAL, b3 REAL, breite REAL, netto13 REAL, fg REAL, "
              "stand INTEGER, stufe_roh TEXT, stufe TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ampel_lauf (am TEXT PRIMARY KEY, status TEXT, fehler TEXT, letzter_tag TEXT, stufe TEXT, seit TEXT, "
              "tage INTEGER, revision_b3 REAL, quellen TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ampel_meldung (am TEXT, stufe TEXT, seit TEXT, art TEXT, mail_am TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS protokoll (am TEXT, symbol TEXT, art TEXT, text TEXT)")
    c.commit()
    return c


def _seit(T: pd.DataFrame) -> str | None:
    if not len(T):
        return None
    s = T.stufe
    w = s[s != s.shift(1)]
    return w.index[-1].date().isoformat()


def lauf(ordner: str, conn_prod=None, fred_key: str | None = None, heute: date | None = None, http=None, quellen: dict | None = None) -> dict:
    """Holt, rechnet, legt ab und entscheidet die Mail-Lage. ``quellen`` (Pruefstand): {'fred': {...}, 'stb': Series} statt Abruf.
    -> {'status': ok|fehler, 'stufe', 'seit', 'letzter_tag', 'faellig': None | {'stufe', 'seit', 'handlung'}, 'wechsel', 'fehler', ...}"""
    heute = heute or datetime.now(timezone.utc).date()
    bis = heute - timedelta(days=1)                                     # die laufende Tageskerze ist nicht abgeschlossen
    jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    erg = {"status": None, "stufe": None, "seit": None, "letzter_tag": None, "faellig": None, "wechsel": None, "fehler": None,
           "revision_b3": None, "tage": 0}
    c = oeffne(ordner)
    try:
        try:
            if quellen is None:
                fred_key = os.environ.get("FRED_API_KEY", "") if fred_key is None else fred_key
                if not fred_key:
                    raise RuntimeError("kein FRED-Schluessel")
                fr, sb = fred_reihen(fred_key, heute, http), stablecoins(http)
            else:
                fr, sb = quellen["fred"], quellen["stb"]
            K, U = kopie(ordner, bis)
            if "BTC" not in K.columns:
                raise RuntimeError("BTC fehlt in der Betriebskopie")
            T = rechne(K, U, stabile(ordner, K), fr, sb, fear_greed(conn_prod), bis)
            if not len(T):
                raise RuntimeError("keine rechenbaren Tage")
        except Exception as exc:                                         # noqa: BLE001
            txt = "%s: %s" % (type(exc).__name__, str(exc).replace(fred_key or "\0", "***")[:200])
            c.execute("INSERT OR REPLACE INTO ampel_lauf (am, status, fehler) VALUES (?,?,?)", (jt, "fehler", txt))
            c.commit()
            logger.warning("Season-Ampel nicht neu berechnet - alter Stand bleibt: %s", txt)
            erg.update(status="fehler", fehler=txt)
            return erg
        alt = {r[0]: r[1] for r in c.execute("SELECT datum, b3 FROM ampel_tag")}
        rev = [abs(float(v) - alt[d.date().isoformat()]) for d, v in T.B3.items() if alt.get(d.date().isoformat()) is not None]
        c.execute("DELETE FROM ampel_tag")
        c.executemany("INSERT INTO ampel_tag VALUES (?,?,?,?,?,?,?,?,?,?)", [
            (d.date().isoformat(), float(r.B1), float(r.B2), float(r.B3), None if r.Breite != r.Breite else float(r.Breite),
             None if r.netto13 != r.netto13 else float(r.netto13), None if r.fg != r.fg else float(r.fg), int(r.stand), r.stufe_roh, r.stufe)
            for d, r in T.iterrows()])
        st, seit = T.stufe.iloc[-1], _seit(T)
        erg.update(status="ok", stufe=st, seit=seit, letzter_tag=T.index[-1].date().isoformat(), tage=len(T),
                   revision_b3=(max(rev) if rev else None))
        q = {"btc_bis": K["BTC"].last_valid_index().date().isoformat(), "m2_bis": fr["M2SL"].index.max().date().isoformat(),
             "stablecoins_bis": sb.index.max().date().isoformat(), "stablecoins_usd": float(sb.iloc[-1])}
        c.execute("INSERT OR REPLACE INTO ampel_lauf VALUES (?,?,?,?,?,?,?,?,?)",
                  (jt, "ok", None, erg["letzter_tag"], st, seit, len(T), erg["revision_b3"], json.dumps(q)))
        # ---- Mail-Lage: nur gegen die zuletzt GEMELDETE Stufe (Revisionen erzeugen keinen Scheinwechsel)
        letzte = c.execute("SELECT stufe, seit, art FROM ampel_meldung ORDER BY am DESC, rowid DESC LIMIT 1").fetchone()
        if letzte is None:
            c.execute("INSERT INTO ampel_meldung VALUES (?,?,?,?,?)", (jt, st, seit, "startmarke", None))
        elif letzte[0] != st:
            art = "faellig" if st in HANDLUNG else "wechsel"
            c.execute("INSERT INTO ampel_meldung VALUES (?,?,?,?,?)", (jt, st, seit, art, None))
            erg["wechsel"] = {"von": letzte[0], "nach": st, "seit": seit}
            if art == "faellig":
                erg["faellig"] = {"stufe": st, "seit": seit, "handlung": HANDLUNG[st], "von": letzte[0]}
        elif letzte[2] == "faellig":                                     # noch nicht zugestellt (Schalter aus oder Versand gescheitert)
            erg["faellig"] = {"stufe": st, "seit": seit, "handlung": HANDLUNG.get(st), "von": None}
        c.commit()
        return erg
    finally:
        c.close()


def vermerke_mail(ordner: str, stufe_: str) -> None:
    """Nur nach Zustellung: die offene Meldung dieser Stufe gilt als gemailt."""
    c = oeffne(ordner)
    try:
        jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE ampel_meldung SET art='gemailt', mail_am=? WHERE rowid=(SELECT rowid FROM ampel_meldung WHERE stufe=? AND "
                  "art='faellig' ORDER BY am DESC LIMIT 1)", (jt, stufe_))
        c.commit()
    finally:
        c.close()


def vermerke_ohne_mail(ordner: str, stufe_: str) -> None:
    """Schalter aus: der Wechsel ist protokolliert, aber nie gemailt - er wird beim Einschalten NICHT nachgeholt."""
    c = oeffne(ordner)
    try:
        c.execute("UPDATE ampel_meldung SET art='ohne_mail' WHERE rowid=(SELECT rowid FROM ampel_meldung WHERE stufe=? AND art='faellig' "
                  "ORDER BY am DESC LIMIT 1)", (stufe_,))
        c.commit()
    finally:
        c.close()


# ══ Lesen und Texte ═══════════════════════════════════════════════════════════════════════════════════════════════════════
def lade(ordner: str) -> dict | None:
    """Letzter Stand fuer Anzeige und Mails: {'tag': {...}, 'lauf': {...}, 'letzter_ok': {...}, 'verlauf': [(datum, stufe, stand)]}."""
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return None
    c = _ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='ampel_tag'").fetchone():
            return None
        sp = ("datum", "b1", "b2", "b3", "breite", "netto13", "fg", "stand", "stufe_roh", "stufe")
        z = c.execute("SELECT %s FROM ampel_tag ORDER BY datum DESC LIMIT 1" % ", ".join(sp)).fetchone()
        lsp = ("am", "status", "fehler", "letzter_tag", "stufe", "seit", "tage", "revision_b3", "quellen")
        l_ = c.execute("SELECT %s FROM ampel_lauf ORDER BY am DESC LIMIT 1" % ", ".join(lsp)).fetchone()
        ok = c.execute("SELECT %s FROM ampel_lauf WHERE status='ok' ORDER BY am DESC LIMIT 1" % ", ".join(lsp)).fetchone()
        vl = c.execute("SELECT datum, stufe, stand, b1, b2, b3, breite FROM ampel_tag WHERE datum >= ? ORDER BY datum",
                       ((date.fromisoformat(z[0]) - timedelta(days=365)).isoformat() if z else "9999",)).fetchall()
        def vor(n):
            if not z:
                return None
            r = c.execute("SELECT %s FROM ampel_tag WHERE datum <= ? ORDER BY datum DESC LIMIT 1" % ", ".join(sp),
                          ((date.fromisoformat(z[0]) - timedelta(days=n)).isoformat(),)).fetchone()
            return dict(zip(sp, r)) if r else None
        return {"tag": dict(zip(sp, z)) if z else None, "lauf": dict(zip(lsp, l_)) if l_ else None, "letzter_ok": dict(zip(lsp, ok)) if ok else None,
                "vor30": vor(30), "vor90": vor(90), "verlauf": vl}
    finally:
        c.close()


def zustand(d: dict | None, heute: date | None = None) -> str:
    """'ok' | 'veraltet' | 'fehlt'."""
    if not d or not d.get("tag"):
        return "fehlt"
    heute = heute or datetime.now(timezone.utc).date()
    return "veraltet" if (heute - date.fromisoformat(d["tag"]["datum"])).days > VERALTET_TAGE else "ok"


def _pct(x) -> str:
    from agent import schreibweise as S
    return "–" if x is None else S.de(100 * float(x), 1, True) + " %"


def bedingungen(t: dict) -> list:
    """[(Name, Wert-Text, an, Schwelle-Text)] je Bedingung."""
    return [("BTC 91 T", _pct(t["b1"]), t["b1"] > SCHWELLE["B1"], "> +20 %"),
            ("M2 J/J", _pct(t["b2"]), t["b2"] > SCHWELLE["B2"], "> +5 %"),
            ("Stablecoins 91 T", _pct(t["b3"]), t["b3"] > SCHWELLE["B3"], "> +10 %")]


def zeile(ordner: str | None = None, d: dict | None = None, heute: date | None = None) -> str:
    """Eine Zeile fuer die Spot-Mails B1/B3/B4 und die Statusseite (ohne Netto-Liquiditaet: die steht als K2 in der Makro-Zeile)."""
    if d is None:
        from agent import regel0_nachlader as NL
        d = lade(ordner or NL.DATEN_VORGABE)
    z = zustand(d, heute)
    if z == "fehlt":
        return "Season-Ampel NICHT VERFÜGBAR (noch nicht berechnet) – kein Urteil"
    t = d["tag"]
    seit = (d.get("letzter_ok") or {}).get("seit")
    txt = "%s%s (%d von 3: %s) – %s · Stand %s" % (
        NAME.get(t["stufe"], t["stufe"]), (" seit %s" % date.fromisoformat(seit).strftime("%d.%m.%Y")) if seit else "", t["stand"],
        " · ".join("%s %s %s" % (n, w, "✔" if an else "✗") for n, w, an, _ in bedingungen(t)), VORBEHALT,
        date.fromisoformat(t["datum"]).strftime("%d.%m."))
    if z == "veraltet":
        txt += " ⚠ VERALTET"
    if (d.get("lauf") or {}).get("status") == "fehler":
        txt += " · letzter Abruf gescheitert"
    return txt


def mail(fall: dict, d: dict, kandidaten: dict | None = None, makro_text: str | None = None) -> tuple:
    """Mail beim Wechsel der geltenden Stufe in eine Stufe mit Handlung (E-91: jede Mail eine Handlung). -> (Betreff, Text)"""
    st = fall["stufe"]
    t = d["tag"]
    betreff = "Season-Ampel %s – %s" % (NAME.get(st, st), fall["handlung"])
    zeilen = ["%s" % fall["handlung"], "",
              "Die Season-Ampel steht seit %s auf %s (%s)%s." % (date.fromisoformat(fall["seit"]).strftime("%d.%m.%Y"), NAME.get(st, st),
                                                                BEDEUTUNG.get(st, ""), (", vorher %s" % NAME.get(fall["von"], fall["von"])) if fall.get("von") else ""),
              ""]
    if makro_text:
        zeilen += [("" if makro_text.startswith("Makro") else "Makro-Lage ") + makro_text + ".", ""]
    zeilen += ["Bedingungen am %s:" % date.fromisoformat(t["datum"]).strftime("%d.%m.%Y")]
    zeilen += ["  %-17s %8s  %s  (Schwelle %s)" % (n, w, "erfüllt" if an else "nicht erfüllt", s) for n, w, an, s in bedingungen(t)]
    if t.get("breite") is not None:
        zeilen.append("  %-17s %8s  (Überhitzung ab 0,60)" % ("Breite", ("%.2f" % t["breite"]).replace(".", ",")))
    if kandidaten:
        zeilen += ["", "Einstiegs-Kandidaten (oberes Fünftel des Watchlist-Werts, bei Bitpanda handelbar; ordnet den Fortbestand, "
                       "ein Einstieg je Asset ist NICHT belegt):"]
        for kl in ("H", "M", "S"):
            if kandidaten.get(kl):
                zeilen.append("  %s: %s" % (kl, ", ".join(kandidaten[kl])))
    zeilen += ["", "⚠ " + VORBEHALT[0].upper() + VORBEHALT[1:] + ". Die Haltezeit von 7 Tagen ist schon abgewartet.",
               "Ausführung manuell über die Bitpanda-App."]
    return betreff, "\n".join(zeilen)


def uebersicht(ordner: str | None = None, heute: date | None = None) -> dict:
    """Fuer Statusseite, Teilexport und Diagnose."""
    from agent import regel0_nachlader as NL
    ordner = ordner or NL.DATEN_VORGABE
    d = lade(ordner)
    aus = {"zustand": zustand(d, heute), "zeile": zeile(ordner, d, heute)}
    if d and d.get("tag"):
        t = d["tag"]
        aus.update(stufe=t["stufe"], stufe_name=NAME.get(t["stufe"], t["stufe"]), bedeutung=BEDEUTUNG.get(t["stufe"]), stand=t["stand"],
                   datum=t["datum"], seit=(d.get("letzter_ok") or {}).get("seit"), breite=t.get("breite"), netto13=t.get("netto13"),
                   fg=t.get("fg"), bedingungen=[(n, w, bool(an), s) for n, w, an, s in bedingungen(t)],
                   vor30=d.get("vor30"), vor90=d.get("vor90"), lauf=d.get("lauf"), roh_heute=t.get("stufe_roh"))
    return aus
