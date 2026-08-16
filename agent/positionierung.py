# -*- coding: utf-8 -*-
"""Die Fakten, die der Trader NICHT sieht - Grundlage der Rolle G (16.08.2026).

WOZU. Die zweite Stufe bekam bisher denselben Faktentext wie Rolle BC und
beantwortete dieselbe Frage. Nach der Literatur ist das der Fehlerfall
(*Homogeneous Debate*): teilen zwei Pruefer Modell und Informationsgrenze,
sinkt die epistemische Vielfalt, und das zweite Modell rationalisiert
nachtraeglich statt unabhaengig zu pruefen.

    Gemessen an unseren eigenen Daten: 17x LONG in 2.469 Pruefungen.
    SHORT 1.246, NEUTRAL 1.206. Ein Merkmal, das fast immer denselben Wert
    hat, kann nichts unterscheiden (R-T6).

DIE KONSTRUKTIONSBEDINGUNG. Ein Parameter gehoert zu GENAU EINEM Modell. Was
hier steht, darf NICHT in den Faktentext von BC - sonst ist die zweite Stufe
wieder das, was sie war.

    LLM1 (Rolle BC)  was aus Kursreihe und Depot folgt
    LLM2 (Rolle G)   was AUSSERHALB davon liegt - Positionierung

WAS HIER STEHT UND WAS NICHT. Positionierung heisst: wie sind die anderen
aufgestellt. Open Interest, Finanzierungsrate als Extremwert, Anteil der
Long-Konten. Das ist keine zweite Lesart des Charts - es ist eine Information,
die im Chart nicht steht.

NICHT hier: Nachrichten und Termine. Sie gehoeren ebenfalls zu Rolle G, sind
aber eine eigene Quelle und ein eigenes Vorhaben (Phase IV).

ALLE SAETZE MIT BEZUG, KEINE NACKTE ZAHL. Dieselbe Regel wie in
`lagebeschreibung.py`, und aus demselben Grund: eine Zahl ohne Massstab wird
zertokenisiert und traegt nicht. Die Bestandserhebung vom 16.08. hat fuer die
bestehenden Bloecke 41 Saetze geprueft - keiner trug eine nackte Zahl. Dieser
Block haelt denselben Stand.
"""
from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)

# Wie weit zurueck der Open-Interest-Vergleich reicht. Dieselbe Groesse, die
# `hebel_screening.cfg["oi_lookback_stunden"]` benutzt - dort steht sie als
# Konfiguration, hier als Vorgabe, falls sie nicht lesbar ist.
OI_RUECKBLICK_STUNDEN = 8.0

# Ab wann eine Finanzierungsrate als extrem gilt. NICHT frei gesetzt: es ist
# das Perzentil der EIGENEN Historie, und 90/10 ist die uebliche Grenze fuer
# "aussergewoehnlich" - dieselbe, die `atr_percentile` im Projekt verwendet.
EXTREM_OBEN, EXTREM_UNTEN = 90, 10


def _reihe(conn, symbol: str, spalte: str, grenze: int = 400) -> list:
    try:
        return [r[0] for r in conn.execute(
            f"SELECT {spalte} FROM open_interest_snapshot "
            "WHERE symbol = ? AND exchange = 'binance' "
            f"AND {spalte} IS NOT NULL "
            "ORDER BY fetched_at DESC LIMIT ?", (symbol, grenze))]
    except sqlite3.Error as exc:
        logger.info("Positionierung %s/%s nicht lesbar: %s", symbol, spalte, exc)
        return []


def _perzentil(werte: list, wert: float) -> int | None:
    """Wo steht dieser Wert in seiner eigenen Geschichte?"""
    if not werte or wert is None:
        return None
    kleiner = sum(1 for w in werte if w < wert)
    return int(round(100.0 * kleiner / len(werte)))


