# -*- coding: utf-8 -*-
"""Cooldown - wann darf dasselbe Asset wieder ein Signal bekommen (13.08.2026).

DER GRUND STEHT IN DEN EIGENEN MESSDATEN dieses Projekts:

    Die Verlustquelle war die Wiederholung - fuenf Symbole trugen 102 % des
    Minus.

Die alte Kette hat daraus Konsequenzen gezogen und fuehrt acht
Cooldown-Einstellungen. **Die Rollen-Kette las keine einzige davon.** Sie lief
bei jedem Durchgang ueber alle Symbole und durfte jedes Mal dasselbe Asset
empfehlen - bei zwei Laeufen am Tag und 250 EUR je Tranche waeren das 500 EUR
taeglich in dasselbe Asset, solange das Modell es mag.

Gefunden bei der vollstaendigen Pruefung der alten Kette am 13.08. (Umbauplan
Kap. 16.4), ausgeloest durch die Nutzerfrage nach den Betraegen.

WARUM HIER UND NICHT IM GATE. Das Gate zaehlt, wo Signale verlorengehen - es
entscheidet nicht, warum. Die Frage "ist dieses Asset gerade gesperrt" ist eine
eigene, und sie braucht die Datenbank; das Gate braucht sie sonst nirgends.

WAS DIESE DATEI NICHT TUT: sie kennt keine Sonderfaelle der alten Kette
(ausgemustert, Re-Evaluierung, Position). Die Rollen-Kette hat diese Zustaende
nicht - sie hier nachzubilden hiesse, Begriffe zu uebernehmen, die zu ihr nicht
gehoeren. Wenn sie gebraucht werden, kommen sie mit einer Begruendung dazu.
"""
from __future__ import annotations

# Die Werte der alten Kette, als Vorgabe. Ueberschreibbar unter
# `budget_allocator.*` - DENSELBEN Schluesseln, damit es nicht zwei Wahrheiten
# gibt (die Kopierfalle, die dieses Projekt schon dreimal erwischt hat).
VORGABE_STUNDEN: dict[str, float] = {
    "spot": 15.0,          # budget_allocator.spot_cooldown_stunden
    "hebel": 3.5,          # budget_allocator.cooldown_stunden
    "absicherung": 15.0,   # kein eigener Wert in der alten Kette - wie Spot,
                           # weil eine Absicherung eher laenger traegt als ein
                           # Hebel-Trade, nicht kuerzer
}

_SCHLUESSEL = {"spot": "spot_cooldown_stunden", "hebel": "cooldown_stunden"}

# Abweichungen je GRUPPE (14.08.). Boersengehandelte Werte bewegen sich
# langsamer als Krypto und handeln nicht rund um die Uhr - ein 15-Stunden-Takt
# fragt dort mehrfach am selben Handelstag dasselbe.
#
# 24 STUNDEN IST KEIN GEMESSENER WERT, sondern die Handelstagslogik: einmal je
# Tag reicht fuer eine Position, die man ueber Wochen haelt. Bei Krypto bleibt
# es bei 15 h, weil dort auch nachts und am Wochenende gehandelt wird.
VORGABE_JE_GRUPPE: dict[str, float] = {
    "aktien": 24.0,
    "rohstoffe": 24.0,
    "themen_etf": 24.0,
    "hedge": 24.0,
}


