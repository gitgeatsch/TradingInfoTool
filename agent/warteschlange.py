# -*- coding: utf-8 -*-
"""In welcher Reihenfolge die Assets drankommen (14.08.2026).

NUTZEREINWAND, der das erzwungen hat: *"in der Praxis ist eine bestehende
Position bzw. bestimmte Assets wichtiger"* - als Antwort auf meinen Vorschlag,
nach Screening-Rang zu sortieren.

Er hat recht, und der Grund ist einfach: **bei einer Position, die ich halte,
muss ich taeglich entscheiden.** Halten, nachkaufen, reduzieren - das ist eine
echte Frage, jeden Tag. Bei einem Symbol, das ich nicht halte, kann ich warten.

WAS DIESE DATEI NICHT TUT - und das ist der ganze Unterschied zum Vorfilter,
den die alte Kette hatte: sie schliesst NICHTS AUS. Sie sagt "du zuerst", nie
"du nie". Wer heute hinten steht, steht morgen vorn. Ein Ausschluss waere die
Mechanik, die den Deadloop erzeugt hat (98,2 % HALTEN, weil vorher
weggeschnitten wurde, was nie jemand sah).

DIE VIER STUFEN:

    1  eigener Bestand   beim Hebel die OFFENE Hebelposition, bei Spot der
                         Spot-Bestand - taeglich eine echte Entscheidung
    2  anderer Bestand   dasselbe Symbol im jeweils anderen Topf
    3  vorgemerkt        was der Nutzer manuell markiert hat
    4  Screening-Rang    nur REIHENFOLGE, keine Aussage ueber Erfolg
    5  Wartezeit         wer am laengsten kein Urteil hatte

STUFE 2 IST HEUTE LEER, und das steht hier statt in einem Nachtrag: die Tabelle
`watchlist` hat in dieser Datenbank keine Spalten. Es gibt also keinen Ort, an
dem eine Vormerkung stuende. Die Stufe bleibt im Code, damit sie einen Platz
hat, wenn es ihn gibt - sie ist heute schlicht wirkungslos.

ZU STUFE 3, damit es nicht verwechselt wird: der Screening-Score
(`hebel_triggers.score_gesamt`, 36-78) ist NICHT der Regime-Score. Der Regime-
Score ist als Filter gestrichen (E4/12b); dieser hier ist ein deterministischer
Setup-Erkenner und war NIE gegen Ergebnisse gemessen. Deshalb steht er an
DRITTER Stelle und entscheidet nur die Reihenfolge unter denen, zu denen weder
Bestand noch Nutzer etwas gesagt haben.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# FUENF Stufen, nicht vier - Nutzereinwand 14.08.: *"Bei Hebel soll der Hebel
# bestand ganz oben sein."*
#
# Die beiden Bestaende sind NICHT gleichwertig, und welcher oben steht, haengt
# am Instrument. Eine offene Hebelposition hat einen Liquidationspreis: sie kann
# nicht nur schlechter werden, sie kann verschwinden. Bei einem Hebel-Lauf ist
# sie deshalb die dringendste Frage ueberhaupt - dringender als ein Spot-Bestand
# desselben Symbols, der einfach weiter dasteht.
#
# Umgekehrt gilt dasselbe: bei einem Spot-Lauf steht der Spot-Bestand oben.
# Die Regel lautet also nicht "Hebel zuerst", sondern "das eigene Instrument
# zuerst" - und beim Hebel faellt beides zusammen.
EIGENER_BESTAND, ANDERER_BESTAND, VORGEMERKT, RANG, WARTEZEIT = 0, 1, 2, 3, 4


def _bestand_spot(conn) -> set:
    """Der Spot-Bestand aus `holdings`."""
    try:
        return {str(r[0]).upper() for r in conn.execute(
            "SELECT symbol FROM holdings WHERE quantity > 0")}
    except Exception:                                        # noqa: BLE001
        return set()


def _bestand_hebel(conn) -> set:
    """Die OFFENEN Hebelpositionen.

    `status = 'offen'` - NACHGESEHEN, NICHT GERATEN. Meine erste Fassung nahm
    `geschlossen_am IS NULL`, weil die Spalte danach aussah. Die Quelle sagt
    etwas anderes: `db.get_open_hebel_positions()` und
    `backward_tracking.py:4794` fragen beide `status = 'offen'` ab. Beide
    Spalten existieren, und ob sie immer zusammenpassen, weiss niemand -
    also gilt die Definition, die der Rest des Systems benutzt.

    WOHER DIE ZEILEN KOMMEN, und das war die Frage des Nutzers: aus der
    Bitpanda-Abfrage. Der Margin-Positions-Sync laeuft in
    `hebel_screening_job()` und ist von P-8 gedeckt (ohne API-Schluessel wird
    er stillschweigend uebersprungen). Gepruefte Reihenfolge im Job: der Sync
    steht VOR dem Schnitt auf die Rollen-Kette - er bleibt also erhalten, auch
    wenn der Budget-Allocator uebersprungen wird. Ohne das waere diese Tabelle
    fuer immer leer, und der Hebel-Bestand fuer die Warteschlange unsichtbar."""
    try:
        return {str(r[0]).upper() for r in conn.execute(
            "SELECT symbol FROM hebel_positions WHERE status = 'offen'")}
    except Exception:                                        # noqa: BLE001
        return set()


def _bestaende(conn, instrument: str) -> tuple:
    """(eigener, anderer) Bestand - in der Reihenfolge, die das Instrument
    vorgibt.

    NUTZEREINWAENDE 14.08., zwei hintereinander: *"es gibt einen Spot bestand
    und Hebel bestand - also aktiven Hebel"* und dann *"Bei Hebel soll der
    hebel bestand ganz oben sein."*

    Der zweite ist die scharfe Fassung des ersten: es genuegt nicht, beide zu
    kennen - beim Hebel muss der Hebel-Bestand VOR dem Spot-Bestand kommen. Ein
    Symbol, das ich gehebelt halte, kann liquidiert werden; dasselbe Symbol im
    Spot steht einfach weiter da.

    Der ANDERE Bestand faellt nicht weg, er kommt nur danach: wer BTC im Spot
    haelt und ueber einen Hebel-Einstieg nachdenkt, hat dort eine
    Vorgeschichte."""
    spot, hebel = _bestand_spot(conn), _bestand_hebel(conn)
    if str(instrument or "").strip().lower() == "hebel":
        return hebel, spot - hebel
    return spot, hebel - spot


def _vorgemerkt(conn) -> set:
    """Manuell markierte Symbole. Heute leer - siehe Modul-Docstring."""
    try:
        spalten = {r[1] for r in conn.execute("PRAGMA table_info(watchlist)")}
    except Exception:                                        # noqa: BLE001
        return set()
    feld = next((s for s in ("vorgemerkt", "schwerpunkt", "favorit")
                 if s in spalten), None)
    if feld is None:
        return set()
    try:
        return {str(r[0]).upper() for r in conn.execute(
            f"SELECT symbol FROM watchlist WHERE {feld}")}
    except Exception:                                        # noqa: BLE001
        return set()


def _rang(conn) -> dict:
    """Der juengste Screening-Score je Symbol. Hoeher = frueher."""
    try:
        return {str(s).upper(): float(w or 0) for s, w in conn.execute(
            "SELECT symbol, MAX(score_gesamt) FROM hebel_triggers "
            "GROUP BY symbol")}
    except Exception:                                        # noqa: BLE001
        return {}


def _zuletzt(conn) -> dict:
    """Wann jedes Symbol zuletzt ein Urteil der NEUEN Kette hatte.

    Nur die eigene Kette: die Altsignale stammen aus einer anderen Logik, und
    ein Symbol deswegen hinten anzustellen hiesse, es fuer eine Entscheidung zu
    bestrafen, die diese Kette nie getroffen hat."""
    try:
        return {str(s).upper(): str(w or "") for s, w in conn.execute(
            "SELECT symbol, MAX(created_at) FROM signals "
            "WHERE quelle_kette = 'rollen' GROUP BY symbol")}
    except Exception:                                        # noqa: BLE001
        return {}


def sortiere(conn, symbole: list, instrument: str = "spot") -> list:
    """Die Symbole in Bearbeitungsreihenfolge. Nichts faellt weg.

    GIBT IMMER ALLE ZURUECK, in anderer Reihenfolge. Wer kuerzen will, kuerzt
    danach - dann steht die Entscheidung "wir schaffen heute nur N" an EINER
    Stelle und nicht verteilt auf vier Kriterien."""
    if not symbole:
        return []
    eigen, anderer = _bestaende(conn, instrument)
    vorgemerkt = _vorgemerkt(conn)
    rang, zuletzt = _rang(conn), _zuletzt(conn)

    def schluessel(sym: str):
        s = str(sym).upper()
        if s in eigen:
            stufe = EIGENER_BESTAND
        elif s in anderer:
            stufe = ANDERER_BESTAND
        elif s in vorgemerkt:
            stufe = VORGEMERKT
        elif s in rang:
            stufe = RANG
        else:
            stufe = WARTEZEIT
        # Innerhalb einer Stufe: wer am laengsten wartet zuerst, dann der
        # hoehere Rang. Ein Symbol ohne Urteil hat "" und steht damit vorn -
        # das ist gewollt: es war noch nie dran.
        return (stufe, zuletzt.get(s, ""), -rang.get(s, 0.0), s)

    return sorted(symbole, key=schluessel)


def erklaere(conn, symbole: list, anzahl: int = 5,
             instrument: str = "spot") -> list[str]:
    """Warum diese Reihenfolge - fuer das Log, nicht fuer die Mail."""
    eigen, anderer = _bestaende(conn, instrument)
    vorgemerkt, rang = _vorgemerkt(conn), _rang(conn)
    zuletzt = _zuletzt(conn)
    aus = []
    for s in sortiere(conn, symbole, instrument)[:anzahl]:
        u = str(s).upper()
        grund = (f"{instrument}-Bestand" if u in eigen else
                 "anderer Bestand" if u in anderer else
                 "vorgemerkt" if u in vorgemerkt else
                 f"Rang {rang[u]:.0f}" if u in rang else "wartet")
        aus.append(f"{s} ({grund}"
                   + (f", zuletzt {zuletzt[u][:10]}" if zuletzt.get(u) else "")
                   + ")")
    return aus
