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
    from agent.handelsauftrag import AuftragUngueltig, pruefe as pruefe_auftrag

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

    for symbol in symbole:
        if max_aufrufe is not None and ergebnis["aufrufe"] >= max_aufrufe:
            ergebnis.setdefault("budget_gestoppt", []).append(symbol)
            continue
        durchlauf.beginne(symbol)
        _vor_aufrufe = ergebnis["aufrufe"]
        _vor_signale = len(ergebnis.get("signale") or [])
        try:
            _ein_asset(symbol=symbol, reihen=reihen, tag=tag, lagebild=lagebild,
                       lagebild_id=lagebild_id, gleichlauf=gleichlauf,
                       durchlauf=durchlauf, betriebsart=betriebsart,
                       client=client, modell=modell, conn=conn, db=db,
                       config=config, aufgezeichnet=aufgezeichnet,
                       instrument=instrument, strategie=strategie,
                       ergebnis=ergebnis, versand=versand,
                       assetklasse=assetklasse, watchlist=_wl,
                       auswahl=_auswahl, marktzustand=_markt,
                       auswahl_lauf=_auswahl_lauf,
                       module=(AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB,
                               ZM, BE, WH),
                       zai_client=zai_client, bilanz=bilanz,
                       fehlertypen=(EmpfehlungUngueltig, AuftragUngueltig,
                                    RT.TraderAntwortUngueltig),
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
               durchlauf, betriebsart, client, modell, conn, db, config,
               instrument, strategie,
               aufgezeichnet, ergebnis, versand, module, fehlertypen,
               pruefe_auftrag, zai_client=None, bilanz=None,
               assetklasse="krypto", watchlist=None,
               auswahl=None, marktzustand=None,
               auswahl_lauf=None) -> None:
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

        sperre = WH.gesperrt_bis(conn, symbol, instrument, config=config,
                                 gruppe=assetklasse)
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
        ergebnis["aufrufe"] = ergebnis.get("aufrufe", 0) + 1
        bc_roh = _frage(client, modell, RT.prompt_fuer(instrument, strategie),
                        bc_ein, "agent.rolle_trader")
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
                               assetklasse=assetklasse, fakten=bc_ein)
            return
        durchlauf.bestanden(symbol, "aktion")
        _sende_ausstieg(
            symbol=symbol, befund=befund, verkauf=verkauf, kurs_e=kurs_e,
            instrument=instrument, strategie=strategie, tag=tag,
            lagebild_id=lagebild_id, modell=modell, conn=conn, db=db,
            betriebsart=betriebsart, versand=versand, ergebnis=ergebnis,
            # B1/B2 (23.08.2026): der Faktensatz, der in den Prompt ging,
            # und die Reihe fuer die Merkmalsfamilien.
            fakten=bc_ein, reihe=reihe, idx=idx)
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
                           fakten=bc_ein)
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
                           fakten=bc_ein)
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
        _topf_instrument = ("hebel" if _vor["etikett"] == "hebel"
                            else instrument)
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
    if not bewertung["traegt"]:
        durchlauf.verloren(symbol, "entscheider", "traegt sich nicht")
    else:
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
    try:
        from agent import vorfilter as _VF
        _vf_bewertung = _VF.bewerte(
            _bloecke.get("_marken_werte"),
            rechnung.get("stop_eur"), rechnung.get("ziel_eur"),
            bool(rechnung.get("ist_short")), assetklasse)
        _vf_zeilen = _VF.saetze(_vf_bewertung)
    except Exception:                                        # noqa: BLE001
        logger.exception("Vorfilter-Schatten fuer %s uebersprungen", symbol)
        _vf_bewertung, _vf_zeilen = None, []

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
            h=(_vf_bewertung or {}).get("h"))
    except Exception:                                        # noqa: BLE001
        logger.exception("Wahrscheinlichkeit fuer %s uebersprungen", symbol)
        _wk_zeilen = []

    def baue(zweite_zeilen: list) -> tuple:
        return SM.baue_mail(
            wahrscheinlichkeit=_wk_zeilen or None,
            lebendigkeit=_leben or None,
            vorfilter=_vf_zeilen or None,
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
            einordnung=TB.satz(bewertung,
                               einstieg=rechnung.get("einstieg_eur")
                               or kurs_e,
                               stop=rechnung["stop_eur"],
                               einsatz_eur=rechnung["betrag_eur"])
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
                    reihe=None, idx=None) -> None:
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
            instrument=instrument, rechnung=None, modell=modell)
        # `gate_passed = 1`, weil es eine HANDLUNG ist - anders als die
        # Nein-Buchung, die eine Messung ist.
        felder["gate_passed"] = 1
        felder["position_size_eur"] = round(float(verkauf["gegenwert_eur"]), 2)
        SA2.schreibe_signal(conn, felder, symbol=symbol)
    except Exception as exc:                                 # noqa: BLE001
        ergebnis.setdefault("fehler", []).append(
            f"{symbol}: Ausstiegszeile nicht geschrieben: {exc}")


def _schreibe_nein(*, symbol, befund, kurs_e, atr_e, tag, reihe, idx,
                   lagebild_id, instrument, strategie, conn, db, config,
                   modell, ergebnis, module, assetklasse="krypto",
                   fakten=None) -> None:
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
            strategie=strategie,
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
