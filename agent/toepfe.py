# -*- coding: utf-8 -*-
"""Getrennte Toepfe je Zweck: Spot, Hebel, Absicherung (Paket 5, 12.08.2026).

NUTZERVORGABE, die das erzwungen hat: *"Absicherung soll nicht ausgeschlossen
werden, sondern es benoetigt eine Sonderstellung, ohne dass die anderen
Handlungen beeinflusst werden - gilt fuer alle Bereiche, wo mit Betraegen
gerechnet wird. Beispiel: es kommen keine Kaufpositionen rein, weil Hedge gering
ist. Oder kein Hebel, weil mein aktueller Cash-Anteil zu gering ist."*

DIE EINE REGEL, aus der alles folgt:

    Ein Topf begrenzt sich SELBST. Sein Fuellstand veraendert keinen anderen.

Ein niedriger Absicherungsgrad ERZEUGT einen Hedge-Vorschlag - er unterdrueckt
keinen Kauf. Ein knapper Cash-Anteil BEGRENZT die Groesse im eigenen Topf - er
verhindert keine Aktion in einem anderen. Wo eine Groesse doch ueber Toepfe
hinweg wirken soll, ist das eine ausdrueckliche Regel MIT NAMEN (siehe
UEBERGREIFEND unten), nie ein Nebeneffekt einer Budgetformel.

DER FACHSTANDARD DAZU - Core-Satellite mit explizitem Risikobudget:

    KERN        die Basisallokation, stabile Risikogrundlinie      -> spot
    SATELLIT    nach EIGENER Volatilitaet und Drawdown bemessen,
                nicht durch Verrechnung mit dem Kern               -> hebel
    HEDGING     eine eigene Saeule fuer Tail-Risiken, bemessen am
                abzusichernden Exposure, NICHT an einem Renditeziel -> absicherung

Der entscheidende Satz der Quelle: Satelliten werden nach ihrer eigenen
erwarteten Volatilitaet, ihrem Drawdown-Potenzial und ihrer Korrelation zum Kern
bemessen. Nicht als Rest, der uebrigbleibt.

WAS AUS DER RECHERCHE **NICHT** UEBERNOMMEN WURDE, und warum. Fuer
Absicherungsbudgets nennt die Praxis 0,5 bis 2 % des Portfoliowerts pro Jahr und
einen Drag von 1 bis 4 %. Diese Zahlen gelten fuer OPTIONSBASIERTE Absicherung
(Puts, Praemie). Unsere Instrumente sind 3QSS und DBPK - GEHEBELTE INVERSE ETFs.
Deren Kosten sind taeglicher Rebalancing-Zerfall, keine Praemie, und ihre
Groessenlogik ist eine voellig andere:

    benoetigter Einsatz = abzusicherndes Exposure / Hebelfaktor

Eine Prozentzahl aus der Optionswelt hierher zu uebernehmen waere eine Zahl mit
falscher Herkunft. Der Bedarf wird deshalb ueber das EXPOSURE bemessen - und
einen Deckel bekommt die Absicherung gar nicht (siehe VORGABE_DECKEL_EUR).

ALLE DECKEL SIND ABSOLUT IN EURO, nicht in Prozent des Portfolios. Der Grund
steht unten ausfuehrlich; kurz: ein Prozentdeckel schrumpft mit dem Verlust und
bremst damit am staerksten, wenn Handeln am noetigsten ist.

WAS DIESES MODUL NICHT TUT: es rechnet keine Positionsgroesse. Das bleibt beim
deterministischen Risikomanagement (RM-1 bis RM-7). Hier steht nur, WELCHER TOPF
gilt und WIEVIEL in ihm noch frei ist.
"""
from __future__ import annotations

TOEPFE = ("spot", "hebel", "absicherung")

# Welcher Topf gilt fuer welches Instrument. Eins zu eins - ein Instrument
# gehoert genau einem Topf an, sonst waere die Trennung keine.
TOPF_FUER_INSTRUMENT = {"spot": "spot", "hebel": "hebel",
                        "absicherung": "absicherung"}

