# -*- coding: utf-8 -*-
"""VOLLABRUF: historische Umlaufmenge (Free Float) von CoinGecko.

⚠️ Der Nenner von `turnover`. Heute: Coin Metrics `SplyCur` = die
GESAMTAUSGABE auf dem Ledger, 61 frische Symbole. Hier: Free Float,
abgeleitet als **Marktkapitalisierung / Preis**, 365 Tage, taeglich.

## Warum dieser Weg - und warum er 2.417 nicht widerspricht

Die Suche am 13.09. galt der MEHRJAEHRIGEN Historie (2.636 Kalendertage)
und ist daran gescheitert. `market_chart?days=365` liefert genau ein
Jahr - zu wenig fuer H20 (6 Bloecke), genug fuer H2 (60) und H5 (24).

## ⚠️⚠️ Survivorship - und warum er sich hier aufloest

Die Messmenge V1 fuehrt 179 EINGESTELLTE Paare mit Absicht (Kapitel
120.3). Ueber `/exchanges/binance/tickers` sind sie nicht zu bekommen -
CoinGecko fuehrt sie nicht mehr als Binance-Ticker. Aber:

    TRADING                        350 in V1, 345 zuordenbar (99 %)
    BREAK, letzter Kurs < 365 Tage  59 - ueber den HISTORISCHEN Preis
    BREAK, aelter                  122 - im Messfenster GAR NICHT
                                        handelbar, gehoeren nicht dazu

Die Grundgesamtheit eines 365-Tage-Fensters ist, wer in diesem Fenster
gehandelt wurde: 350 + 59 = 409. Die 59 sind die im Fenster
GESTORBENEN - genau sie trennen eine saubere von einer
ueberlebensverzerrten Menge.

## Die drei Auflagen aus der Machbarkeitspruefung

    1 PLAUSIBILITAET  Menge <= 0 verwerfen; Reihen mit zu vielen
                      Loechern ganz ablehnen (der FTT-Fall: 185 Punkte
                      ohne Wert, Menge -4,32)
    2 SPRUENGE        nicht glaetten, sondern ZAEHLEN und ausweisen.
                      TAO +18 %, MORPHO +50 % an einem Tag sind echte
                      Unlocks - `SplyCur` sieht sie nicht, weil die
                      Token laengst ausgegeben waren
    3 OHNE ID         ausweisen, nicht raten. Ein Kuerzel ist keine
                      Kennung

⚠️ SCHREIBT IN EINE EIGENE DATEI, nicht in die Produktionsdatenbank.
⚠️ Eigener Abruf, nicht ueber api/* (das buchte ueber `api_health` in
die Standard-DB).
⚠️ WIEDERAUFNEHMBAR: ein zweiter Lauf holt nur, was fehlt.

    python hole_umlaufmenge_cg.py
    python hole_umlaufmenge_cg.py --ziel data/umlaufmenge_cg.db --nur 20
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CG = "https://api.coingecko.com/api/v3"
BINANCE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
ZIEL_VORGABE = "data/umlaufmenge_cg.db"
TAGE = 365
# ⚠️⚠️ GEMESSEN, NICHT GESCHAETZT (Probelauf 21.09.2026): CoinGecko
# antwortet fuenfmal mit 200 und beim SECHSTEN mit 429. Die freie Grenze
# liegt also bei rund fuenf Abrufen je Minute, nicht bei dreissig. Mit
# 2,6 s Pause brauchten fuenf Symbole 5,4 Minuten - fast alles davon
# Nachwartezeit.
#
# Deshalb ADAPTIV: langsam anfangen, bei 429 deutlich bremsen, nach
# vielen sauberen Abrufen vorsichtig wieder beschleunigen. Eine feste
# Pause waere entweder zu schnell (Drosselung) oder zu langsam.
# ⚠️⚠️ NACHGEMESSEN AM LAUFENDEN LAUF (21.09.2026): mit PAUSE_MIN 3,0
# brauchte der Abruf 35 s JE SYMBOL statt der geschaetzten 12 - weil die
# Erholung zu traege war. Nach einem einzigen 429 klebte die Pause bei
# 20 s, und `_lockern` brauchte 15 saubere Abrufe fuer 15 % Nachlass.
#
# Die gemessene Grenze ist 5 Abrufe je Minute = 12 s. Eine Pause UNTER
# dieser Grenze kauft nichts: sie erzeugt nur den naechsten 429 und
# dessen Nachwartezeit. Deshalb ist der BODEN jetzt die gemessene
# Grenze, nicht ein optimistischer Wunschwert.
PAUSE_START = 12.0
PAUSE_MAX = 25.0
PAUSE_MIN = 12.0
MIND_PUNKTE = 300                # unter 300 von 366 ist die Reihe unbrauchbar
SPRUNG_GRENZE = 0.10             # ab 10 % an einem Tag gilt es als Sprung


def _arg(flagge, vorgabe=None):
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


_PAUSE = [PAUSE_START, 0]        # [aktuelle Pause, saubere Abrufe in Folge]


def _bremsen():
    _PAUSE[0] = min(PAUSE_MAX, max(_PAUSE[0] * 1.6, 8.0))
    _PAUSE[1] = 0


def _lockern():
    _PAUSE[1] += 1
    if _PAUSE[1] >= 5 and _PAUSE[0] > PAUSE_MIN:
        _PAUSE[0] = max(PAUSE_MIN, _PAUSE[0] * 0.85)
        _PAUSE[1] = 0


def hole(url, versuche=4):
    """401/403 = Verbot, 429 = Drosselung - getrennt, mit Nachwartezeit."""
    for i in range(versuche):
        try:
            r = urllib.request.Request(
                url, headers={"User-Agent": "TradingInfoTool-Umlaufmenge"})
            with urllib.request.urlopen(r, timeout=50) as a:
                _lockern()
                return a.status, json.loads(a.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                _bremsen()
                if i < versuche - 1:
                    time.sleep(_PAUSE[0] * 2)
                    continue
            return e.code, None
        except Exception as exc:                             # noqa: BLE001
            if i < versuche - 1:
                time.sleep(5)
                continue
            return str(exc)[:60], None
    return "?", None


def baue(ziel):
    c = sqlite3.connect(ziel)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS umlaufmenge (
        symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL,
        PRIMARY KEY (symbol, datum));
    CREATE TABLE IF NOT EXISTS abruf_symbol (
        symbol TEXT PRIMARY KEY, coingecko_id TEXT, status TEXT,
        punkte INTEGER, verworfen INTEGER, spruenge INTEGER,
        groesster_sprung REAL, urteil TEXT, geholt_am TEXT);
    CREATE TABLE IF NOT EXISTS _quelle (
        hinweis TEXT, groesse TEXT, tage INTEGER, gebaut_am TEXT);
    """)
    # ⚠️⚠️ DIE HERKUNFTSMARKE FUER DEN BUENDELFAKTOR (22.09.2026, S3).
    #
    # `vervielfacher` teilt die Menge durch den Buendelfaktor, damit sie
    # zum Binance-BUENDELvolumen passt. Wer die Datei spaeter liest, kann
    # dem Zahlenwert NICHT ansehen, ob das geschehen ist - und eine
    # zweite Anwendung machte ihn tausendfach zu klein (Befund 2.522).
    # Deshalb schreibt der Erzeuger es hin. Nachtraeglich per ALTER, damit
    # eine bestehende Datei nicht neu gebaut werden muss.
    #
    # ⚠️ EINE ALTE ZEILE BEKOMMT DIE MARKE NICHT GESCHENKT. Sie bleibt
    # NULL, und der Leser liest das als "nicht geprueft" - eine Marke,
    # die man sich selbst ausstellt, ist keine.
    if "buendelfaktor" not in {r[1] for r in
                               c.execute("PRAGMA table_info(_quelle)")}:
        c.execute("ALTER TABLE _quelle ADD COLUMN buendelfaktor TEXT")
    if not c.execute("SELECT 1 FROM _quelle").fetchone():
        c.execute(
            "INSERT INTO _quelle (hinweis, groesse, tage, gebaut_am, "
            "buendelfaktor) VALUES (?,?,?,?,?)",
            ("CoinGecko market_chart, Menge = Marktkapitalisierung / Preis. "
             "⚠️ FREE FLOAT - NICHT dieselbe Groesse wie Coin Metrics "
             "`SplyCur` (Gesamtausgabe auf dem Ledger). Die beiden duerfen "
             "nicht im selben Nenner gemischt werden.",
             "free_float", TAGE,
             dt.datetime.now(dt.timezone.utc).isoformat(),
             "angewandt (hole_umlaufmenge_cg.vervielfacher)"))
    c.commit()
    return c