def lage(conn, symbol: str) -> dict:
    """Die Positionierungslage - oder ein leeres dict, wenn nichts vorliegt.

    FAIL-SOFT MIT VERMERK: was fehlt, steht unter `fehlt` und wird im Satzbau
    BENANNT. Ein stiller Ausfall waere hier besonders teuer, weil die ganze
    Rolle G auf diesen Zahlen steht - eine leere Antwort saehe aus wie
    'kein Einwand'."""
    sym = str(symbol or "").strip().upper()
    aus: dict = {"symbol": sym, "fehlt": []}

    oi = _reihe(conn, sym, "open_interest")
    fund = _reihe(conn, sym, "funding_rate")
    lang = _reihe(conn, sym, "long_account_pct")

    if oi:
        aus["oi_jetzt"] = oi[0]
        # Der Rueckblick in SCHRITTEN, nicht in Stunden: die Snapshots kommen
        # im 15-Minuten-Takt des Screenings, acht Stunden sind also rund 32.
        n = min(len(oi) - 1, int(OI_RUECKBLICK_STUNDEN * 4))
        if n > 0 and oi[n]:
            aus["oi_aenderung_pct"] = round(100.0 * (oi[0] - oi[n]) / oi[n], 2)
            aus["oi_fenster_stunden"] = round(n / 4.0, 1)
    else:
        aus["fehlt"].append("Open Interest")

    if fund:
        aus["funding_jetzt"] = fund[0]
        aus["funding_perzentil"] = _perzentil(fund, fund[0])
        aus["funding_n"] = len(fund)
    else:
        aus["fehlt"].append("Finanzierungsrate")

    if lang:
        aus["long_anteil_pct"] = round(float(lang[0]), 1)
        aus["long_perzentil"] = _perzentil(lang, lang[0])
    else:
        aus["fehlt"].append("Anteil der Long-Konten")

    # DAS REGIME MIT SEINER DAUER (16.08.2026). Es ist gerechnet und stand
    # bisher in keinem Prompt. Fuer Rolle G gehoert es hierher und NICHT zu
    # Rolle BC: es beschreibt nicht diesen Wert, sondern den Rahmen, in dem
    # jedes Urteil steht - und die Trennung der Informationsgrenzen ist die
    # Konstruktionsbedingung der zweiten Stufe.
    #
    # DIE DAUER IST DER EIGENTLICHE PUNKT. "baer" allein ist ueber alle
    # Signale eines Tages identisch und damit ein konstantes Feld (R-T6);
    # "seit 27 Tagen" macht daraus eine Aussage, die sich bewegt.
    # NICHT AUS EINER TABELLE - es gibt keine. Das Regime steht auf der
    # juengsten Signalzeile, die Dauer rechnet `regime.regime_persistenz_tage()`.
    # Meine erste Fassung fragte `regime_status` ab; die Tabelle existiert
    # nicht, und der Fail-soft haette das stillschweigend als "keine Angabe"
    # gemeldet - richtig gefangen, aber dauerhaft leer.
    try:
        r = conn.execute(
            "SELECT regime FROM signals WHERE regime IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1").fetchone()
        if r and r[0]:
            aus["regime"] = str(r[0])
            # DIE DAUER SEPARAT - faellt sie aus, ist das Regime trotzdem da.
            # Erste Fassung fing beides gemeinsam: die Zeile "Regime baer" UND
            # "keine Angabe zum Marktregime" standen nebeneinander in derselben
            # Ausgabe. Ein Widerspruch, den der Leser nicht aufloesen kann.
            #
            # ⚠️ DIE DAUER KAM IM BETRIEB NIE AN (gefunden 16.08. abends beim
            # Rendern fuer die Parameteruebersicht). `regime_persistenz_tage`
            # liest ueber `get_hebel_regime_tageshistorie()`, und die greift
            # mit `row["tag"]` auf die Spalten zu - das setzt
            # `conn.row_factory = sqlite3.Row` voraus. `rolle_g` oeffnet aber
            # eine gewoehnliche Verbindung. Ergebnis: TypeError, vom breiten
            # `except` verschluckt, und in JEDER Ausgabe stand nur "Regime
            # 'baer'" ohne Dauer.
            #
            # DAS WAR GENAU DER SCHADEN, gegen den die Dauer eingebaut wurde:
            # das Regime allein ist ueber alle Signale eines Tages identisch -
            # ein konstantes Feld (R-T6). Erst "seit 27 Tagen" bewegt sich.
            # Fail-soft ist fail-silent, hier in seiner teuersten Form.
            #
            # DIE ZEILENFABRIK WIRD GELIEHEN, NICHT UEBERNOMMEN. `conn` kann
            # dem Aufrufer gehoeren; sie bleibt hinterher, wie sie war.
            try:
                from agent.krypto.regime import regime_persistenz_tage

                _alt = conn.row_factory
                try:
                    conn.row_factory = sqlite3.Row
                    aus["regime_tage"] = regime_persistenz_tage(conn, str(r[0]))
                finally:
                    conn.row_factory = _alt
            except Exception as exc:                         # noqa: BLE001
                # GEZAEHLT STATT VERSCHLUCKT. Ohne diese Zeile war der Ausfall
                # nur daran zu sehen, dass ein Halbsatz fehlte.
                logger.info("Regime-Dauer fuer %s nicht ermittelbar: %s",
                            sym, exc)
        else:
            aus["fehlt"].append("Marktregime")
    except Exception as exc:                                 # noqa: BLE001
        logger.info("Regime nicht lesbar: %s", exc)
        aus["fehlt"].append("Marktregime")
    return aus