def sql_bedingung(instrument: str) -> str:
    """Woran eine Signalzeile ihrem Topf zugeordnet wird - als SQL-Fragment.

    DIESE ZEILE STAND ZWEIMAL, und beim zweiten Mal fast. `belegt_eur` hatte
    sie, und die Trefferbilanz brauchte am 14.08. dieselbe Unterscheidung -
    eine Kopie waere die vierte in diesem Projekt gewesen, die irgendwann
    auseinanderlaeuft.

    ES GIBT KEINE INSTRUMENTSPALTE, und es soll keine geben: `hebel` wird nur
    gesetzt, wenn ein Hebelfaktor gerechnet wurde. Eine zweite Spalte daneben
    waere eine zweite Wahrheit ueber dieselbe Sache.

    O-16 ERLEDIGT (14.08.2026): Spot und Absicherung sind jetzt trennbar.
    Beide haben `hebel IS NULL` - die Unterscheidung kommt aus der EINEN
    Stelle, an der sie im Projekt steht: `hedge/pipeline.SYMBOL_ZU_HEBEL_FAKTOR`.

    WARUM DAS OHNE WATCHLIST GEHT und ohne neue Spalte: die Liste ist statisch
    (DBPK, 3QSS). Hedge ist keine Assetklasse - die Watchlist fuehrt beide als
    `etf`, und ihre Mitgliedschaft in dieser Zuordnung ist das einzige, was sie
    zu Absicherungen macht. Genau deshalb steht die Abgrenzung dort und nicht
    hier.

    WAS ES AENDERT, und das ist mehr als eine Bilanzfrage: bis heute zaehlten
    offene Absicherungen gegen den SPOT-Topf. Der hat einen Deckel, die
    Absicherung nicht - eine gehaltene Hedge-Position hat also stillschweigend
    Spot-Budget belegt.

    Fail-soft: kennt das Projekt die Liste nicht (Importfehler), bleibt es bei
    der groben Trennung. Eine Bilanz mit zwei vermischten Instrumenten ist
    schlechter als eine getrennte, aber besser als keine."""
    if topf_fuer(instrument) == "hebel":
        return "hebel IS NOT NULL"
    try:
        from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR

        liste = ", ".join(f"'{s}'" for s in sorted(SYMBOL_ZU_HEBEL_FAKTOR))
    except Exception:                                        # noqa: BLE001
        return "hebel IS NULL"
    if not liste:
        return "hebel IS NULL"
    art = "IN" if topf_fuer(instrument) == "absicherung" else "NOT IN"
    return f"hebel IS NULL AND UPPER(symbol) {art} ({liste})"