_VORSATZ = re.compile(r"^(\d+)(M?)(?=[A-Z])")


def vervielfacher(sym):
    """`1000CAT` = 1000 x CAT · `1MBABYDOGE` = 1.000.000 x BABYDOGE.

    ⚠️⚠️ BINANCE HANDELT BUENDEL, COINGECKO FUEHRT DEN EINZELTOKEN.
    `turnover` ist Stueck durch Menge - und die Stuecke sind Buendel.
    Ohne den Faktor stuende die Menge um bis zu einer Million zu hoch
    und das Symbol faende sich am untersten Rand des Rangs wieder, ohne
    dass am Markt irgendetwas passiert waere.

    ⚠️ Faktor 1 ist KEIN Vorsatz: `1INCH` heisst so. Nur groesser 1
    zaehlt - sonst zerlegte die Regel einen echten Namen.
    """
    m = _VORSATZ.match(sym)
    if not m:
        return 1.0, sym
    f = float(m.group(1)) * (1e6 if m.group(2) == "M" else 1.0)
    if f <= 1.0:
        return 1.0, sym
    return f, sym[m.end():]


def zerlege(sym, d, faktor=1.0):
    """market_chart-Antwort -> (Reihe, weg, Spruenge, groesster Sprung).

    ⚠️ EINE Stelle. Der Nachzug ruft dieselbe Funktion - eine zweite
    Fassung waere eine Kopie, die still auseinanderlaeuft.
    """
    mc = (d or {}).get("market_caps") or []
    pr = (d or {}).get("prices") or []
    reihe, weg = [], 0
    vorher = None
    spruenge = 0
    groesster = 0.0
    for (t1, m), (t2, k) in zip(mc, pr):
        if not m or not k or k <= 0 or (m / k) <= 0:
            weg += 1
            continue
        menge = m / k / faktor
        tag = dt.datetime.fromtimestamp(
            t1 / 1000, dt.timezone.utc).date().isoformat()
        if vorher and vorher > 0:
            ab = abs(menge - vorher) / vorher
            if ab >= SPRUNG_GRENZE:
                spruenge += 1
            groesster = max(groesster, ab)
        vorher = menge
        reihe.append((sym, tag, menge))
    return reihe, weg, spruenge, groesster


