# -*- coding: utf-8 -*-
"""H als SCHATTEN - markieren, nicht sperren (22.08.2026, V1).

⚠️ DIESES MODUL SPERRT NICHTS. Es rechnet ein Merkmal aus, schreibt es weg
und stellt zwei Zeilen fuer die Mail bereit. Kein Signal wird verhindert,
keine Reihenfolge geaendert, kein Budget umgelenkt.

DER GRUND FUER DIESE BAUFORM. H ist auf 523 Binance-USDT-Reihen gemessen
(Kapitel 108-122): +4,5 Punkte Trefferquote gegen eine Zufallsschwelle von
+2,6, bestaetigt in Large (+5,9) und Small (+7,9). Auf der echten Watchlist
stimmt der Punktschaetzer (+4,8) - aber 27 Reihen tragen die noetige Schwelle
(+9,2) NICHT. Der Befund steht also auf fremden Reihen, nicht auf unseren.

    Und die Zahl, um die es geht: H trifft auf 3,3 % der Ankertage zu.
    Ueber 29 Symbole ist das rund EIN Symboltag pro Tag - aus 24
    Eroeffnungen wuerde ungefaehr eine.

Ein Schnitt dieser Groesse wird nicht auf einen Befund von fremden Reihen
gebaut. Deshalb erst der Schatten: vier Wochen mitschreiben, dann pruefen, ob
die von H aussortierten Signale WIRKLICH die schlechteren waren - auf unseren
eigenen. Erst danach die Entscheidung, ob H sperrt, die Reihenfolge bestimmt
oder die Positionsgroesse.

⚠️ NUR LONG. Kapitel 110 hat die gespiegelte Bedingung H' gemessen: sie
spiegelt NICHT. Sie hilft im Bullenmarkt und schadet im Baermarkt, genau wie
H - die Richtung dreht nicht mit. Fuer SHORT ist H damit unbelegt, und
unbelegt heisst hier: `h = None`, nicht `h = False`. Ein Merkmal, das man
nicht kennt, darf nie aussehen wie eines, das man geprueft hat.

DIE DEFINITION IST WOERTLICH DIE DER MESSUNG (`messe_marken.laufe`):

    A  frei      keine Marke ueber dem Kurs mit >= 2 Beruehrungen
                 unterhalb des ZIELS
    B  gedeckt   eine Marke unter dem Kurs mit >= 2 Beruehrungen
                 oberhalb des STOPS
    H  = A und B

⚠️ EIN UNTERSCHIED ZUR MESSUNG BLEIBT, UND ER IST BEABSICHTIGT. Dort standen
Stop und Ziel auf fester Geometrie (k * ATR, CRV 2,0); hier stehen die
ECHTEN Werte des Signals. Das ist die Groesse, die uns interessiert - ob H
auf dem hilft, was wir tatsaechlich handeln. Kapitel 117/118 stuetzen das:
H braucht keine eigene Geometrie, sein Optimum liegt in derselben Ecke wie
das der Basis.

⚠️ DESHALB WERDEN DIE ZUTATEN MITGESCHRIEBEN, nicht nur das Urteil. Preis
und Beruehrungszahl beider Marken stehen in der Zeile; wer H spaeter anders
schneiden will (drei Beruehrungen, ein anderer Abstand), rechnet es aus den
Rohdaten nach, ohne vier Wochen zu verlieren.
"""
from __future__ import annotations

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Dieselbe Zahl wie `messe_marken.MIN_BERUEHRUNGEN` - ein einzelner
# Wendepunkt ist keine Marke.
MIN_BERUEHRUNGEN = 2

# Was auf 523 Reihen gemessen wurde, in Punkten Trefferquote. Steht hier,
# damit die Mail den Befund nennen kann, auf den sie sich beruft.
GEMESSEN = {"vorsprung_punkte": 4.5, "schwelle_punkte": 2.6,
            "reihen": 523, "anteil_traeger": 0.033,
            "kapitel": "108-122"}

_TABELLE = "vorfilter_schatten"