# `None` heisst KEINE BEGRENZUNG. Bei zweien von dreien ist das die Vorgabe.
#
# ZWEI NUTZEREINWAENDE haben diese Zeilen geformt, und der zweite hat die erste
# Fassung ganz umgeworfen.
#
# (1) *"mit cash und Absicherung nicht zu restriktiv sein, um Blockaden zu
#     vermeiden."* - Ein Deckel auf ABSICHERUNG ist rueckwaerts: man deckelt
#     keinen Schutz. Wer im fallenden Markt absichern will und an eine
#     Obergrenze stoesst, hat sie am falschen Ende.
#
# (2) *"das Portfolio ist 70 Prozent im Minus und koennte somit von sich aus
#     schon ein Blocker sein, da man hier ein 2 oder 3x insgesamt benoetigt
#     fuer einen Gewinn."*
#
#     DAS IST DER ENTSCHEIDENDE PUNKT, und er trifft die erste Fassung im Kern.
#     Sie bemass jeden Topf als PROZENTSATZ DES AKTUELLEN Portfoliowerts. Ein
#     solcher Deckel SCHRUMPFT MIT DEM VERLUST:
#
#         Portfolio -70 %  ->  jeder Topf nur noch 30 % seiner Groesse
#         Erholung braucht  ->  +233 %
#
#     Der Deckel bremst also am staerksten, wenn Handeln am noetigsten ist.
#     Prozyklisch und selbstverstaerkend - und obendrein braucht er bei JEDER
#     Entscheidung einen aktuellen Portfoliowert, dessen Ausfall dann alles
#     sperrt.
#
# DESHALB ABSOLUT IN EURO, nicht in Prozent. Damit
#     * schrumpft kein Topf, weil der Markt gefallen ist,
#     * braucht keine Entscheidung eine Portfoliobewertung,
#     * und ein Bewertungsfehler kann nichts blockieren.
#
# Das passt zu dem, was ohnehin schon absolut ist: die Tranchen (100/300/500
# EUR) und `hebel.eigenkapital_richtwert_eur` (500 EUR). Der Nutzer setzt
# Betraege selbst - dieselbe Linie wie R-A2.
#
# HEBEL BEHAELT ALS EINZIGER EINEN DECKEL: er ist die einzige Position, die
# MEHR verlieren kann als ihr Einsatz. Dort ist eine Obergrenze kein Hindernis,
# sondern der Sinn der Sache.
VORGABE_DECKEL_EUR: dict[str, float | None] = {
    "spot": None,           # die RM-Regeln begrenzen die Einzelposition; ein
                            # zweiter Deckel darueber waere nur eine zweite
                            # Stelle, an der etwas blockieren kann
    "hebel": 3000.0,        # NUTZERENTSCHEIDUNG 13.08.: *"Hebeltopf gesamt
                            # kann 3000 Euro sein, eine Hebelposition vorerst
                            # 1000"* - drei Positionen gleichzeitig.
                            #
                            # VORHER 500, gleichgesetzt mit
                            # `hebel.eigenkapital_richtwert_eur`. Das war eine
                            # Verwechslung zweier Ebenen: jener Wert ist der
                            # Richtwert je POSITION, dieser der Deckel fuer den
                            # GANZEN Topf. Bei 500/500 waere genau eine
                            # Hebel-Position moeglich gewesen - im Live-Lauf vom
                            # 13.08. bekamen drei Signale je 500 EUR, zusammen
                            # 1.500 in einem 500er Topf. Moeglich nur, weil
                            # `belegt_eur=0.0` fest verdrahtet war.
    "absicherung": None,    # Schutz wird nicht gedeckelt
}


class TopfUnbekannt(ValueError):
    """Kein Topf fuer dieses Instrument."""


def topf_fuer(instrument: str) -> str:
    """Wirft, statt still auf `spot` zu fallen.

    Ein stiller Rueckfall waere hier genau der Fehler, den die Trennung
    verhindern soll: ein Hebel-Trade, der aus dem Spot-Topf bezahlt wird."""
    t = TOPF_FUER_INSTRUMENT.get(str(instrument or "").strip().lower())
    if t is None:
        raise TopfUnbekannt(
            f"Instrument {instrument!r} gehoert zu keinem Topf - bekannt: "
            f"{sorted(TOPF_FUER_INSTRUMENT)}")
    return t


def deckel_eur(config: dict | None = None) -> dict[str, float | None]:
    """Der absolute Deckel je Topf. `None` heisst: keine Begrenzung."""
    cfg = ((config or {}).get("risiko") or {}).get("toepfe_deckel_eur") or {}
    aus: dict[str, float | None] = {}
    for t in TOEPFE:
        wert = cfg.get(t, VORGABE_DECKEL_EUR[t])
        aus[t] = None if wert in (None, "") else float(wert)
    return aus


# Was als sofort verfuegbares Geld zaehlt. Fiat steht in `meta` (manuell
# gepflegt, die App sieht es sonst nirgends), Stablecoins stehen als Bestand.
#
# BEWUSST EINE KURZE, EXPLIZITE LISTE statt einer Heuristik ueber den Namen.
# Ein Token, das zufaellig "USD" im Namen traegt, ist noch kein Stablecoin -
# und ein falsch mitgezaehlter Bestand macht die Reserve wertlos.
STABLECOINS = ("EURCV", "USDC", "USDT", "DAI", "EURC", "EURT")