def speichere(c, sym, cid, stat, reihe, weg, spruenge, groesster):
    """Reihe ablegen und das Urteil protokollieren. Gibt das Urteil."""
    urteil = "ok" if len(reihe) >= MIND_PUNKTE else "verworfen"
    if urteil == "ok":
        c.executemany("INSERT OR REPLACE INTO umlaufmenge VALUES (?,?,?)",
                      reihe)
    c.execute("INSERT OR REPLACE INTO abruf_symbol "
              "VALUES (?,?,?,?,?,?,?,?,?)",
              (sym, cid, stat, len(reihe), weg, spruenge,
               round(groesster, 4), urteil,
               dt.datetime.now(dt.timezone.utc).isoformat()))
    c.commit()
    return urteil


def kurse_aus_messbasis(datei, symbole, tage=TAGE):
    """Binance-Tagesschluss je Symbol - der SCHLUESSEL zur Zuordnung.

    ⚠️ Ein Kuerzel ist keine Kennung (`symbol-ist-keine-eindeutige-
    kennung`). Ein PREISVERLAUF ueber Monate ist praktisch eine: zwei
    verschiedene Token haben nicht zufaellig dieselbe Kurve.
    """
    ab = (dt.date.today() - dt.timedelta(days=tage + 5)).isoformat()
    c = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    aus = {}
    fragezeichen = ",".join("?" * len(symbole))
    for sym, tag, schluss in c.execute(
            "SELECT symbol, date, close FROM price_history_ohlc "
            " WHERE date >= ? AND close > 0 AND symbol IN (%s)"
            % fragezeichen, [ab] + list(symbole)):
        aus.setdefault(str(sym).upper(), {})[str(tag)[:10]] = float(schluss)
    c.close()
    return aus


# ⚠️⚠️ DIE DECKE VON `turnover` - AUS DER VERTEILUNG ABGELESEN, NICHT
# GESETZT (21.09.2026, 376 Symbole). `turnover` ist ein ANTEIL: welcher
# Bruchteil aller existierenden Einheiten wechselt an einem Tag den
# Besitzer. Gemessene Verteilung der Mediane je Symbol:
#
#     50. Perzentil  0,0133      99. Perzentil  0,127
#     90. Perzentil  0,0598     100. Perzentil  49,66
#
# Zwischen 0,139 und 49,66 liegt NICHTS. Die Grenze 1,0 ("der ganze
# Bestand wechselt einmal am Tag") hat damit den Faktor 7 Abstand zum
# groessten echten Wert und den Faktor 50 zum Ausreisser.
#
# ⚠️ EIN ABSURDER UMSCHLAG IST KEIN MARKT-, SONDERN EIN NENNERBEFUND -
# und dieser eine Test faengt alles, wonach man sonst einzeln suchen
# muesste: gebrueckte Token (die Menge ist nur das, was ueber der
# Bruecke liegt), Buendelpaare, Skalenfehler, falsche Namensvettern.
# Ohne Namensliste ("bridged", "wrapped", "peg"), die beim naechsten
# Praefix still veraltet.
UMSCHLAG_DECKE = 1.0


