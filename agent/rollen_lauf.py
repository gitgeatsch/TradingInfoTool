# -*- coding: utf-8 -*-
"""B1 - DER EINE ORT, AN DEM DIE ROLLEN-KETTE ZUSAMMENGESETZT WIRD.

DIE LUECKE, DIE ER SCHLIESST. Die Gesamtpruefung vom 13.08. hat gezaehlt: alle
15 neuen Module haben NULL Betriebsaufrufer. Zwei hingen nicht einmal
innerhalb der Kette - `toepfe` liefert einen Deckel, den
`entscheidungsrechnung` als Parameter erwartet, und `faktenblock_quellen`
speist die Mail. Es gab niemanden, der sie haette verbinden koennen.

DREI BETRIEBSARTEN, VON ANFANG AN EINGEBAUT - nicht nachtraeglich:

    trocken   KEIN Modellaufruf, KEIN Schreiben, KEINE Mail. Laeuft auf
              aufgezeichneten Antworten. Findet Verdrahtungsfehler, fehlende
              Spalten, Abstuerze - und kostet nichts.
    probe     echte Modellaufrufe, Schreiben in die UEBERGEBENE Verbindung,
              Mail wird GEBAUT aber nicht verschickt.
    scharf    wie probe, und die Mail geht raus.

WARUM DER SCHALTER VON ANFANG AN DA IST. Ein Weg, den man erst nachtraeglich
absichert, ist in der Zwischenzeit ungesichert - und die Zwischenzeit ist
genau die Phase, in der man ihn am meisten braucht. Von den drei Fehlern, die
die Gesamtpruefung fand, haette ein Trockenlauf zwei sofort gezeigt: die Mail
haette "Kein Einstieg geplant" gedruckt, und das Schreiben waere am Vokabular
gescheitert. Dafuer braucht es kein einziges Modell.

DIE VERBINDUNG WIRD UEBERGEBEN, NIE HIER GEOEFFNET. Wer diesen Lauf startet,
entscheidet, auf welche Datenbank er wirkt. Eine Vorgabe waere ein stiller
Zugriff auf die Produktivdatei - und diese Kette SCHREIBT.

WAS ER NICHT TUT: er entscheidet nichts. Jede Bewertung liegt in ihrem Modul;
hier steht nur die Reihenfolge und die Frage, was ein Fehlschlag bedeutet.
"""
from __future__ import annotations

import json as _json
import logging
from datetime import datetime, timezone

# ⚠️ AUF MODULEBENE, UND ZWAR MIT EINDEUTIGEM NAMEN (S6b, 22.08.2026).
#
# `assetklassen` ist ein Blattmodul ohne Rueckbezug auf diese Datei - ein
# Import hier ist gefahrlos. Er steht auf Modulebene, weil ein Import INNEN
# nach der Verwendung stehen kann, ohne dass es auffaellt: genau das ist mir
# beim Bauen von S6b zweimal passiert.
#
# ⚠️ UND NICHT `_AK`. Der Name gehoert in `_ein_asset` bereits
# `anlass_kalender`; ein zweiter Traeger desselben Kuerzels waere die Falle
# aus dem Memory ("dreimal in zwei Tagen"), und der breite Fehlerfang haette
# den UnboundLocalError still geschluckt.
from agent import assetklassen as _AKL

logger = logging.getLogger(__name__)


class _KeinHBeiAkkumulation(Exception):
    """H wird bei `akkumulation` uebersprungen - kein Fehler, sondern die Regel.

    Eine eigene Ausnahme statt eines `if`-Zweigs, damit der bestehende
    Fehlerfang darunter unveraendert bleibt und die beiden Faelle im Log
    unterscheidbar sind: uebersprungen gegen ausgefallen."""

TROCKEN, PROBE, SCHARF = "trocken", "probe", "scharf"
BETRIEBSARTEN = (TROCKEN, PROBE, SCHARF)


# Die BEREICHE, in denen gelaufen werden kann - nicht die Assetklassen.
#
# KORREKTUR 14.08.: hier stand dasselbe Tupel mit dem Etikett "Klassen", und
# darin "hedge". Hedge IST KEINE ASSETKLASSE - die Watchlist kennt nur krypto,
# aktien, rohstoffe und etf; DBPK und 3QSS stehen als `etf` darin. Genau dieser
# Fehler hat am 06.08. schon einmal zugeschlagen: ein Filter auf eine
# Assetklasse "hedge", die es nicht gibt, liess beide Instrumente aus.
#
# `agent/assetklassen.py` haelt die Zuordnung jetzt an EINER Stelle; diese
# Liste hier ist nur noch die Menge der gueltigen BEREICHE.
KLASSEN = ("krypto", "aktien", "rohstoffe", "themen_etf", "hedge")


def _bereich(assetklasse: str, instrument: str) -> str:
    """Der Faktenblock-Bereich. Nur Krypto ist nach Instrument getrennt.

    `faktenblock.ZUSATZ_JE_BEREICH` fuehrt `krypto_spot` und `krypto_hebel`
    getrennt (Finanzierung und Liquidation gibt es nur beim Hebel), die uebrigen
    Klassen als EINEN Bereich. Diese Funktion bildet genau das ab - statt den
    Namen an zwei Stellen zusammenzusetzen und darauf zu hoffen."""
    return f"krypto_{instrument}" if assetklasse == "krypto" else assetklasse


def _kostenklasse(assetklasse: str) -> str:
    """Krypto rechnet in Prozent, alles andere hat eine Fixgebuehr.

    Der Unterschied ist nicht kosmetisch: die Fixgebuehr macht die Kosten
    POSITIONSGROESSEN-ABHAENGIG. Bei 200 EUR liegt der Breakeven um ueber fuenf
    Prozentpunkte hoeher als bei 1.000 EUR - bei Krypto kuerzt sich der Betrag
    heraus."""
    return "krypto" if assetklasse == "krypto" else "boerse"


class LaufAbgebrochen(RuntimeError):
    """Der Lauf kann nicht sinnvoll fortgesetzt werden."""


def _tage_bis(datum_text, ab_tag: str | None) -> int | None:
    """Aus dem DATUM des Modells die TAGE der Rechnung.

    GEFUNDEN IM ERSTEN TROCKENLAUF (13.08.), und genau dafuer ist er da: das
    Modell liefert `umgeworfen_bis` als Datum ("2026-09-01"),
    `entscheidungsrechnung.rechne()` erwartet `umgeworfen_tage` als Zahl. Zwei
    Pakete, zwei Einheiten, und niemand dazwischen - bis es diesen Ort gab.

    Ein Datum in der Vergangenheit gibt None statt einer negativen Zahl: eine
    abgelaufene Frist ist keine Haltedauer, sondern ein Fall fuer den
    Ausstieg."""
    from datetime import date

    if not datum_text:
        return None
    try:
        ziel = date.fromisoformat(str(datum_text)[:10])
        start = date.fromisoformat(str(ab_tag)[:10]) if ab_tag else date.today()
    except ValueError:
        return None
    tage = (ziel - start).days
    return tage if tage > 0 else None


def _fuehrung_zu(ergebnis: dict, symbol: str, instrument: str) -> dict:
    """Die Ausstiegsfuehrung zu DIESEM Symbol und DIESEM Instrument.

    DIE EINE STELLE, an der nachgeschlagen wird - drei Aufrufer teilen sie
    sich: die Sperre gegen einen Einstieg auf faelligem Ausstieg, die Mail und
    die Verkaufssammlung. Vorher schlug jede fuer sich nach, und zwar nur nach
    SYMBOL.

    WARUM DAS NICHT REICHTE (15.08.2026). Die Liste enthaelt eine Zeile je
    SIGNAL, nicht je Position. TURBO stand an diesem Tag zweimal darin - einmal
    Spot, einmal Hebel -, VIRTUAL ebenfalls. Wer nur nach Symbol nachschlaegt,
    bekommt, was zufaellig zuletzt geschrieben wurde, und die Mail zeigt unter
    "Bestehende Position" womoeglich die des anderen Instruments.

    STRENG, OHNE RUECKFALL AUF DAS ANDERE INSTRUMENT. Ein Hebel-Lauf, der die
    Spot-Position als "bestehende Position" zeigt, ist genau die Verwechslung,
    die am 15.08. schon den Bestandsblock getroffen hat. Was auf der anderen
    Seite liegt, sagt `rollen_eingabe.gegenbestand_satz()` - benannt, aber
    nicht als eigene Position ausgegeben."""
    return ((ergebnis.get("fuehrung") or {})
            .get((str(symbol).upper(), str(instrument))) or {})


def _marke_am_stop(bloecke: dict | None, ist_short: bool) -> float | None:
    """Die Marke auf der STOPSEITE - Preis in EUR, sonst None.

    S2 des Umbauplans Kapitel 90 (18.08.2026). Bei LONG ist das die naechste
    UNTERSTUETZUNG, bei SHORT der naechste WIDERSTAND - also jeweils die
    ANDERE Marke als bei `_marke_im_weg`, die dem ZIEL im Weg steht.

    ⚠️ SIE DARF NICHT DENSELBEN WEG NEHMEN. `rechne(widerstand=...)` geht an
    `_ziel()` und wuerde den Widerstandsdeckel wieder scharf schalten - der
    wurde am 17.08. gemessen und verworfen (44 von 44 Symbolen gedeckelt,
    98 % unter CRV 0,5). Deshalb ein eigener Parameter, der NUR den Stop
    betrifft.

    LIEST, RECHNET NICHT - dieselbe Quelle wie der Satz in der Mail."""
    m = ((bloecke or {}).get("_marken_werte") or {}).get(
        "widerstand" if ist_short else "unterstuetzung")
    if not m or not m.get("preis_eur"):
        return None
    return float(m["preis_eur"])


def _marke_im_weg(bloecke: dict | None, ist_short: bool) -> tuple | None:
    """Die Marke zwischen Kurs und Ziel - (Preis in EUR, Beruehrungen).

    Bei LONG ist das der naechste WIDERSTAND, bei SHORT die naechste
    UNTERSTUETZUNG: `entscheidungsrechnung._ziel()` will die Marke, die
    dem Ziel im Weg steht, und das Ziel liegt bei SHORT unten.

    `None`, wenn keine da ist - dann greift das mechanische Ziel, und die
    Klammer "kein Widerstand in Reichweite" stimmt dann auch.

    LIEST, RECHNET NICHT. Die Werte stehen in `_marken_werte`, das
    `lagebeschreibung.geteilt()` aus DERSELBEN Ermittlung liefert wie den
    Satz in der Mail. Sie hier neu zu bestimmen waere die zweite Stelle,
    an der beide auseinanderlaufen koennen."""
    m = ((bloecke or {}).get("_marken_werte") or {}).get(
        "unterstuetzung" if ist_short else "widerstand")
    if not m or not m.get("preis_eur"):
        return None
    return (float(m["preis_eur"]), int(m.get("beruehrungen") or 1))


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


# Wie viele Symbole am Ankertag eine Kerze haben muessen. 0,6 ist bewusst
# grosszuegig: die Schranke soll den TOTALAUSFALL abfangen, nicht bei jedem
# fehlenden Kleinwert anhalten.
MINDEST_DECKUNG = 0.6

# Wie lange ein Lagebild wiederverwendet wird. Nutzerentscheidung 14.08.:
# drei Stunden, nicht acht - es speist JEDEN Trader-Aufruf in seinem Fenster.
LAGEBILD_HALTBAR_STUNDEN = 3.0

# Nach wie vielen Aufrufen IN FOLGE ohne Ergebnis ein Lauf aufgibt.
#
# DER FALL, DER DAS ERZWUNGEN HAT (14.08.2026, erster Betriebstag). Der
# Hebel-Topf war durch Schattenbuchungen gefuellt; jedes Symbol bekam damit
# Betrag 0 EUR und fiel an der Stufe "geometrie" heraus - NACH dem
# Modellaufruf. Weil ein so verlorenes Symbol keine Zeile schreibt, griff auch
# der Cooldown nie, und der naechste Lauf fragte dieselben vierzehn wieder.
#
#     698 Modellaufrufe fuer 46 Urteile, alle 15 Minuten von vorn.
#     Ueber Nacht waeren es rund 3.900 gewesen.
#
# ACHT IST BEWUSST GROSSZUEGIG. Ein Lauf ueber 43 Symbole darf durchaus eine
# Handvoll Fehlschlaege haben - schlechte Datenlage, ein Modell, das einmal
# Unsinn liefert. Acht IN FOLGE sind kein Zufall mehr, sondern ein Zustand:
# etwas Systematisches verhindert jedes Ergebnis, und jeder weitere Aufruf
# bezahlt denselben Fehler noch einmal.
#
# WAS ER NICHT TUT: er verhindert den Fehler nicht. Er begrenzt, was er
# kostet. Die Ursache steht danach im Gate - was sie beim ersten Mal auch tat,
# nur hat niemand rechtzeitig hingesehen.
LEERLAUF_ABBRUCH = 8


def _ankertag(reihen: dict, mindest_deckung: float = MINDEST_DECKUNG,
              blick_tage: int = 10) -> tuple:
    """Der Tag, auf dem der Lauf ankert - und wie gut er gedeckt ist.

    DER FEHLER, DEN DAS BEHEBT (15.5b). Vorher stand hier schlicht das MAXIMUM
    ueber alle Symbole. Damit setzt EIN einziges Symbol den Anker fuer alle -
    aktualisiert eine Quelle und 44 nicht, faellt der ganze Rest an der
    Faktenstufe heraus, und der Lauf sieht aus wie ein ruhiger Tag statt wie
    ein Datenausfall.

    GEMESSEN AM 13.08. am echten Bestand:

        2026-07-19   20 von 45  (44 %)   <- das Maximum, und der alte Anker
        2026-07-17   29 von 45  (64 %)
        2026-07-13   44 von 45  (98 %)

    IM GESUNDEN BETRIEB AENDERT SICH NICHTS. Sind alle Reihen aktuell, ist der
    juengste Tag zu 100 % gedeckt und wird gewaehlt - genau wie vorher. Die
    Regel greift nur, wenn sie gebraucht wird.

    LIEBER EINEN TAG AELTER ALS EINE HANDVOLL SYMBOLE. Ein Lauf ueber 44 Assets
    auf vorgestrigen Kursen sagt mehr als einer ueber 20 auf gestrigen - und
    vor allem sagt er nicht faelschlich, es sei nichts los gewesen.

    Gibt `(tag, gedeckt, gesamt)` zurueck; `tag` ist None, wenn kein Tag im
    Blickfenster die Schranke erreicht - dann bricht der Aufrufer ab."""
    if not reihen:
        return None, 0, 0
    gesamt = len(reihen)
    kandidaten = sorted({k.date for r in reihen.values()
                         for k in r[-blick_tage:]}, reverse=True)
    bester = (None, 0)
    for tag in kandidaten:
        gedeckt = sum(1 for r in reihen.values()
                      if any(k.date == tag for k in r[-blick_tage:]))
        if gedeckt > bester[1]:
            bester = (tag, gedeckt)
        if gedeckt >= mindest_deckung * gesamt:
            return tag, gedeckt, gesamt
    # NICHTS ERREICHT DIE SCHRANKE - der beste Tag wird trotzdem GENANNT, damit
    # die Fehlermeldung eine Zahl hat statt nur ein "zu wenig".
    return None, bester[1], gesamt