# Die Reserve, die NICHT investiert wird. Absolut in Euro - die alte Kette
# rechnet zusaetzlich 10 % vom Portfoliowert, und genau den kennt diese Kette
# absichtlich nicht (siehe `budget_eur`). Der feste Betrag ist die Haelfte der
# Regel, die ohne Portfoliobewertung auskommt.
VORGABE_RESERVE_EUR = 2000.0


def cash_frei_eur(conn, config: dict | None = None) -> float | None:
    """Wieviel Geld darf ueberhaupt noch eingesetzt werden - RM-4, absolut.

    DIE EINE UEBERGREIFENDE REGEL (siehe `UEBERGREIFEND` unten) - und sie war
    bis zum 13.08. dokumentiert und NIRGENDS GEBAUT. Der Kommentar dort
    beschrieb sie samt Wirkung, im Code gab es sie nicht.

    SIE BEGRENZT, SIE VERHINDERT NICHT. Das steht so in der Beschreibung der
    Regel, und es ist der Unterschied zwischen einem Deckel und einem Veto:
    knappes Cash macht Positionen kleiner, es macht keine Assetklasse
    unmoeglich.

    ABSOLUT STATT PROZENTUAL, aus demselben Grund wie alle Deckel hier: ein
    Prozentsatz auf ein Portfolio mit 60-Prozent-Positionen schrumpft genau
    dann, wenn wieder gehandelt werden muesste. Die Haelfte der alten Regel
    (`cash_reserve_min_fixed_eur`) kommt ohne Portfoliowert aus - die andere
    (`cash_reserve_min_prozent`) nicht, und sie bleibt deshalb draussen.

    `None` heisst: nicht ermittelbar, also keine Begrenzung. Eine Reserve, die
    wegen einer fehlenden Zahl ALLES sperrt, waere schlimmer als keine."""
    import sqlite3 as _sq

    from database import db as DB

    # DIE ZEILENFABRIK MUSS PASSEN, sonst faellt RM-4 STILL aus.
    #
    # `db.get_cash_reserve_fiat_eur()` liest `row["value"]` - das setzt
    # `sqlite3.Row` voraus. Eine Verbindung ohne diese Einstellung liefert
    # Tupel, der Zugriff wirft, und diese Funktion gaebe `None` zurueck: KEINE
    # BEGRENZUNG. Die Reserve verschwaende dann lautlos, und zwar genau bei dem
    # Aufrufer, der es am wenigsten merkt.
    #
    # Gefunden in der eigenen Gegenpruefung, weil die Testverbindung sie nicht
    # setzt - im Betrieb tut `db.get_connection()` es. Ein Fehler, der nur
    # ausserhalb der Produktion auftritt, ist trotzdem einer.
    _vorher = conn.row_factory
    try:
        conn.row_factory = _sq.Row
        fiat = float(DB.get_cash_reserve_fiat_eur(conn) or 0.0)
    except Exception:                                        # noqa: BLE001
        return None
    finally:
        conn.row_factory = _vorher
    stabil = 0.0
    try:
        for sym, menge in conn.execute(
                "SELECT symbol, quantity FROM holdings WHERE quantity > 0"):
            if str(sym).upper() in STABLECOINS:
                # 1:1 angesetzt. Ein Stablecoin, der von 1 abweicht, hat ein
                # groesseres Problem als diese Rechnung.
                stabil += float(menge or 0.0)
    except Exception:                                        # noqa: BLE001
        pass
    reserve = ((config or {}).get("risiko") or {}).get(
        "cash_reserve_min_fixed_eur", VORGABE_RESERVE_EUR)
    return max(0.0, fiat + stabil - float(reserve))


