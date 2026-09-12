# -*- coding: utf-8 -*-
"""Holt Funding-Rate und aktive Adressen in eigene Messdateien (30.08.2026).

⚠️ SCHREIBT NICHT IN DIE PRODUKTIONS-DB. Ziele:
    data/funding_historie.db   Binance Futures, 8-Stunden-Takt, ab 2019
    data/onchain_historie.db   Coin Metrics Community, taeglich, ab 2015
    data/markt_historie.db     CoinGecko, taeglich, 365 Tage (Schritt 49)

## Warum rueckwirkend moeglich

Im Projekt stand "Positionierung: Wirkung erst ab 22.10.2026 messbar" und
"TVL ab 18.09.2026". Beides beruhte darauf, dass die Module den
MOMENTAUFNAHME-Endpunkt abrufen. Geprueft am 30.08.:

    Funding-Rate   Binance /fapi/v1/fundingRate   ab 2019-09-10 = 7,0 Jahre
    Open Interest  Binance /futures/data/...      nur 30 Tage - NICHT holbar
    Aktive Adressen Coin Metrics Community        ETH 4.049 Punkte ab 2015

## Schonender Abruf

Funding: Pause 0,4 s (Binance-Limit ist weit hoeher, aber Nutzervorgabe
lautet "nicht zu schnell"). Coin Metrics: Limit 10 Anfragen / 6 s -> Pause
0,8 s, mit Reserve.

## Funding wird auf TAGE verdichtet

Die Rate faellt alle 8 Stunden an. Fuer die Messung zaehlt der Tageswert -
gebildet als SUMME der drei Zahlungen, denn genau das kostet ein Halten
ueber diesen Tag.
"""
import datetime as dt
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

# ⚠️ NICHT AUF MODULEBENE UMSTELLEN (12.09.2026, zum zweiten Mal an diesem
# Tag). `pruefe_pakete` ersetzt `sys.stdout` durch einen Mitschnitt ohne
# `reconfigure` - das Modul liess sich dort gar nicht erst importieren, und
# ein Werkzeug, das man nicht importieren kann, kann man auch nicht pruefen.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import messe_eigenschaft_beitrag as B

KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}


def hole(url, versuche=3, pause=1.0, timeout=60):
    for n in range(versuche):
        try:
            r = urllib.request.Request(url, headers=KOPF)
            with urllib.request.urlopen(r, timeout=timeout) as a:
                return json.loads(a.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if n == versuche - 1:
                raise
            # ⚠️ EIN 429 IST KEINE STOERUNG, SONDERN EINE ANSAGE (12.09.2026).
            # Wer nach zwei Sekunden wieder anklopft, bekommt wieder 429 und
            # verbrennt seinen Versuch. Gemessen am ersten Turnover-Lauf: 2
            # Symbole je Minute statt 27, weil fast jede Anfrage abgewiesen
            # wurde. Bei einem 429 wird deshalb DEUTLICH laenger gewartet.
            _code = getattr(e, "code", None)
            time.sleep((15.0 * (n + 1)) if _code == 429 else pause * (n + 2))
    return None


def anlegen(conn, tabelle):
    conn.execute("""CREATE TABLE IF NOT EXISTS %s (
        symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL,
        PRIMARY KEY (symbol, datum))""" % tabelle)
    conn.commit()


# ---------------------------------------------------------------------------
def funding(unsere, pause=0.4):
    print("=" * 78)
    print("A. FUNDING-RATE (Binance Futures)")
    print("=" * 78)
    info = hole("https://fapi.binance.com/fapi/v1/exchangeInfo")
    paare = {}
    # ⚠️ NUR PERPETUAL. Grosse Werte haben zusaetzlich Quartalskontrakte
    # (BTCUSDT_260925, BTCUSDT_261225) - die haben KEINE Funding-Rate. Ohne
    # diesen Filter ueberschreibt der Quartalskontrakt das Perpetual, und
    # ausgerechnet BTC und ETH fallen still aus (Fehler vom 30.08.2026,
    # gefunden erst bei der Abdeckungspruefung der Watchlist).
    for s in info.get("symbols", []):
        if (s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"
                and s.get("contractType") == "PERPETUAL"):
            basis = str(s.get("baseAsset") or "").upper()
            if basis in unsere:
                paare[basis] = s["symbol"]
    print("Unsere Symbole mit Binance-Futures-Paar: %d von %d"
          % (len(paare), len(unsere)))
    conn = sqlite3.connect("data/funding_historie.db")
    anlegen(conn, "funding")
    ok = 0
    for i, (basis, paar) in enumerate(sorted(paare.items()), 1):
        try:
            # ⚠️ MUSS bei 2019 beginnen und VORWAERTS paginieren.
            # Ohne `startTime` liefert Binance nur die letzten 500 Eintraege -
            # die Abbruchbedingung greift dann sofort, und man bekommt fuenf
            # Monate statt sieben Jahren (Fehler vom 30.08.2026, behoben).
            je_tag, runden = {}, 0
            start = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)
                        .timestamp() * 1000)
            while runden < 60:                       # Deckel gegen Endlosschleife
                url = ("https://fapi.binance.com/fapi/v1/fundingRate?symbol=%s"
                       "&limit=1000&startTime=%d" % (paar, start))
                d = hole(url, pause=pause)
                if not d:
                    break
                for e in d:
                    tag = dt.datetime.fromtimestamp(
                        e["fundingTime"] / 1000, dt.timezone.utc).date().isoformat()
                    je_tag[tag] = je_tag.get(tag, 0.0) + float(e["fundingRate"])
                if len(d) < 1000:
                    break
                start = d[-1]["fundingTime"] + 1
                runden += 1
                time.sleep(pause)
            if je_tag:
                conn.executemany("INSERT OR REPLACE INTO funding VALUES (?,?,?)",
                                 [(basis, t, v) for t, v in je_tag.items()])
                conn.commit()
                ok += 1
        except Exception as e:                       # noqa: BLE001
            print("  %-9s FEHLER: %s" % (basis, str(e)[:50]))
        if i % 20 == 0:
            print("  %3d von %d  (ok %d)" % (i, len(paare), ok))
        time.sleep(pause)
    n, s, a, b = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(datum), MAX(datum) "
        "FROM funding").fetchone()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (s, n, a, b))
    conn.close()