def fuehre_lauf(*, conn, reihen: dict, symbole: list,
                betriebsart: str = TROCKEN,
                instrument: str = "spot",
                strategie: str = "einstieg",
                datum: str | None = None,
                client=None, modell: str | None = None,
                antworten: dict | None = None,
                config: dict | None = None,
                db: str = "data/tradinginfotool.db",
                versand=None, zai_client=None,
                assetklasse: str = "krypto",
                max_aufrufe: int | None = None) -> dict:
    """Ein vollstaendiger Durchgang ueber alle Symbole.

    `antworten` ist die Aufzeichnung fuer den Trockenlauf:
    `{"lagebild": {...}, "befund": {symbol: {...}}}`. Fehlt sie dort, wird das
    Symbol als Fehlschlag der Stufe gezaehlt - NICHT uebersprungen. Ein
    Trockenlauf, der stillschweigend weniger prueft, als er behauptet, ist
    schlimmer als keiner.

    Gibt `{"durchlauf": ..., "signale": [...], "mails": [...], "z1": {...}}`
    zurueck."""
    if betriebsart not in BETRIEBSARTEN:
        raise LaufAbgebrochen(f"unbekannte Betriebsart {betriebsart!r} - "
                              f"erlaubt {BETRIEBSARTEN}")
    if betriebsart != TROCKEN and client is None:
        raise LaufAbgebrochen(
            f"Betriebsart {betriebsart!r} braucht einen Modell-Client. Ohne ihn "
            f"waere es ein Trockenlauf, der sich als echter ausgibt.")
    if conn is None:
        raise LaufAbgebrochen(
            "ohne Verbindung kein Lauf - sie wird uebergeben, nie hier "
            "geoeffnet: diese Kette schreibt.")

    from agent import (ausstiegsrechnung as AR, entscheidungsrechnung as ER,
                       faktenblock as FB, faktenblock_quellen as FQ,
                       gegenpruefer_rollen as Z1, rolle_analyst as RA,
                       rolle_trader as RT, rollen_eingabe as RE,
                       rollen_gate as RG, signal_abbildung as SA,
                       signal_mail as SM, toepfe as TO, trefferbilanz as TB,
                       wiederholung as WH, zweite_meinung as ZM,
                       betraege as BE, verkaufsrechnung as VK2)
    from agent.empfehlung_vertrag import EmpfehlungUngueltig
    from agent.handelsauftrag import (AuftragUngueltig,
                                     pruefe as pruefe_auftrag,
                                     strategie_fuer as HA_STRAT)

    # DER AUFTRAG WIRD EINMAL GEPRUEFT, NICHT JE ASSET (13.08.). Vorher stand
    # hier fest `("spot", "einstieg")` - ein Hebel-Lauf war damit gar nicht
    # moeglich, obwohl Paket 13 alles dafuer gebaut hatte. Die Pruefung gehoert
    # VOR die Schleife: ein unvorgesehenes Paar soll den Lauf abbrechen, nicht
    # vierzigmal dasselbe melden.
    try:
        instrument, strategie = pruefe_auftrag(instrument, strategie)
    except AuftragUngueltig as exc:
        raise LaufAbgebrochen(f'Auftrag ungueltig: {exc}') from exc

    # DIE ASSETKLASSE WIRD EINMAL GEPRUEFT, wie der Auftrag. Ein Tippfehler
    # soll den Lauf abbrechen und nicht vierzigmal in einen unbekannten
    # Faktenblock-Bereich laufen.
    assetklasse = str(assetklasse or "").strip().lower()
    if assetklasse not in KLASSEN:
        raise LaufAbgebrochen(
            f"Assetklasse {assetklasse!r} unbekannt - erlaubt {KLASSEN}")
    ergebnis = {"betriebsart": betriebsart, "signale": [], "mails": [],
                "fehler": [], "assetklasse": assetklasse}
    # EINMAL JE LAUF, nicht je Asset - 45 Symbole waeren sonst 45 Abfragen ueber
    # dieselbe Tabelle. Dass die Bilanz waehrend des Laufs nicht mitwaechst, ist
    # richtig so: alle Assets eines Durchgangs sollen gegen denselben
    # Kenntnisstand bewertet werden, sonst haenge das Urteil an der Reihenfolge.
    # DIE DETERMINISTISCHE AUSSTIEGSFUEHRUNG, einmal je Lauf.
    #
    # WOFUER SIE HIER GEBRAUCHT WIRD. Am 14.08. liefen fuer BTC zwei
    # Ausstiegswege parallel: der taegliche 7:15-Job (Trailing, Ziel, Frist)
    # und das REDUZIEREN aus dem 15-Minuten-Lauf. Getrennt verschickt sehen die
    # beiden aus wie zwei Meinungen zum selben Symbol; nebeneinander sind sie
    # zwei Befunde auf verschiedene Fragen. Deshalb traegt die Verkaufsmail den
    # Stand der Fuehrung mit.
    #
    # REIN LESEND UND OHNE MODELLAUFRUF - es kostet kein Kontingent.
    ergebnis["fuehrung"] = {}
    # AUSSERHALB DES `try`, weil `_wl` weiter unten an `_ein_asset` geht
    # (15.08.2026). Stuende die Zuweisung im Block und scheiterte der Import
    # darueber, waere der Name spaeter nicht definiert - ein NameError, den der
    # breite Fehlerfang je Symbol schlucken wuerde.
    _wl = None
    try:
        from agent.krypto.backward_tracking import compute_ausstiegs_empfehlungen

        # MIT WATCHLIST - sonst warnt die Funktion selbst und wirft alle
        # Spot-Signale in einen Sammel-Topf 'spot'. Gefunden in der
        # Gegenpruefung vom 14.08., an ihrer eigenen Logzeile:
        #
        #   "compute_ausstiegs_empfehlungen() ohne watchlist aufgerufen -
        #    keine Assetklassen-Aufschluesselung moeglich"
        #
        # Ohne sie traegt jede Zeile `tier = "spot"`, und die
        # Gruppenueberschriften der Ausstiegsmail (Krypto-Spot, Aktien,
        # Rohstoffe ...) waeren gebaut und wirkungslos - alles stuende unter
        # "SPOT (nicht aufgeschluesselt)".
        import config as _config_modul

        try:
            _wl = _config_modul.get_watchlist()
        except Exception:                                    # noqa: BLE001
            pass
        _f = compute_ausstiegs_empfehlungen(conn, watchlist=_wl)
        # JE SYMBOL **UND** INSTRUMENT, nicht nur je Symbol (15.08.2026).
        #
        # Die Liste enthaelt eine Zeile je SIGNAL, nicht je Position - TURBO
        # stand am 15.08. zweimal darin (einmal Spot, einmal Hebel), VIRTUAL
        # ebenfalls. Die alte Schleife schrieb beide in denselben Schluessel:
        # es gewann, was zufaellig zuletzt kam. Die Mail zeigte dann unter
        # "Bestehende Position" moeglicherweise die des anderen Instruments.
        #
        # UND EINE ECHTE POSITION SCHLAEGT EINE ALTE SIGNALZEILE. `ist_bestand`
        # unterscheidet beides: von den neun SCHLIESSEN-Zeilen jenes Tages
        # bezogen sich nur drei auf einen tatsaechlichen Bestand.
        for _e in (_f or {}).get("alle", []):
            _sym = str(_e.get("symbol", "")).upper()
            _inst = "hebel" if _e.get("ist_hebel") else "spot"
            _bisher = ergebnis["fuehrung"].get((_sym, _inst))
            if _bisher is None or (_e.get("ist_bestand")
                                   and not _bisher.get("ist_bestand")):
                ergebnis["fuehrung"][(_sym, _inst)] = _e
    except Exception as exc:                                 # noqa: BLE001
        # P-8: ohne die Fuehrung ist die Verkaufsmail aermer, nicht falsch.
        ergebnis.setdefault("fehler", []).append(
            f"Ausstiegsfuehrung nicht lesbar: {exc}")

    try:
        bilanz = TB.zaehle(conn, quelle_kette="rollen",
                           instrument=instrument)
    except Exception as exc:                                 # noqa: BLE001
        ergebnis["fehler"].append(f"Trefferbilanz nicht lesbar: {exc}")
        bilanz = {}
    ergebnis["bilanz_zellen"] = len(bilanz)
    durchlauf = RG.Durchlauf("rollen")
    ergebnis["durchlauf"] = durchlauf
    aufgezeichnet = antworten or {}

    # ---- ROLLE A: einmal je Lauf, nicht je Asset ----------------------------
    #
    # ERST DIE ABBRUCHGRUENDE, DANN DIE ARBEIT. Die erste Fassung baute die
    # Lagebild-Eingabe VOR der Pruefung auf die Aufzeichnung - bei leeren
    # Kursreihen stuerzte sie dort ab, statt mit einer Begruendung
    # abzubrechen. Ein Absturz sagt nicht, was fehlt.
    # ⚠️ DER ANKER GILT FUER DIESE GRUPPE, NICHT FUER DAS GANZE UNIVERSUM
    # (16.08.2026, aus dem NB-Export).
    #
    # `rollen_job` uebergibt ALLE Kursreihen - das Lagebild und der Gleichlauf
    # brauchen sie, denn sie beschreiben den GESAMTEN Markt. `symbole` ist
    # dagegen auf die Gruppe gefiltert. Der Ankertag wurde bis heute ueber
    # `reihen` gerechnet, also ueber alle sechzig.
    #
    # WAS DAS AN EINEM SAMSTAG ANRICHTET: Krypto handelt durchgehend und hatte
    # am 16.08. eine Kerze, Aktien, ETF und Rohstoffe nicht. 41 von 60 sind
    # 68 % und reissen die 60-%-Schranke - also ankerte AUCH der Aktienlauf auf
    # dem Samstag, an dem keine seiner Reihen einen Kurs hat.
    #
    #     aktien/spot     fakten (0 bestanden, 2 verloren)
    #     hedge           fakten (0 bestanden, 2 verloren)
    #     rohstoffe/spot  fakten (0 bestanden, 4 verloren)
    #     themen_etf      fakten (0 bestanden, 5 verloren)
    #     krypto/hebel    fakten (41 bestanden, 0 verloren), 16 Signale
    #
    # VIER VON SECHS GRUPPEN OHNE EIN EINZIGES URTEIL, und der Lauf meldete
    # "0 Signale, 0 Fehler" - er sah aus wie ein ruhiger Markt.
    #
    # DER DOCSTRING VON `_ankertag` BESCHREIBT GENAU DIESEN FEHLER, eine Ebene
    # tiefer: "EIN einziges Symbol setzt den Anker fuer alle". Dass er auch
    # zwischen ASSETKLASSEN auftritt, ist niemandem aufgefallen, weil `reihen`
    # ungefiltert durchgereicht wird.
    eigene_reihen = {s: reihen[s] for s in (symbole or []) if s in reihen}
    if datum:
        tag, gedeckt, gesamt = datum, len(eigene_reihen), len(eigene_reihen)
    else:
        tag, gedeckt, gesamt = _ankertag(eigene_reihen or reihen)
    ergebnis["ankertag"] = {"tag": tag, "gedeckt": gedeckt, "gesamt": gesamt}
    if not reihen:
        raise LaufAbgebrochen(
            "keine Kursreihen - ohne sie gibt es weder ein Lagebild noch "
            "einen Ankertag, und ein Lauf ohne Anker vergleicht nichts.")
    if tag is None:
        raise LaufAbgebrochen(
            f"kein Ankertag mit ausreichender Deckung - bestenfalls {gedeckt} "
            f"von {gesamt} Symbolen ({100 * gedeckt / gesamt:.0f} %, noetig "
            f"{100 * MINDEST_DECKUNG:.0f} %). Das ist ein Datenausfall, kein "
            f"ruhiger Tag - ein Lauf darauf saehe aus wie das eine und waere "
            f"das andere.")
    if betriebsart == TROCKEN and aufgezeichnet.get("lagebild") is None:
        raise LaufAbgebrochen(
            "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts zu "
            "pruefen, und ein leerer Durchlauf saehe aus wie ein Erfolg.")

    a_ein = RE.baue_lagebild_eingabe(reihen, tag, config)

    # DAS LAGEBILD WIEDERVERWENDEN, SOLANGE ES FRISCH IST (14.08.).
    #
    # Rolle A beschreibt den Gesamtmarkt. Im 15-Minuten-Takt waere das 96-mal
    # taeglich dieselbe Frage - fuer eine Aussage, die sich in einer
    # Viertelstunde nicht aendert. Drei Stunden Haltbarkeit machen daraus acht.
    #
    # NUR IM ECHTEN BETRIEB. Der Trockenlauf soll die Verdrahtung pruefen und
    # nicht davon abhaengen, was zufaellig in der Datenbank liegt.
    lagebild = lagebild_id = None
    if betriebsart != TROCKEN:
        gefunden = SA.juengstes_lagebild(conn, LAGEBILD_HALTBAR_STUNDEN)
        if gefunden:
            lagebild_id, lagebild = gefunden
            ergebnis["lagebild_wiederverwendet"] = True

    if lagebild is None:
        # BEIDE ZWEIGE BAUEN DAS LAGEBILD, nicht nur einer. Meine erste Fassung
        # der Wiederverwendung liess die Aufbereitung im `else` stehen - der
        # Trockenlauf hatte danach `lagebild = None` und waere an der naechsten
        # Zeile gestorben. Gefunden beim Nachlesen, nicht vom Testlauf.
        if betriebsart == TROCKEN:
            a_roh = aufgezeichnet.get("lagebild")
            if a_roh is None:
                raise LaufAbgebrochen(
                    "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts "
                    "zu pruefen, und ein leerer Durchlauf saehe aus wie ein "
                    "Erfolg.")
        else:
            a_roh = _frage(client, modell, RA.SYSTEM_PROMPT_ANALYST, a_ein,
                           "agent.rolle_analyst")
        lagebild = RE.stempel_gleichlauf(RA.validiere(a_roh), reihen, tag)
    gleichlauf = lagebild.get("gleichlauf")

    # Z1 auf das Lagebild - ZAEHLEN, nicht verwerfen.
    ergebnis["z1_lagebild"] = Z1.pruefe(lagebild, a_ein.get("fakten", a_ein),
                                        gleichlauf)

    if betriebsart != TROCKEN and lagebild_id is None:
        SA.migriere(conn)
        RG.migriere(conn)
        lagebild_id = SA.schreibe_lagebild(
            conn, datum=tag, antwort=lagebild, fakten=a_ein,
            prompt_stand=getattr(RA, "PROMPT_STAND", "?"), modell=modell or "-")

    # ---- ROLLE BC: je Asset -------------------------------------------------
    #
    # DIE REIHENFOLGE ENTSCHEIDET, WER BEI KNAPPEM BUDGET DRANKOMMT - und der
    # Nutzer hat sie bestimmt: Bestand zuerst. Bei einer Position, die er haelt,
    # steht taeglich eine echte Entscheidung an; bei einem fremden Symbol kann
    # er warten. Ausgeschlossen wird dabei NICHTS (siehe `warteschlange`).
    from agent import warteschlange as WS
    if betriebsart != TROCKEN:
        symbole = WS.sortiere(conn, symbole, instrument)
        ergebnis["reihenfolge"] = WS.erklaere(conn, symbole,
                                              instrument=instrument)

    # DER DECKEL ZAEHLT NUR ECHTE MODELLAUFRUFE, nicht Symbole. Ein Symbol, das
    # am Cooldown scheitert, kostet nichts und darf den Deckel nicht verbrauchen
    # - sonst haette ein gesperrtes Asset dieselbe Wirkung wie ein bezahltes.
    ergebnis["aufrufe"] = 0
    # A1 - DIE AUSWAHL, EINMAL JE LAUF (23.08.2026).
    #
    # ⚠️ NICHT JE ASSET. Die Rangliste ist eine Aussage ueber die GRUPPE;
    # sie vierzigmal zu rechnen waere nicht nur teuer, sondern gefaehrlich:
    # jede Wiederholung koennte eine andere Grundmenge sehen, und dann waere
    # "Rang 2 von 40" in zwei Mails zweierlei.
    #
    # Faellt sie aus, waehlt sie NICHT - dann laufen alle durch wie bisher.
    # Eine Stufe, die wegen eines Fehlers alles sperrt, waere schlimmer als
    # keine (dieselbe Linie wie beim Cooldown).
    try:
        from agent import auswahl as _AW
        _auswahl = _AW.waehle(reihen, symbole)
        _markt = _AW.marktzustand(reihen, assetklasse)
    except Exception as exc:                             # noqa: BLE001
        logger.exception("Auswahl fuer %s ausgefallen", assetklasse)
        ergebnis.setdefault("fehler", []).append(f"Auswahl: {exc}")
        _auswahl, _markt = {"aktiv": False}, None
    # DER SCHATTEN (23.08.2026): eine Zeile je Symbol - was die Auswahl
    # empfohlen haette. Die Aktion der Kette wird spaeter nachgetragen.
    # ⚠️ NICHT IM TROCKENLAUF: er schreibt grundsaetzlich nichts.
    _auswahl_lauf = None
    if betriebsart != TROCKEN:
        try:
            _auswahl_lauf = _AW.schreibe_lauf(
                conn, auswahl=_auswahl, gruppe=assetklasse,
                symbole=symbole, zustand=_markt)
        except Exception as exc:                         # noqa: BLE001
            logger.exception("Auswahl-Schatten nicht geschrieben")
            ergebnis.setdefault("fehler", []).append(
                f"Auswahl-Schatten: {exc}")
    ergebnis["auswahl"] = {"aktiv": bool(_auswahl.get("aktiv")),
                           "k": _auswahl.get("k"),
                           "von": _auswahl.get("von"),
                           "gewaehlt": sorted(_auswahl.get("gewaehlt") or ()),
                           "marktzustand": (_markt or {}).get("abstand")}

    # ---- 2e: DIE MARKTRAENGE, EINMAL JE LAUF (30.08.2026) ----------------
    #
    # ⚠️ EINMAL, NICHT JE SYMBOL - und das ist keine Sparmassnahme, sondern
    # die Messung selbst. Gemessen wurde ein QUERSCHNITT: "wer hat HEUTE,
    # verglichen mit den anderen, das niedrigste Funding". Die Je-Reihe-Sicht
    # ("guenstig fuer seine eigenen Verhaeltnisse") wurde ebenfalls geprueft
    # und traegt NICHT - marktbereinigt -0,0755 R, also reines Markt-Timing.
    # Ein Rang je Symbol berechnet waere deshalb nicht dieselbe Groesse mit
    # weniger Aufrufen, sondern eine andere Groesse ohne Befund.
    #
    # ⚠️ FAELLT ER AUS, SPERRT ER NICHTS. Die Merkmale fehlen dann, und
    # `wahrscheinlichkeit.rechne()` traegt fuer sie null bei ("an diesem
    # Anker nicht bestimmbar"). Kein fehlender Wert wird zur schlechtesten
    # Stufe - das waere ein stiller Sperrgrund aus einem Netzwerkfehler.
    #
    # ⚠️ KONTINGENT: ein Aufruf Binance (frei) und einer CoinGecko
    # (10.000/Monat, Grundverbrauch ~230/Tag) - je Lauf, nicht je Symbol.
    # ⚠️ IM TROCKENLAUF WIRD NICHT ABGERUFEN (31.08.2026). Die erste Fassung
    # rief `marktrang` in JEDER Betriebsart - auch in der Pruefsuite. Folge:
    # die Suite verbrauchte CoinGecko-Kontingent und lief in HTTP 429. Ein
    # Trockenlauf, der echte Quellen anfasst, ist keiner; dasselbe Muster
    # gilt hier wie beim Lagebild, das aus `aufgezeichnet` kommt.
    _raenge, _rang_fehler = {}, None
    # ⚠️ IM TROCKENLAUF AUS `antworten`, NICHT AUS DEM NETZ (31.08.2026).
    #
    # Dasselbe Muster wie beim Lagebild: der Trockenlauf nimmt, was
    # aufgezeichnet ist. Ohne diesen Weg gab es trocken NIE Raenge - und
    # seit G-6 (Stufe 11 verwirft) hiess das: jeder Trockenlauf endet mit
    # null Signalen, weil jedes Potential bei 0,000 liegt. Damit waeren
    # alle Pruefungen, die eine Mail brauchen, wertlos geworden.
    #
    # ⚠️ WER NICHTS STELLT, BEKOMMT NICHTS. Ein Vorgabewert ("nimm Fuenftel
    # 2") waere eine erfundene Zahl an genau der Stelle, an der das System
    # entscheidet.
    # ⚠️ GESTELLTE RAENGE HABEN VORRANG - in JEDER Betriebsart (31.08.2026).
    # Die erste Fassung band das an TROCKEN; ein Probelauf rief dann doch
    # die echte API, verbrauchte Kontingent und lieferte fuer Testsymbole
    # keine Raenge - mit G-6 also keine Mail. Wer Raenge stellt, meint sie
    # auch; wer keine stellt, bekommt sie aus dem Netz (ausser trocken).
    _gestellt = dict((antworten or {}).get("marktraenge") or {})
    if _gestellt:
        _raenge = _gestellt
    elif betriebsart == TROCKEN:
        _raenge = {}
    elif str(assetklasse or "").lower() == "krypto":
        try:
            from agent import marktrang as _MR
            _raenge = _MR.raenge(symbole)
        except Exception as exc:                         # noqa: BLE001
            logger.exception("Marktraenge fuer %s nicht abrufbar", assetklasse)
            _rang_fehler = str(exc)
            ergebnis.setdefault("fehler", []).append(f"Marktrang: {exc}")
            _raenge = {}
    _mit_f = sum(1 for v in _raenge.values()
                 if v.get("funding_fuenftel") is not None)
    _mit_t = sum(1 for v in _raenge.values()
                 if v.get("turnover_fuenftel") is not None)
    ergebnis["marktrang"] = {
        "abgerufen": bool(_raenge), "mit_funding": _mit_f,
        "mit_turnover": _mit_t, "von": len(symbole or ()),
        "uebersprungen": betriebsart == TROCKEN and not _raenge,
        "gestellt": bool(_gestellt),
        "fehler": _rang_fehler}

    # ⚠️⚠️ EIN AUSFALL DARF NICHT STILL SEIN - und das ist seit R1 keine
    # Vorsichtsmassnahme mehr, sondern eine Betriebsfrage. Funding und
    # Turnover sind die EINZIGEN tragenden Beitraege; fehlen sie, liegt
    # jedes Potential bei 0,000 und die Schwelle sperrt ALLES. Genau der
    # Zustand, aus dem H gerade herausgefuehrt wurde - nur diesmal durch
    # einen Netzwerkfehler statt durch eine Registrierung.
    #
    # Es wird NICHT durchgelassen ("keine Empfehlung ohne Grund" gilt
    # weiter), aber es wird BENANNT. Ein Lauf ohne Signale wegen API-Ausfall
    # sieht sonst genauso aus wie ein Lauf ohne Signale wegen schlechter
    # Lage - und das sind zwei sehr verschiedene Aussagen.
    if betriebsart != TROCKEN and str(assetklasse or "").lower() == "krypto"             and not _mit_f and not _mit_t:
        _warnung = ("⚠️ MARKTRANG AUSGEFALLEN - Funding und Turnover fehlen "
                    "fuer ALLE %d Symbole%s. Damit liegt jedes Potential bei "
                    "0,000 und Stufe 11 sperrt den ganzen Lauf. Das ist ein "
                    "Datenausfall, kein ruhiger Tag."
                    % (len(symbole or ()),
                       (": %s" % _rang_fehler) if _rang_fehler else ""))
        logger.error(_warnung)
        ergebnis.setdefault("warnungen", []).append(_warnung)
        ergebnis["marktrang"]["totalausfall"] = True

    # ---- SCHRITT 3: DIE SCHLEIFE LAEUFT UEBER ZELLEN (01.09.2026) -------
    #
    # Nutzervorgabe 31.08.: *„Asset z. B. LINK kommt in die Bewertung -
    # entweder es kommt nur eine Strategie in Frage, weil dies die Bewertung
    # ergibt, oder u. U. beides, Akkumulation und Hebel, aber nur wenn die
    # Bewertung dies zulaesst."*
    #
    # Bis hierher bekam ein Asset GENAU EINE Strategie: `strategie_fuer`
    # waehlte sie, und ein Kern-Asset wurde damit nur akkumuliert ODER nur
    # eingestiegen - nie beides. Jetzt liefert `assetklassen.zellen()` je
    # Asset die zulaessigen Paare, und die Schleife laeuft ueber sie.
    #
    # ⚠️ DIE ZELLEN KOMMEN AUS DER EINEN QUELLE. `zellen()` liest die
    # Paar-Matrix und die beiden Nutzerschalter (`hebel_pruefung_erlaubt`,
    # `dca_erlaubt`) - eine zweite Liste hier waere die naechste, die einen
    # Schalter vergisst.
    #
    # ⚠️ UND SIE WIRD AUF DAS INSTRUMENT DIESES LAUFS GEFILTERT. Fuer Krypto
    # liefert `laeufe()` seit S6b nur "spot"; Hebelzellen fallen damit von
    # selbst heraus - und das ist richtig so: gebuehrenfrei liefert
    # `hebel x einstieg` dasselbe Potential wie `spot x einstieg` (F-163,
    # gemessen 01.09.), es waere also ein ZWEITES, identisches Signal. Der
    # Hebel entsteht weiterhin dort, wo er hingehoert - in der Rechnung
    # (`hebel = verlustanteil / stop_rel`) und am Freigabeschalter.
    #
    # ⚠️⚠️ GESAMMELT WIRD DIE STRATEGIE, NICHT DAS INSTRUMENT (01.09.2026,
    # Nutzerklaerung). Das Instrument einer Zelle ist ein WUNSCH; welches
    # es wird, faellt aus der Rechnung an - Kapitel 88, *„Hebel als Ergebnis
    # statt als Kategorie"*.
    #
    # Meine erste Fassung filterte `_z["instrument"] != instrument` und warf
    # damit alle Hebelzellen weg. Das war fuer LINK richtig (dort ist
    # `hebel x einstieg` dieselbe Frage wie `spot x einstieg`, nur anders
    # ausgefuehrt) und fuer BTC FALSCH: dort ersetzt die Akkumulation den
    # Spot-Einstieg, und `hebel x einstieg` waere die EINZIGE taktische
    # Kauffrage. Genau das steht seit dem 28.08. als A2 im Plan: *„Ein
    # Kern-Asset soll beides koennen - langfristig aufbauen und kurzfristig
    # gehebelt handeln. Das sind zwei Positionen, zwei Horizonte, zwei
    # Fragen."*
    #
    # Ueber die Strategie zu sammeln loest beides auf:
    #
    #     BTC  (dca an)   -> {akkumulation, einstieg}   zwei Fragen
    #     LINK (dca aus)  -> {einstieg}                 eine Frage
    _zellen_je_symbol: dict = {}
    try:
        for _z in _AKL.zellen(_wl, conn):
            _vorhandene = _zellen_je_symbol.setdefault(_z["symbol"], [])
            if _z["strategie"] not in _vorhandene:
                _vorhandene.append(_z["strategie"])
    except Exception:                                        # noqa: BLE001
        logger.exception("Zellen nicht bestimmbar - Rueckfall auf eine "
                         "Strategie je Asset")
        _zellen_je_symbol = {}

    # ⚠️ DIE REIHENFOLGE IST FESTGELEGT, NICHT ZUFAELLIG: `einstieg` zuerst.
    # Das Modellurteil wird EINMAL je Asset geholt (Schritt 4) und von der
    # zweiten Zelle wiederverwendet; geholt wird es mit der Einstiegsfrage,
    # weil die die Obermenge ist (sie fragt Einstieg und Stop, die
    # Akkumulation braucht beides nicht).
    _REIHENFOLGE = ("einstieg", "swing", "akkumulation")
    _paare = []
    for _s in (symbole or ()):
        _st = _zellen_je_symbol.get(_s)
        if not _st:
            _paare.append((_s, None, False))   # Rueckfall: `strategie_fuer`
            continue
        _st = sorted(set(_st), key=lambda x: _REIHENFOLGE.index(x)
                     if x in _REIHENFOLGE else 99)
        for _x in _st:
            # ⚠️ DIE TAKTISCHE ZELLE - und was sie von der gewoehnlichen
            # unterscheidet (Nutzerentscheidung 01.09.).
            #
            # Ein Asset mit Akkumulation kauft auf der Spot-Seite gestaffelt;
            # ein zusaetzlicher Spot-Einstieg mit Stop waere dort eine dritte
            # Frage, die es bisher nicht gab. Der Nutzer will sie nur, WENN
            # daraus tatsaechlich ein Hebelgeschaeft wird - woertlich: *„nur
            # wenn die Rechnung tatsaechlich einen Hebel ergibt waere mir
            # natuerlich lieber."*
            #
            # Ob es einer wird, weiss erst die Rechnung (`hebel =
            # verlustanteil / stop_rel`). Die Zelle laeuft deshalb an und
            # faellt in der Geometrie-Stufe wieder heraus, wenn kein Hebel
            # anfaellt - gezaehlt und begruendet, nicht still.
            _taktisch = (_x == "einstieg" and "akkumulation" in _st)
            _paare.append((_s, _x, _taktisch))
    ergebnis["zellen"] = {"paare": len(_paare), "symbole": len(symbole or ()),
                          "je_symbol": {k: sorted(v)
                                        for k, v in _zellen_je_symbol.items()}}

    # ⚠️ EIN MODELLURTEIL JE ASSET, nicht je Zelle (Schritt 4). Der Speicher
    # lebt nur fuer diesen Lauf und wird in `_ein_asset` gefuellt und
    # gelesen - zwei Zellen desselben Assets kosten damit EINEN Aufruf.
    _urteil_memo: dict = {}

    for symbol, _zelle_strategie, _zelle_taktisch in _paare:
        if max_aufrufe is not None and ergebnis["aufrufe"] >= max_aufrufe:
            ergebnis.setdefault("budget_gestoppt", []).append(symbol)
            continue
        durchlauf.beginne(symbol)
        _vor_aufrufe = ergebnis["aufrufe"]
        _vor_signale = len(ergebnis.get("signale") or [])
        # A (27.08.2026): DIE STRATEGIE GEHOERT ZUM ASSET, NICHT ZUM LAUF.
        #
        # Bis hierher wurde `strategie` laufweit vorgegeben und unveraendert
        # durchgereicht. Gemessen ueber 7.294 Signale: `akkumulation` kam NULL
        # Mal vor - die Paar-Matrix lief nie, der Nutzerschalter nie, und ein
        # langfristig gehaltener Spot-Bestand bekam einen Trailing-Stop, den es
        # dort nicht gibt (N-11, 35 SCHLIESSEN am 26.08., 32 davon im Verlust).
        #
        # Die Zuordnung kommt aus `asset_dca_settings` - dem Schalter, den der
        # Nutzer in der GUI setzt und den `asset_schalter` schon heute prueft.
        # ⚠️ NUR KRYPTO (Nutzerentscheidung 27.08.2026, Korrektur am selben
        # Tag). Der Vorgabewert `_DCA_ERLAUBT_DEFAULT_SYMBOLS` enthaelt neben
        # BTC/ETH/SOL dreizehn Multi-Asset-Positionen - freigegeben am 09.08.
        # fuer TRANCHEN-VORSCHLAEGE, also einen Text in der Mail. Sie auf eine
        # Strategieumstellung zu uebertragen, die Stop und Trailing entfernt,
        # waere eine stille Bedeutungsverschiebung.
        #
        # UND ES IST FACHLICH ETWAS ANDERES:
        #   Handel      Krypto 24/7 ohne Gap; Aktien haben Handelszeiten und
        #               Kursluecken ueber Nacht - ohne Stop unbegrenzt
        #   Zyklik      -80 % ist bei Krypto ein Zyklus, bei einer Aktie meist
        #               ein Fundamentalproblem
        #   Regelbasis  AZ-1..AZ-8 sind FUER KRYPTO entwickelt (BTC-Regime,
        #               Funding, Fear & Greed) und dort nie gemessen
        #   Messbarkeit C1 - bei 2 bis 7 Symbolen je Klasse ist nichts pruefbar
        # ⚠️ AUS DER ZELLE, mit `strategie_fuer` als Rueckfall. Der Rueckfall
        # greift, wenn `zellen()` fuer dieses Symbol nichts liefert - etwa
        # weil es nicht in der Watchlist steht oder die Schalterabfrage
        # ausfiel. Dann bleibt es beim bisherigen Verhalten, statt das Asset
        # still zu ueberspringen.
        _strategie = _zelle_strategie or HA_STRAT(
            symbol, instrument, conn=conn, vorgabe=strategie,
            assetklasse=assetklasse, nur_klassen={"krypto"})
        try:
            _ein_asset(symbol=symbol, reihen=reihen, tag=tag, lagebild=lagebild,
                       lagebild_id=lagebild_id, gleichlauf=gleichlauf,
                       durchlauf=durchlauf, betriebsart=betriebsart,
                       client=client, modell=modell, conn=conn, db=db,
                       config=config, aufgezeichnet=aufgezeichnet,
                       instrument=instrument, strategie=_strategie,
                       ergebnis=ergebnis, versand=versand,
                       assetklasse=assetklasse, watchlist=_wl,
                       auswahl=_auswahl, marktzustand=_markt,
                       auswahl_lauf=_auswahl_lauf, marktraenge=_raenge,
                       module=(AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB,
                               ZM, BE, WH),
                       zai_client=zai_client, bilanz=bilanz,
                       fehlertypen=(EmpfehlungUngueltig, AuftragUngueltig,
                                    RT.TraderAntwortUngueltig),
                       urteil_memo=_urteil_memo,
                       ist_taktisch=_zelle_taktisch,
                       pruefe_auftrag=pruefe_auftrag)
        except Exception as exc:                       # noqa: BLE001
            # EIN ASSET DARF DEN LAUF NICHT BEENDEN. Was hier abbricht, ist
            # gezaehlt und benannt - stilles Ueberspringen waere derselbe
            # Fehler wie ein Filter, der seine Wirkung verbirgt.
            ergebnis["fehler"].append(f"{symbol}: {type(exc).__name__}: {exc}")
            # DIE STUFE MUSS STIMMEN - JE SYMBOL, nicht global.
            #
            # Die erste Fassung suchte die letzte Stufe, auf der IRGENDEIN
            # Symbol bestanden hatte. Im Watchlist-Probelauf vom 13.08. brach
            # RENDER mit einem Gemini-503 im URTEIL ab und wurde als Verlust
            # der RISIKOSCHICHT gezaehlt - weil andere Symbole dort schon durch
            # waren. Die Tabelle zeigte auf die falsche Stelle, und das ist der
            # einzige Zweck, den sie hat.
            letzte = durchlauf.naechste_stufe(symbol)
            durchlauf.verloren(symbol, letzte, type(exc).__name__)

        # --- Leerlaufwache: hat dieser Aufruf etwas erbracht? -------------
        #
        # GEZAEHLT WIRD NUR, WO EIN AUFRUF STATTFAND. Ein gesperrtes Symbol
        # kostet nichts und darf die Wache nicht ausloesen - sonst wuerde
        # ausgerechnet der sparsame Fall den Lauf anhalten.
        # L1 (23.08.2026, Nutzerentscheidung): EIN BESTAND ZAEHLT NICHT.
        #
        # ⚠️ DER GRUND: bei einer gehaltenen Position lautet die Frage
        # "halten oder verkaufen". Ein HALTEN ist dort die ERWARTETE
        # Antwort und erzeugt kein Signal - es ist ein Ergebnis, kein
        # Leerlauf. Seit die Bestandsausnahme in der Auswahl-Stufe alle
        # gehaltenen Werte durchlaesst, stellt die Warteschlange sie
        # nach vorn, und acht HALTEN in Folge hielten den Lauf an -
        # BEVOR die zwei ausgewaehlten Kandidaten gefragt wurden. Genau
        # die Einstiegsseite, fuer die A1 gebaut ist, waere verstummt.
        #
        # ⚠️ WAS DAS KOSTET, steht in `auswahl.stumme_laeufe`: mit dieser
        # Ausnahme bleibt EIN zaehlender Aufruf je Lauf uebrig, und der
        # Zaehler hier entsteht je Lauf neu - die Bremse ist damit
        # unerreichbar. Ersatz ist der LAUFUEBERGREIFENDE Zaehler am
        # Ende dieses Laufs, als MELDUNG statt Abbruch (ein
        # laufuebergreifender Abbruch waere eine Falle: keine Signale ->
        # Bremse an -> keine Aufrufe -> keine Signale).
        if ergebnis["aufrufe"] > _vor_aufrufe and not _war_bestand(
                symbol, db, instrument):
            if len(ergebnis.get("signale") or []) > _vor_signale:
                ergebnis["leerlauf"] = 0
            else:
                ergebnis["leerlauf"] = ergebnis.get("leerlauf", 0) + 1
                if ergebnis["leerlauf"] >= LEERLAUF_ABBRUCH:
                    ergebnis["abgebrochen"] = (
                        f"{LEERLAUF_ABBRUCH} Aufrufe in Folge ohne Ergebnis - "
                        f"Lauf angehalten. Die Ursache steht im Gate "
                        f"(verloren_je_stufe); jeder weitere Aufruf haette "
                        f"denselben Fehler noch einmal bezahlt.")
                    logger.error("Rollen-Kette %s/%s: %s", assetklasse,
                                 instrument, ergebnis["abgebrochen"])
                    break

    # DIE FAEDEN ZUSAMMENFUEHREN, BEVOR DER LAUF ENDET. Erst danach steht fest,
    # was Z.ai gesagt hat - und geschrieben wird im Hauptfaden, weil die
    # Verbindung nicht zwischen Threads teilbar ist.
    #
    # DER DECKEL IST DER Z.AI-DECKEL PLUS EINE MINUTE. Wer hier ewig wartet,
    # verlagert das Blockieren nur ans Ende; wer gar nicht wartet, verliert die
    # Gegenpruefung eines langsamen Signals.
    # DIE EINE VERKAUFSMAIL - nach den Einstiegen, vor dem Warten auf Z.ai.
    # Sie braucht kein zweites Modell (siehe verkaufsrechnung.sammel_mail) und
    # soll deshalb nicht bis zu vier Minuten dahinter warten muessen.
    _sammel = VK2.sammel_mail(ergebnis.get("ausstiege") or [],
                              modell=modell, zeitpunkt=tag)
    if _sammel:
        ergebnis.setdefault("mails", []).append(
            {"symbol": "(Sammel)", "betreff": _sammel[0], "text": _sammel[1],
             "seite": "ausstieg"})
        # DER SCHALTER FUER DIE RATENFRAGE (14.08.).
        #
        # Die alte Kette hat ueber ihre gesamte Historie NULL von 1.142
        # Spot-Signalen als VERKAUFEN geurteilt (98,2 % HALTEN, Befund vom
        # 01.08.). Die Rollen-Kette liefert elf in EINEM Lauf ueber 45 Symbole.
        #
        # Von null auf ein Viertel. Das ist entweder genau die Korrektur, die
        # gesucht wurde - oder die Kalibrierung ist ins andere Extrem gekippt.
        # Beantworten laesst sich das aus vorliegenden Daten, ohne einen
        # Modellaufruf; bis dahin soll man die Urteile ZAEHLEN koennen, ohne
        # sie verschicken zu muessen.
        #
        # WAS DIESER SCHALTER NICHT TUT: er unterdrueckt keine Zeile. Gebucht
        # wird immer - sonst waere es wieder das Verschlucken, nur mit einem
        # Schalter davor.
        _mailt = ((config or {}).get("rollen_kette") or {}).get(
            "verkauf_mailt", True)
        if betriebsart == SCHARF and versand is not None and _mailt:
            versand(*_sammel)
        elif betriebsart == SCHARF and not _mailt:
            ergebnis["verkauf_nicht_gemailt"] = len(
                ergebnis.get("ausstiege") or [])

    for faden, kennung, eintrag in ergebnis.pop("_faeden", []):
        faden.join(timeout=ZM.WARTE_MAX_SEKUNDEN + 60)
        if faden.is_alive():
            ergebnis.setdefault("fehler", []).append(
                f"zweite Meinung fuer Signal {kennung} nicht rechtzeitig fertig")
            continue
        zweite = eintrag.get("zweite_meinung")
        if zweite:
            ZM.schreibe(conn, kennung, zweite)

    # DER ERSATZ FUER DIE BREMSE, LAUFUEBERGREIFEND (23.08.2026).
    #
    # ⚠️ ALS MELDUNG, NICHT ALS ABBRUCH. Ein laufuebergreifender
    # Abbruch waere eine Falle: keine Signale -> Bremse an -> keine
    # Aufrufe -> keine Signale. Und ein Abbruch sparte nichts mehr, wo
    # nach A1 nur noch ein zaehlender Aufruf je Lauf stattfindet.
    #
    # DIE ZAHL STEHT IM ERGEBNIS UND IM LOG, damit sie in der
    # Diagnose auftaucht - eine Meldung, die niemand sieht, ist keine.
    if betriebsart != TROCKEN:
        try:
            _stumm = _AW.stumme_laeufe(conn, assetklasse)
            ergebnis["stumme_laeufe"] = _stumm
            if _stumm.get("stumm"):
                logger.warning(
                    "Einstiegsseite %s: %d Laeufe in Folge ohne "
                    "Einstieg bei einem GEWAEHLTEN Wert. Die Auswahl "
                    "liefert Kandidaten, die Kette nimmt keinen - das "
                    "ist die Stelle, an der nachzusehen ist.",
                    assetklasse, _stumm["laeufe"])
        except Exception:                                    # noqa: BLE001
            logger.exception("Stummzaehler fuer %s", assetklasse)
        RG.schreibe(conn, durchlauf, _jetzt())
    return ergebnis