def belegt_eur(conn, instrument: str) -> float:
    """Was in DIESEM Topf schon steckt - offene Signale der eigenen Kette.

    BIS ZUM 13.08. GAB ES DAS NICHT. `rollen_lauf` uebergab fest `0.0`, der
    Topf meldete sich bei jedem Signal als vollstaendig frei, und der Deckel
    konnte nie greifen: im Live-Lauf bekamen drei Hebel-Signale je 500 EUR aus
    einem 500-EUR-Topf. Der Parametername sagte die ganze Zeit, was gebraucht
    wird - gefuellt hat ihn niemand.

    WORAN EIN HEBEL-SIGNAL ERKANNT WIRD: an der Spalte `hebel`. Sie wird nur
    gesetzt, wenn ein Hebelfaktor gerechnet wurde - `signals` hat keine
    Instrumentspalte, und eine einzufuehren waere eine zweite Wahrheit neben
    einer, die schon eindeutig ist.

    NUR OFFENE POSITIONEN. Ein aufgeloestes Signal belegt nichts mehr.

    Fail-soft: ohne die Spalten (aeltere Datei) gilt der Topf als leer. Das ist
    die Richtung, in die ein Fehler hier fallen DARF - ein Topf, der sich wegen
    eines Schemafehlers als voll meldet, sperrt lautlos alles."""
    try:
        spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
        if not {"quelle_kette", "hebel", "position_size_eur"} <= spalten:
            return 0.0
        bedingung = sql_bedingung(instrument)
        # NUR EINSTIEGE BELEGEN KAPITAL (14.08.2026 - die Ursache des
        # Hebel-Stillstands am ersten Betriebstag).
        #
        # WAS PASSIERT IST. `_schreibe_nein()` schreibt fuer jedes
        # NICHTS_TUN/HALTEN eine Zeile MIT `position_size_eur` und `hebel` -
        # als Messpunkt, damit sich der Kontrollarm spaeter aufloesen laesst.
        # Diese Funktion zaehlte sie als belegtes Kapital mit. Drei solche
        # Schattenbuchungen zu je 1.000 EUR fuellen den Hebel-Topf (3.000 EUR)
        # vollstaendig.
        #
        # DIE FOLGE WAR EINE SCHLEIFE, die sich selbst am Leben hielt:
        #
        #   Topf voll  ->  Betrag 0 EUR  ->  Verlust an der Stufe "geometrie"
        #              ->  KEINE Zeile geschrieben
        #              ->  Cooldown findet nichts
        #              ->  naechster Lauf fragt dieselben Symbole wieder
        #
        # Gemessen am 14.08.: 14 von 41 Hebel-Symbolen je Lauf, alle vier
        # Viertelstunden neu, 698 Modellaufrufe fuer 46 Urteile. Ohne den
        # Stopp durch den Nutzer waeren es ueber Nacht rund 3.900 gewesen.
        #
        # EIN SCHATTEN IST KEINE POSITION. Er bindet kein Geld, weil nie
        # gekauft wurde - er haelt nur fest, was passiert waere. Ihn im Topf
        # mitzuzaehlen verwechselt die Messung mit der Sache.
        #
        # ALS EINSCHLUSSLISTE, nicht als Ausschluss: gezaehlt wird, was eine
        # Position EROEFFNET. Ein Verkaufsvorschlag bindet ebenso wenig Kapital
        # wie ein Schatten, und eine Liste des Erlaubten faengt auch die
        # Aktionen, die es noch nicht gibt.
        from agent.signal_mail import AKTIONEN_MIT_EINSTIEG

        platzhalter = ", ".join("?" for _ in AKTIONEN_MIT_EINSTIEG)
        zeile = conn.execute(
            f"SELECT COALESCE(SUM(position_size_eur), 0) FROM signals "
            f"WHERE quelle_kette = 'rollen' AND outcome_status IS NULL "
            f"AND action IN ({platzhalter}) AND {bedingung}",
            tuple(AKTIONEN_MIT_EINSTIEG)).fetchone()
        return float(zeile[0] or 0.0)
    except Exception:                                        # noqa: BLE001
        return 0.0