def stunden(instrument: str, config: dict | None = None,
            gruppe: str | None = None) -> float:
    """Wie lange dasselbe Asset nach einem Signal gesperrt ist.

    Das Spezifischere gewinnt: Konfiguration je Gruppe, dann Konfiguration je
    Instrument, dann Gruppen-Vorgabe, dann Instrument-Vorgabe."""
    i = str(instrument or "").strip().lower()
    g = str(gruppe or "").strip().lower()
    ba = (config or {}).get("budget_allocator") or {}
    je_gruppe = ((config or {}).get("rollen_kette") or {}).get(
        "cooldown_stunden_je_gruppe") or {}
    # DAS SPEZIFISCHERE GEWINNT - und eine GRUPPE ist spezifischer als ein
    # INSTRUMENT (korrigiert 15.08.2026).
    #
    # DER FEHLER, DEN DAS BEHEBT. Die erste Fassung fragte in dieser
    # Reihenfolge: Konfiguration je Gruppe, dann Konfiguration je INSTRUMENT,
    # dann Gruppen-Vorgabe. Weil `budget_allocator.spot_cooldown_stunden` in
    # der config.yaml steht (15), kam die Gruppen-Vorgabe NIE zum Zug:
    #
    #     aktien/rohstoffe/themen_etf   gebaut 24 h, gelaufen 15 h
    #
    # Die 24 Stunden, die ich am 14.08. mit der Handelstagslogik begruendet
    # habe, waren toter Code. Aufgefallen erst bei der Budget-Hochrechnung zum
    # Vollumstieg - im Krypto-Betrieb war der Unterschied unsichtbar, weil
    # Krypto ohnehin 15 h hat.
    #
    # DIE REGEL LAUTET JETZT: erst alles Gruppenspezifische (Konfiguration vor
    # Code), dann alles Instrumentspezifische. Innerhalb derselben
    # Spezifitaet gewinnt weiterhin die Konfiguration gegen den Code - das
    # bleibt.
    if g in je_gruppe:
        return float(je_gruppe[g])
    if g in VORGABE_JE_GRUPPE:
        return float(VORGABE_JE_GRUPPE[g])
    schluessel = _SCHLUESSEL.get(i)
    wert = ba.get(schluessel) if schluessel else None
    if wert is not None:
        return float(wert)
    return float(VORGABE_STUNDEN.get(i, 15.0))