def _war_bestand(symbol, db, instrument) -> bool:
    """Haelt der Nutzer diesen Wert? Fuer die Leerlaufwache (L1).

    ⚠️ EIGENE FUNKTION, KEINE ZWEITE ABFRAGE: die Auswahl-Stufe
    stellt dieselbe Frage, und zwei Kopien liefen auseinander. Faellt
    sie aus, gilt "kein Bestand" - dann zaehlt die Wache im Zweifel
    MIT, und die Bremse bleibt scharf. Der Rueckfall geht also zur
    sicheren Seite."""
    from agent import rollen_eingabe as _RE
    try:
        menge, _einstand = _RE.bestand(symbol, db, instrument)
        return bool(menge and float(menge) > 0)
    except Exception:                                        # noqa: BLE001
        logger.exception("Bestandspruefung (Wache) fuer %s", symbol)
        return False


def _ein_asset(*, symbol, reihen, tag, lagebild, lagebild_id, gleichlauf,
               urteil_memo=None, ist_taktisch=False,
               durchlauf, betriebsart, client, modell, conn, db, config,
               instrument, strategie,
               aufgezeichnet, ergebnis, versand, module, fehlertypen,
               pruefe_auftrag, zai_client=None, bilanz=None,
               assetklasse="krypto", watchlist=None,
               auswahl=None, marktzustand=None,
               auswahl_lauf=None, marktraenge=None) -> None:
    """Ein Asset durch alle Stufen. Wirft, wenn es nicht weitergeht.

    `watchlist` wird DURCHGEREICHT, nicht hier geladen (15.08.2026). Meine
    erste Fassung griff auf `_wl` zu - eine Variable aus `fuehre_lauf`, die
    diese Funktion nicht sieht. Genau dieselbe Falle wie `VK` am 14.08.: der
    breite Fehlerfang haette sie geschluckt, und JEDES Symbol waere in den
    Fehlerzweig gelaufen."""
    AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB, ZM, BE, WH = module

    # --- Stufe: Auftrag --- (schon vor der Schleife geprueft)
    durchlauf.bestanden(symbol, "auftrag")

    # --- Stufe: Fakten ---
    reihe = reihen.get(symbol)
    if not reihe:
        durchlauf.verloren(symbol, "fakten", "keine Kursreihe")
        return
    idx = len(reihe) - 1
    if tag:
        treffer = next((i for i, k in enumerate(reihe) if k.date >= tag), None)
        if treffer is None:
            durchlauf.verloren(symbol, "fakten", f"keine Daten ab {tag}")
            return
        idx = treffer
    # TROCKEN HEISST AUCH: KEIN NETZ. `baue_fall()` holt sonst die
    # Finanzierungsrate von der Boerse - und JEDER externe Aufruf bucht seinen
    # Gesundheitsstand in `api_health_status`. Der erste Trockenlauf hat damit
    # in die Produktivdatenbank geschrieben, obwohl er nichts schreiben
    # sollte. Gefunden von der eigenen Pruefung, nicht vermutet.
    #
    # `mit_finanzierung=False` steht dafuer schon im Modul bereit - es war als
    # Vergleichsarm fuer gepaarte Messungen gebaut und passt hier genau: der
    # Trockenlauf soll die VERDRAHTUNG pruefen, nicht die Boerse.
    # INSTRUMENT, STRATEGIE UND ASSETKLASSE MUESSEN MIT (15.08.2026).
    #
    # Ohne sie fiel `baue_fall()` auf seine Vorgabewerte zurueck, und im
    # AUFTRAG-Block jedes Laufs stand "ohne Hebel und ohne laufende Kosten" -
    # auch dort, wo mit Hebel gehandelt wird. Der Rollenprompt war richtig, die
    # Fakten widersprachen ihm, und die Fakten stehen zuerst (R-T9).
    #
    # Der Bestand haengt an derselben Angabe: mit ihr liest `RE.bestand()`
    # `hebel_positions` statt `holdings`. Beides gehoert in EINEN Aufruf -
    # zwei getrennte Wege waeren die naechste Stelle, an der eines von beiden
    # vergessen wird.
    # DIE BLOECKE MIT ABGREIFEN, ohne sie zweimal zu rechnen (O-36,
    # 15.08.2026). `bloecke_ziel` ist ein AUSGANG: der Faktensatz bleibt
    # unveraendert - er geht so in den Prompt -, und daneben liegen die
    # Bloecke einzeln fuer die Anlassmessung. Sie neu zu rechnen hiesse,
    # die Finanzierungsrate ein zweites Mal von der Boerse zu holen.
    _bloecke_anlass = {}
    _, bc_ein = RE.baue_fall(symbol=symbol, reihe=reihe, index=idx,
                             reihen=reihen, db=db,
                             mit_finanzierung=(betriebsart != "trocken"),
                             instrument=instrument, strategie=strategie,
                             assetklasse=assetklasse,
                             bloecke_ziel=_bloecke_anlass)
    atr_e = RE.atr_eur(symbol, reihe, idx, db)
    kurs_e = RE.kurs_eur(symbol, reihe, idx, db)

    # MINDESTGRUNDLAGE VON ROLLE BC (16.08.2026 abends, R-R1).
    #
    # Geprueft wird, was ohne Ausnahme dastehen MUSS - Auftrag, Lage, Bestand,
    # Verlauf. NICHT die volle CSTI-Liste: Ausloeser, Handelbarkeit und
    # Katalysator fehlen strukturell und haben eine eigene Phase. Eine Warnung,
    # die bei jedem Urteil kommt, liest niemand.
    #
    # MELDEN IST DIE VORGABE. Gesperrt wird nur, wenn "BC" in
    # `config.yaml mindestkriterien.sperren` steht.
    from agent import mindestkriterien as MK

    # ⚠️ NUR DIE SATZBLOECKE (17.08.2026). `geteilt()` liefert seit heute
    # zusaetzlich `_marken_werte` - Zahlen fuer die Zielrechnung, keine
    # Saetze. Beide Zaehlungen hier arbeiten ueber die ZAHL der Bloecke
    # (Kursreihenanteil, Fingerabdruck je Block); ein Eintrag mehr wuerde
    # sie verschieben, ohne dass jemand etwas liest.
    from agent import lagebeschreibung as _LB

    _bloecke_saetze = _LB.nur_saetze(_bloecke_anlass)
    _mk_fehlt = MK.pruefe_bc(bc_ein, _bloecke_saetze or None)
    if MK.melde("BC", _mk_fehlt, config, bezug=f"{symbol}/{instrument}"):
        durchlauf.verloren(symbol, "fakten",
                           "Mindestgrundlage: " + "; ".join(_mk_fehlt))
        return
    durchlauf.bestanden(symbol, "fakten")
    durchlauf.bestanden(symbol, "lagebild")

    # --- Cooldown: VOR dem Modellaufruf ---------------------------------
    #
    # HIER UND NIRGENDWO SPAETER. Die erste Fassung stand NACH dem
    # Trader-Aufruf - sie verhinderte die Mail, nicht die Kosten. Das Geld war
    # ausgegeben, wenn sie griff, und der Lauf machte bei jedem 15-Minuten-Takt
    # einen vollen Durchgang: 4.800 Trader-Aufrufe am Tag gegen ein
    # Gemini-Budget von 500.
    #
    # An dieser Stelle kostet dieselbe Pruefung nichts und spart alles:
    # 41 Symbole bei 15 h Cooldown ergeben 66 Aufrufe am Tag statt 3.936.
    #
    # DER GRUND, WARUM ES DEN COOLDOWN GIBT, ist die eigene Messung dieses
    # Projekts: fuenf Symbole trugen 102 % des Minus, und die Ursache war die
    # WIEDERHOLUNG. Die alte Kette fuehrt dafuer acht Einstellungen; die
    # Rollen-Kette las bis zum 13.08. keine davon.
    #
    # GEBUCHT WIRD DER VERLUST AUF DER URTEILSSTUFE - dort, wo das Symbol
    # gerade stand. Es hat Auftrag, Fakten und Lagebild bestanden und ist nie
    # zu einem Urteil gekommen; der Trichter bleibt damit monoton. Dass es der
    # Cooldown war und kein schlechtes Urteil, steht im Grund.
    # ⚠️ AUCH IM TROCKENLAUF (O-38, 16.08.2026). Hier stand
    # `if betriebsart != TROCKEN` - und `asset_schalter` ist ein REINER
    # LESER, es gab also nie einen Grund dafuer. Die Folge: jeder
    # Trockenlauf liess Assets durch, die der Nutzer ausdruecklich
    # abgeschaltet hat, und meldete einen Durchsatz, den der scharfe
    # Betrieb nie erreicht. Auch die Laeufe, mit denen der Vollumstieg
    # geprueft wurde.
    if True:
        # DIE SCHALTER DES NUTZERS ZUERST (Querpruefung 14.08.). Drei
        # GUI-Schalter je Asset - DCA, Hebel-Pruefung, Bitpanda-Override -
        # wurden von den alten Pipelines gelesen und von dieser Kette
        # vollstaendig ignoriert. Sie erzeugte damit Signale, wo der Nutzer
        # ausdruecklich keine wollte. Seine Vorgabe steht woertlich im alten
        # Code: *"ueberall moeglich, aber nur dort Signale erzeugen, wo ich das
        # selektiv moechte."*
        from agent import asset_schalter as AS
        # DIE WATCHLIST MIT, statt sie je Symbol neu zu laden. Sie liegt im
        # Lauf ohnehin vor; ohne sie laese `_ist_cash_aequivalent()` die
        # config.yaml bei jedem Asset erneut.
        erlaubt, warum = AS.darf_analysiert_werden(
            conn, symbol, instrument, strategie, watchlist=watchlist)
        if not erlaubt:
            durchlauf.verloren(symbol, "auftrag", warum or "abgeschaltet")
            return
    # --- Stufe: Anlass - MISST, SPERRT NICHT (O-36, 15.08.2026) -------------
    #
    # VOR DEM COOLDOWN, NICHT DANACH (korrigiert 15.08.2026 abends).
    #
    # Meine erste Fassung sass NACH der Wiederholungsstufe - und haette
    # damit nur Symbole gesehen, bei denen der Cooldown ohnehin schon
    # abgelaufen war: mindestens 3,5 Stunden beim Hebel, 15 beim Spot. In
    # dieser Zeit hat sich der Faktensatz fast immer bewegt.
    #
    #     Der Filter haette fast nie gegriffen, und wir haetten daraus
    #     geschlossen, dass er nichts taugt - obwohl wir die Population,
    #     in der er wirkt, nie gemessen haetten.
    #
    # Der Nutzer hat genau das befuerchtet: *"woran es lag sollten wir
    # morgen auch schon sehen koennen oder gar nicht wie ich befuerchte"*.
    #
    # HIER KOSTET SIE NICHTS. Die Messung braucht keinen Modellaufruf -
    # nur einen Hash ueber Text, der ohnehin gebaut ist. Sie darf deshalb
    # JEDES Symbol sehen, auch die, die der Cooldown gleich entfernt.
    #
    # UND ERST DAMIT WIRD DIE INTERESSANTE FRAGE BEANTWORTBAR: koennte der
    # Anlassfilter den Cooldown ERSETZEN? Der Cooldown ist eine grobe
    # Zeitregel, der Anlass eine genaue Aussage ueber dieselbe Sache. Wer
    # nur hinter dem Cooldown misst, kann die beiden nie vergleichen.
    #
    # NUTZERVORGABE: *"erstmal soviele Daten wie moeglich zulassen und spaeter
    # selektiv einschraenken - bis wir ein Gefuehl haben, ob und wie die
    # Bewertungen der Rollen zustandekamen."* Diese Stufe verliert deshalb
    # NIEMANDEN. Sie schreibt mit, wie oft sie gegriffen haette.
    #
    # UND SIE ZAEHLT ZWEI ABDRUECKE: einen ueber alles, was das Modell liest,
    # und einen ohne das Lagebild. Das Lagebild ist Modellprosa und wechselt
    # alle drei Stunden - naehme man es mit, waere fast jede Frage "neu". Ob
    # das der richtige Schnitt ist, soll die Messung sagen.
    _anlass_sperrt, _anlass_grund = False, ""
    # ⚠️ AUCH IM TROCKENLAUF, ABER OHNE ZU SCHREIBEN (O-38, 16.08.2026).
    # Diese Stufe war ausgenommen, weil sie eine Zeile anlegt. Das Urteil
    # braucht sie aber nicht - `schreiben=False` rechnet den Fingerabdruck,
    # liest den Vergleich und legt nichts an. Ohne das kannte der
    # Trockenlauf die schaerfste Stufe der Kette nicht: sie hat am 16.08.
    # 35 von 41 Kryptosymbolen gestoppt.
    if True:
        try:
            from agent import anlass as AN

            _beob = AN.beobachte(conn, symbol=symbol, instrument=instrument,
                                 fakten=bc_ein, bloecke=_bloecke_saetze,
                                 schreiben=betriebsart != TROCKEN)
            ergebnis.setdefault("anlass", []).append(dict(
                _beob, symbol=symbol, instrument=instrument))
            # SEIT 16.08.2026 SPERRT SIE - wenn der Nutzer sie einschaltet.
            #
            # Die Entscheidung steht in `config.yaml` unter `anlass.aktiv`;
            # die Vorgabe im Code ist AUS. Begruendung, Messwerte und die
            # Feinjustierung stehen im Kopf von `agent/anlass.py`.
            #
            # DIE BEOBACHTUNG WIRD TROTZDEM GESCHRIEBEN, auch wenn gesperrt
            # wird. Sonst verschwaende mit der Sperre auch die Zahl, an der man
            # sie spaeter beurteilen koennte - und man saehe nur noch, dass
            # weniger kommt, nicht warum.
            _anlass_sperrt, _anlass_grund = AN.sperrt(_beob, config)
        except Exception as exc:                             # noqa: BLE001
            # EINE MESSUNG DARF DEN BETRIEB NICHT ANHALTEN - aber sie muss
            # sagen, wenn sie ausfaellt. Sonst ist sie ein stiller Ausfall,
            # und davon hatte dieses Projekt heute genug.
            logger.warning("Anlass-Messung fuer %s ausgefallen: %s",
                           symbol, exc)
            ergebnis.setdefault("fehler", []).append(
                f"{symbol}: Anlass-Messung: {exc}")

        # DIE SPERRE WIRKT HIER, NICHT IM `try` DARUEBER. Ein Fehler in der
        # Messung darf nicht dazu fuehren, dass gesperrt wird - `sperrt()`
        # gibt bei jeder Luecke `False` zurueck, und ein abgestuerzter
        # `try`-Block laesst die Vorbelegung `False` stehen. Im Zweifel
        # durchlassen.
        if _anlass_sperrt:
            durchlauf.verloren(symbol, "anlass", _anlass_grund)
            return
        # ⚠️ HIER BUCHEN, NICHT ERST NACH DEM COOLDOWN (16.08.2026, gefunden
        # von `simuliere_kette.py` gegen echte Produktionsdaten).
        #
        # Meine erste Fassung buchte beide Stufen gemeinsam am Ende. Griff der
        # Cooldown, kehrte die Funktion vorher zurueck - und die Anlass-Stufe
        # stand mit "0 bestanden, 0 verloren" da, obwohl zwei Symbole sie
        # passiert hatten. Ein Trichterloch, dessen Summe nicht mehr aufgeht:
        # genau das, was die eigene Stufe verhindern sollte.
        durchlauf.bestanden(symbol, "anlass")

        # --- Stufe: Auswahl (A1, 23.08.2026) ---
        #
        # ⚠️ HIER WIRD ENTSCHIEDEN, WELCHE WERTE UEBERHAUPT BEURTEILT
        # WERDEN - vorher tat das der Cooldown, also die Uhr. Der Grund
        # steht jetzt in der Zeile: "Rang 17 von 40" statt "Cooldown bis
        # 22:14". Nutzergrundsatz: jede Entscheidung braucht eine
        # Begruendung, und "das Asset ist in der Zeitschleife dran" ist
        # keine.
        #
        # SIE STEHT NACH DER ANLASS-BUCHUNG, damit die Anlass-Messung ihre
        # Beobachtung fuer ALLE Symbole weiterschreibt. Eine Auswahl, die
        # der Messung die Grundmenge nimmt, macht sich selbst unpruefbar.
        # ⚠️ DER BESTAND PASSIERT IMMER (23.08.2026, gefunden bei der
        # Abhaengigkeitspruefung, die der Nutzer VOR dem Weiterbauen
        # verlangt hat).
        #
        # DER FEHLER, DEN DAS BEHEBT: die Auswahl beantwortet die
        # Frage "welchen soll ich KAUFEN". Bei einem gehaltenen Wert
        # lautet die Frage aber "halten oder verkaufen" - und die
        # stellt sich unabhaengig davon, ob er heute unter den besten
        # zwei ist. Ohne diese Ausnahme faellt die gesamte
        # Verkaufsseite aus der Kette.
        #
        # GEMESSEN, nicht befuerchtet: von 24 Bestandspositionen ueber
        # alle Gruppen waeren 21 nicht mehr beurteilt worden - 14 von
        # 15 bei Krypto, 6 von 7 bei ETF, 1 von 2 bei Aktien.
        #
        # ⚠️ UND ES STAND SCHON IM EIGENEN DOKUMENT: "Bestand ist
        # nicht Teil von A1 - das ist die Verkaufsfrage." Die
        # Konsequenz daraus habe ich beim Bau nicht gezogen: was nicht
        # Teil der Auswahl ist, darf von ihr auch nicht gesperrt
        # werden.
        _hat_bestand = False
        try:
            _m, _e = RE.bestand(symbol, db, instrument)
            _hat_bestand = bool(_m and float(_m) > 0)
        except Exception:                                    # noqa: BLE001
            logger.exception("Bestandspruefung fuer %s ausgefallen", symbol)
        if (auswahl or {}).get("aktiv") and not _hat_bestand:
            if symbol not in (auswahl.get("gewaehlt") or set()):
                from agent import auswahl as _AW2
                durchlauf.verloren(symbol, "auswahl",
                                   _AW2.grund(auswahl, symbol))
                return
        durchlauf.bestanden(symbol, "auswahl")

        # L4/L5 (28.08.): die STRATEGIE geht mit in den Cooldown. Eine
        # Akkumulation braucht keine Frage alle 3,5 Stunden - ihr Horizont ist
        # in Jahren gemessen. Den Hebel des letzten Signals liest
        # `gesperrt_bis` selbst aus der Zeile, die es ohnehin holt.
        sperre = WH.gesperrt_bis(conn, symbol, instrument, config=config,
                                 gruppe=assetklasse, strategie=strategie)
        if sperre:
            # AUF DIE EIGENE STUFE, nicht auf "urteil" (14.08.). Hier wurde
            # NICHT gefragt - das ist ein gesparter Aufruf, kein verworfener.
            durchlauf.verloren(symbol, "wiederholung",
                               f"Cooldown bis {sperre[:16]}")
            return
    # IM TROCKENLAUF laeuft weder die Anlassmessung noch der Cooldown -
    # gebucht werden muessen beide trotzdem, sonst klafft im Trichter ein
    # Loch. Im scharfen Betrieb hat `anlass` oben schon gebucht.
    #
    # ⚠️ DER GUARD IST ZWINGEND, nicht kosmetisch. Ich hatte hier zuerst
    # geschrieben, ein zweiter Aufruf zaehle nicht doppelt, weil `Durchlauf`
    # Mengen fuehre. Nachgesehen: `bestanden_je_stufe[stufe] += 1` ist ein
    # ZAEHLER. Ohne den Guard staende im scharfen Betrieb die doppelte Zahl -
    # und der Trichter waere wieder falsch, nur in die andere Richtung.
    # ⚠️ HIER STAND EINE NACHBUCHUNG FUER DEN TROCKENLAUF - SIE ZAEHLTE
    # SEIT DEM 16.08.2026 DOPPELT (gefunden 23.08. beim Bau von A1).
    #
    # Die Begruendung war richtig, als sie geschrieben wurde: "im
    # Trockenlauf laeuft die Anlassmessung nicht, gebucht werden muss
    # sie trotzdem". Am 16.08. wurde der umschliessende
    # `if betriebsart != TROCKEN` zu `if True` (O-38, weil
    # `asset_schalter` ein reiner Leser ist) - seither LAEUFT die
    # Messung auch trocken und bucht selbst. Die Nachbuchung addierte
    # ein zweites Mal.
    #
    # GEMESSEN, nicht geschlossen: ein Trockenlauf ueber drei Symbole
    # meldete `anlass bestanden 4` bei `hinein 3`. Der Trichter war an
    # dieser Stelle nicht monoton, sondern zu gross - und niemandem
    # aufgefallen, weil kein Test die Summe gegen `hinein` prueft.
    # Genau das tut jetzt die Dauerpruefung im Paket "Auswahl".
    durchlauf.bestanden(symbol, "wiederholung")

    # --- Stufe: Urteil ---
    bc_ein["marktlage_beurteilung"] = {"lage": lagebild["lage"],
                                       "gleichlauf": gleichlauf}

    # PAKET 14: DIE ABSICHERUNGSLAGE (15.08.2026).
    #
    # Nur fuer `absicherung`, und das ist der ganze Punkt: bei 3QSS und DBPK
    # ist die Frage nicht, ob der Chart gut aussieht, sondern wieviel Risiko im
    # Depot ungedeckt ist. Der Prompt fragt danach (`_HANDELN["absicherung"]`),
    # also muss die Antwort auch in den Fakten stehen.
    #
    # SIE STEHT VOR DEM URTEIL, nicht danach - ein Faktum, das erst in der Mail
    # auftaucht, hat die Entscheidung nicht beeinflusst.
    _abs_lage = {}
    if instrument == "absicherung":
        try:
            from agent import absicherung_fakten as AB

            _abs_lage = AB.lage(conn, symbol)
            if _abs_lage:
                bc_ein["absicherungslage"] = AB.saetze(_abs_lage)
        except Exception as exc:                             # noqa: BLE001
            ergebnis.setdefault("fehler", []).append(
                f"{symbol}: Absicherungslage: {exc}")
    if betriebsart == "trocken":
        bc_roh = (aufgezeichnet.get("befund") or {}).get(symbol)
        if bc_roh is None:
            durchlauf.verloren(symbol, "urteil", "keine aufgezeichnete Antwort")
            return
    else:
        # ---- SCHRITT 4: EIN MODELLURTEIL JE ASSET, NICHT JE ZELLE ------
        #
        # Der Plan sagt: *„Asset -> EINE Faktenlage, EIN Lagebild, EIN
        # Modellurteil (teuer, einmal) -> je Zelle ein eigenes Potential."*
        # Genau das passiert hier: die erste Zelle holt das Urteil, die
        # zweite liest es aus dem Speicher.
        #
        # ⚠️ GEHOLT WIRD MIT DER EINSTIEGSFRAGE - der Obermenge. Sie fragt
        # nach Einstiegskurs und Stop; die Akkumulation braucht beides
        # nicht (`handelsauftrag._MIT_KURSEN[("spot","akkumulation")] =
        # False`, weil ein Stop die Staffelung genau dann aufhoebe, wenn
        # sie am guenstigsten kauft). Die Akkumulationszelle uebernimmt
        # daraus Richtung und Aktion; ihre eigene Lage rechnet
        # `akkumulationslage.py` deterministisch.
        #
        # ⚠️⚠️ UND DAS WIRD BENANNT, NICHT VERSCHWIEGEN. Eine Antwort auf
        # eine Frage zu benutzen, die so nicht gestellt wurde, ist genau
        # der H-Fehler ("die Anwendung reicht weiter als die Messung") -
        # er ist hier vertretbar, weil Richtung und Aktion strategieneutral
        # sind, aber er gehoert in den Trichter UND in die Mail.
        #
        # Die Alternative waere ein zweiter Modellaufruf je Asset. Das war
        # Anlauf 1 des Umbaus und ist an Kosten und Takt gescheitert.
        _gemerkt = (urteil_memo or {}).get(symbol)
        if _gemerkt is not None:
            bc_roh = _gemerkt
            durchlauf.notiz(
                symbol, "urteil",
                "Urteil aus der Einstiegsfrage uebernommen - fuer %s wurde "
                "kein eigener Modellaufruf gemacht" % strategie)
        else:
            ergebnis["aufrufe"] = ergebnis.get("aufrufe", 0) + 1
            bc_roh = _frage(client, modell,
                            RT.prompt_fuer(instrument, strategie),
                            bc_ein, "agent.rolle_trader")
            if urteil_memo is not None:
                urteil_memo[symbol] = bc_roh
    try:
        befund = RT.validiere(bc_roh, symbol, atr=atr_e, instrument=instrument,
                              strategie=strategie, kurs=kurs_e)
    except fehlertypen as exc:
        durchlauf.verloren(symbol, "urteil", type(exc).__name__)
        ergebnis["fehler"].append(f"{symbol}: {exc}")
        return
    z1 = Z1.pruefe_und_zaehle(befund, bc_ein, symbol=symbol,
                              durchlauf=durchlauf, stufe="urteil",
                              gleichlauf_wert=gleichlauf)
    durchlauf.faktorzahl(befund.get("unabhaengige_faktoren"))

    # --- Stufe: Aktion ---
    aktion = befund.get("aktion")
    # DER SCHATTEN BEKOMMT SEINE ANTWORT (23.08.2026). Hier steht fest, was
    # die Kette aus dem gewaehlten Wert gemacht hat - und erst der Vergleich
    # mit der mechanischen Auswahl sagt, ob die LLM-Ebene etwas beitraegt.
    if auswahl_lauf:
        try:
            from agent import auswahl as _AW4
            _AW4.vermerke_aktion(conn, lauf=auswahl_lauf,
                                 gruppe=assetklasse, symbol=symbol,
                                 aktion=aktion or "")
        except Exception:                                    # noqa: BLE001
            logger.exception("Auswahl-Schatten fuer %s nicht ergaenzt", symbol)

    # --- Stufe: Ausstieg - DIE VERKAUFSSEITE (14.08.2026) ---------------
    #
    # ELF VON 45 URTEILEN DES ERSTEN ECHTBETRIEBS WAREN VERKAUFSSEITE, und
    # keines hat den Nutzer erreicht: neun REDUZIEREN und zwei VERKAUFEN
    # fielen in `_schreibe_nein()` und wurden als "reines LLM-Halten" gebucht.
    # Verkaufen lag mit Nichtstun in einem Topf.
    #
    # DREI KLASSEN STATT ZWEI - Einstieg, Ausstieg, Nichts. Diese Abzweigung
    # steht VOR der Nein-Buchung, denn sonst verschluckt dieselbe Zeile wieder
    # alles, was nicht "kaufen" heisst.
    # LOKALER IMPORT, weil `_ein_asset` eine eigene Funktion ist und den
    # Sammelimport von `fuehre_lauf` NICHT sieht. Genau daran ist die erste
    # Fassung gescheitert: `VK` war undefiniert, der breite Fehlerfang hat es
    # geschluckt, und JEDES Symbol lief in den Fehlerzweig - die Pruefung
    # "ein Hebel-Lauf erzeugt eine Mail" fiel als erste um.
    from agent import verkaufsrechnung as VK

    if VK.betrifft_bestand(aktion):
        # DER BESTAND STEHT IN ZWEI TABELLEN, je nach Instrument (14.08.2026).
        #
        # DER FEHLER, DEN DAS BEHEBT. Meine erste Fassung sah IMMER in
        # `holdings` nach - der Spot-Tabelle. Ein Hebel-SCHLIESSEN auf eine
        # tatsaechlich offene Position landete damit bei "ohne Bestand" und
        # wurde als Schatten gebucht statt als Auftrag. Im Gate des ersten
        # Betriebstags stand es als "5x SCHLIESSEN ohne Bestand" - und sah aus
        # wie ein Modell, das Unsinn vorschlaegt.
        #
        # Es ist derselbe Fehler wie beim Cooldown und beim CRV-Faktor: EINE
        # Regel auf zwei Instrumente angewandt, die verschiedene Wirklichkeiten
        # haben. Ein Hebel-Bestand ist keine Menge in `holdings`, er ist eine
        # offene Position in `hebel_positions`.
        #
        # DIESELBE QUELLE WIE DIE WARTESCHLANGE (`status = 'offen'`), die sie
        # ihrerseits von `db.get_open_hebel_positions()` hat - nachgesehen,
        # nicht geraten.
        # `db` IST HIER DER PFAD, NICHT DAS MODUL (gefunden im Trockenlauf
        # ueber beide Instrumente, 15.08.2026).
        #
        # `_ein_asset` bekommt `db: str = "data/tradinginfotool.db"` - den
        # Dateinamen, den `rollen_eingabe` fuer seine eigenen Abfragen
        # braucht. Mein Verkaufszweig rief darauf `db.get_all_holdings(conn)`
        # auf, und eine Zeichenkette hat diese Methode nicht:
        #
        #     'str' object has no attribute 'get_all_holdings'
        #
        # Der Fehler landete im breiten Fehlerfang als "Bestand nicht lesbar",
        # die Menge blieb None, und JEDES Verkaufsurteil wurde damit als "ohne
        # Bestand" abgetan und zum Schatten gebucht. Die Verkaufsseite war
        # seit ihrem Bau am 14.08. vollstaendig tot.
        #
        # UND GESTERN HABE ICH DARAUF EINEN FIX GESETZT. Im Gate stand "5x
        # SCHLIESSEN ohne Bestand"; ich habe daraus geschlossen, dass die
        # falsche TABELLE abgefragt wird, und auf `hebel_positions`
        # umgestellt. Das war richtig - und es hat nichts geheilt, weil der
        # Aufruf davor schon scheiterte. Ein Symptom kann zwei Ursachen haben,
        # und die erste gefundene ist nicht automatisch die einzige.
        from database import db as DBM

        bestand_row = None
        menge = einstand = gestakt = None
        try:
            # ⚠️ S6b: BEIDE BESTAENDE, NICHT EINER JE LAUF.
            #
            # Vorher las der Spot-Lauf den Spot-Bestand und der Hebel-Lauf
            # die offene Hebelposition. Mit EINEM Lauf muss dieser eine
            # beides sehen - sonst urteilte er ueber ein Asset, dessen
            # Hebelposition er nicht kennt.
            #
            # DIE HEBELPOSITION HAT VORRANG, wenn es sie gibt: sie traegt ein
            # Ausfallrisiko (Liquidation), der Spot-Bestand nicht. Heute ist
            # das theoretisch - alle 188 Positionen sind geschlossen, die
            # letzte wurde am 22.07.2026 eroeffnet -, aber es kehrt zurueck,
            # sobald wieder eine offen ist.
            _hebelpos = next(
                (p for p in DBM.get_open_hebel_positions(conn)
                 if str(p.symbol).upper() == str(symbol).upper()), None)
            if _hebelpos is not None:
                # Eine Hebelposition fuehrt keine Stueckzahl im Sinne des
                # Spot-Bestands - `positionsmenge` ist das Gegenstueck.
                menge = getattr(_hebelpos, "positionsmenge", None)
                # Und keinen Einstandspreis je Stueck: der Buchwert steckt
                # im Positionswert. Ohne Einstand rechnet
                # `verkaufsrechnung` das Ergebnis schlicht nicht aus,
                # statt eine Zahl zu erfinden.
                bestand_row = _hebelpos
            else:
                h = next((x for x in DBM.get_all_holdings(conn)
                          if str(x.symbol).upper() == str(symbol).upper()),
                         None)
                if h is not None:
                    gestakt = getattr(h, "staked_quantity", None)
                    # ⚠️ GESAMTMENGE, NICHT NUR DIE FREIE (17.08.2026).
                    #
                    # `quantity` ist der freie Wallet-Bestand; das Gestakte
                    # kommt ADDITIV dazu (Bitpanda bucht einen Stake als
                    # Abgang aus der Wallet, siehe
                    # `rollen_eingabe.bestand()`). `verkaufsrechnung.rechne`
                    # zieht das Gestakte selbst wieder ab, um die
                    # verkaeufliche Menge zu bekommen - bekam sie bis heute
                    # aber die FREIE Menge, zog also ein zweites Mal ab.
                    #
                    # FOLGE: bei einem vollstaendig gestakten Wert ergab das
                    # `frei = 0 - gestakt` und damit `None` - kein Auftrag,
                    # obwohl der Wert gehalten wird. Bei einem teilweise
                    # gestakten war der Verkaufsbetrag zu klein.
                    menge = (float(getattr(h, "quantity", 0.0) or 0.0)
                             + float(gestakt or 0.0)) or None
                    einstand = (getattr(h, "avg_buy_price_manual_eur", None)
                                or getattr(h, "avg_buy_price_eur", None))
                    bestand_row = h
        except Exception as exc:                             # noqa: BLE001
            ergebnis.setdefault("fehler", []).append(
                f"{symbol}: Bestand nicht lesbar: {exc}")
        # ZWEI KLASSEN HINTER EINER ABZWEIGUNG (O-31, 15.08.). Ein Verkauf
        # aendert die MENGE, eine Hebelaenderung den KREDIT - beide setzen
        # einen Bestand voraus, aber sie ergeben verschiedene Anweisungen.
        if VK.ist_anpassung(aktion):
            verkauf = VK.anpassung(
                aktion=aktion, menge=menge or 0.0, kurs_eur=kurs_e,
                hebel_jetzt=getattr(bestand_row, "hebel_effektiv", None))
        else:
            verkauf = VK.rechne(aktion=aktion, menge=menge or 0.0,
                                kurs_eur=kurs_e, einstand_eur=einstand,
                                gestakt=gestakt)
        if verkauf is None:
            # KEIN BESTAND HEISST KEIN AUFTRAG. Ein VERKAUFEN auf etwas, das
            # man nicht haelt, ist kein Fehler des Modells - es kennt den
            # Bestand nicht. Es ist aber auch keine Handlung, also wird es
            # gebucht wie ein HALTEN und misst mit, wie oft das vorkommt.
            #
            # ZWEI SEHR VERSCHIEDENE GRUENDE, EIN WORT (17.08.2026). "Ohne
            # Bestand" stimmte fuer den leeren Fall - und log bei einem
            # vollstaendig GESTAKTEN Wert: dort gibt es den Bestand, er ist
            # nur nicht frei verkaeuflich. Wer das im Protokoll als "ohne
            # Bestand" liest, sucht den Fehler an der falschen Stelle.
            _grund = ("vollstaendig gestakt, nicht frei verkaeuflich"
                      if (menge or 0.0) > 0 else "ohne Bestand")
            durchlauf.verloren(symbol, "aktion", f"{aktion} {_grund}")
            if betriebsart != TROCKEN:
                _schreibe_nein(symbol=symbol, befund=befund, kurs_e=kurs_e,
                               atr_e=atr_e, tag=tag, reihe=reihe, idx=idx,
                               lagebild_id=lagebild_id, instrument=instrument,
                               strategie=strategie, conn=conn, db=db,
                               config=config, modell=modell,
                               ergebnis=ergebnis, module=module,
                               assetklasse=assetklasse, fakten=bc_ein,
                               z1=z1)
            return
        durchlauf.bestanden(symbol, "aktion")
        _sende_ausstieg(
            symbol=symbol, befund=befund, verkauf=verkauf, kurs_e=kurs_e,
            instrument=instrument, strategie=strategie, tag=tag,
            lagebild_id=lagebild_id, modell=modell, conn=conn, db=db,
            betriebsart=betriebsart, versand=versand, ergebnis=ergebnis,
            # B1/B2 (23.08.2026): der Faktensatz, der in den Prompt ging,
            # und die Reihe fuer die Merkmalsfamilien.
            fakten=bc_ein, reihe=reihe, idx=idx, z1=z1,
            # B3 (23.08.2026): die Gegenpruefung gehoert auch hierher.
            zai_client=zai_client, config=config,
            assetklasse=assetklasse)
        return

    if aktion not in SM.AKTIONEN_MIT_EINSTIEG:
        durchlauf.verloren(symbol, "aktion", aktion or "?")
        # DAS NEIN WIRD MITGESCHRIEBEN - und zwar AUFLOESBAR (14.08.).
        #
        # NUTZERSORGE, die das ausgeloest hat: *"es werden laufend Signale
        # erzeugt deren Qualitaet nie oder in Monaten bewertet werden koennen"*
        # und *"die Signale sind Wuerfel mit Bonusinfo"*.
        #
        # Beide Fragen brauchen BEIDE Arme. Ob das JA des Modells den
        # Kosten-Breakeven schlaegt, misst man an den Einstiegen; ob das NEIN
        # besser ist als der Zufall, nur an den Nein-Faellen. Die Urteile
        # fallen ohnehin - sie wurden bisher nur weggeworfen.
        #
        # KOSTET KEINEN EINZIGEN ZUSAETZLICHEN AUFRUF und halbiert die Zeit bis
        # zu einer Antwort auf die Zufallsfrage.
        #
        # MIT GERECHNETEN ZONEN, sonst ist es wertlos: `backward_tracking.
        # _hat_selbst_halten_these()` verlangt Einstieg, Stop UND Ziel - ohne
        # sie bliebe die Zeile fuer immer unaufgeloest und waere genau das,
        # wovor der Nutzer warnt. Die Zonen sind hier eine GEGENRECHNUNG, keine
        # Empfehlung: sie sagen, was passiert waere.
        if betriebsart != TROCKEN:
            _schreibe_nein(symbol=symbol, befund=befund, kurs_e=kurs_e,
                           atr_e=atr_e, tag=tag, reihe=reihe, idx=idx,
                           lagebild_id=lagebild_id, instrument=instrument,
                           strategie=strategie, conn=conn, db=db,
                           config=config, modell=modell, ergebnis=ergebnis,
                           module=module, assetklasse=assetklasse,
                           fakten=bc_ein, z1=z1)
        return

    # KEIN EINSTIEG, WO DER AUSSTIEG SCHON FAELLIG IST (O-37, 15.08.2026).
    #
    # GEMESSEN AM LAUF DESSELBEN TAGES, und es war kein Grenzfall: von den
    # sieben Symbolen, deren deterministische Ausstiegsrechnung SCHLIESSEN
    # sagte, bekamen **sieben** eine Eroeffnungsempfehlung - ALGO, ETH, INJ,
    # SUI, TAO, TURBO, VIRTUAL.
    #
    # DIE MAIL WUSSTE ES LAENGST. `signal_mail.baue_mail()` schreibt in genau
    # diesem Fall "Kein zusaetzlicher Einstieg: der Ausstieg steht auf
    # SCHLIESSEN" und zeigt Zone, Stop und Ziel gar nicht erst. Die
    # SIGNALZEILE wurde trotzdem als EROEFFNEN ueber 500 EUR geschrieben.
    #
    #     Der Text sagte nein, die Datenbank sagte ja.
    #
    # Und die Datenbank ist es, die spaeter gemessen wird: die Trefferbilanz
    # haette diese Zeilen als Einstiege gezaehlt, die nie empfohlen wurden.
    #
    # DAS IST KEIN QUALITAETSFILTER und braucht keine Prognose. Er behauptet
    # nicht, dass der Einstieg schlecht waere - er stellt fest, dass die
    # Nachricht ihn ohnehin verweigert. Eine Empfehlung, die im eigenen Text
    # zurueckgenommen wird, traegt keine Information.
    #
    # DAS URTEIL BLEIBT GEMESSEN: es wird als Nein-Fall geschrieben, mit
    # gerechneten Zonen, genau wie ein NICHTS_TUN. Was wegfaellt, ist die
    # widerspruechliche Mail - nicht der Messwert.
    # NUR BEI EINEM ECHTEN BESTAND. `ist_bestand` unterscheidet die offene
    # Position von der alten Signalzeile: von den neun SCHLIESSEN-Zeilen des
    # 15.08. bezogen sich nur DREI auf einen tatsaechlichen Bestand. Eine
    # abgelaufene Empfehlung von vorletzter Woche darf keinen neuen Einstieg
    # verhindern - das waere eine Sperre ohne Gegenstand.
    _fuehrung = _fuehrung_zu(ergebnis, symbol, instrument)
    if (_fuehrung.get("ist_bestand")
            and str(_fuehrung.get("empfehlung") or "").startswith("SCHLIESSEN")):
        durchlauf.verloren(symbol, "aktion",
                           f"{aktion}, aber Ausstieg steht auf SCHLIESSEN")
        if betriebsart != TROCKEN:
            _schreibe_nein(symbol=symbol, befund=befund, kurs_e=kurs_e,
                           atr_e=atr_e, tag=tag, reihe=reihe, idx=idx,
                           lagebild_id=lagebild_id, instrument=instrument,
                           strategie=strategie, conn=conn, db=db,
                           config=config, modell=modell, ergebnis=ergebnis,
                           module=module, assetklasse=assetklasse,
                           fakten=bc_ein, z1=z1)
        return
    durchlauf.bestanden(symbol, "aktion")


    # --- Stufe: Geometrie + Risikoschicht ---
    # HIER HAENGT `toepfe` ENDLICH DRAN. Bis zum 13.08. war das Modul gebaut
    # und von nichts aufgerufen; `entscheidungsrechnung` bekam den Deckel als
    # Parameter, den niemand fuellte.
    # DER BESTAND DES TOPFES, nicht die Null. Bis zum 13.08. stand hier fest
    # `belegt_eur=0.0` - der Topf meldete sich bei JEDEM Signal als vollstaendig
    # frei, und der Deckel konnte nie greifen. Im Live-Lauf bekamen drei
    # Hebel-Signale je 500 EUR aus einem 500-EUR-Topf.
    # RM-4: was nach der Reserve ueberhaupt noch einsetzbar ist. Im
    # Trockenlauf None - er hat keine Verbindung zu einer echten Lage.
    cash_frei = TO.cash_frei_eur(conn, config) if betriebsart != TROCKEN else None
    # ⚠️ DER TOPF FOLGT DER ZAHL, NICHT DEM LAUF (19.08.2026).
    #
    # Vorher stand hier `instrument` - also das Etikett des LAUFS. Seit S5
    # faellt in vier von fuenf Faellen Hebel 1,0 an; diese Signale belegten
    # trotzdem den HEBELTOPF (3.000 EUR, bei 1.000 EUR Einsatz also drei
    # Positionen). Der Hebeltopf fuellte sich mit Geschaeften, die keine
    # Hebelgeschaefte sind - und der Spot-Topf blieb leer.
    #
    # KEIN ZIRKELBEZUG MEHR. `Hebel = Verlustanteil / Stopabstand` enthaelt
    # weder Topf noch Einsatz; das Etikett steht also fest, BEVOR der Topf
    # gebraucht wird. Genau deshalb sind F3 und F4 aus 88.5 entfallen.
    _topf_instrument = instrument
    try:
        _vor = ER.dimensioniere(
            kurs=kurs_e, atr=atr_e,
            k=(BE.stop_min_atr(config)
               or ER.GRENZEN["stop_min_atr"]),
            verlustanteil=BE.verlustanteil(instrument, config),
            einsatz_eur=BE.einsatz_eur(instrument, strategie, config,
                                       assetklasse),
            marke_preis=_marke_am_stop(_bloecke_anlass,
                                       befund.get("richtung") == "SHORT"),
            umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
            ist_short=(befund.get("richtung") == "SHORT"),
            # ⚠️ S6b: DIE HANDELBARKEIT KOMMT AUS DER GRUPPE, NICHT AUS
            # DEM LAUF. Vorher stand hier `(instrument == "hebel")` - mit
            # dem Wegfall des zweiten Laufs waere daraus dauerhaft False
            # geworden, und der Hebel waere still verschwunden.
            # ⚠️ NICHT `_AK` - DER NAME GEHOERT `anlass_kalender` (Zeile
            # 1348). Meine erste Fassung nahm ihn, und weil dieser Aufruf
            # DAVOR steht, waere es ein UnboundLocalError gewesen - den der
            # breite Fehlerfang darunter still geschluckt haette. Dieselbe
            # Falle wie `_LB` am 20.08. und `assetklasse` am 14.08.
            hebel_handelbar=_AKL.hebel_handelbar(assetklasse))
        # ⚠️ S6b: DER TOPF FOLGT DEM ERGEBNIS, NICHT DEM LAUF. Der zweite
        # Zweig (`"spot" if instrument == "hebel"`) war die Ruecknahme des
        # Lauf-Etiketts, wenn die Rechnung keinen Hebel ergab - es gibt
        # keinen Hebel-Lauf mehr, den man zuruecknehmen muesste.
        # ⚠️⚠️ DIE TAKTISCHE ZELLE FAELLT OHNE HEBEL WEG (01.09.2026).
        #
        # Nutzerentscheidung, woertlich: *„nur wenn die Rechnung tatsaechlich
        # einen Hebel ergibt waere mir natuerlich lieber."*
        #
        # Betroffen ist ausschliesslich die zusaetzliche Einstiegszelle eines
        # Assets, das ohnehin akkumuliert wird (BTC/ETH/SOL). Ihr Zweck ist
        # der kurzfristige, gehebelte Trade neben dem langfristigen Aufbau -
        # A2 im Plan. Ergibt die Rechnung KEINEN Hebel, waere sie ein
        # gewoehnlicher Spot-Einstieg mit Stop, und den will der Nutzer fuer
        # diese drei Assets nicht: dort wird gestaffelt gekauft.
        #
        # ⚠️ ES WIRD GEZAEHLT UND BEGRUENDET, nicht still uebersprungen. Ein
        # Filter, der seine Wirkung verbirgt, ist im Projekt mehrfach teuer
        # geworden.
        #
        # ⚠️ UND ES BETRIFFT NUR DIESE ZELLE. Ein Asset ohne Akkumulation
        # (LINK, TAO, ...) behaelt seinen Einstieg unveraendert - ob er als
        # Spot oder gehebelt ausgefuehrt wird, faellt dort weiterhin aus der
        # Rechnung an und aus dem Freigabeschalter.
        if ist_taktisch and _vor.get("etikett") != "hebel":
            durchlauf.verloren(
                symbol, "geometrie",
                "taktische Zelle ohne Hebel - dieses Asset wird akkumuliert, "
                "ein Spot-Einstieg mit Stop ist hier nicht vorgesehen")
            return
        _topf_instrument = ("hebel" if _vor["etikett"] == "hebel"
                            else instrument)
        # I-2 (28.08.2026): DIE PAARPRUEFUNG DORT, WO DAS ETIKETT ENTSTEHT.
        #
        # ⚠️ `pruefe_auftrag` laeuft EINMAL am Lauf-Anfang - mit der VORGABE
        # ("spot"/"einstieg"). Danach setzt `strategie_fuer` fuer den Kern
        # `akkumulation`, und die Rechnung kann daraus `etikett = "hebel"`
        # machen. Damit entsteht `hebel x akkumulation` - ein Paar, das
        # `ERLAUBTE_PAARE` ausdruecklich ausschliesst, weil die Finanzierung
        # JEDEN Tag kostet und eine Akkumulation bewusst lange laeuft.
        #
        # Gemessen, wie leicht das eintritt: bei Krypto ergibt die Rechnung
        # das Hebel-Etikett schon ab einem Stop von 10 % - also praktisch
        # immer. Der Topf folgte dem Etikett; Geld kam aus dem Hebeltopf fuer
        # eine Strategie, die keinen Hebel haben darf.
        #
        # ⚠️ ES WIRD GEMELDET, NICHT GESPERRT. Ein Abbruch hier naehme dem
        # Kern seine Meldung, und die Ursache liegt nicht am Asset, sondern
        # an der Stopregel (Rauschboden gegen Modellurteil). Wer sperrt,
        # versteckt den Konflikt; wer meldet, macht ihn zaehlbar.
        if _topf_instrument == "hebel":
            # I-1b (28.08.2026): DER HEBEL-SCHALTER GREIFT WIEDER - hier.
            #
            # ⚠️ `asset_schalter` prueft `if i == "hebel"`, und `instrument`
            # ist seit S6b immer "spot". Der Schalter, mit dem der Nutzer je
            # Asset entscheidet, ob es ueberhaupt gehebelt beurteilt werden
            # darf, wurde damit NIE gefragt - die GUI zeigte eine Einstellung
            # ohne Wirkung.
            #
            # ER KANN DORT AUCH NICHT MEHR GEFRAGT WERDEN: `asset_schalter`
            # laeuft VOR der Rechnung, und vorher gibt es kein Etikett. Die
            # Frage "darf dieses Asset gehebelt werden?" ist erst
            # beantwortbar, wenn feststeht, dass es ein Hebelgeschaeft waere.
            #
            # ⚠️ MELDEN UND ZURUECKSTUFEN, NICHT VERWERFEN. Nutzervorgabe:
            # "ueberall moeglich, aber nur dort Signale erzeugen, wo ich das
            # selektiv moechte." Ein abgeschaltetes Asset soll kein
            # HEBEL-Signal bekommen - aber sein Spot-Signal behalten. Der
            # Topf faellt deshalb auf "spot" zurueck; verworfen wird nichts.
            try:
                # ⚠️ `db` IST HIER DER PFAD, NICHT DAS MODUL - der Docstring
                # dieser Funktion sagt es ausdruecklich, und ich habe es
                # trotzdem zuerst falsch geschrieben. `db.get_...` auf einem
                # String wirft AttributeError; mein eigener Fehlerfang haette
                # ihn gefangen und den Hebel dann fuer JEDES Asset
                # abgeschaltet - fail-soft mit falschem Verhalten, still.
                # Achte Namensfalle in drei Tagen.
                import database.db as _dbmod
                if not _dbmod.get_hebel_pruefung_erlaubt(conn, symbol):
                    _topf_instrument = instrument
                    ergebnis.setdefault("hebel_abgeschaltet", []).append(symbol)
                    logger.info(
                        "%s: Hebel fuer dieses Asset abgeschaltet - die "
                        "Rechnung ergab das Hebel-Etikett, gefuehrt wird es "
                        "als %s.", symbol, instrument)
            except Exception as _hs:                         # noqa: BLE001
                # EIN LESEFEHLER HEISST NICHT "ERLAUBT" - dieselbe Linie wie
                # in `asset_schalter`. Aber auch nicht "verworfen": der
                # sichere Zustand ist der ungehebelte.
                _topf_instrument = instrument
                logger.warning("Hebel-Schalter fuer %s nicht lesbar (%s) - "
                               "als %s gefuehrt", symbol, _hs, instrument)

        if _topf_instrument == "hebel":
            try:
                # ⚠️ `AuftragUngueltig` IST HIER NICHT IM SCOPE - sie wird in
                # `fuehre_lauf` importiert, nicht in dieser Funktion. Vor dem
                # ersten Lauf gefunden (AST-Probe), nicht im Betrieb: der
                # breite Fehlerfang darunter haette den NameError geschluckt
                # und die Meldung waere nie erschienen. Siebtes Mal dieselbe
                # Falle in drei Tagen.
                from agent.handelsauftrag import AuftragUngueltig as _AU
                pruefe_auftrag(_topf_instrument, strategie)
            except _AU as _pf:
                ergebnis.setdefault("paarkonflikt", []).append(
                    f"{symbol}: {strategie} + Etikett hebel - {_pf}")
                logger.warning(
                    "ACHTUNG: %s laeuft als %s, die Rechnung ergibt aber das "
                    "Etikett 'hebel' - ein Paar, das die Matrix ausschliesst. "
                    "Ursache ist die Stopweite, nicht das Asset.",
                    symbol, strategie)
    except Exception as exc:                                 # noqa: BLE001
        # FAIL-SOFT MIT VERMERK. Faellt die Vorabrechnung aus, gilt das alte
        # Verhalten - aber es steht im Lauf, statt still zu passieren.
        ergebnis.setdefault("fehler", []).append(
            f"{symbol}: Topfzuordnung aus dem Lauf statt aus der Zahl: {exc}")
    frei = TO.frei_eur(_topf_instrument, config=config,
                       belegt_eur=(TO.belegt_eur(conn, _topf_instrument)
                                   if betriebsart != TROCKEN else 0.0))
    # DIE BETRAEGE KOMMEN AUS `betraege`, NICHT AUS DIESER ZEILE. Vorher standen
    # hier 75.0 und 500.0 - Zahlen, die niemand hergeleitet hatte und die jedes
    # Signal gleich gross machten.
    try:
        rechnung = ER.rechne(kurs=kurs_e, atr=atr_e,
                             # Nur fuer den Trichter: welche Faktoren
                             # gelten hier? (93 A/A2)
                             assetklasse=assetklasse,
                             risiko_eur=BE.risiko_eur(instrument, strategie,
                                                      config, assetklasse),
                             instrument=instrument,
                             betrag_wunsch_eur=BE.einsatz_eur(
                                 instrument, strategie, config, assetklasse),
                             topf_frei_eur=frei, cash_frei_eur=cash_frei,
                             umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
                             # DIE RICHTUNG KOMMT VOM MODELL (Paket 13) und
                             # dreht Stop, Ziel und Liquidation. Bei Spot gibt
                             # es sie nicht - dort ist LONG die einzige Lage.
                             ist_short=(befund.get("richtung") == "SHORT"),
                             # S1, Kapitel 90: der Rauschboden aus der
                             # Konfiguration. Ohne Eintrag None - dann
                             # gilt die Vorgabe und nichts aendert sich.
                             # ⚠️ A1: DIE HANDELBARKEIT DER GRUPPE, NICHT
                             # DER LAUF. Seit S6b heisst `instrument` fuer
                             # Krypto immer "spot" - ohne diese Zeile ergibt
                             # die Rechnung nie wieder einen Hebel.
                             hebel_handelbar=_AKL.hebel_handelbar(assetklasse),
                             stop_min_atr=BE.stop_min_atr(config),
                             # S2, Kapitel 90: die Marke auf der
                             # STOPSEITE. Sie liegt vorerst ungenutzt im
                             # Ergebnis - angeschlossen wird sie in S5.
                             marke_stop_eur=_marke_am_stop(
                                 _bloecke_anlass,
                                 befund.get("richtung") == "SHORT"),
                             # ⚠️ KEIN DECKEL MEHR (17.08.2026, gemessen).
                             # Heute frueh reichte diese Stelle den
                             # naechsten Widerstand an `_ziel` durch. Das
                             # Ergebnis: 44 von 44 Symbolen gedeckelt,
                             # 98 % unter CRV 0,5, Median 0,21 - weil auf
                             # Tagesfraktalen im Median DREI Marken
                             # zwischen Kurs und 2R-Ziel liegen.
                             #
                             # Die Marken stehen jetzt in der Mail, statt
                             # das Ziel zu begrenzen. `_marke_im_weg`
                             # bleibt als Werkzeug bestehen - wer den
                             # Deckel je will, findet hier, warum er
                             # abgeschaltet wurde.
                             kostenklasse=_kostenklasse(assetklasse),
            umgeworfen_tage=_tage_bis(
                                 befund.get("umgeworfen_bis"), tag))
    except ER.RechnungBlockiert as exc:
        durchlauf.verloren(symbol, "geometrie", str(exc)[:40])
        return
    durchlauf.bestanden(symbol, "geometrie")
    durchlauf.bestanden(symbol, "risikoschicht")

    # --- Stufe: Entscheider - ZAEHLT, verwirft nicht ---
    #
    # DIE FAMILIEN WERDEN HIER GEBRAUCHT, nicht erst in der Mail: sie sind seit
    # 15.1 der Konstellationsschluessel. Deshalb steht die Berechnung jetzt vor
    # dem Entscheider statt darunter - dieselben Werte, eine Stelle.
    kern = FB.werte_aus_reihe([k.high for k in reihe], [k.low for k in reihe],
                              [k.close for k in reihe],
                              [getattr(k, "volume", 0) or 0 for k in reihe],
                              i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
    # DIE KOSTENKLASSE MUSS MIT (17.3). Vorher lief das auf die Vorgabe
    # "krypto" hinaus - bei der ersten Aktie haette der Entscheider mit
    # Krypto-Gebuehren (1,5 % je Seite) statt Boersengebuehren (1 EUR fix
    # + 0,25 % Spread) gerechnet, und der Breakeven waere grob falsch
    # gewesen, ohne dass irgendetwas meldet.
    # ---- DIE BEWERTUNG, VOR DER ENTSCHEIDUNG (U-1, 30.08.2026) ----
    #
    # ⚠️ H WURDE BIS HEUTE 145 ZEILEN SPAETER GERECHNET - also NACH Stufe 11.
    # Die Entscheidungsstufe kannte damit den einzigen tragenden Beitrag des
    # Systems nicht. Hier steht nur die BERECHNUNG; die Mailzeilen entstehen
    # unveraendert an ihrer alten Stelle aus demselben Ergebnis.
    #
    # Die Eingaben liegen alle vor: `rechnung` seit Zeile 1517,
    # `_bloecke_anlass` seit Zeile 822.
    _ist_akkumulation = str(strategie or "").strip().lower() == "akkumulation"
    _vf_bewertung = None
    try:
        from agent import vorfilter as _VF0
        if _ist_akkumulation:
            raise _KeinHBeiAkkumulation
        _vf_bewertung = _VF0.bewerte(
            (_bloecke_anlass or {}).get("_marken_werte"),
            rechnung.get("stop_eur"), rechnung.get("ziel_eur"),
            bool(rechnung.get("ist_short")), assetklasse,
            # ⚠️ NUR FUER DIE MAIL (R2): ohne den Einstieg bleiben in der
            # Mail Rohpreise stehen, und die sagen einem Leser nichts.
            einstieg_eur=rechnung.get("einstieg_eur"))
    except _KeinHBeiAkkumulation:
        # KEIN FEHLER, SONDERN DIE REGEL - deshalb ohne `logger.exception`.
        _vf_bewertung = None
    except Exception:                                        # noqa: BLE001
        logger.exception("Vorfilter fuer %s uebersprungen", symbol)
        _vf_bewertung = None

    kosten_r = TB.kosten_r_aus_stop(
        kurs_e, rechnung["stop_eur"], klasse=_kostenklasse(assetklasse),
        position_eur=rechnung["betrag_eur"],
        # DIE DREI, DIE DIE UEBRIGEN KOSTENARTEN AUFSCHLIESSEN: das Instrument
        # entscheidet die Art, der Hebel die Hoehe des geliehenen Kapitals, die
        # Haltedauer die Tagesgebuehr und die laufende ETP-Gebuehr.
        instrument=instrument, hebel=rechnung.get("hebel"),
        tage=rechnung.get("haltedauer_tage"))
    # DIE EIGENE BILANZ, NICHT EIN LEERES DICT. Bis zum 13.08. stand hier
    # `TB.bewerte({}, ...)` - der Entscheider las eine leere Tabelle und fiel
    # damit IMMER auf die Basisrate zurueck, auch wenn Faelle vorlagen. Zusammen
    # mit dem fehlenden Schreiben (Schritt 1) waren das zwei Luecken in Reihe:
    # nichts wurde gezaehlt, und das Nichts wurde auch nicht gelesen.
    bewertung = TB.bewerte(bilanz or {}, TB.merkmale(
        vola_perzentil=TB._prozent((kern or {}).get("schwankung_perzentil")),
        spanne_perzentil=TB._prozent((kern or {}).get("momentum_perzentil")),
        gleichlauf=TB._band_grob((kern or {}).get("volumen_perzentil"))),
        kosten_r=kosten_r or 0.0, crv=rechnung["crv"])
    # ---- STUFE 11 ENTSCHEIDET AB JETZT UEBER DAS POTENTIAL (U-1) ----
    #
    # ⚠️ VORHER: `bewertung["traegt"]` aus `trefferbilanz` - und die misst mit
    # `(1 + kosten_r)/(1 + CRV)`, also MIT Bitpanda-Gebuehren. Bei 5 % Stop
    # verlangte sie 53 % Trefferquote, wo die Geometrie 33 % hergibt. Sie sagte
    # damit bei praktisch JEDEM Signal "traegt sich nicht" - was nur deshalb
    # nicht auffiel, weil die Stufe ausschliesslich zaehlt.
    #
    # Nutzervorgabe 30.08.: *"die Bewertung soll ohne Wirtschaftlichkeit,
    # Gebuehren usw. erfolgen - also neutral"*. `potential.rechne()` ruft
    # `wahrscheinlichkeit` mit `gebuehr_je_seite=0.0`.
    #
    # ⚠️ DIE TREFFERBILANZ BLEIBT - als Auskunft in der Mail. Nur ENTSCHIEDEN
    # wird nicht mehr mit ihr.
    _potential = None
    try:
        from agent import potential as _PT
        # ⚠️ DIE MERKMALE AUS DEM QUERSCHNITT (2e). Nur Schluessel, deren
        # Wert tatsaechlich vorliegt - ein fehlendes Fuenftel darf NICHT als
        # 0 ankommen, sonst saehe "unbekannt" aus wie "bestes Fuenftel".
        # ⚠️ DURCHGEREICHT, NICHT GEGRIFFEN. Meine erste Fassung von 2e las
        # hier `_raenge` - eine Variable aus `fuehre_lauf`, die diese
        # Funktion nicht sieht. Exakt die Falle, die der Docstring oben seit
        # dem 15.08. fuer `watchlist` beschreibt: im Betrieb ein NameError,
        # den der breite Fehlerfang schluckt, und der Beitrag traegt still
        # null. Gefunden hat es Paket "Kalibrierung", nicht ich.
        _mr = (marktraenge or {}).get(symbol) or {}
        _merkmale = {k: _mr[k] for k in ("funding_fuenftel",
                                         "turnover_fuenftel",
                                         "schnitt_fuenftel")
                     if _mr.get(k) is not None}
        _potential = _PT.rechne(
            crv=rechnung["crv"], stop_relativ=rechnung.get("stop_relativ"),
            klasse=assetklasse, instrument=instrument, strategie=strategie,
            h=(_vf_bewertung or {}).get("h"),
            merkmale=_merkmale or None)
    except Exception:                                        # noqa: BLE001
        logger.exception("Potential fuer %s nicht rechenbar", symbol)

    if _potential is None:
        # ⚠️ KEINE ZAHL HEISST NICHT "TRAEGT NICHT". Wer bei fehlender Rechnung
        # verwirft, sperrt bei jedem Datenausfall den ganzen Lauf - genau der
        # Deadloop, aus dem das System kommt.
        durchlauf.bestanden(symbol, "entscheider")
    else:
        from agent import potential as _PT2
        # ⚠️⚠️ ZWEI VERSCHIEDENE GRUENDE, NICHT EINER (31.08.2026).
        #
        # Bis heute las Stufe 11 nur die Zahl - und ein Wert OHNE jedes
        # Merkmal bekam dieselbe Behandlung wie einer mit gemessen
        # schlechten Werten. Beide landen bei rund 0,000.
        #
        # Gemessen am 31.08. (`pruefe_beitragsabdeckung.py`): 29 von 56
        # Werten der Watchlist haben KEINEN Beitrag - bei allen Klassen
        # ausser Krypto sind es 100 %. Mit verwerfender Stufe 11 waere das
        # ein Ausschluss nach DATENLAGE, nicht nach Qualitaet.
        #
        # ⚠️ VORFILTER H HATTE DIESES PROBLEM NIE: er wurde je Anker aus
        # den Marken gerechnet und galt fuer jeden Wert. Wer ihn durch
        # Merkmale mit Luecken ersetzt, muss die Luecke benennen - sonst
        # verschwinden Werte lautlos aus dem System.
        #
        # Der Trichter bekommt deshalb ZWEI Gruende. Gesperrt wird in
        # beiden Faellen (keine Empfehlung ohne Grund), aber in der
        # Auswertung ist unterscheidbar, ob eine MESSUNG oder eine
        # DATENLUECKE dahinterstand.
        # ⚠️⚠️ DREI ZUSTAENDE, NICHT ZWEI (31.08.2026, gefunden von der
        # Kettensimulation gegen die Notebook-Produktion).
        #
        # Die erste Fassung von G-6 kannte nur "bewertbar ja/nein" und
        # sperrte alles ohne Beitrag. Ergebnis der Simulation gegen die
        # echten Produktionsdaten: **null Signale ueber alle fuenf
        # Gruppen.** Nicht wegen der Datenlage einzelner Werte, sondern
        # eine Ebene darueber - vier von fuenf Assetklassen haben keinen
        # einzigen registrierten Beitrag:
        #
        #     krypto      3 (Funding, Turnover, Schnittabstand)
        #     aktien      0        themen_etf  0
        #     rohstoffe   0        hedge       0
        #
        # Eine Sperre aus diesem Grund ist ein Verstoss gegen Regel 4:
        # "fuer diese Klasse haben wir nie gemessen" ist ein FAKT ueber
        # unseren Kenntnisstand, keine Aussage darueber, was kommt. Der
        # Filter haette nach DATENLAGE gesperrt, nicht nach Qualitaet -
        # derselbe Fehlertyp wie bei H, nur eine Ebene hoeher.
        #
        # Die Nutzervorgabe deckt beide Faelle mit einem Satz (31.08.):
        # *"Die Scharfschaltung muss und darf erst erfolgen, wenn alle
        # Assets einen Beitrag haben."* Fuer Krypto ist sie erfuellt
        # (43 von 43 seit P2), fuer die vier anderen noch nicht.
        if not _potential.vermessen:
            # NICHT VERMESSEN - zaehlen, nicht sperren. Der Trichter
            # weist es aus, damit die Luecke sichtbar bleibt und nicht
            # als stilles Durchwinken verschwindet.
            durchlauf.notiz(
                symbol, "entscheider",
                "Klasse %s ist nicht vermessen - Stufe 11 zaehlt nur"
                % (assetklasse or "?"))
        elif not _potential.bewertbar:
            # VERMESSEN, ABER OHNE WERT - das ist ein Mangel DIESES
            # Assets, und hier sperrt die Stufe zu Recht.
            durchlauf.verloren(
                symbol, "entscheider",
                "keine Datengrundlage - kein Beitrag bestimmbar")
            return
        elif not _potential.traegt_hier:
            # ⚠️⚠️ DIE SCHWELLE JE DATENLAGE (31.08.2026, Nutzerentscheidung).
            #
            # Hier stand `_PT2.traegt(_potential.wert_r)` - eine FESTE
            # Schwelle fuer alle. Das Potential ist aber die SUMME der
            # Beitragspunkte, und die Datenlage ist ungleich:
            #
            #     nur Funding    max +0,0390 R    36 von 43 Werten
            #     beide          max +0,1335 R     7 von 43 Werten
            #
            # Eine feste Schwelle ueber 0,039 R waere fuer 36 von 43 Werten
            # UNERREICHBAR gewesen - eine Sperre nach Datenlage statt nach
            # Qualitaet (Regel 4). Gemessen an den echten Signalen: ab
            # 0,040 R kam NICHTS mehr durch.
            #
            # `Potential.traegt_hier` misst gegen die Schwelle SEINER
            # Datenlage - denselben ANTEIL der erreichbaren Spanne. Die
            # volle Datenlage behaelt die Vorgabe als Bezug.
            durchlauf.verloren(
                symbol, "entscheider",
                "Potential %.3f R unter der Schwelle %.3f R (Datenlage: "
                "max %.3f R erreichbar)"
                % (_potential.wert_r, _potential.schwelle,
                   _potential.erreichbar_max))
            # ⚠️⚠️ G-6, ZWEITER TEIL (31.08.2026) - UND DER WICHTIGERE.
            #
            # `rollen_gate.NUR_ZAEHLEN = ()` allein aendert nur die
            # BUCHHALTUNG: der Trichter bucht den Verlust, und der Ablauf
            # lief hier trotzdem weiter - Mail, Signal, DB-Zeile. Die
            # Kettensimulation zeigte es unmittelbar: "0 bestanden (2
            # verloren)" und daneben "5 Signale, 6 Mails".
            #
            # Ein Filter, der zaehlt und nicht abbricht, ist kein Filter.
            # Genau das war der Zustand seit U-1.
            #
            # ⚠️ WAS DIESES `return` NICHT TUT: es unterdrueckt nichts
            # still. Der Verlust steht mit Grund und Zahl im Trichter
            # ("Potential -0,000 R unter der Schwelle 0,010 R"), und der
            # Lauf meldet ihn wie jede andere Stufe.
            return
        durchlauf.bestanden(symbol, "entscheider")

    # --- Die Mail ---
    # UND HIER `faktenblock_quellen` - das zweite Modul ohne Aufrufer.
    zusatz, _fehlt = FQ.abbilden(bc_ein.get("fakten_roh"),
                                 bereich=_bereich(assetklasse, instrument),
                                 position_eur=rechnung["betrag_eur"],
                                 hebel=rechnung.get("hebel"))
    block = FB.baue(_bereich(assetklasse, instrument), kern_werte=kern,
                    zusatz_werte=zusatz, symbol=symbol) if kern else []
    # DIE MAIL ALS BAUPLAN, NICHT ALS FERTIGER TEXT. Die Zeilen der zweiten
    # Meinung entstehen erst, wenn Z.ai geantwortet hat - und darauf wartet
    # die Kette bis zu vier Minuten. Sie danach in einen fertigen String
    # hineinzuflicken hiesse, die Reihenfolge der Abschnitte an zwei Orten zu
    # pflegen; ein Bauplan kennt sie an einem.
    # --- O-19 bis O-23: die fuenf Bloecke, die an nichts angeschlossen waren
    #
    # `baue_mail` kann sechzehn Eingaben darstellen; die Kette uebergab elf.
    # Bestand, Marken, Umfeld, Ausstieg und Coin-Fakten blieben leer - deshalb
    # las sich die Mail generisch, obwohl die Vorlage es nicht ist.
    #
    # DIE SAETZE GAB ES LAENGST. Sie stehen im Faktentext, der ans Modell geht:
    # neun Saetze je Asset, darunter "X ist nicht im Bestand", "Der naechste
    # Widerstand liegt ... bei 0,0111 EUR". Sie wurden nur nie in die Mail
    # gereicht. `lagebeschreibung.geteilt()` gibt jetzt dieselben Saetze nach
    # Bloecken - dieselbe Quelle, kein zweiter Textweg.
    # DIE BLOECKE, DIE DAS MODELL GELESEN HAT - nicht neu gerechnete.
    #
    # Bis heute stand hier ein ZWEITER `LB.geteilt()`-Aufruf. Er war am 14.08.
    # richtig gebaut; seit dem 15.08. legt `baue_fall(bloecke_ziel=...)`
    # dieselben Bloecke fuer den Anlassfilter ohnehin daneben, und damit war
    # der zweite Aufruf eine Kopie - genau die Kopierfalle, gegen die sein
    # eigener Kommentar argumentierte.
    #
    # ER LIEF AUSSERDEM AUSEINANDER, und zwar an zwei Stellen:
    #
    #   ATR IN DER FALSCHEN WAEHRUNG. Er bekam `atr_e` (EUR), waehrend
    #   `baue_fall` `atr_bis()` (Quellwaehrung) uebergibt. `_niveaus()` rechnet
    #   die Abstaende gegen die QUELLreihe - die Mail zeigte dem Leser also
    #   andere Schwankungsbreiten als dem Modell, bei USD-Assets um den
    #   Wechselkurs daneben. Derselbe Fehler wie am 12.08. in
    #   `leite_zonen_ab()`, nur auf der Anzeigeseite.
    #
    #   NEUE BLOECKE FEHLTEN. Seit Phase I gibt es `hebelgeometrie`,
    #   `referenz` und `luecken`. Der zweite Aufruf kannte weder den
    #   Sektorbezug noch die Finanzierung - er haette sie stillschweigend
    #   weggelassen, und die Mail waere aermer gewesen als der Prompt.
    #
    # EINE QUELLE, EINE RECHNUNG. Was das Modell liest, liest der Nutzer.
    _bloecke = _bloecke_anlass or {}

    # DAS UMFELD - das Lagebild, das Rolle A einmal je Lauf rechnet. Es ging
    # bisher NUR ins Modell; der Leser sah das Urteil, nicht die Lage.
    _lage = []
    _mb = (bc_ein.get("fakten_roh") or {}).get("marktlage_beurteilung") or {}
    if _mb.get("lage"):
        _lage.append(str(_mb["lage"]))
    _kl = _mb.get("klasse") or {}
    if _kl.get("beurteilung"):
        _lage.append(f"{_kl.get('klasse', '?').capitalize()}: "
                     f"{_kl['beurteilung']}")

    # 93 D: BEKANNTE TERMINE - Anzeige, kein Gate. Das Deckelproblem ist
    # durch die Bauform geloest: diese Zeilen sperren nichts, und sie sagen
    # ausdruecklich, welche Ereignisarten NICHT abgedeckt sind.
    try:
        from agent import anlass_kalender as _AK
        _anlaesse = _AK.saetze(symbol, assetklasse)
    except Exception:                                        # noqa: BLE001
        _anlaesse = []

    # 93 B Punkt 3: DER RANGPLATZ ALS TATSACHE, mit dem gemessenen Wert
    # daneben. Kein Gate - er sperrt nichts und empfiehlt nichts.
    try:
        from agent import drift as _DR
        _leben0 = _DR.saetze(reihen, symbol, assetklasse)
    except Exception:                                        # noqa: BLE001
        _leben0 = []

    # 93 C: LEBENDIGKEIT ALS MERKMAL, mit Warnhinweis solange die eigene
    # Reihe zu kurz ist. Faellt sie aus, fehlt eine Zeile - nie die Mail.
    try:
        # ⚠️ NICHT `_LB` - DER NAME GEHOERT SCHON `lagebeschreibung`
        # (Kollision, gefunden 20.08.2026). Mein Import vom 19.08. hat ihn
        # ueberschrieben; die frueheren Verwendungen liefen noch richtig,
        # weil sie VOR dieser Zeile stehen. Erst der Zugriff auf
        # `BLOCK_REIHENFOLGE` weiter unten flog auf - mit einem
        # AttributeError, der das falsche Modul nannte.
        from agent import lebendigkeit as _LEB
        _leben = _LEB.saetze(conn, symbol, assetklasse)
    except Exception:                                        # noqa: BLE001
        _leben = []
    # A1d - DIE BEGRUENDUNG DER AUSWAHL, ganz oben in diesem Block
    # (23.08.2026). Sie steht VOR dem Rangplatz, weil sie die
    # Entscheidung traegt und er nur die Tatsache ist. Der
    # Marktzustand haengt daran - als Angabe, die nichts sperrt.
    try:
        from agent import auswahl as _AW3
        _aw_zeilen = _AW3.saetze(auswahl, symbol, marktzustand)
    except Exception:                                        # noqa: BLE001
        logger.exception("Auswahl-Saetze fuer %s uebersprungen", symbol)
        _aw_zeilen = []
    if _aw_zeilen:
        _leben0 = _aw_zeilen + ([""] if _leben0 else []) + _leben0

    # Rangplatz zuerst, Lebendigkeit darunter - beide sind Merkmale ueber
    # den WERT, keine Rechnung; sie gehoeren nebeneinander.
    if _leben0:
        _leben = _leben0 + ([""] if _leben else []) + _leben
    if _anlaesse:
        _leben = _leben + ([""] if _leben else []) + _anlaesse

    # V1 (22.08.2026): H ALS SCHATTEN. Rechnet aus denselben Marken, die
    # in der Mail stehen, und aus dem ECHTEN Stop und Ziel dieses Signals.
    # ⚠️ SPERRT NICHTS - das Ergebnis geht in die Mail und in die Datenbank,
    # in keine Entscheidung. Faellt es aus, fehlt eine Zeile, nie ein Signal.
    # I-4 (28.08.2026): KEIN H BEI AKKUMULATION.
    #
    # ⚠️ H IST EINE BARRIERENFRAGE. Es ist auf "Ziel vor Stop" bei CRV 2,0
    # gemessen (`messe_marken.py`) und beantwortet: liegt zwischen Kurs und
    # Ziel kein Widerstand, und traegt unterhalb eine Unterstuetzung?
    #
    # Die Akkumulation hat KEINE Barriere. `handelsauftrag` gibt ihr
    # ausdruecklich ein anderes Erfolgsmass ("Durchschnittskurs und
    # Endvermoegen statt Ziel vor Stop"), und `vorfilter.bewerte()` gibt
    # deshalb `h = None` mit dem Grund "Stop oder Ziel fehlt".
    #
    # ⚠️ NUR: DIE RECHNUNG LIEFERT IMMER EINEN STOP. Damit bekam H Stop und
    # Ziel und urteilte doch - ueber ein Signal, dessen Erfolgsmass ein
    # anderes ist. Eine Zahl aus der falschen Messung ist schlimmer als
    # keine; genau deshalb laeuft `akkumulationslage` nur bei akkumulation
    # und H ab jetzt nur bei allem anderen.
    # ⚠️ DIE BERECHNUNG STEHT SEIT U-1 (30.08.2026) WEITER OBEN - vor Stufe 11,
    # die sie braucht. Hier entstehen nur noch die MAILZEILEN, aus genau
    # demselben Ergebnis. Eine Quelle, zwei Leser.
    try:
        from agent import vorfilter as _VF
        _vf_zeilen = _VF.saetze(_vf_bewertung) if _vf_bewertung else []
    except Exception:                                        # noqa: BLE001
        logger.exception("Vorfilter-Zeilen fuer %s uebersprungen", symbol)
        _vf_zeilen = []

    # DIE ZUSAMMENFUEHRUNG (22.08.2026). Sie rechnet aus DERSELBEN
    # Geometrie, die weiter unten in der Mail steht, und aus demselben
    # H-Ergebnis wie der Schatten darueber - keine zweite Ermittlung, die
    # auseinanderlaufen koennte.
    try:
        from agent import wahrscheinlichkeit as _WK
        _wk_zeilen = _WK.saetze(
            crv=rechnung.get("crv"),
            stop_relativ=rechnung.get("stop_relativ"),
            klasse=assetklasse,
            h=(_vf_bewertung or {}).get("h"),
            # ⚠️ DIESELBEN MERKMALE WIE STUFE 11 (B-a, 31.08.2026). Ohne
            # sie rechnete die Mail ohne Funding und Turnover und zeigte
            # eine andere Quote als die, mit der entschieden wurde.
            merkmale=_merkmale or None,
            # ⚠️ HEBEL UND HALTEDAUER (01.09.2026). Ohne sie fehlte in der
            # Zeile "noetig X %" die Finanzierung - die Mail nannte fuer
            # einen Hebeltrade eine zu niedrige Huerde.
            hebel=rechnung.get("hebel"),
            tage=rechnung.get("haltedauer_tage"))
    except Exception:                                        # noqa: BLE001
        logger.exception("Wahrscheinlichkeit fuer %s uebersprungen", symbol)
        _wk_zeilen = []

    # ---- DIE MARKTRAENGE IN DIE MAIL (31.08.2026) -----------------------
    #
    # ⚠️⚠️ `marktrang.saetze()` WAR GEBAUT UND WURDE VON NIEMANDEM AUFGERUFEN.
    # Gefunden hat es `simuliere_kette.py`, nicht die Paketpruefung - genau
    # der Grund, warum im Projekt gilt: *eine Stufe gilt erst als gebaut,
    # wenn die Kettensimulation sie in der fertigen Mail nachweist.*
    #
    # Das wog schwer: Funding und Turnover sind seit R1 die EINZIGEN
    # tragenden Beitraege. Sie bestimmen, ob ein Signal ueberhaupt
    # entsteht - und standen in keiner Mail. Der Leser sah die Zahl, nie
    # ihre Herkunft.
    _mr_zeilen = []
    try:
        from agent import marktrang as _MR2
        _mr_zeilen = _MR2.saetze(_mr) if _mr else []
    except Exception:                                        # noqa: BLE001
        logger.exception("Marktrang-Zeilen fuer %s uebersprungen", symbol)
        _mr_zeilen = []

    # DIE LAGE-BEWERTUNG DER AKKUMULATION (28.08.2026, Entscheidung B+C).
    #
    # SPERRT NICHTS - wie der Vorfilter darueber. Sie geht in die Mail, in
    # keine Entscheidung. Faellt sie aus, fehlt ein Absatz, nie ein Signal.
    #
    # NUR BEI `akkumulation`: fuer einen Einstieg ist die Verbilligung nicht
    # das Erfolgsmass, und eine Zahl aus der falschen Messung waere schlimmer
    # als keine.
    _akl_zeilen = []
    if str(strategie or "").strip().lower() == "akkumulation":
        try:
            # ⚠️ NICHT `_AKL` - DER NAME IST SEIT ZEILE 50 BELEGT
            # (`assetklassen`). Ein Import unter diesem Namen HIER macht ihn
            # zur lokalen Variable der ganzen Funktion - und die Zugriffe in
            # Zeile 1412/1453, die VORHER laufen, greifen dann auf eine
            # ungebundene Lokale. Genau die Falle aus
            # `feedback_freie_namen_falle`: der breite Fehlerfang hat den
            # UnboundLocalError geschluckt und als "Topfzuordnung aus dem Lauf
            # statt aus der Zahl" protokolliert. Kein Signal, keine Mail,
            # keine erkennbare Ursache.
            from agent import akkumulationslage as _AKLAGE
            _akl_zeilen = _AKLAGE.saetze(symbol, (reihen or {}).get(symbol))
        except Exception:
            logger.exception("Akkumulationslage fuer %s uebersprungen", symbol)
            _akl_zeilen = []

    def baue(zweite_zeilen: list) -> tuple:
        return SM.baue_mail(
            akkumulationslage=_akl_zeilen or None,
            wahrscheinlichkeit=_wk_zeilen or None,
            lebendigkeit=_leben or None,
            # ⚠️ ZUSAMMEN MIT DEN VORFILTERZEILEN, aber davor: die
            # Marktraenge tragen die Bewertung, die Marken nicht mehr.
            vorfilter=((_mr_zeilen + ([""] if _mr_zeilen and _vf_zeilen else [])
                        + _vf_zeilen) or None),
            # DER BESTAND GANZ OBEN - Nutzervorgabe 12.08.: "Das fuer mich
            # wichtige zuerst." Habe ich das ueberhaupt, ist die erste Frage.
            bestand=(_bloecke.get("bestand") or [None])[0],
            marken=_bloecke.get("marken") or None,
            # DIE MARKEN ALS ZAHLEN - damit die Mail sagen kann, wessen
            # Unterstuetzung sie gerade nennt, wenn das Modell eine
            # ANDERE meint (17.08.2026).
            marken_werte=_bloecke.get("_marken_werte"),
            umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
            # Sie entscheidet ueber den NAMEN der Marken, nicht ueber
            # ihre Berechnung: "Liquiditaetszone" gilt nur fuer Krypto
            # Spot und Hebel (Nutzerentscheidung 23.07., bestaetigt
            # 17.08.).
            assetklasse=assetklasse,
            # DIE DREI NEUEN BLOECKE STEHEN HIER MIT DRIN (Phase I). Der
            # Leser soll denselben Faktensatz sehen wie das Modell - und
            # gerade der Luecken-Block gehoert ihm: er sagt, worueber diese
            # Empfehlung NICHTS weiss.
            # ⚠️ ALLE BLOECKE, IN DER REIHENFOLGE VON `BLOCK_REIHENFOLGE`.
            #
            # Bis zum 20.08.2026 fehlten hier ZWEI: `umschlag` und
            # `fundamental`. Sie gingen ans Modell und nicht an den Nutzer -
            # genau der Zustand, den der Docstring von `geteilt()` als behoben
            # beschreibt ("die Saetze gingen bisher nur ans Modell").
            #
            # SICHTBAR WURDE ES AN DEN BELEGEN: das Modell begruendete in 15
            # von 15 Mails mit "Umschlag von 11,2 % im 100. Perzentil" - einer
            # Zahl, die in der Mail nirgends stand. Der Leser konnte die
            # Begruendung nicht nachpruefen, weil ihm der Fakt fehlte.
            #
            # Die Liste wird nicht mehr von Hand gefuehrt: was in
            # `BLOCK_REIHENFOLGE` steht und nicht eigens dargestellt wird,
            # landet hier. Eine Paketpruefung haelt das fest.
            coin_fakten=[z for _n in _LB.BLOCK_REIHENFOLGE
                         if _n not in ("bestand", "marken")
                         for z in (_bloecke.get(_n) or [])] or None,
            # DIESELBEN SAETZE AN MODELL UND NUTZER. Bei der Absicherung
            # steht die Portfoliolage VOR dem Marktumfeld: sie ist der Grund
            # der Entscheidung, das Umfeld nur ihr Hintergrund.
            lage_fakten=((bc_ein.get("absicherungslage") or []) + _lage) or None,
            # DIE AUSSTIEGSFUEHRUNG ZU DIESEM SYMBOL. Sie wird ohnehin einmal
            # je Lauf gelesen; hier kostet sie einen Nachschlag. Steht eine
            # Position offen, gehoert ihre Behandlung VOR den Nachkauf -
            # `baue_mail` ordnet das selbst (50 % standen bei +1 R, 17,6 %
            # kamen an).
            ausstieg=_fuehrung_zu(ergebnis, symbol, instrument) or None,
            symbol=symbol, name=symbol, kurs_eur=kurs_e, instrument=instrument,
            strategie=strategie, rechnung=rechnung, urteil=befund,
            faktenblock=block, modell=modell, zeitpunkt=tag,
            # DER GEPLANTE EINSTIEG, NICHT DER AKTUELLE KURS (14.08.2026,
            # erste Produktionsmail). Die Mail nannte zwei Stop-Abstaende fuer
            # denselben Stop, zwei Zeilen auseinander:
            #
            #   2. DIE RECHNUNG   Stop 5,5 %   (gegen die Einstiegszone)
            #   4. EINORDNUNG     Stop 11,2 %  (gegen den aktuellen Kurs)
            #
            # Beide Zahlen waren fuer sich richtig - die Zone lag 6 % unter dem
            # Kurs. Fuer den Leser ist es trotzdem ein Widerspruch, und zwar
            # der schlimmere: er kann nicht sehen, welcher Bezugspunkt gemeint
            # ist, und wuerde sein Risiko doppelt so hoch einschaetzen wie
            # geplant. Die Einordnung gehoert an die Zahlen der RECHNUNG - sie
            # ordnet den geplanten Trade ein, nicht einen, der jetzt zum
            # Marktpreis stattfaende.
            # DIE MITTE DER ZONE, NICHT IHRE UNTERE KANTE (16.08.2026).
            #
            # Der Fix vom 14.08. hat die Einordnung richtig an die
            # RECHNUNG gebunden - aber am falschen Punkt. `einstieg_von_eur`
            # ist die untere Kante der Einstiegszone; gegen sie gemessen
            # sieht der Stop naeher aus, als er ist. Am AKT-Signal:
            #
            #     2. DIE RECHNUNG   Stop 4,8 %   (gegen den Kurs)
            #     4. EINORDNUNG     Stop 3,3 %   (gegen die untere Kante)
            #
            # Ein Drittel Unterschied auf derselben Mail - und die
            # Folgezeile erbt ihn: "die Gebuehren fressen 92 % Ihres
            # Risikos" waren mit der Zonenmitte 62 %.
            #
            # `einstieg_eur` IST die Mitte und liegt in derselben Rechnung.
            # ⚠️ INSTRUMENT, HEBEL UND HALTEDAUER GEHEN MIT (01.09.2026).
            # Ohne sie rechnete `satz()` jeden Trade als Spot - ein
            # Hebeltrade zeigte in der Mail weder seine Finanzierung noch
            # ihr Anwachsen mit der Haltedauer. Dieselben drei Groessen,
            # die schon `kosten_r_aus_stop` oben bekommt; sie stehen in
            # derselben `rechnung`, es fehlte nur die Weitergabe.
            einordnung=TB.satz(bewertung,
                               einstieg=rechnung.get("einstieg_eur")
                               or kurs_e,
                               stop=rechnung["stop_eur"],
                               einsatz_eur=rechnung["betrag_eur"],
                               klasse=_kostenklasse(assetklasse),
                               instrument=instrument,
                               hebel=rechnung.get("hebel"),
                               tage=rechnung.get("haltedauer_tage"))
            + Z1.satz(z1),
            # DIE ZWEITE STUFE IN IHREN EIGENEN ABSCHNITT.
            gegenpruefung=list(zweite_zeilen))

    betreff, text = baue([])
    # O-24: DAS BILD ZUM GEPLANTEN TRADE. Einmal gerechnet, an beide
    # Versandstellen gereicht (mit und ohne zweite Meinung).
    _bilder = []
    try:
        from ui.trade_chart import render_trade_chart

        _png = render_trade_chart(
            reihe=reihe, index=idx, rechnung=rechnung, symbol=symbol,
            # ⚠️ HIER STAND `None` (17.08.2026). Der Chart zeichnete die
            # Marken nie, obwohl er es konnte - dieselbe Sorte nicht
            # gefuellter Parameter wie beim Widerstand in der
            # Zielrechnung, nur eine Stelle weiter.
            #
            # DIE DREI NAECHSTEN JE SEITE. Mehr macht das Bild voll; die
            # Mail nennt ohnehin nur die drei auf dem Weg zum Ziel.
            marken=(((_bloecke.get("_marken_werte") or {}).get("oben")
                     or [])[:3]
                    + ((_bloecke.get("_marken_werte") or {}).get("unten")
                       or [])[:3]),
            fx_eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db))
        if _png:
            _bilder.append({"png": _png, "alt": f"{symbol} - geplanter Trade",
                            "filename": f"{symbol.lower()}_trade.png"})
    except Exception as exc:                                 # noqa: BLE001
        ergebnis.setdefault("fehler", []).append(f"{symbol}: Chart: {exc}")
    eintrag = {"symbol": symbol, "betreff": betreff, "text": text,
               "bilder": _bilder}
    ergebnis["mails"].append(eintrag)

    # --- Schreiben ----------------------------------------------------------
    #
    # HIER ENTSTEHT DIE SIGNALZEILE - bis zum 13.08. entstand sie NIE. Die
    # Felder wurden gebaut und in `ergebnis` gelegt, geschrieben hat sie
    # niemand. Folge: `trefferbilanz.zaehle()` selektiert
    # `WHERE quelle_kette = 'rollen'` und lieferte dauerhaft {} - der
    # Entscheider rechnete nicht "mit wenig Daten", sondern mit null, und die
    # 34 % waren nie eine geschrumpfte Schaetzung, sondern der unberuehrte
    # Mittelwert.
    if betriebsart == TROCKEN:
        return
    felder = SA.felder_aus_entscheidung(
        befund, fakten=bc_ein, lagebild_id=lagebild_id,
        prompt_stand=getattr(RT, "PROMPT_STAND", "?"), modell=modell,
        eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db),
        # S-2 (23.08.2026): der AUFTRAG geht mit, nicht nur das Instrument.
        strategie=strategie,
        # P1 (24.08.2026): das Urteil von Z1 auch - es lief bisher,
        # ging in die Mail und war trotzdem nie messbar.
        z1=z1,
        # DIE RECHNUNG MIT - sie traegt den Hebelfaktor, den das Modell nicht
        # nennt und nicht nennen soll.
        rechnung=rechnung,
        # UND DAS INSTRUMENT - es entscheidet, ob die Hebelspalte gefuellt
        # wird. Am WERT zu unterscheiden hat am 15.08. zwei echte Hebel-Trades
        # als Spot in die Datenbank geschrieben.
        instrument=instrument,
        # DIE DREI GEMESSENEN FAMILIEN - dieselben Werte, die oben schon in den
        # Faktenblock der Mail gingen. Sie sind das einzige Material fuer den
        # Konstellationsschluessel, das NICHT die Entscheidung wiederholt.
        familien=kern)
    # P1a (19.08.2026): die auffaelligen Perzentilzeilen der FERTIGEN Mail
    # mitschreiben - dieselbe Quelle, die der Leser sieht. Sie neu zu
    # bestimmen waere die zweite Stelle, an der beide auseinanderlaufen.
    try:
        _auf = SM.auffaellige((eintrag.get("text") or "").splitlines())
        if _auf:
            felder["auffaellige_json"] = _json.dumps(_auf, ensure_ascii=False)
    except Exception as exc:                                 # noqa: BLE001
        # KEIN GRUND, EIN SIGNAL ZU VERLIEREN. Das Merkmal ist eine
        # Beobachtung, keine Voraussetzung.
        ergebnis.setdefault("fehler", []).append(
            f"{symbol}: Auffaelligkeiten nicht notiert: {exc}")

    signal_id = SA.schreibe_signal(conn, felder, symbol=symbol)
    eintrag["signal_id"] = signal_id
    # ⚠️ ERST HIER, WEIL ERST HIER DIE `signal_id` FESTSTEHT. Ohne sie
    # laesst sich die Zeile spaeter nicht mit dem Ausgang verbinden - und
    # genau das ist der ganze Zweck der Schattenmessung.
    if _vf_bewertung:
        try:
            from agent import vorfilter as _VF2
            _VF2.schreibe(conn, symbol=symbol, bewertung=_vf_bewertung,
                          signal_id=signal_id, assetklasse=assetklasse,
                          instrument=instrument)
        except Exception:                                    # noqa: BLE001
            logger.exception("Vorfilter-Schatten fuer %s nicht geschrieben",
                             symbol)
    ergebnis["signale"].append({"symbol": symbol, "id": signal_id,
                                "felder": felder})

    # --- Der Richtungsschalter, AUSSCHLIESSLICH am Versand (15.08.2026) ------
    #
    # DIE VORGABE DES NUTZERS vom 05.08., woertlich: der Schalter soll "NULL
    # Einfluss auf die Funktionsweise im Hintergrund" haben - SHORTs sollen
    # lediglich nicht per E-Mail kommen und nicht in der GUI erscheinen.
    #
    # ALLES DAVOR IST SCHON PASSIERT und bleibt so: das Modell wurde gefragt,
    # das Signal steht mit echter `richtung` und echter `action` in der
    # Datenbank, das Gate hat es als durchgekommen gezaehlt, der Ausgang wird
    # normal verfolgt. NUR die Mail unterbleibt.
    #
    # WARUM NICHT FRUEHER - etwa im Prompt, indem man SHORT gar nicht anbietet:
    # genau das war der Zustand bis zum 05.08., und er hat 313 SHORT-Vorschlaege
    # als "HALTEN" in die Datenbank gelegt. Jede Auswertung ueber Richtungen war
    # dadurch verzerrt, und beim 31.07.-Bruch hat es einen ganzen Tag gekostet.
    # Der Schalter darf die MESSUNG nicht anfassen.
    #
    # UND DIE FUNKTION WIRD GEHOLT, NICHT NACHGEBAUT - sie steht bei den
    # uebrigen Nutzerschaltern, und der alte Weg fragt dieselbe.
    _mail_erlaubt = True
    try:
        from agent.asset_schalter import mail_richtung_erlaubt

        _mail_erlaubt = mail_richtung_erlaubt(befund.get("richtung"), config)
    except Exception as exc:                                 # noqa: BLE001
        # FAIL-OPEN: lieber eine Mail zuviel als eine verschluckte.
        ergebnis.setdefault("fehler", []).append(
            f"{symbol}: Richtungsschalter nicht lesbar: {exc}")
    if not _mail_erlaubt:
        eintrag["nicht_versendet"] = "nur_long"
        ergebnis.setdefault("mails_unterdrueckt", []).append(
            {"symbol": symbol, "richtung": befund.get("richtung"),
             "signal_id": signal_id})
        logger.info(
            "Mail fuer %s (%s) unterdrueckt - hebel_richtung_modus=nur_long. "
            "Das Signal bleibt vollstaendig erhalten und wird weiter gemessen.",
            symbol, befund.get("richtung") or "?")

    # --- Zweite Meinung, dann versenden -------------------------------------
    #
    # DIE REIHENFOLGE IST DER GANZE PUNKT: schreiben -> Z.ai -> warten ->
    # Mail bauen -> versenden. Ginge die Mail vorher raus, kehrte der Fund vom
    # 28.07. zurueck - die BTC-SHORT-Mail ohne Gegenpruefungszeilen, obwohl das
    # Urteil zum Versandzeitpunkt vorlag.
    #
    # AUCH IN `probe`, nicht erst in `scharf`. Eine Wartemechanik, die nur im
    # scharfen Betrieb laeuft, ist genau dort zum ersten Mal erprobt, wo ein
    # Fehler eine echte Mail kostet.
    # EIN FADEN JE SIGNAL - die Lehre vom 23.07., woertlich im alten Code:
    #
    #     "ein einzelner Kandidat mit langsamem externen Call durfte NIE
    #      nachfolgende, laengst fertige Signale in derselben Charge blockieren"
    #
    # Meine erste Fassung rief Z.ai SYNCHRON in der Schleife. Bei 12 Einstiegen
    # und 4 Z.ai-Aufrufen zu je ~34 s sind das 27 Minuten, im schlechtesten Fall
    # 48 - bei einem Takt von 15. Der Lauf haette sich selbst ueberholt.
    #
    # WAS IM FADEN PASSIERT: Z.ai fragen, Mail bauen, Mail verschicken. Was
    # NICHT: schreiben. Eine sqlite3-Verbindung ist nicht zwischen Threads
    # teilbar, und die Kette oeffnet grundsaetzlich keine eigene - das Ergebnis
    # wird deshalb eingesammelt und nach dem Zusammenfuehren im Hauptfaden
    # geschrieben.
    def _nacharbeit() -> None:
        try:
            zweite = ZM.hole(faktentext=bc_ein, urteil=befund,
                             symbol=symbol, assetklasse=assetklasse,
                             instrument=instrument,
                             zai_client=zai_client, config=config)
            if zweite:
                eintrag["zweite_meinung"] = zweite
                eintrag["betreff"], eintrag["text"] = baue(ZM.zeilen(zweite))
        except Exception as exc:                             # noqa: BLE001
            ergebnis.setdefault("fehler", []).append(
                f"{symbol}: zweite Meinung: {exc}")
        # DIE MAIL GEHT AUCH RAUS, WENN Z.AI AUSFAELLT (P-8) - lieber ohne die
        # Gegenpruefungszeilen als gar nicht.
        if (betriebsart == SCHARF and versand is not None
                and _mail_erlaubt):
            versand(eintrag["betreff"], eintrag["text"],
                    eintrag.get("bilder"))

    if zai_client is None:
        # Nichts zu warten - dann auch kein Faden. Ein Thread, der sofort
        # zurueckkehrt, ist nur Verwaltung.
        if (betriebsart == SCHARF and versand is not None
                and _mail_erlaubt):
            versand(eintrag["betreff"], eintrag["text"],
                    eintrag.get("bilder"))
    else:
        import threading

        faden = threading.Thread(target=_nacharbeit, daemon=True,
                                 name=f"zweite-meinung-{symbol}")
        ergebnis.setdefault("_faeden", []).append((faden, signal_id, eintrag))
        faden.start()