def budget_eur(instrument: str, config: dict | None = None) -> float | None:
    """Wieviel Kapital steht DIESEM Topf hoechstens zu? `None` = unbegrenzt.

    KEIN PORTFOLIOWERT ALS PARAMETER, und das ist der Kern von Paket 5. Die
    erste Fassung nahm einen und rechnete Prozente davon - sie hatte damit zwei
    Fehler auf einmal: sie schrumpfte im Drawdown (genau dann, wenn Handeln
    noetig ist) und sie sperrte alles, sobald die Bewertung fehlte.

    Bewusst OHNE Kenntnis der anderen Toepfe: die Funktion kann gar nicht
    verrechnen, weil sie die anderen nicht sieht. Das ist die Trennung als
    Bauform, nicht als Absichtserklaerung."""
    return deckel_eur(config)[topf_fuer(instrument)]


def frei_eur(instrument: str, belegt_eur: float,
             config: dict | None = None) -> float | None:
    """Wieviel ist in DIESEM Topf noch frei? `None` heisst: unbegrenzt.

    `belegt_eur` ist ausdruecklich der Bestand DESSELBEN Topfes. Wer hier den
    Gesamtbestand uebergibt, hat die Trennung aufgehoben - deshalb steht es im
    Namen des Parameters und in dieser Zeile."""
    budget = budget_eur(instrument, config)
    if budget is None:
        return None
    return max(0.0, budget - max(0.0, float(belegt_eur or 0.0)))


def absicherung_bedarf_eur(abzusicherndes_exposure_eur: float,
                           hebel_faktor: float) -> float:
    """Wieviel Einsatz braucht es, um dieses Exposure abzusichern?

    Ein Drei-fach-Short deckt mit einem Euro drei Euro Exposure ab. Deshalb
    NICHT eine Prozentzahl des Portfolios, sondern:

        Einsatz = Exposure / Hebelfaktor

    Die Literaturzahlen (0,5-2 % des Portfoliowerts pro Jahr) stammen aus der
    OPTIONSWELT - dort kauft man eine Praemie, hier eine Position. Sie hierher
    zu uebernehmen waere eine Zahl mit falscher Herkunft.

    ACHTUNG, und das gehoert zu jeder Verwendung dazu: gehebelte inverse ETFs
    verlieren durch taegliches Rebalancing ueber laengere Haltedauern auch dann,
    wenn der Basiswert am Ende gleich steht. Der Bedarf hier ist eine
    MOMENTAUFNAHME, keine Jahresrechnung."""
    if not abzusicherndes_exposure_eur or abzusicherndes_exposure_eur <= 0:
        return 0.0
    if not hebel_faktor or hebel_faktor <= 0:
        return 0.0
    return float(abzusicherndes_exposure_eur) / float(hebel_faktor)


# --- UEBERGREIFEND: die einzigen Groessen, die ueber Toepfe hinweg wirken ----
#
# Sie stehen hier NAMENTLICH, damit es keine zweite Stelle gibt, an der sich
# eine Verrechnung einschleicht. Wer eine hinzufuegt, muss diese Liste anfassen
# - und damit begruenden.
#
#   CASH-RESERVE (RM-4)  Sie gilt fuer das GESAMTE Portfolio, weil sie
#                        Handlungsfaehigkeit sichert, nicht eine Strategie. Sie
#                        BEGRENZT die Groesse einer neuen Position - sie
#                        VERHINDERT keine Aktion in einem anderen Topf. Gemessen
#                        hat sie in 118 Signalen kein einziges Mal gegriffen.
#   RM-1 / RM-2          Risiko je Trade und Allokation je Asset gelten INNERHALB
#                        eines Topfes und sind je Instrument verschieden
#                        (Spot 2 %, Hebel 1 %). Sie verrechnen nichts.
#
# Was ausdruecklich NICHT uebergreifend wirkt:
#   * ein niedriger Absicherungsgrad senkt KEINEN Kauf-Betrag
#   * ein voller Hebel-Topf senkt KEINEN Spot-Betrag
#   * ein knapper Cash-Anteil verhindert KEINE Absicherung
UEBERGREIFEND = ("cash_reserve",)