def gesperrt_bis(conn, symbol: str, instrument: str, *,
                 config: dict | None = None, gruppe: str | None = None,
                 jetzt: str | None = None) -> str | None:
    """Bis wann ist `symbol` gesperrt? `None` heisst: frei.

    ZAEHLT NUR SIGNALE DER EIGENEN KETTE. Die Altsignale stammen aus einer
    anderen Logik mit anderem Vokabular; sie hier mitzuzaehlen hiesse, die neue
    Kette fuer Entscheidungen zu sperren, die sie nie getroffen hat.

    JEDES URTEIL SPERRT, nicht nur ein Einstieg - korrigiert am 14.08. nach
    drei Probelaeufen.

    Meine erste Fassung sperrte nur Einstiege, mit der Begruendung "ein
    NICHTS_TUN erzeugt keine Position, also keine Wiederholungsgefahr". Das
    stimmt fuer das RISIKO und ist fuer die KOSTEN falsch: von 25 Urteilen
    waren 19 ein NICHTS_TUN, und die wurden bei jedem Lauf neu erfragt. Lauf 2
    machte deshalb noch 17 Trader-Aufrufe statt 8.

    ZWEI ZWECKE, EINE MECHANIK. Die Wiederholung ist die gemessene
    Verlustquelle (fuenf Symbole trugen 102 % des Minus) - dafuer genuegten
    Einstiege. Der Cooldown traegt seit dem 14.08. aber auch die Kosten, und
    dort zaehlt jede Frage, die wir schon gestellt haben.

    WAS ES BEDEUTET: haben wir vor drei Stunden "nichts tun" geurteilt, fragen
    wir nicht in fuenfzehn Minuten noch einmal. Bei Spot mit 15 h Cooldown und
    einer laengerfristigen Strategie ist das die richtige Antwort.

    Fail-soft: fehlt die Spalte (aeltere Datei), gibt es keine Sperre. Ein
    Cooldown, der wegen eines Schemafehlers ALLES sperrt, waere schlimmer als
    keiner."""
    from datetime import datetime, timedelta, timezone

    try:
        spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
        if "quelle_kette" not in spalten:
            return None
        # NACH INSTRUMENT GETRENNT (14.08.2026) - O-28.
        #
        # DER FUND: der erste Echtbetrieb erzeugte 45 Urteile und KEIN
        # EINZIGES Hebel-Signal. Nicht, weil der Hebel-Durchgang ausfiel -
        # er lief, und wurde vollstaendig vom Cooldown blockiert.
        #
        # `assetklassen.laeufe()` faehrt krypto/spot VOR krypto/hebel, ueber
        # dieselben 43 Symbole. Die Sperre fragte nur nach `symbol` und
        # `quelle_kette`; nach dem Spot-Durchgang war damit JEDES Symbol
        # gesperrt, und der Hebel-Durchgang fand nichts mehr vor.
        #
        # UND DAS IST FACHLICH FALSCH, nicht nur technisch: "soll ich BTC mit
        # Hebel handeln" ist eine andere Frage als "soll ich eine
        # Spot-Tranche nachlegen". Andere Geometrie, andere Kosten, andere
        # Haltedauer - die eine zu beantworten sperrt die andere nicht.
        #
        # DIESELBE UNTERSCHEIDUNG WIE IN DEN TOEPFEN, aus derselben Funktion:
        # `hebel IS NOT NULL`. Eine zweite Definition waere die Kopierfalle.
        from agent import toepfe as TP

        # ⚠️ DIE TOPFTRENNUNG GILT NUR, WO ES ZWEI LAEUFE GIBT (23.08.2026).
        #
        # DER FEHLER, DEN DAS BEHEBT - und er entstand erst durch A1/A2 von
        # heute. `sql_bedingung("spot")` lautet `hebel IS NULL`. Seit die
        # Rechnung wieder Hebelwerte schreibt, FALLEN HEBEL-SIGNALE AUS DER
        # ABFRAGE HERAUS: ein Symbol, das vor einer Stunde ein Hebel-Signal
        # erzeugt hat, gilt als frei und wird alle 15 Minuten neu beurteilt.
        # Nachgestellt und bestaetigt, bevor diese Zeile entstand.
        #
        # WARUM DIE TRENNUNG UEBERHAUPT DA WAR: bis S6b lief Krypto mit ZWEI
        # Laeufen, und der Hebel-Lauf brauchte einen eigenen Topf - sonst
        # sperrte der Spot-Durchgang ihn mit (O-28, 14.08.).
        #
        # ⚠️ SEIT S6b HAT JEDE GRUPPE GENAU EINEN LAUF - geprueft ueber
        # `INSTRUMENTE_JE_GRUPPE`, nicht fuer Krypto angenommen. Ein Lauf
        # stellt eine Frage, und die Sperre gilt der Frage, nicht dem Topf,
        # in dem die Antwort landet.
        #
        # DIE BEDINGUNG BLEIBT STEHEN, NICHT WEIL SIE HEUTE GREIFT, sondern
        # weil sie von selbst zurueckkehrt, sobald eine Gruppe wieder zwei
        # Laeufe bekommt. Ein geloeschter Zweig waere eine Entscheidung ueber
        # etwas, das noch nicht entschieden ist.
        from agent.assetklassen import INSTRUMENTE_JE_GRUPPE as _IJG

        # ⚠️ `gruppe`, NICHT `g`. In `stunden()` heisst die kleingeschriebene
        # Fassung `g`; hier gibt es sie nicht - und der breite Fehlerfang
        # darunter schluckte den NameError, sodass JEDE Gruppe als frei galt.
        # Sechstes Mal dieselbe Falle in zwei Tagen, und wieder still.
        _mehrere_laeufe = len(_IJG.get(
            str(gruppe or "").strip().lower(), ("spot",))) > 1
        bedingung = (TP.sql_bedingung(instrument)
                     if ("hebel" in spalten and _mehrere_laeufe) else "1=1")
        zeile = conn.execute(
            "SELECT MAX(created_at) FROM signals WHERE symbol = ? "
            f"AND quelle_kette = 'rollen' AND {bedingung}",
            (symbol,)).fetchone()
    except Exception:                                        # noqa: BLE001
        return None
    if not zeile or not zeile[0]:
        return None
    try:
        zuletzt = datetime.fromisoformat(str(zeile[0]))
        if zuletzt.tzinfo is None:
            zuletzt = zuletzt.replace(tzinfo=timezone.utc)
        frei_ab = zuletzt + timedelta(hours=stunden(instrument, config, gruppe))
        nun = (datetime.fromisoformat(jetzt) if jetzt
               else datetime.now(timezone.utc))
        if nun.tzinfo is None:
            nun = nun.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return frei_ab.isoformat() if frei_ab > nun else None
