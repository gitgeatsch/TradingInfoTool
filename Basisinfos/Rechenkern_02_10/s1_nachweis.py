# -*- coding: utf-8 -*-
"""NACHWEIS S1-Ergänzung (01.11.2026, Nutzer: „1a, 2a, 3 ja – prüfen gegenprüfen und doku“).

Nur lesend: ``data/_sichten/sichten.db``, Desktop-Messbasen, die NB-Kopie ``spot_betrieb.db`` aus dem Austauschordner und
öffentliche Schnittstellen (eine Abfrage je Reihe).

    G1  Vollständigkeit: je Reihe keine Lücke > 1 Tag im eigenen Zeitraum
    G2  Kein Vorgriff: bekannt_ab = Folgetag 00:00 UTC, kein Tag >= heute (UTC)
    G3  Kurs BTC/ETH  = Desktop-Messbasis (Binance), gleiche Tage
    G4  Funding       x Zahl der Zahlungen = funding_historie.db (dort Tagessumme)
    G5  OI            Metrikdatei gegen openInterestHist an den gemeinsamen Tagen (≤ 0,5 %, begruendet bei G5)
    G6  Breite/Stufe  in der Grundgesamtheit des BETRIEBS zum Zeitpunkt (G6a, 01.11.): Regression, Desktop = NB-Kopie,
                      NB-Ampel am letzten Tag, jede fruehere Abweichung = andere Mitgliedschaft; Stufe gegen ampel_tag
    G7  Stablecoins   B3 (91 T) aus unserer Reihe gegen NB ampel_tag.b3 (gleiche Datierung wie die Ampel)

    python -X utf8 Basisinfos/Rechenkern_02_10/s1_nachweis.py
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
SICHT = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/_sichten/sichten.db?mode=ro"
MESS = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/messdaten.db?mode=ro"
FUND = "file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/funding_historie.db?mode=ro"
NB_SPOT = "file:K:/My Drive/Claude_Austauschordner/spot_betrieb.db?mode=ro"
NB_ORDNER = r"K:\My Drive\Claude_Austauschordner"       # NB-Betriebskopie messdaten.db (01.11., nur gelesen) + spot_betrieb.db
DESKTOP = r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\data"
NEU = [("kurs", "BTC"), ("kurs", "ETH"), ("dvol", "BTC"), ("dvol", "ETH"), ("funding", "BTC"), ("funding", "ETH"),
       ("oi", "BTC"), ("oi", "ETH"), ("stablecoins", "USD"), ("breite", "TOP50"), ("season", "STUFE")]
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-Sichten"}
ergebnis = []


def urteil(name, ok, text):
    ergebnis.append((name, ok))
    print("  %s  %-44s %s" % ("OK  " if ok else "FEHL", name, text))


def reihe(c, q, s) -> pd.DataFrame:
    return pd.read_sql("SELECT datum, wert, bekannt_ab FROM reihe WHERE quelle=? AND symbol=? ORDER BY datum", c, params=(q, s))


def main() -> int:
    c = sqlite3.connect(SICHT, uri=True)
    heute = datetime.now(timezone.utc).date().isoformat()
    print("=" * 100)
    print("S1-ERGÄNZUNG — NACHWEIS (%s UTC)" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    print("=" * 100)

    # G1, G2
    for q, s in NEU:
        r = reihe(c, q, s)
        if not len(r):
            urteil("G1 %s %s vorhanden" % (q, s), False, "leer")
            continue
        d = pd.to_datetime(r.datum)
        luecke = int(d.diff().dt.days.max() or 1)
        urteil("G1 %s %s lückenlos" % (q, s), luecke <= 1, "%d Tage, %s bis %s, größter Abstand %d T"
               % (len(r), r.datum.iloc[0], r.datum.iloc[-1], luecke))
        soll = (d + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%dT00:00:00+00:00")
        falsch = int((soll != r.bekannt_ab).sum())
        urteil("G2 %s %s ohne Vorgriff" % (q, s), falsch == 0 and r.datum.max() < heute,
               "bekannt_ab ≠ Folgetag: %d · letzter Tag %s (< %s)" % (falsch, r.datum.max(), heute))

    # G3 Kurs gegen Messbasis
    m = sqlite3.connect(MESS, uri=True)
    for b in ("BTC", "ETH"):
        r = reihe(c, "kurs", b).set_index("datum").wert
        mb = pd.read_sql("SELECT substr(date,1,10) AS datum, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' "
                         "AND currency='USD'", m, params=(b,)).set_index("datum").close
        # ⚠️ der LETZTE Tag der eingefrorenen Messbasis (2026-09-20) wurde mit noch offener Kerze geladen (01.11. gefunden: BTC 0,8 %,
        # ETH 2,6 % daneben) - er wird ausgewiesen, nicht verglichen
        letzt = mb.index.max()
        g = r.index.intersection(mb.index).drop(letzt, errors="ignore")
        abw = float(((r[g] / mb[g]) - 1).abs().max()) if len(g) else float("nan")
        urteil("G3 Kurs %s = Messbasis" % b, len(g) > 1000 and abw < 1e-9,
               "%d gemeinsame Tage, größte Abweichung %.2e · letzter Messbasis-Tag %s (offene Kerze) %+.2f %%"
               % (len(g), abw, letzt, 100 * (mb[letzt] / r[letzt] - 1) if letzt in r.index else float("nan")))

    # G4 Funding gegen funding_historie (Tagessumme)
    f = sqlite3.connect(FUND, uri=True)
    for b in ("BTC", "ETH"):
        r = reihe(c, "funding", b).set_index("datum").wert
        alt = pd.read_sql("SELECT datum, wert FROM funding WHERE symbol=?", f, params=(b,)).set_index("datum").wert
        g = r.index.intersection(alt.index)
        quot = (alt[g] / r[g]).replace([float("inf")], float("nan")).dropna()
        drei = float(((quot - 3).abs() < 1e-6).mean()) if len(quot) else 0.0
        urteil("G4 Funding %s ×3 = funding_historie" % b, len(g) > 1000 and drei > 0.99,
               "%d gemeinsame Tage, Verhältnis 3 an %.1f %% (Rest: Tage mit anderer Zahl an Zahlungen)" % (len(g), 100 * drei))

    # G5 OI Datei gegen API
    for b in ("BTC", "ETH"):
        r = reihe(c, "oi", b).set_index("datum").wert
        a = requests.get("https://fapi.binance.com/futures/data/openInterestHist",
                         params={"symbol": b + "USDT", "period": "1d", "limit": 30}, headers=H, timeout=30).json()
        api = pd.Series({(date.fromisoformat(datetime.fromtimestamp(x["timestamp"] / 1000, timezone.utc).date().isoformat())
                          - timedelta(days=1)).isoformat(): float(x["sumOpenInterest"]) for x in a})
        g = r.index.intersection(api.index)
        rel = ((r[g] / api[g]) - 1).abs()
        gleich = int((rel < 1e-12).sum())                              # Tage, an denen die Reihe selbst aus der API kommt
        rel_d = rel[rel >= 1e-12]
        # Grenze 0,5 % (01.11. begruendet): die 30-T-Veraenderung von OI liegt im Median bei 7–10 %, im 10. Perzentil bei 1,3 %;
        # aus der API kommt nur der jeweils LETZTE Tag (die Datei des Folgetags ist noch nicht erschienen)
        urteil("G5 OI %s Datei ≈ API (≤ 0,5 %%)" % b, len(g) >= 25 and (rel_d.max() if len(rel_d) else 0) < 5e-3,
               "%d gemeinsame Tage (davon %d aus der API selbst), Datei gg. API größte Abweichung %.3f %%, Median %.3f %%"
               % (len(g), gleich, 100 * (rel_d.max() if len(rel_d) else 0), 100 * (rel_d.median() if len(rel_d) else 0)))

    # G6 Breite und Stufe: Grundgesamtheit des BETRIEBS zum Zeitpunkt (G6a-Ursache 01.11.: die Messbasis zählte junge Coins
    # rückwirkend, trug Fremdreihen und keine Neulistungen - und die NB-Tabelle ampel_tag rechnet ihre Historie ebenfalls rückwirkend)
    import api.sichten_quellen as SQ
    from agent import season_ampel as SA
    from scheduler.background import BETRIEBSREIHEN_MINDEST
    SEASON_CODE = SQ.SEASON_CODE
    n = sqlite3.connect(NB_SPOT, uri=True)
    nb = pd.read_sql("SELECT datum, breite, stufe, b3 FROM ampel_tag", n).set_index("datum")
    st = reihe(c, "season", "STUFE").set_index("datum").wert
    bis = date(2026, 9, 20)                                            # Ende der eingefrorenen Messbasis
    K, U = SA.kopie(DESKTOP, bis)
    stab = SA.stabile(DESKTOP, K)
    alts = [s for s in K.columns if s not in stab and s != "BTC"]
    tage = list(pd.date_range("2020-01-01", pd.Timestamp(bis), freq="D"))
    Kd = K.reindex(pd.date_range(K.index[0], pd.Timestamp(bis), freq="D"))
    v0 = SA.breite(Kd, U.reindex(Kd.index), alts, Kd["BTC"], tage)
    r = SQ.breite_zum_zeitpunkt(K, U, alts, pd.DataFrame(True, index=Kd.index, columns=K.columns), tage)
    gleich = int((((r - v0).abs() < 1e-12) | (r.isna() & v0.isna())).sum())
    urteil("G6a-1 Regression: alle Mitglieder = Ampel", gleich == len(tage),
           "breite_zum_zeitpunkt mit Mitgliedschaft 'alle' = season_ampel.breite an %d von %d Tagen" % (gleich, len(tage)))
    mit_d, _ = SQ.betriebsmenge(K, SQ._quellen(DESKTOP))
    p_d = SQ.breite_zum_zeitpunkt(K, U, alts, mit_d, tage)
    br = reihe(c, "breite", "TOP50").set_index("datum").wert
    br.index = pd.to_datetime(br.index)
    gb = br.index.intersection(p_d.dropna().index)
    urteil("G6a-2 sichten.db = Betriebsmenge (Desktop)", len(gb) == len(br) and float((br[gb] - p_d[gb]).abs().max()) < 1e-12,
           "%d Zeilen, alle aus der Betriebsmenge, größte Abweichung %.1e · rechenbar ab %s"
           % (len(br), float((br[gb] - p_d[gb]).abs().max()), br.index.min().date()))
    # Desktop gegen NB-Kopie, beide in der Betriebsmenge, an den Tagen, an denen die Kopie die Mitgliedschaft trägt
    Kn, Un = SA.kopie(NB_ORDNER, date(2026, 10, 31))
    stab_n = SA.stabile(NB_ORDNER, Kn)
    alts_n = [s for s in Kn.columns if s not in stab_n and s != "BTC"]
    mit_n, ab_n = SQ.betriebsmenge(Kn, SQ._quellen(NB_ORDNER))
    ab_lose = Kn["BTC"].first_valid_index() + pd.Timedelta(days=BETRIEBSREIHEN_MINDEST - 1)
    tn = list(pd.date_range(ab_lose, "2026-10-31", freq="D"))
    pn = SQ.breite_zum_zeitpunkt(Kn, Un, alts_n, mit_n, tn)
    gd = [t for t in tn if t < pd.Timestamp(bis) and p_d.get(t) == p_d.get(t)]   # 20.09. = offene Kerze der Messbasis (G3)
    dd = (p_d[gd] - pn[gd]).abs()
    urteil("G6a-3 Desktop = NB-Kopie (beide Betriebsmenge)", len(gd) >= 50 and float(dd.max()) < 1e-12,
           "%d gemeinsame Tage (%s bis %s), gleich an %d, größte Abweichung %.3f"
           % (len(gd), gd[0].date(), gd[-1].date(), int((dd < 1e-12).sum()), float(dd.max())))
    # Abrufer auf der NB-Kopie gegen die NB-Ampel: am letzten Tag gleich, davor nur dort anders, wo die Menge eine andere war
    letzt = tn[-1]
    nbb = nb.breite.copy()
    nbb.index = pd.to_datetime(nbb.index)
    T = SQ._season_tabelle(NB_ORDNER)
    ok_letzt = abs(T.at[letzt, "Breite"] - nbb[letzt]) < 1e-12 and T.at[letzt, "stufe"] == nb.stufe[letzt.date().isoformat()]
    urteil("G6a-4 NB letzter Tag: Abrufer = Ampel", bool(ok_letzt),
           "%s Breite %.3f / %.3f, Stufe %s / %s · geschrieben würde am NB ab %s"
           % (letzt.date(), T.at[letzt, "Breite"], nbb[letzt], T.at[letzt, "stufe"], nb.stufe[letzt.date().isoformat()], ab_n.date()))
    anders = [t for t in tn if abs(pn[t] - nbb[t]) > 1e-12]
    # einzige Ursache = Mitgliedschaft: mit Mitgliedschaft 'alle' muss auf den NB-Daten an JEDEM Tag die Ampel herauskommen -
    # dann unterscheidet Abrufer und Ampel nur noch die Mitgliedschaft. (Nicht 'die Menge des letzten Tages': in der fehlen
    # die inzwischen EINGESTELLTEN, die damals mitliefen - 01.11. so geprüft und verworfen, 61 von 101)
    pf = SQ.breite_zum_zeitpunkt(Kn, Un, alts_n, pd.DataFrame(True, index=mit_n.index, columns=mit_n.columns), tn)
    gleich_f = int(((pf[tn] - nbb[tn]).abs() < 1e-12).sum())
    urteil("G6a-5 NB davor: einzige Ursache = Mitgliedschaft", gleich_f == len(tn),
           "%d Tage, Abrufer anders an %d · mit Mitgliedschaft 'alle' = Ampel an %d von %d (die Ampel rechnet rückwirkend)"
           % (len(tn), len(anders), gleich_f, len(tn)))
    for t in anders[-3:]:
        neu = [s for s in mit_n.columns if mit_n.at[letzt, s] and not mit_n.at[t, s] and s in alts_n]
        print("       %s Abrufer %.3f / Ampel %.3f · am Tag noch nicht Mitglied: %s" % (t.date(), pn[t], nbb[t], ", ".join(neu[:8])))

    # Wirkung (Auskunft, kein Urteil): Klasse im 5-J-Rang, Betriebsmenge gegen Messbasis-Menge
    def klasse(p):
        return "sehr tief" if p <= 5 else "tief" if p <= 20 else "sehr hoch" if p >= 95 else "hoch" if p >= 80 else "normal"
    g = [t for t in tage if p_d[t] == p_d[t] and v0[t] == v0[t]]
    k_anders = 0
    for t in g:
        f = p_d[(p_d.index > t - pd.Timedelta(days=5 * 365)) & (p_d.index <= t)].dropna()
        rang = lambda x: 100 * (f < x).mean() + 50 * (f == x).mean()   # noqa: E731
        k_anders += klasse(rang(p_d[t])) != klasse(rang(v0[t]))
    print("       Wirkung: Klasse im 5-J-Rang Betriebsmenge gg. Messbasis-Menge anders an %d von %d Tagen (%.1f %%)"
          % (k_anders, len(g), 100 * k_anders / len(g)))
    gs = st.index.intersection(nb.index)
    nb_code = nb.stufe[gs].map(SEASON_CODE)
    gleich = int((st[gs] == nb_code).sum())
    urteil("G6b Season-Stufe Desktop = NB", len(gs) > 300 and gleich == len(gs), "%d gemeinsame Tage, gleich an %d" % (len(gs), gleich))

    # G7 Stablecoins: B3 aus unserer Reihe (datiert wie die Ampel: Verfügbarkeitstag = Beobachtung + 1)
    sb = reihe(c, "stablecoins", "USD")
    s = pd.Series(sb.wert.values, index=pd.to_datetime(sb.datum) + pd.Timedelta(days=1))
    s = s.reindex(pd.date_range(s.index[0], s.index[-1], freq="D")).ffill()
    b3 = (s / s.shift(91) - 1)
    b3.index = b3.index.strftime("%Y-%m-%d")
    g = b3.dropna().index.intersection(nb.index)
    d = (b3[g] - nb.b3[g]).abs()
    urteil("G7 Stablecoins B3 = NB-Ampel", len(g) > 300 and float(d.max()) < 1e-3,
           "%d gemeinsame Tage, größte Abweichung %.2e (Revisionen DefiLlama zwischen den Abrufen)" % (len(g), float(d.max())))

    print("=" * 100)
    fehl = [x for x, ok in ergebnis if not ok]
    print("%d Prüfungen, %s" % (len(ergebnis), "ALLE BESTANDEN" if not fehl else "%d FEHLGESCHLAGEN: %s" % (len(fehl), ", ".join(fehl))))
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