def _sende_ausstieg(*, symbol, befund, verkauf, kurs_e, instrument, strategie,
                    tag, lagebild_id, modell, conn, db, betriebsart, versand,
                    ergebnis, fakten=None, familien=None,
                    reihe=None, idx=None, zai_client=None,
                    config=None, assetklasse="krypto",
                    z1=None) -> None:
    """Einen Ausstieg VORMERKEN und seine Zeile schreiben - nicht mailen.

    NUTZEREINWAND 14.08., waehrend dieser Umbau lief: *"45 Signale sind
    durchgekommen - 9 Spot, Rest irgendwas z.B. Verkaufen - das ist zu viel."*

    Meine erste Fassung hat genau das verschlimmert: elf Einzelmails fuer die
    Verkaufsseite waeren zu den zehn Kaufmails dazugekommen. Einundzwanzig
    Mails aus einem Lauf - und die Verkaufsseite ist die, die man nicht
    uebersehen darf.

    DESHALB SAMMELT DIESE FUNKTION NUR. Eine Mail je Lauf baut
    `verkaufsrechnung.sammel_mail()` am Ende von `fuehre_lauf`, nach Gegenwert
    sortiert. Die Einstiegsmails bleiben einzeln: sie sind seltener und tragen
    eine vollstaendige Planung, die sich nicht buendeln laesst.

    DIE ZEILE WIRD TROTZDEM SOFORT GESCHRIEBEN, nicht am Ende. Sonst greift der
    Cooldown nicht, und ein zweiter Lauf im selben Fenster faende dasselbe
    Symbol wieder frei."""
    from agent import signal_abbildung as SA2

    ergebnis.setdefault("ausstiege", []).append(
        {"symbol": symbol, "verkauf": verkauf,
         "begruendung": befund.get("begruendung"),
         # DIE DETERMINISTISCHE FUEHRUNG ZU DIESEM SYMBOL, falls es eine gibt.
         # Sie wird EINMAL je Lauf geholt (wie das Lagebild) und hier nur
         # nachgeschlagen - 45 Symbole waeren sonst 45 Abfragen ueber
         # dieselben Tabellen.
         "fuehrung": _fuehrung_zu(ergebnis, symbol, instrument) or None})

    if betriebsart == TROCKEN:
        return
    try:
        # ⚠️ DER PROMPT-STAND STAND HIER AUF `None` - eine Messluecke, keine
        # Absicht (gefunden 16.08.2026 am NB-Export). 30 von 285 Signalen
        # trugen keinen Stand, und es waren AUSSCHLIESSLICH Verkaufszeilen:
        # 28 REDUZIEREN und 2 VERKAUFEN.
        #
        # WARUM DAS ZAEHLT. Jeder Messbefund gehoert zu einem Prompt-Stand -
        # ohne ihn faellt die Verkaufsseite aus jedem Vorher-Nachher-Vergleich
        # heraus. Und ausgerechnet sie ist der Teil, ueber den am wenigsten
        # bekannt ist: O-29 hat gemessen, dass KEIN Merkmal Verkaufen von
        # Halten trennt.
        #
        # ES IST DERSELBE STAND WIE BEIM EINSTIEG: `befund` ist die Antwort
        # von Rolle BC, und die entsteht aus demselben Prompt. Ein eigener
        # Stand waere hier eine Erfindung.
        from agent import rolle_trader as RT2

        # B2 (23.08.2026): DIE MERKMALSFAMILIEN, aus derselben Reihe
        # und mit derselben Funktion wie auf der Nein-Seite.
        #
        # ⚠️ HIER STAND `familien=None`, und zwar als EINZIGE der drei
        # Schreibstellen. Gemessen: bei REDUZIEREN hatten 10 von 75
        # Zeilen ueberhaupt Merkmale. Eine Verkaufsseite ohne Merkmale
        # laesst sich nicht auswerten - egal wie viele Faelle sie
        # ansammelt.
        if familien is None and reihe is not None and idx is not None:
            try:
                from agent import faktenblock as _FB2
                familien = _FB2.werte_aus_reihe(
                    [k.high for k in reihe], [k.low for k in reihe],
                    [k.close for k in reihe],
                    [getattr(k, "volume", 0) or 0 for k in reihe],
                    i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
            except Exception:                                # noqa: BLE001
                logger.exception("Merkmale fuer %s nicht rechenbar", symbol)

        # B1/B2 (23.08.2026): DER ECHTE FAKTENSATZ UND DIE ECHTEN
        # MERKMALE - statt eines 17-Zeichen-Stummels.
        #
        # ⚠️ WAS HIER STAND: `fakten={"asset": symbol}` und
        # `familien=None`. Gemessen ueber die Produktionsdaten:
        # EROEFFNEN 2.187 Zeichen, HALTEN/REDUZIEREN/VERKAUFEN 17.
        # Das erklaert O-29 ("die Verkaufsseite ist durch nichts
        # erklaert, alle p > 0,47"): ES GAB KEINE MERKMALE ZU MESSEN.
        #
        # Der Faktensatz ist DERSELBE, der in den Prompt ging - er
        # wird durchgereicht, nicht neu gebaut. Eine zweite Fassung
        # waere die naechste Stelle, an der Mail und Datenbank
        # auseinanderlaufen.
        felder = SA2.felder_aus_entscheidung(
            befund, fakten=(fakten or {"asset": symbol}),
            lagebild_id=lagebild_id,
            prompt_stand=getattr(RT2, "PROMPT_STAND", "?"),
            eur_je_usd=None, familien=familien, strategie=strategie,
            instrument=instrument, rechnung=None, modell=modell,
            z1=z1)
        # `gate_passed = 1`, weil es eine HANDLUNG ist - anders als die
        # Nein-Buchung, die eine Messung ist.
        felder["gate_passed"] = 1
        felder["position_size_eur"] = round(float(verkauf["gegenwert_eur"]), 2)
        _kennung = SA2.schreibe_signal(conn, felder, symbol=symbol)

        # B3 (23.08.2026): DIE GEGENPRUEFUNG AUCH AUF DER
        # VERKAUFSSEITE - gemessen 0 von 561.
        #
        # ⚠️ SIE SCHREIBT, SIE MAILT NICHT. Die Verkaufsmail wird
        # bewusst VOR dem Warten auf Z.ai gebaut ("soll deshalb nicht
        # bis zu vier Minuten dahinter warten muessen"). Wuerde man
        # aufnehmen, was zufaellig schon fertig ist, staende in der
        # Mail mal eine Gegenpruefung und mal keine - dasselbe Signal,
        # zwei Darstellungen. Das ist schlimmer als keine.
        #
        # DAFUER STEHT SIE IN DER ZEILE, und genau die fehlt: O-29 hat
        # gemessen, dass KEIN Merkmal Verkaufen von Halten trennt -
        # mit B1/B2 gibt es jetzt Merkmale, mit B3 auch ein zweites
        # Urteil daneben.
        #
        # DERSELBE FADEN-AUFBAU WIE BEIM EINSTIEG, und aus demselben
        # Grund: Z.ai braucht rund 34 s je Aufruf, und elf Ausstiege
        # nacheinander waeren mehr als ein ganzer Takt. Der Deckel von
        # zwei gleichzeitigen Aufrufen sitzt in `zweite_meinung`
        # selbst - hier wird nichts zusaetzlich begrenzt, sonst gaebe
        # es zwei Bremsen fuer dieselbe Leitung.
        if _kennung and zai_client is not None:
            import threading

            from agent import zweite_meinung as ZM2

            _eintrag = {}

            def _gegenpruefung() -> None:
                try:
                    _z = ZM2.hole(
                        faktentext=(fakten or {"asset": symbol}),
                        urteil=befund, symbol=symbol,
                        assetklasse=assetklasse, instrument=instrument,
                        zai_client=zai_client, config=config)
                    if _z:
                        _eintrag["zweite_meinung"] = _z
                except Exception as exc:                # noqa: BLE001
                    ergebnis.setdefault("fehler", []).append(
                        f"{symbol}: zweite Meinung (Ausstieg): {exc}")

            _faden = threading.Thread(
                target=_gegenpruefung, daemon=True,
                name=f"zweite-meinung-ausstieg-{symbol}")
            ergebnis.setdefault("_faeden", []).append(
                (_faden, _kennung, _eintrag))
            _faden.start()
    except Exception as exc:                                 # noqa: BLE001
        ergebnis.setdefault("fehler", []).append(
            f"{symbol}: Ausstiegszeile nicht geschrieben: {exc}")


def _schreibe_nein(*, symbol, befund, kurs_e, atr_e, tag, reihe, idx,
                   lagebild_id, instrument, strategie, conn, db, config,
                   modell, ergebnis, module, assetklasse="krypto",
                   fakten=None, z1=None) -> None:
    """Ein NICHTS_TUN als auflösbare Zeile - der Kontrollarm der Messung.

    `assetklasse` IST PFLICHT UND STAND HIER NICHT (gefunden 15.08.2026, an
    den Daten). Die Funktion rief `_kostenklasse(assetklasse)` auf - einen
    Namen, den nur `_ein_asset` kennt. Sie ist eine eigene Funktion und sieht
    ihn nicht.

        NameError: name 'assetklasse' is not defined

    DAS ZUM DRITTEN MAL DIESELBE FALLE, nach `VK` (14.08.) und `_wl`
    (15.08.) - und dieses Mal am teuersten, weil sie nichts umbrachte,
    sondern nur schwieg: der breite Fehlerfang unten legt sie in
    `ergebnis["nein_fehler"]`, und das las niemand. Gemessen am Export:

        809 Nein-Zeilen bis 14.08. 17:55, danach KEINE EINZIGE.

    Zwei Vormittage mit 67 Nein-Urteilen haben null Zeilen erzeugt. Damit
    fehlt genau der Arm, der die Frage des Nutzers beantworten sollte, ob das
    NEIN des Modells besser ist als der Zufall.

    DER FEHLER WIRD JETZT GELOGGT, nicht nur gesammelt - siehe unten.

    `ist_reines_llm_halten = 1` ist der Schluessel: `backward_tracking` sucht
    genau danach (Zeile 1192) und loest solche Zeilen ueber das
    Selbst-HALTEN-Schatten-Tracking auf. Die Maschine existiert seit dem
    31.07. - sie bekam nur nie Futter aus der neuen Kette.

    STILL BEI EINEM FEHLSCHLAG. Diese Zeile ist eine Messung, kein Signal - sie
    darf den Lauf unter keinen Umstaenden aufhalten. Wer hier abbricht, verliert
    ein Urteil, das ohnehin schon bezahlt ist."""
    AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB, ZM, BE, WH = module
    try:
        rechnung = ER.rechne(
            kurs=kurs_e, atr=atr_e,
            risiko_eur=BE.risiko_eur(instrument, strategie, config),
            instrument=instrument,
            betrag_wunsch_eur=BE.einsatz_eur(instrument, strategie, config),
            umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
            ist_short=(befund.get("richtung") == "SHORT"),
            kostenklasse=_kostenklasse(assetklasse),
            # ⚠️ A1: auch die Nein-Zeile - sonst truege sie ein anderes
            # Etikett als dasselbe Symbol im Hauptpfad.
            hebel_handelbar=_AKL.hebel_handelbar(assetklasse),
            umgeworfen_tage=_tage_bis(befund.get("umgeworfen_bis"), tag))
        kern = FB.werte_aus_reihe(
            [k.high for k in reihe], [k.low for k in reihe],
            [k.close for k in reihe],
            [getattr(k, "volume", 0) or 0 for k in reihe],
            i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
        # B1 (23.08.2026): der ECHTE Faktensatz statt des Stummels -
        # dieselbe Begruendung wie im Ausstiegspfad. `familien` war
        # hier schon richtig (`kern`), nur die Fakten fehlten.
        felder = SA.felder_aus_entscheidung(
            befund, fakten=(fakten or {"asset": symbol}),
            lagebild_id=lagebild_id,
            prompt_stand=getattr(RT, "PROMPT_STAND", "?"),
            eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db),
            strategie=strategie, z1=z1,
            # UND DAS INSTRUMENT (15.08.2026, zweite Haelfte desselben Fundes).
            # Seit die Hebelspalte am INSTRUMENT haengt statt am Wert, bekam
            # eine Nein-Zeile aus dem Hebel-Lauf keine - sie galt als Spot.
            # Folge waere gewesen: der Hebel-Cooldown (`hebel IS NOT NULL`)
            # findet sie nicht und fragt dasselbe Symbol alle 15 Minuten neu.
            instrument=instrument,
            familien=kern, rechnung=rechnung, modell=modell)
        # DIE ZONEN KAMEN FRUEHER HIER NACHTRAEGLICH DAZU, weil
        # `felder_aus_entscheidung` sie aus der ANTWORT nahm und ein NICHTS_TUN
        # keine nennt. Das war ein Flicken an EINEM von zwei Wegen - der
        # Hauptpfad schrieb weiter die Zahlen des Modells, und niemand sah,
        # dass Mail und Zeile auseinanderliefen.
        #
        # SEIT DEM 15.08. NIMMT DIE ABBILDUNG SELBST die Rechnung, fuer beide
        # Wege. Der Flicken ist damit weg, und es gibt die Geometrie einmal -
        # samt USD-Umrechnung, die hier ebenfalls doppelt stand.
        felder["ist_reines_llm_halten"] = 1
        felder["gate_passed"] = 0        # es ist kein Signal, es ist eine Messung
        kennung = SA.schreibe_signal(conn, felder, symbol=symbol)
        ergebnis.setdefault("nein_gemessen", []).append(
            {"symbol": symbol, "id": kennung})
    except Exception as exc:                                 # noqa: BLE001
        # GELOGGT, NICHT NUR GESAMMELT (15.08.2026). `ergebnis["nein_fehler"]`
        # las niemand - weder der Scheduler, der die Laufzeile schreibt, noch
        # der Export. Zwei Vormittage lang schlug hier bei JEDEM Nein-Urteil
        # ein NameError zu, und im Log stand kein Wort davon.
        #
        # "Fail-soft ist fail-silent" steht seit dem 02.08. als stehende
        # Vorgabe im Projekt. Diese Stelle war der Beweis.
        logger.error("Nein-Zeile fuer %s nicht geschrieben: %s", symbol, exc)
        ergebnis.setdefault("nein_fehler", []).append(f"{symbol}: {exc}")


def _frage(client, modell, system_prompt, eingabe, modulname):
    """Der Modellaufruf - in der Form, die die Clients wirklich haben.

    MEINE ERSTE FASSUNG WAR ERFUNDEN: sie rief
    `client.chat(modell=..., system=..., nachricht=...)`. Kein Client dieses
    Projekts hat diese Schnittstelle - sie nehmen eine NACHRICHTENLISTE und
    geben Text zurueck. Der Trockenlauf konnte das nicht finden, weil er
    `_frage()` nie aufruft; es waere erst beim ersten echten Aufruf
    hochgekommen, mit verbrauchtem Kontingent.

    Die Form ist woertlich die von `pruefe_rollenkette.frage()`, die seit dem
    12.08. gegen echte Antworten laeuft. Eine eigene Variante daneben waere
    die naechste Stelle zum Auseinanderlaufen.

    JSON WIRD AUS DEM TEXT GESCHNITTEN, nicht erwartet: Modelle setzen
    gelegentlich einen Satz davor. Fehlt eine Struktur ganz, ist das ein
    Fehler und keine leere Antwort.
    """
    import json

    from agent import llm_schema

    fmt = llm_schema.response_format_fuer(client, modulname)
    roh = client.chat(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
        **({"model": modell} if modell else {}), response_format=fmt,
        temperature=0.2)
    text = roh if isinstance(roh, str) else str(roh)
    anfang, ende = text.find("{"), text.rfind("}")
    if anfang < 0 or ende < anfang:
        raise LaufAbgebrochen(
            f"keine JSON-Struktur in der Antwort von {modulname}: {text[:180]}")
    return json.loads(text[anfang:ende + 1])