def saetze(e: dict) -> list[str]:
    """Die Positionierung als Aussagen - fuer Rolle G.

    JEDE ZAHL MIT IHREM MASSSTAB. "Die Finanzierungsrate liegt im 96.
    Perzentil der letzten 400 Messungen" traegt; "0.0312 %" traegt nicht."""
    if not e:
        return []
    z: list[str] = []

    if e.get("oi_aenderung_pct") is not None:
        richtung = "gestiegen" if e["oi_aenderung_pct"] > 0 else "gefallen"
        z.append(
            f"Die offenen Kontrakte am Terminmarkt sind in den letzten "
            f"{e['oi_fenster_stunden']:.0f} Stunden um "
            f"{abs(e['oi_aenderung_pct']):.1f} % {richtung}.")

    p = e.get("funding_perzentil")
    if p is not None:
        n = e.get("funding_n", 0)
        wo = ("aussergewoehnlich hoch" if p >= EXTREM_OBEN else
              "aussergewoehnlich niedrig" if p <= EXTREM_UNTEN else
              "im gewohnten Bereich")
        z.append(
            f"Die Finanzierungsrate steht im {p}. Perzentil der letzten {n} "
            f"Messungen dieses Werts - {wo}.")
        # DER HINWEIS AUF DIE UMKEHR, und zwar NUR bei einem Extremwert.
        # Die Praxisliteratur ist hier eindeutig: extremes Funding geht
        # scharfen Umkehrungen oft voraus. Bei einem gewoehnlichen Wert waere
        # derselbe Satz ein konstantes Feld (R-T6) und damit schaedlich.
        if p >= EXTREM_OBEN:
            z.append("Bei so hohen Raten zahlen die Long-Positionen an die "
                     "Short-Positionen; historisch gingen solche Extremwerte "
                     "haeufig scharfen Rueckschlaegen voraus.")
        elif p <= EXTREM_UNTEN:
            z.append("Bei so niedrigen Raten zahlen die Short-Positionen an "
                     "die Long-Positionen; historisch gingen solche "
                     "Extremwerte haeufig scharfen Erholungen voraus.")

    if e.get("long_anteil_pct") is not None:
        lp = e.get("long_perzentil")
        satz = (f"{e['long_anteil_pct']:.0f} % der Konten stehen long")
        if lp is not None:
            satz += f"; das ist das {lp}. Perzentil der eigenen Historie"
        z.append(satz + ".")

    if e.get("regime"):
        satz = f"Der Gesamtmarkt steht im Regime {e['regime']!r}"
        if e.get("regime_tage") is not None:
            satz += f", seit {e['regime_tage']} Tagen ununterbrochen"
        z.append(satz + ".")

    for f in (e.get("fehlt") or []):
        # BENANNT, NICHT VERSCHWIEGEN. Ohne diesen Satz liest das Modell die
        # Abwesenheit als "unauffaellig" - derselbe Fehler, den die
        # Bestandserhebung am 16.08. bei acht Assets gefunden hat.
        z.append(f"Zu diesem Wert liegt keine Angabe vor: {f}.")
    return z