def _tabelle(conn) -> bool:
    try:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {_TABELLE} (
                    id INTEGER PRIMARY KEY,
                    erfasst_am TEXT NOT NULL,
                    signal_id INTEGER,
                    symbol TEXT NOT NULL,
                    assetklasse TEXT,
                    instrument TEXT,
                    ist_short INTEGER,
                    h INTEGER,
                    frei INTEGER,
                    gedeckt INTEGER,
                    grund TEXT,
                    zutaten_json TEXT)""")
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{_TABELLE}_signal "
            f"ON {_TABELLE}(signal_id)")
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.info("Vorfilter-Tabelle nicht anlegbar: %s", exc)
        return False


# ⚠️ AUF WELCHER ANLAGEKLASSE IST H UEBERHAUPT GEMESSEN? Auf genau einer.
# Die 523 Reihen sind Binance-USDT - also Krypto. Fuer Aktien, Rohstoffe,
# Themen-ETF und Hedge ist H nicht etwa unbestaetigt, sondern NIE GEPRUEFT;
# Kapitel 106 hat gezeigt, dass 2 Aktien- und 4 ETF-Reihen dafuer nicht
# reichen. Der Schatten laeuft trotzdem ueber alle Klassen - sonst haben wir
# in vier Wochen wieder nur Krypto-Daten und stehen an derselben Stelle.
# Aber die Mail sagt es dazu.
GEMESSEN_AUF = "krypto"


def bewerte(marken_werte: dict | None, stop_eur, ziel_eur,
            ist_short: bool = False, assetklasse: str = "",
            einstieg_eur=None) -> dict:
    """A, B, H - und die Zutaten. Urteilt ueber das Signal NICHT.

    Gibt `h=None` zurueck, wenn die Frage hier nicht beantwortbar ist:
    bei SHORT (unbelegt, siehe Modulkopf) und wenn Marken, Stop oder Ziel
    fehlen. `None` ist nicht `False` - das eine heisst "wissen wir nicht",
    das andere "geprueft und nein"."""
    aus = {"h": None, "frei": None, "gedeckt": None, "grund": "",
           "widerstand_eur": None, "widerstand_beruehrungen": None,
           "traeger_eur": None, "traeger_beruehrungen": None,
           "stop_eur": stop_eur, "ziel_eur": ziel_eur,
           # ⚠️ NUR FUER DIE MAIL (R2, 31.08.2026). Ohne den Einstieg
           # laesst sich kein ABSTAND angeben, und dann bleiben nur
           # Rohpreise - "Marke bei 0,0234 EUR" sagt einem Leser nichts.
           # Optional, damit kein bestehender Aufrufer bricht.
           "einstieg_eur": einstieg_eur,
           "assetklasse": str(assetklasse or "").lower(),
           "in_gemessener_klasse":
               str(assetklasse or "").lower() == GEMESSEN_AUF}
    if ist_short:
        aus["grund"] = ("SHORT - die gespiegelte Bedingung wurde gemessen "
                        "und traegt nicht (Kapitel 110)")
        return aus
    if not marken_werte:
        aus["grund"] = "keine Marken ermittelt"
        return aus
    try:
        stop = float(stop_eur)
        ziel = float(ziel_eur)
    except (TypeError, ValueError):
        aus["grund"] = "Stop oder Ziel fehlt"
        return aus
    if not (stop > 0 and ziel > 0):
        aus["grund"] = "Stop oder Ziel nicht positiv"
        return aus

    def traegt(m) -> bool:
        return int((m or {}).get("beruehrungen") or 0) >= MIN_BERUEHRUNGEN

    # A - FREIER WEG: keine mehrfach beruehrte Marke unter dem Ziel.
    oben = [m for m in (marken_werte.get("oben") or [])
            if traegt(m) and m.get("preis_eur") is not None
            and float(m["preis_eur"]) < ziel]
    aus["frei"] = not oben
    if oben:
        # Die NAECHSTE am Kurs ist die, auf die er zuerst trifft - dieselbe
        # Wahl wie in der Messung (Kapitel 112), nicht "die staerkste".
        w = min(oben, key=lambda m: float(m["preis_eur"]))
        aus["widerstand_eur"] = float(w["preis_eur"])
        aus["widerstand_beruehrungen"] = int(w.get("beruehrungen") or 0)

    # B - STOP GEDECKT: eine mehrfach beruehrte Marke ueber dem Stop.
    unten = [m for m in (marken_werte.get("unten") or [])
             if traegt(m) and m.get("preis_eur") is not None
             and float(m["preis_eur"]) > stop]
    aus["gedeckt"] = bool(unten)
    if unten:
        t = max(unten, key=lambda m: float(m["preis_eur"]))
        aus["traeger_eur"] = float(t["preis_eur"])
        aus["traeger_beruehrungen"] = int(t.get("beruehrungen") or 0)

    aus["h"] = bool(aus["frei"] and aus["gedeckt"])
    return aus


def saetze(b: dict | None) -> list[str]:
    """Die Zeilen fuer die Mail. FAKTEN, keine Bewertung.

    ⚠️ NEU GEFASST AM 31.08.2026 (R2). Die alte Fassung hatte drei Fehler,
    und der erste ist der schwerste:

      1. SIE WERTETE - und zwar mit einer Aussage, die seither widerlegt
         ist: *"auf 523 fremden Reihen hatten solche Einstiege 4,5 Punkte
         mehr Treffer."* Der Befund war gepoolt gemessen; je Kalendertag
         liegt er bei -1,02 [-2,18 .. +0,14], also bei null (R1).
      2. SIE SPRACH FACHJARGON - "Vorfilter H (Schattenmessung)", "A", "B".
         Der Leser dieser Mail ist der Nutzer, nicht der Messcode.
      3. SIE NANNTE ROHPREISE - "Marke bei 0,0234 EUR (3-mal beruehrt)".
         Nutzervorgabe 31.08.: *"wenn Mailtext, auch fuer mich lesbar
         machen, keine Rohzahlen."* Ein Preis ohne Bezug ist keine
         Information; der ABSTAND ist eine.

    Was bleibt: die Lage der Marken ist eine Tatsache ueber die Gegenwart
    und gehoert in die Mail. Sie ist nur kein Argument fuer oder gegen den
    Trade - genau die Unterscheidung aus CLAUDE.md ("ein Fakt ist keine
    Begruendung").
    """
    if not b:
        return []
    from agent.schreibweise import de

    kopf = "Kursmarken rund um diesen Einstieg"
    if b.get("h") is None:
        return [kopf, "   Hier nicht bestimmbar: %s" % (b.get("grund") or "?")]

    def _abstand(preis) -> str:
        """'3,2 % hoeher' - oder der Preis, wenn der Einstieg fehlt."""
        ein = b.get("einstieg_eur")
        try:
            ein = float(ein)
            preis = float(preis)
        except (TypeError, ValueError):
            return "bei %s EUR" % de(preis, 4)
        if ein <= 0:
            return "bei %s EUR" % de(preis, 4)
        p = 100.0 * (preis - ein) / ein
        return "%s %% %s" % (de(abs(p), 1), "hoeher" if p >= 0 else "tiefer")

    def _mal(n) -> str:
        """'dreimal' statt '(3-mal)' - Zahlwoerter bis zehn."""
        worte = ("null", "ein", "zwei", "drei", "vier", "fuenf", "sechs",
                 "sieben", "acht", "neun", "zehn")
        n = int(n or 0)
        return ("%smal" % worte[n]) if 0 <= n <= 10 else "%d-mal" % n

    if b["frei"]:
        oben = ("   Nach oben ist der Weg bis zum Ziel frei - keine Marke, "
                "die der Kurs schon mehrfach angelaufen hat.")
    else:
        oben = ("   Nach oben liegt eine Marke %s, die der Kurs schon %s "
                "angelaufen hat - noch vor dem Ziel."
                % (_abstand(b["widerstand_eur"]),
                   _mal(b["widerstand_beruehrungen"])))
    if b["gedeckt"]:
        unten = ("   Nach unten liegt eine solche Marke %s - zwischen "
                 "Einstieg und Stop."
                 % _abstand(b["traeger_eur"]))
    else:
        unten = ("   Nach unten liegt bis zum Stop keine solche Marke.")

    # ⚠️ DER SCHLUSSSATZ IST DER KERN VON R2. Er sagt, WOFUER die Zeilen da
    # sind - und wofuer nicht. Ohne ihn liest sie jeder als Argument.
    # ⚠️ "bestimmt den Stop" WAERE ZU STARK. Der Strukturboden ist eine
    # UNTERGRENZE und greift gemessen bei 1,05 % der Anker
    # (`pruefe_strukturstop.py`); sonst gewinnt der Rausch- oder
    # ATR-Boden. "Nie enger als" ist die genaue Aussage.
    schluss = ("   Das ist eine Beobachtung, keine Bewertung: gemessen ueber "
               "609.527 Einstiege sagt die Lage dieser Marken nichts darueber, "
               "wie der Handel ausgeht. In die Stopsetzung geht sie ein - der "
               "Stop wird nie enger gesetzt als die naechste Marke darunter.")
    zeilen = [kopf, oben, unten, schluss]
    # ⚠️ AUSSERHALB VON KRYPTO IST DAS KEINE SCHWAECHERE AUSSAGE, SONDERN
    # GAR KEINE. Die gemessenen Reihen sind Binance-USDT. Der Satz oben
    # ("sagt nichts") stammt von dort und darf nicht als geprueftes Urteil
    # ueber Aktien oder ETF gelesen werden - derselbe Fehler wie Kap. 109.
    if not b.get("in_gemessener_klasse"):
        zeilen.append(
            "   Auf %s wurde das nie gemessen - hier ist es nur eine "
            "Beschreibung der Lage, ohne jeden Befund dahinter."
            % ((b.get("assetklasse") or "dieser anlageklasse").capitalize()))
    return zeilen


def schreibe(conn, *, symbol: str, bewertung: dict,
             signal_id: int | None = None, assetklasse: str = "",
             instrument: str = "", jetzt: str | None = None) -> bool:
    """Eine Schattenzeile. Faellt sie aus, fehlt ein Messpunkt - nie ein
    Signal; deshalb faengt sie breit ab und meldet nur."""
    from datetime import datetime, timezone

    if conn is None or not bewertung or not _tabelle(conn):
        return False
    zutaten = {k: bewertung.get(k) for k in
               ("widerstand_eur", "widerstand_beruehrungen", "traeger_eur",
                "traeger_beruehrungen", "stop_eur", "ziel_eur")}
    try:
        conn.execute(
            f"INSERT INTO {_TABELLE} (erfasst_am, signal_id, symbol, "
            f"assetklasse, instrument, ist_short, h, frei, gedeckt, grund, "
            f"zutaten_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (jetzt or datetime.now(timezone.utc).isoformat(),
             int(signal_id) if signal_id else None, str(symbol).upper(),
             str(assetklasse or ""), str(instrument or ""),
             1 if bewertung.get("stop_eur") is not None
             and "SHORT" in (bewertung.get("grund") or "") else 0,
             None if bewertung.get("h") is None else int(bewertung["h"]),
             None if bewertung.get("frei") is None
             else int(bewertung["frei"]),
             None if bewertung.get("gedeckt") is None
             else int(bewertung["gedeckt"]),
             str(bewertung.get("grund") or ""),
             json.dumps(zutaten, ensure_ascii=False, default=float)))
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.info("Vorfilter %s nicht schreibbar: %s", symbol, exc)
        return False


def stand(conn) -> dict:
    """Wie weit ist die Schattenmessung? Fuer den NB-Export.

    ⚠️ MELDET GESUNDHEIT, NICHT NUR WACHSTUM (Methodik 2.57). Deshalb der
    letzte Lauf einzeln und die Zahl der nicht bestimmbaren Faelle - eine
    reine Gesamtzahl waere gewachsen, auch wenn `h` seit Tagen nur noch
    `NULL` ist."""
    try:
        n = conn.execute(f"SELECT COUNT(*) FROM {_TABELLE}").fetchone()[0]
        je = {("h" if r[0] == 1 else "nicht_h" if r[0] == 0
               else "nicht_bestimmbar"): r[1] for r in conn.execute(
            f"SELECT h, COUNT(*) FROM {_TABELLE} GROUP BY 1")}
        spanne = conn.execute(
            f"SELECT MIN(erfasst_am), MAX(erfasst_am), "
            f"COUNT(DISTINCT substr(erfasst_am, 1, 10)) "
            f"FROM {_TABELLE}").fetchone()
        aus = {"zeilen": n, "je_urteil": je,
               "erste": spanne[0], "letzte": spanne[1], "tage": spanne[2],
               "je_tag": {r[0]: r[1] for r in conn.execute(
                   f"SELECT substr(erfasst_am,1,10), COUNT(*) FROM {_TABELLE}"
                   f" GROUP BY 1 ORDER BY 1 DESC LIMIT 14")},
               "ohne_signal_id": conn.execute(
                   f"SELECT COUNT(*) FROM {_TABELLE} "
                   f"WHERE signal_id IS NULL").fetchone()[0],
               "hinweis": ("V1 schreibt nur mit. Die Auswertung braucht "
                           "aufgeloeste Signale - ohne signal_id ist eine "
                           "Zeile fuer den Vergleich verloren.")}
        # ⚠️ WARUM NICHT, NICHT NUR WIEVIELE (23.08.2026).
        #
        # DER ANLASS WAR EINE FALSCHE AUSSAGE VON MIR. Der Export meldete
        # "51 Zeilen, 49 nicht_h, 0 h", und ich habe daraus geschlossen, H
        # wuerde "die Kette schliessen". Der Nutzer hat widersprochen, und er
        # hatte recht: `h=True` ist auf echten Marken problemlos erreichbar -
        # nachgeprueft. Die Zahl allein sagt nichts darueber, WORAN es lag.
        #
        # H = A und B. Faellt es aus, gehoert dazu, WELCHE der beiden Haelften
        # fehlte - "kein freier Weg" ist etwas anderes als "kein Traeger ueber
        # dem Stop", und beides etwas anderes als "keine Marken ermittelt".
        aus["je_haelfte"] = {r[0]: r[1] for r in conn.execute(
            f"SELECT CASE WHEN h = 1 THEN 'H erfuellt' "
            f"            WHEN frei = 1 AND gedeckt = 0 THEN 'nur A: Weg frei,"
            f" kein Traeger ueber dem Stop' "
            f"            WHEN frei = 0 AND gedeckt = 1 THEN 'nur B: Traeger "
            f"da, Widerstand unter dem Ziel' "
            f"            WHEN frei = 0 AND gedeckt = 0 THEN 'weder noch' "
            f"            ELSE 'nicht bestimmbar' END, COUNT(*) "
            f"FROM {_TABELLE} GROUP BY 1 ORDER BY 2 DESC")}
        aus["je_grund"] = {(r[0] or "(ohne Grund)"): r[1] for r in
                           conn.execute(
            f"SELECT grund, COUNT(*) FROM {_TABELLE} "
            f"WHERE h IS NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 8")}
        aus["je_instrument"] = {f"{r[0] or '?'}/{r[1] or '?'}": r[2]
                                for r in conn.execute(
            f"SELECT assetklasse, instrument, COUNT(*) FROM {_TABELLE} "
            f"GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 8")}
        if not n:
            aus["WARNUNG"] = (
                "KEINE Zeile. Der Vorfilter-Schatten schreibt nicht - jeder "
                "Tag ohne Zeile verschiebt die Entscheidung um einen Tag.")
        return aus
    except sqlite3.Error as exc:
        return {"nicht_verfuegbar": str(exc),
                "WARNUNG": "Tabelle fehlt - der Schatten hat nie geschrieben."}
