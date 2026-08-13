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
        bedingung = ("hebel IS NOT NULL" if topf_fuer(instrument) == "hebel"
                     else "hebel IS NULL")
        zeile = conn.execute(
            f"SELECT COALESCE(SUM(position_size_eur), 0) FROM signals "
            f"WHERE quelle_kette = 'rollen' AND outcome_status IS NULL "
            f"AND {bedingung}").fetchone()
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