# ---------------------------------------------------------------------------
def onchain(unsere, metrik="AdrActCnt", pause=0.8):
    print()
    print("=" * 78)
    print("B. %s (Coin Metrics Community)" % metrik)
    print("=" * 78)
    d = hole("https://community-api.coinmetrics.io/v4/catalog/asset-metrics"
             "?metrics=%s" % metrik)
    eintrag = (d.get("data") or [{}])[0]
    tages = next((f for f in (eintrag.get("frequencies") or [])
                  if f.get("frequency") == "1d"), {})
    verfuegbar = [a for a in (tages.get("assets") or []) if a.upper() in unsere]
    print("Unsere Symbole mit dieser Metrik: %d" % len(verfuegbar))
    conn = sqlite3.connect("data/onchain_historie.db")
    anlegen(conn, metrik.lower())
    ok = 0
    for i, asset in enumerate(sorted(verfuegbar), 1):
        try:
            d = hole("https://community-api.coinmetrics.io/v4/timeseries/"
                     "asset-metrics?assets=%s&metrics=%s&frequency=1d"
                     "&start_time=2013-01-01&page_size=10000" % (asset, metrik),
                     pause=pause)
            zeilen = []
            for e in (d.get("data") or []):
                v = e.get(metrik)
                if v not in (None, ""):
                    zeilen.append((asset.upper(), e["time"][:10], float(v)))
            if zeilen:
                conn.executemany("INSERT OR REPLACE INTO %s VALUES (?,?,?)"
                                 % metrik.lower(), zeilen)
                conn.commit()
                ok += 1
        except Exception as e:                       # noqa: BLE001
            print("  %-9s FEHLER: %s" % (asset, str(e)[:50]))
        if i % 20 == 0:
            print("  %3d von %d  (ok %d)" % (i, len(verfuegbar), ok))
        time.sleep(pause)
    n, s, a, b = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(datum), MAX(datum) "
        "FROM %s" % metrik.lower()).fetchone()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (s, n, a, b))
    conn.close()