def umschlag_verdacht(menge_je_tag, volumen_je_tag, decke=UMSCHLAG_DECKE,
                      mindest=30):
    """Median-Umschlag und Urteil: ist der NENNER plausibel?

    Gibt (median, verdaechtig) oder (None, False), wenn zu wenige
    gemeinsame Tage vorliegen - dann wird NICHT geurteilt.
    """
    werte = [volumen_je_tag[t] / menge_je_tag[t]
             for t in (set(volumen_je_tag) & set(menge_je_tag))
             if menge_je_tag[t] > 0 and volumen_je_tag[t] > 0]
    if len(werte) < mindest:
        return None, False
    werte.sort()
    med = werte[len(werte) // 2]
    return med, med > decke


SPITZE_GRENZE = 0.10             # Abweichung vom Umfeld, ab der geprueft wird
SPITZE_FENSTER = 7               # Tage davor und danach


def entferne_spitzen(reihe, grenze=SPITZE_GRENZE, fenster=SPITZE_FENSTER):
    """Einzelausschlaege AUSWERFEN - nicht glaetten. Gibt die Indizes.

    ⚠️⚠️ GEMESSEN AM 21.09.2026, nicht vermutet: an vier Kalendertagen
    (10.02., 12.03., 27.06., 10.07.) springen 22 bis 39 Symbole
    GLEICHZEITIG, und 25 Prozent der Spruenge landen auf einer exakt
    runden Zahl (1e10, 5e9, 2e9) gegen 7,2 Prozent im uebrigen Verlauf.
    CELR steht tagelang auf 7,15885e9, am 10. und 11.02. auf exakt
    1e10, am 12.02. wieder auf 7,15885e9 - und das viermal im Jahr.

    **Eine Umlaufmenge geht nicht hoch und wieder herunter.** Die
    Quelle meldet an diesen Tagen offenbar die Gesamt-/Maximalmenge
    statt des freien Umlaufs.

    ⚠️ DIE REGEL IST STRUKTURELL, KEIN DATUMSKATALOG. Vier Termine
    aufzuzaehlen waere beim fuenften still veraltet
    (`pruefung-zaehlt-zustaende-auf`). Ausgeworfen wird, was
    gleichzeitig beides ist:

        1 weit vom Umfeld weg  (>= `grenze` gegen den Median der
          `fenster` Tage davor UND danach)
        2 UMGEBEN VON RUHE     (die beiden Umfeldmediane liegen
          untereinander naeher als `grenze`/2)

    Punkt 2 ist der Unterschied zwischen SPITZE und STUFE: ein echter
    Unlock hebt das Niveau danach dauerhaft, dann weichen die beiden
    Mediane voneinander ab und der Punkt BLEIBT. Genau so soll es
    sein - eine Emission ist ein echter Vorgang.

    ⚠️ AUSWERFEN, NICHT ERSETZEN. Ein interpolierter Wert waere eine
    Erfindung; ein fehlender Tag heisst schlicht, dass das Symbol an
    diesem Tag nicht in den Rang eingeht.
    """
    w = [float(x) for x in reihe]
    raus = set()
    for i in range(len(w)):
        vor = [w[j] for j in range(max(0, i - fenster), i)
               if j not in raus and w[j] > 0]
        nach = [w[j] for j in range(i + 1, min(len(w), i + 1 + fenster))
                if w[j] > 0]
        if len(vor) < 3 or len(nach) < 3 or w[i] <= 0:
            continue
        mv = sorted(vor)[len(vor) // 2]
        mn = sorted(nach)[len(nach) // 2]
        if mv <= 0 or mn <= 0:
            continue
        if abs(mn - mv) / mv >= grenze / 2.0:
            continue                       # STUFE - das Niveau hat sich
        bezug = (mv + mn) / 2.0            # geaendert, der Punkt bleibt
        if abs(w[i] - bezug) / bezug >= grenze:
            raus.add(i)
    return raus


MIND_GEMEINSAM = 30              # weniger Tage belegen keine Identitaet
BAND = 0.05                      # 5 % Median-Abweichung im Preis
HOECHSTENS_KANDIDATEN = 6        # Kostendeckel je Kuerzel - wird AUSGEWIESEN


def preisabgleich(binance_tage, d, faktor):
    """Wie gut deckt sich die CoinGecko-Kurve mit der Binance-Kurve?

    Gibt (gemeinsame Tage, Median der relativen Abweichung).
    """
    pr = (d or {}).get("prices") or [] if isinstance(d, dict) else []
    ab = []
    for t, k in pr:
        if not k or k <= 0:
            continue
        tag = dt.datetime.fromtimestamp(
            t / 1000, dt.timezone.utc).date().isoformat()
        b = binance_tage.get(tag)
        if b:
            ab.append(abs(b - k * faktor) / (k * faktor))
    if not ab:
        return 0, None
    ab.sort()
    return len(ab), ab[len(ab) // 2]


def nachzug(ziel, grenze):
    """Die ohne `coin_id` ueber den PREISVERLAUF zuordnen.

    ⚠️⚠️ DAS SIND DIE IM FENSTER GESTORBENEN. Ohne sie ist die Menge
    ueberlebensverzerrt - und genau der Boden der Verteilung fehlt
    (`grundgesamtheit-ist-keine-stellschraube`: die 167 Fehlenden lagen
    im Median -0,6551 unter dem eigenen Schnitt).

    ⚠️ ZUGEORDNET WIRD NUR, WAS EINDEUTIG IST. Passt kein Kandidat oder
    passen zwei, bleibt das Symbol offen und wird ausgewiesen. Raten
    waere schlimmer als auslassen.
    """
    t0 = time.time()
    print("=" * 100)
    print("NACHZUG: DIE EINGESTELLTEN UEBER DEN PREISVERLAUF ZUORDNEN")
    print("=" * 100)
    c = baue(ziel)
    # ⚠️⚠️ AUCH DIE VERWORFENEN. Ein Verwurf heisst "unter dieser
    # coin_id gab es keine brauchbare Reihe" - das kann eine FEHLENDE
    # GROESSE sein oder eine FALSCHE ZUORDNUNG, und die beiden sind am
    # Verwurf nicht zu unterscheiden. Der Preisabgleich unterscheidet
    # sie: findet er eine Kurve, die passt, war es die Zuordnung. Wer
    # nur 'keine coin_id' nachzoege, liesse genau die Faelle liegen,
    # bei denen die Zuordnung schon einmal danebengriff.
    offen = [r[0] for r in c.execute(
        "SELECT symbol FROM abruf_symbol "
        " WHERE urteil IN ('keine coin_id', 'verworfen') ORDER BY symbol")]
    wieso, bstatus = {}, {}
    for sym, u, stx in (c.execute(
            "SELECT symbol, urteil, status FROM abruf_symbol "
            " WHERE urteil IN ('keine coin_id', 'verworfen')")):
        wieso[sym] = u
        bstatus[sym] = stx          # Binance-Status erhalten, nicht raten
    if not offen:
        print("  nichts offen - erst den Vollabruf laufen lassen")
        return 0
    import agent.marktrang as MR
    datei, _sql = MR.MESSBASIS["schnitt"]
    kurse = kurse_aus_messbasis(datei, offen)
    print("  offen: %d (%d ohne coin_id, %d verworfen) · davon mit "
          "Binance-Kurs im Fenster: %d"
          % (len(offen),
             sum(1 for s in offen if wieso.get(s) == "keine coin_id"),
             sum(1 for s in offen if wieso.get(s) == "verworfen"),
             sum(1 for s in offen
                 if len(kurse.get(s, {})) >= MIND_GEMEINSAM)))

    st, liste = hole("%s/coins/list" % CG)
    if not isinstance(liste, list):
        print("  ⚠️ /coins/list Status %s - Nachzug nicht moeglich" % st)
        return 1
    je_kuerzel = {}
    for e in liste:
        je_kuerzel.setdefault((e.get("symbol") or "").upper(), []).append(
            e.get("id"))
    print("  /coins/list: %d Eintraege, %d verschiedene Kuerzel"
          % (len(liste), len(je_kuerzel)))
    print()

    gefunden = leer = mehrdeutig = knapp = 0
    gedeckelt = []
    for n, sym in enumerate(offen if not grenze else offen[:grenze], 1):
        faktor, basis = vervielfacher(sym)
        tage = kurse.get(sym, {})
        if len(tage) < MIND_GEMEINSAM:
            knapp += 1
            print("  %3d/%d  %-12s nur %d Binance-Tage im Fenster - "
                  "nicht pruefbar" % (n, len(offen), sym, len(tage)))
            continue
        kand = je_kuerzel.get(basis, [])
        if len(kand) > HOECHSTENS_KANDIDATEN:
            gedeckelt.append((sym, len(kand)))
        treffer = []
        for cid in kand[:HOECHSTENS_KANDIDATEN]:
            st, d = hole("%s/coins/%s/market_chart?vs_currency=usd&days=%d"
                         "&interval=daily" % (CG, cid, TAGE))
            time.sleep(_PAUSE[0])
            if not isinstance(d, dict):
                continue
            gem, med = preisabgleich(tage, d, faktor)
            if gem >= MIND_GEMEINSAM and med is not None and med <= BAND:
                treffer.append((cid, gem, med, d))
        if len(treffer) == 1:
            cid, gem, med, d = treffer[0]
            reihe, weg, spr, gr = zerlege(sym, d, faktor)
            urteil = speichere(c, sym, cid, bstatus.get(sym),
                               reihe, weg, spr, gr)
            gefunden += 1
            print("  %3d/%d  %-12s [%s] -> %-24s %s  (Preis %.1f %% ueber "
                  "%d Tagen, Faktor %g, %d Punkte)"
                  % (n, len(offen), sym, wieso.get(sym, "?")[:9], cid,
                     urteil, 100 * med, gem, faktor, len(reihe)))
        elif len(treffer) > 1:
            mehrdeutig += 1
            print("  %3d/%d  %-12s MEHRDEUTIG (%d Kandidaten im Band) - "
                  "bleibt offen" % (n, len(offen), sym, len(treffer)))
        else:
            leer += 1
            print("  %3d/%d  %-12s kein Kandidat im Band (%d geprueft)"
                  % (n, len(offen), sym, min(len(kand),
                                             HOECHSTENS_KANDIDATEN)))

    print()
    print("=" * 100)
    print("  zugeordnet %d · kein Treffer %d · mehrdeutig %d · "
          "zu wenig Kurse %d · Dauer %.1f min"
          % (gefunden, leer, mehrdeutig, knapp, (time.time() - t0) / 60.0))
    if gedeckelt:
        print("  ⚠️ Kandidatenliste gedeckelt bei %d: %s"
              % (HOECHSTENS_KANDIDATEN,
                 ", ".join("%s(%d)" % x for x in gedeckelt)))
    r = c.execute("SELECT COUNT(DISTINCT symbol), COUNT(*) "
                  "FROM umlaufmenge").fetchone()
    print("  in der Datei jetzt: %d Symbole · %d Punkte" % r)
    return 0


def pruefe_nenner(ziel):
    """Symbole mit unmoeglichem Umschlag als `nenner falsch` markieren.

    ⚠⚠ KEIN eigener Abruf - der Test benutzt nur, was schon da
    ist: das Binance-Stueckvolumen der Messbasis und die geholte Menge.
    Er ist damit jederzeit und kostenlos wiederholbar.

    ⚠ MARKIERT, NICHT GELOESCHT. Die Reihe bleibt in der Datei; nur
    das Urteil wechselt von `ok` auf `nenner falsch`, und alle Leser
    filtern auf `ok`. Wer nachsehen will, warum ein Symbol fehlt,
    findet den Grund in derselben Zeile.
    """
    import agent.marktrang as MR
    print("=" * 100)
    print("NENNERPRUEFUNG: hat `turnover` irgendwo eine unmoegliche Decke "
          "gerissen?")
    print("=" * 100)
    c = baue(ziel)
    menge = {}
    for sym, tag, w in c.execute(
            "SELECT u.symbol, u.datum, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol a ON a.symbol = u.symbol "
            " WHERE a.urteil = 'ok' AND u.wert > 0"):
        menge.setdefault(sym.upper(), {})[str(tag)[:10]] = float(w)
    if not menge:
        print("  keine Reihen mit Urteil ok")
        return 0
    datei, _sql = MR.MESSBASIS["schnitt"]
    ab = min(t for d in menge.values() for t in d)
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    vol = {}
    for sym, tag, v in m.execute(
            "SELECT symbol, date, volume FROM price_history_ohlc "
            " WHERE date >= ? AND volume > 0", (ab,)):
        s = sym.upper()
        if s in menge:
            vol.setdefault(s, {})[str(tag)[:10]] = float(v)
    m.close()
    print("  geprueft: %d Symbole · Decke %.1f (aus der Verteilung "
          "abgelesen)" % (len(menge), UMSCHLAG_DECKE))
    getroffen, ohne = [], 0
    for sym in sorted(menge):
        med, schlecht = umschlag_verdacht(menge[sym], vol.get(sym, {}))
        if med is None:
            ohne += 1
            continue
        if schlecht:
            getroffen.append((sym, med))
    for sym, med in getroffen:
        cid = c.execute("SELECT coingecko_id FROM abruf_symbol "
                        "WHERE symbol=?", (sym,)).fetchone()
        c.execute("UPDATE abruf_symbol SET urteil='nenner falsch' "
                  " WHERE symbol=?", (sym,))
        print("  ⚠ %-12s Median-Umschlag %.4g - der ganze Bestand "
              "%.0f x am Tag (%s)"
              % (sym, med, med, (cid or ["-"])[0]))
    c.commit()
    print()
    print("  ergebnis: %d markiert · %d ohne genug gemeinsame Tage "
          "(kein Urteil)" % (len(getroffen), ohne))
    r = c.execute("SELECT COUNT(*) FROM abruf_symbol "
                  " WHERE urteil='ok'").fetchone()
    print("  Symbole mit Urteil ok: %d" % r[0])
    return 0


BULK = 120               # ids je `/coins/markets`-Abruf


def taeglich(ziel):
    """EINEN Punkt je Symbol nachtragen - zwei Abrufe statt 332.

    ⚠⚠ WARUM DAS NOETIG IST (2.509-kein-schreiber): die Reihe
    hat keinen Schreiber. CoinGecko gibt zwar 365 Tage rueckwirkend,
    ein spaeterer Vollabruf holt sie also wieder - VERLOREN GEHEN NUR
    DIE SYMBOLE, DIE IN DER ZWISCHENZEIT EINGESTELLT WERDEN. Und genau
    die waren der Grund fuer den Nachzug (Ueberlebensverzerrung). Der
    gemessene Schwund liegt bei rund 15 Prozent im Jahr und trifft
    nicht zufaellig: eingestellt wird, was klein und illiquide ist -
    der Boden der Verteilung.

    ⚠⚠ ZWEI ENDPUNKTE, EINE GROESSE - VOR dem Bau geprueft.
    Der Vollabruf rechnet `Marktkapitalisierung / Preis` aus
    `market_chart`; hier kommt `circulating_supply` aus
    `/coins/markets`. Zwei verschieden ABGELEITETE Werte in EINER
    Reihe waeren derselbe Fehler wie 2.500-ergaenzung-ausgeschlossen,
    nur innerhalb einer Quelle. GEMESSEN an 119 Symbolen: Median-
    Abweichung 0,000 Prozent, einer ueber 1 Prozent (CAKE, ein echter
    Burn). Dieselbe Groesse.

    ⚠ Der Buendelfaktor gilt hier genauso (2.501-buendelpaare).
    ⚠ Der Spitzenfilter NICHT - der braucht Nachbarn und laeuft
    beim LESEN (`menge_neu`), nicht beim Schreiben.
    """
    t0 = time.time()
    print("=" * 100)
    print("TAGESFORTSCHREIBUNG DER UMLAUFMENGE")
    print("=" * 100)
    c = baue(ziel)
    ids = {}
    for sym, cid in c.execute(
            "SELECT symbol, coingecko_id FROM abruf_symbol "
            " WHERE urteil = 'ok' AND coingecko_id IS NOT NULL"):
        ids[sym] = cid
    if not ids:
        print("  nichts fortzuschreiben - erst den Vollabruf laufen "
              "lassen")
        return 1
    heute = dt.date.today().isoformat()
    schon = {r[0] for r in c.execute(
        "SELECT symbol FROM umlaufmenge WHERE datum = ?", (heute,))}
    offen = sorted(s for s in ids if s not in schon)
    print("  bekannte Symbole %d · heute schon da %d · zu holen %d"
          % (len(ids), len(schon), len(offen)))
    if not offen:
        print("  heute ist alles da")
        return 0
    paare = [(s, ids[s]) for s in offen]
    geschrieben = ohne = 0
    for i in range(0, len(paare), BULK):
        teil = paare[i:i + BULK]
        st, d = hole("%s/coins/markets?vs_currency=usd&ids=%s&per_page=250"
                     % (CG, ",".join(x[1] for x in teil)))
        if not isinstance(d, list):
            print("  ⚠ Abruf %d fehlgeschlagen (%s) - beim naechsten "
                  "Lauf erneut" % (i // BULK + 1, st))
            time.sleep(_PAUSE[0])
            continue
        je_id = {e.get("id"): e.get("circulating_supply") for e in d}
        for sym, cid in teil:
            w = je_id.get(cid)
            if not w or float(w) <= 0:
                ohne += 1
                continue
            faktor, _b = vervielfacher(sym)
            c.execute("INSERT OR REPLACE INTO umlaufmenge VALUES (?,?,?)",
                      (sym, heute, float(w) / faktor))
            geschrieben += 1
        c.commit()
        time.sleep(_PAUSE[0])
    print("  geschrieben %d · ohne Wert %d · Abrufe %d · "
          "Dauer %.1f min"
          % (geschrieben, ohne, (len(paare) + BULK - 1) // BULK,
             (time.time() - t0) / 60.0))
    r = c.execute("SELECT COUNT(DISTINCT symbol), COUNT(*), MAX(datum) "
                  "FROM umlaufmenge").fetchone()
    print("  in der Datei: %d Symbole · %d Punkte · bis %s" % r)
    return 0


def main() -> int:
    ziel = _arg("--ziel", ZIEL_VORGABE)
    if "--taeglich" in sys.argv[1:]:
        return taeglich(ziel)
    if "--nachzug" in sys.argv[1:]:
        return nachzug(ziel, int(_arg("--nur", "0") or 0))
    if "--pruefe-nenner" in sys.argv[1:]:
        return pruefe_nenner(ziel)
    grenze = int(_arg("--nur", "0") or 0)
    t0 = time.time()
    print("=" * 100)
    print("VOLLABRUF: HISTORISCHE UMLAUFMENGE (FREE FLOAT) VON COINGECKO")
    print("=" * 100)
    print("  Ziel: %s · %d Tage · Pause adaptiv ab %.1f s"
          % (ziel, TAGE, PAUSE_START))

    import agent.marktrang as MR
    datei, sql = MR.MESSBASIS["schnitt"]
    v1 = {r[0].upper() for r in sqlite3.connect(
        "file:%s?mode=ro" % datei, uri=True).execute(sql)}

    # ---- Wer war im FENSTER handelbar? --------------------------------
    st, info = hole(BINANCE_INFO)
    status = {}
    for s in (info or {}).get("symbols", []):
        if s.get("quoteAsset") == "USDT":
            status[s["baseAsset"].upper()] = s.get("status")
    heute = dt.date.today()
    letzte = {}
    c_mess = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    for sym, d in c_mess.execute(
            "SELECT symbol, MAX(date) FROM price_history_ohlc "
            "GROUP BY symbol"):
        try:
            letzte[sym.upper()] = dt.date.fromisoformat(str(d)[:10])
        except Exception:                                    # noqa: BLE001
            pass
    trading = sorted(s for s in v1 if status.get(s) == "TRADING")
    im_fenster = sorted(
        s for s in v1 if status.get(s) == "BREAK"
        and s in letzte and (heute - letzte[s]).days <= TAGE)
    davor = sorted(
        s for s in v1 if status.get(s) == "BREAK"
        and s in letzte and (heute - letzte[s]).days > TAGE)
    print("  Messmenge V1 %d · TRADING %d · BREAK im Fenster %d · "
          "BREAK davor %d (gehoeren nicht dazu)"
          % (len(v1), len(trading), len(im_fenster), len(davor)))

    # ---- Zuordnung ----------------------------------------------------
    print("  Binance-Ticker holen ...")
    karte, seite = {}, 1
    while seite <= 12:
        st, d = hole("%s/exchanges/binance/tickers?page=%d" % (CG, seite))
        tk = (d or {}).get("tickers") or [] if isinstance(d, dict) else []
        if not tk:
            break
        for t in tk:
            if (t.get("target") or "").upper() == "USDT" and t.get("coin_id"):
                karte[(t.get("base") or "").upper()] = t["coin_id"]
        seite += 1
        time.sleep(_PAUSE[0])
    print("  -> %d Paare mit coin_id" % len(karte))

    c = baue(ziel)
    schon = {r[0] for r in c.execute(
        "SELECT symbol FROM abruf_symbol WHERE urteil IN ('ok','verworfen')")}
    if schon:
        print("  bereits geholt: %d - werden uebersprungen" % len(schon))

    aufgabe = [(s, karte.get(s)) for s in trading + im_fenster
               if s not in schon]
    ohne_id = [s for s, cid in aufgabe if not cid]
    mit_id = [(s, cid) for s, cid in aufgabe if cid]
    print("  zu holen: %d (davon %d ohne coin_id - werden ausgewiesen)"
          % (len(aufgabe), len(ohne_id)))
    for s in ohne_id:
        c.execute("INSERT OR REPLACE INTO abruf_symbol "
                  "(symbol, status, urteil, geholt_am) VALUES (?,?,?,?)",
                  (s, status.get(s), "keine coin_id",
                   dt.datetime.now(dt.timezone.utc).isoformat()))
    c.commit()
    if grenze:
        mit_id = mit_id[:grenze]
    print("  Schaetzung: rund %.0f Minuten bei %.1f s je Abruf"
          % (len(mit_id) * PAUSE_START / 60.0, PAUSE_START))
    print()

    ok = verworfen = 0
    for i, (sym, cid) in enumerate(mit_id, 1):
        st, d = hole("%s/coins/%s/market_chart?vs_currency=usd&days=%d"
                     "&interval=daily" % (CG, cid, TAGE))
        # ⚠️⚠️ EIN ABRUFFEHLER IST KEIN URTEIL. Die erste Fassung schrieb
        # ihn als "verworfen" fort - ein Wiederaufnahme-Lauf haette das
        # Symbol dann uebersprungen und die Luecke waere dauerhaft. Genau
        # die Klasse "fail-soft ist fail-silent".
        if not isinstance(d, dict):
            c.execute("INSERT OR REPLACE INTO abruf_symbol "
                      "(symbol, coingecko_id, status, urteil, geholt_am) "
                      "VALUES (?,?,?,?,?)",
                      (sym, cid, status.get(sym), "abruf %s" % st,
                       dt.datetime.now(dt.timezone.utc).isoformat()))
            c.commit()
            print("  %4d/%d  %-10s ABRUF FEHLGESCHLAGEN (%s) - wird beim "
                  "naechsten Lauf erneut versucht" % (i, len(mit_id), sym, st))
            time.sleep(_PAUSE[0])
            continue
        faktor, _ = vervielfacher(sym)
        reihe, weg, spruenge, groesster = zerlege(sym, d, faktor)
        urteil = speichere(c, sym, cid, status.get(sym),
                           reihe, weg, spruenge, groesster)
        if urteil == "ok":
            ok += 1
        else:
            verworfen += 1
        if i % 25 == 0 or i == len(mit_id):
            print("  %4d/%d  %-10s %-6s Punkte %3d  verworfen %3d  "
                  "Spruenge %2d  (%.0f min)"
                  % (i, len(mit_id), sym, urteil, len(reihe), weg, spruenge,
                     (time.time() - t0) / 60.0))
            print("       Pause aktuell %.1f s" % _PAUSE[0])
        time.sleep(_PAUSE[0])

    print()
    print("=" * 100)
    print("  fertig: %d ok · %d verworfen · %d ohne coin_id · Dauer %.1f min"
          % (ok, verworfen, len(ohne_id), (time.time() - t0) / 60.0))
    r = c.execute("SELECT COUNT(DISTINCT symbol), COUNT(*), MIN(datum), "
                  "MAX(datum) FROM umlaufmenge").fetchone()
    print("  in der Datei: %d Symbole · %d Punkte · %s bis %s" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