# ---------------------------------------------------------------------------
def turnover(pause=8.0, tage=365):
    """Umschlag je Tag: Handelsvolumen durch Marktkapitalisierung.

    ⚠️⚠️ WARUM ES DIESE FUNKTION GIBT (Schritt 49, Teil 1, 12.09.2026).
    Befund 2.410: der GEMESSENE und der ANGEWENDETE `turnover` waren nicht
    dieselbe Groesse. Beide rechnen `Volumen / (Preis x Umlaufmenge)` - aber
    die Menge kam aus zwei Quellen:

        Messung      `splycur` aus onchain_historie.db (Coin Metrics)
        Anwendung    `circulating_supply` von CoinGecko

    Von 33 vergleichbaren Symbolen wichen 16 um mindestens 5 % ab, teils um
    25 bis 74 % - LINK aus der Watchlist um -25,2 %. Die Onchain-Werte sind
    runde Zahlen (UNI und LINK je 1.000.000.000): das ist die GESAMTAUSGABE,
    nicht die UMLAUFENDE Menge. Zwei Begriffe unter einem Namen.

    ⚠️ DIE FORMEL KUERZT SICH, und darin liegt die Loesung:

        turnover = Volumen / (Preis x Menge) = Volumen / MARKTKAPITALISIERUNG

    Beide Groessen liefert `market_chart` in EINEM Aufruf - keine
    Umlaufmenge noetig, also auch keine zweite Quelle, die abweichen kann.
    Gegengerechnet an ADA am 12.09.: Historie 0,039040 gegen die
    Live-Funktion 0,039041.

    ⚠️⚠️ GENAU DIE 250 VON SEITE 1, nicht mehr. `marktrang.turnover_werte`
    liest `coins/markets?per_page=250&page=1` - wer hier breiter laedt,
    misst wieder etwas anderes als der Betrieb anwendet und baut 2.410 neu
    auf, nur andersherum. Wer mehr will, aendert BEIDE Seiten.

    ⚠️ `days=365` IST DIE FREIE GRENZE: `days=max` beantwortet CoinGecko
    ohne Schluessel mit HTTP 401 (geprueft 12.09.). 365 Tage reichen fuer
    eine Beitragsmessung um ein Vielfaches.

    ⚠️⚠️ PAUSE 6 s - UND DAS IST GEMESSEN, NICHT GESCHAETZT. Meine erste
    Fassung stand auf 2,2 s mit der Begruendung "die freie Grenze liegt bei
    etwa 30 Anfragen je Minute". Der erste echte Lauf brachte 2 Symbole je
    Minute statt 27: CoinGecko antwortet mit HTTP 429, und jede Wiederholung
    kostet zusaetzlich. Der Abruf selbst dauert 0,2 s - die Zeit geht
    vollstaendig fuer abgewiesene Anfragen drauf.

    ⚠️⚠️ DIE ZAHL IST GEMESSEN, UND ZWAR IM DRITTEN ANLAUF. 2,2 s (aus der
    Doku "30 Anfragen je Minute") ergaben 2 Symbole je Minute - fast jede
    Anfrage wurde abgewiesen. 6 s brachten den Lauf ganz zum Stehen: die
    Drosselung traf danach sogar `/ping`. Erst ein Test mit sechs Anfragen
    hintereinander zeigte, was traegt:

        Pause 8 s = 7,5 Anfragen/Minute -> 6 von 6 durch

    250 Symbole brauchen damit rund 33 Minuten. ⚠️ Die Drosselung ist KEIN
    Bann: sie loest sich in unter einer Minute. Wer sie trifft, verliert
    Zeit, nicht den Zugang.

    ⚠️ WER ES EILIGER BRAUCHT, nimmt einen CoinGecko-Demo-Schluessel (frei,
    30 Anfragen/Minute, 10.000 im Monat). Das ist eine Abhaengigkeit mehr
    und eine Nutzerentscheidung - ohne ihn geht es auch, nur langsamer."""
    print("=" * 78)
    print("C. UMSCHLAG (CoinGecko, Volumen / Marktkapitalisierung)")
    print("=" * 78)
    markets = hole("https://api.coingecko.com/api/v3/coins/markets"
                   "?vs_currency=usd&order=market_cap_desc&per_page=250&page=1")
    # ⚠️ DIE ID UND DAS SYMBOL - beides. Die ID braucht der Abruf, das Symbol
    # ist unser Schluessel. Ueber das Symbol allein waere CANTON schon einmal
    # falsch zugeordnet worden (siehe marktrang._coingecko_namen).
    paare = [(str(e.get("id") or ""), str(e.get("symbol") or "").upper())
             for e in (markets or []) if e.get("id") and e.get("symbol")]
    print("  %d Symbole auf Seite 1 der Marktliste" % len(paare))

    conn = sqlite3.connect("data/markt_historie.db")
    anlegen(conn, "turnover")

    # ---- WIEDERAUFNEHMBAR (12.09.2026) --------------------------------
    #
    # ⚠️ Der Lauf dauert rund 25 Minuten. Ohne diese Stelle kostet jeder
    # Abbruch - Netz weg, Rechner aus, ein Abbruch von Hand - alles, und der
    # naechste Versuch faengt bei null an. Genau das ist beim ersten Lauf
    # passiert: 15 Symbole geladen, dann abgebrochen, alles noch einmal.
    #
    # ⚠️⚠️ ,SCHON DA' HEISST: DER LETZTE TAG STIMMT. Ein Symbol mit Daten
    # bis vorgestern ist NICHT fertig - es zu ueberspringen hiesse, eine
    # Luecke festzuschreiben. Nur wer bis gestern oder heute reicht, wird
    # ausgelassen.
    _gestern = (dt.datetime.now(dt.timezone.utc).date()
                - dt.timedelta(days=1)).isoformat()
    schon_da = {r[0] for r in conn.execute(
        "SELECT symbol FROM turnover GROUP BY symbol HAVING MAX(datum) >= ?",
        (_gestern,))}
    if schon_da:
        print("  %d Symbole sind aktuell und werden uebersprungen"
              % len(schon_da))

    ok = leer = fehler = uebersprungen = 0
    for i, (cg_id, sym) in enumerate(paare, 1):
        if sym in schon_da:
            uebersprungen += 1
            continue
        try:
            d = hole("https://api.coingecko.com/api/v3/coins/%s/market_chart"
                     "?vs_currency=usd&days=%d&interval=daily" % (cg_id, tage))
            vol = {int(t) // 86400000: v for t, v in (d.get("total_volumes") or [])}
            mc = {int(t) // 86400000: v for t, v in (d.get("market_caps") or [])}
            zeilen = []
            for tagnr, v in vol.items():
                m = mc.get(tagnr)
                # ⚠️ KEIN WERT STATT EINER NULL. Eine Marktkapitalisierung
                # von 0 ergaebe eine Division durch null; sie wegzulassen ist
                # ehrlicher als sie zu erfinden (N-40).
                if m and m > 0 and v is not None:
                    datum = dt.datetime.fromtimestamp(
                        tagnr * 86400, dt.timezone.utc).date().isoformat()
                    zeilen.append((sym, datum, float(v) / float(m)))
            if zeilen:
                conn.executemany(
                    "INSERT OR REPLACE INTO turnover VALUES (?,?,?)", zeilen)
                conn.commit()
                ok += 1
            else:
                leer += 1
        except Exception as e:                       # noqa: BLE001
            fehler += 1
            print("  %-9s FEHLER: %s" % (sym, str(e)[:50]))
        if i % 25 == 0:
            print("  %3d von %d  (ok %d, leer %d, Fehler %d, "
                  "uebersprungen %d)"
                  % (i, len(paare), ok, leer, fehler, uebersprungen))
        time.sleep(pause)
    n, sy, a, b = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(datum), MAX(datum) "
        "FROM turnover").fetchone()
    print("FERTIG: %d Symbole, %d Tagespunkte, %s .. %s" % (sy, n, a, b))
    conn.close()


if __name__ == "__main__":
    unsere = {s.upper() for s in B.lade().keys()}
    was = sys.argv[1] if len(sys.argv) > 1 else "beides"
    if was in ("funding", "beides"):
        funding(unsere)
    if was in ("onchain", "beides"):
        onchain(unsere)
    # ⚠️ NICHT IN "beides": `turnover` braucht rund zehn Minuten und laedt
    # 250 Symbole, die mit `unsere` nichts zu tun haben - wer "beides" ruft,
    # will die Reihen zu SEINEN Werten auffrischen, nicht den halben Markt.
    if was == "turnover":
        turnover()
