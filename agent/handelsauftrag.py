# -*- coding: utf-8 -*-
"""Was ueberhaupt gehandelt wird: Instrument und Strategie (Paket 2, 12.08.2026).

DIE LUECKE, die das schliesst. Bis heute kamen `strategie`, `hebel`, `spot` und
`instrument` in der neuen Rollen-Kette **null Mal** vor. Der Trader urteilte,
ohne zu wissen, WORUEBER er urteilt - und deshalb liess sich die Frage des
Nutzers ("Long 3x, Einstieg bei ca., TP bei ca.") gar nicht beantworten.

Ein echter Haendler entscheidet bei 3x Hebel anders als bei einem
Spot-Einmalkauf: dieselben Fakten, anderer Trade. Diese Bedingung fehlte
vollstaendig.

VORGABE, NICHT FRAGE. Der Aufrufer weiss immer, worum es geht - `krypto/pipeline`
und `krypto/hebel_pipeline` sind getrennte Pipelines. Also wird es uebergeben,
nicht erfragt. Dieselbe Linie wie beim Betrag (R-A2): was feststeht, geben wir
vor; ein Modell danach zu fragen fuegt nur eine Fehlerquelle hinzu.

WARUM EIN EIGENES MODUL. Zwei Stellen brauchen dieselbe Definition - der PROMPT
(`rolle_trader`) und der FAKTENSATZ (`rollen_eingabe`). Zwei Kopien einer Liste
laufen auseinander, und dann fragt der Prompt nach etwas, das die Eingabe nicht
kennt. Genau dieser Fehler ist am 12.08. schon einmal passiert: die Marktbreite
war aus den Fakten raus, die Frage danach stand noch im Prompt.

WAS HIER NOCH NICHT STEHT: Richtung (LONG/SHORT) und Hebelfaktor. Die gehoeren
zu Paket 13 - erst wenn Spot durchgemessen ist, wissen wir, ob die Kette traegt.
`hebel` ist hier bereits vorgesehen, damit die Kosten-Fakten schon jetzt richtig
zugeordnet werden.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

INSTRUMENTE = ("spot", "hebel", "absicherung")

# STRATEGIE heisst hier: wie wird eingestiegen und woran wird der Erfolg
# gemessen - nicht, in welche Richtung.
#
#   einstieg      ein Zeitpunkt, ein Ziel, ein Stop. Erfolg = Ziel vor Stop
#   swing         wie einstieg, aber mit Haltekriterium und nachgezogenem Stop
#   akkumulation  gestaffelt ueber Zeit. Sie hat SEHR WOHL ein Ziel - nur
#                 kein nahes: gekauft wird in der Erwartung hoeherer Kurse auf
#                 lange Sicht (Nutzerkorrektur 12.08.: "bei Akkumulation gibt
#                 es eigentlich kein NICHT-Ziel, sondern nur kein NAHES Ziel").
#
#                 Was fehlt, ist nicht die Erwartung, sondern der ABBRUCH: ein
#                 fallender Kurs beendet die Position nicht, er verbilligt sie.
#                 Ein Stop wuerde die Strategie in ihrem besten Moment
#                 abbrechen. Deshalb kein Stop und kein einzelner Zeitpunkt -
#                 und deshalb ein ANDERES Erfolgsmass: Durchschnittskurs und
#                 Endvermoegen statt "Ziel vor Stop".
#
#                 FOLGE, die leicht zu uebersehen ist: `umgeworfen_durch` ist
#                 hier nicht ein Feld unter vielen, sondern das EINZIGE
#                 Ausstiegskriterium. Wo Einstieg und Swing einen Stop haben,
#                 hat die Akkumulation nur die Frage "wann traegt die Erwartung
#                 nicht mehr".
STRATEGIEN = ("einstieg", "swing", "akkumulation")


def ist_hebelgeschaeft(rechnung=None, instrument=None) -> bool:
    """Ist DIESES Geschaeft ein Hebelgeschaeft? (I-1, 28.08.2026)

    ⚠️ DIE FRAGE, DIE SEIT S6b NIRGENDS RICHTIG GESTELLT WURDE. Zwoelf Stellen
    fragten `instrument == "hebel"` - und seit dem 22.08. ist `instrument` im
    Lauf IMMER "spot", weil es nur noch einen Lauf je Asset gibt
    (`INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot",)`). Die Antwort war dort also
    immer nein, unabhaengig davon, was gerechnet wurde.

    Was das kostete, an drei Beispielen:

        asset_schalter       der Hebel-Schalter je Asset wurde nie gefragt
        positionsfuehrung    `hebel_signals` wurde nie gelesen
        trefferbilanz        Kosten mit Spot-Tier: 0,60 R statt 0,76 R

    DIE SACHFRAGE STEHT IM ERGEBNIS, NICHT IM LAUF. `entscheidungsrechnung`
    setzt `etikett` auf "hebel", wenn ein Hebel noetig ist oder es ein SHORT
    ist - genau das ist die Antwort. S6b hat den Topf und die Handelbarkeit
    bereits darauf umgestellt; diese Funktion macht daraus EINE Stelle, damit
    die naechste Umstellung nicht wieder zwoelf Stellen sucht.

    ⚠️ `instrument` BLEIBT ALS RUECKFALL - aber nur, wenn keine Rechnung
    vorliegt. Es gibt Aufrufer ohne Rechnung (Anzeige, Altdaten, die alten
    Ketten mit zwei Laeufen), und fuer die ist das Lauf-Etikett die einzige
    Auskunft, die es gibt. Ein Rueckfall, der still das Gegenteil behauptet,
    waere schlimmer als keiner - deshalb steht er hier sichtbar und nicht
    verteilt an zwoelf Stellen."""
    if rechnung:
        etikett = None
        try:
            etikett = rechnung.get("etikett")
        except AttributeError:
            etikett = getattr(rechnung, "etikett", None)
        if etikett is not None:
            return str(etikett).strip().lower() == "hebel"
    return str(instrument or "").strip().lower() == "hebel"

# WELCHE PAARE SINNVOLL SIND, und warum die uebrigen fehlen:
#
#   hebel x akkumulation   Die Finanzierung kostet JEDEN Tag. Eine Strategie,
#                          die bewusst lange laeuft, zahlt genau diese Kosten
#                          am laengsten - das ist keine Frage der Meinung,
#                          sondern der Kostenrechnung.
#   absicherung x swing    Absicherung folgt dem Portfolio, nicht einem
#                          Kursverlauf. Ein nachgezogener Stop auf einem
#                          Short-Produkt sichert den Schutz weg, den man
#                          aufgebaut hat.
#   absicherung x akkum.   Entschieden am 12.08. (E1a): Absicherung bekommt
#                          keine Tranchen - die Staffelungsregel wirkte dort
#                          mit umgekehrtem Vorzeichen.
#   spot x swing           NUTZERENTSCHEIDUNG 14.08. `swing` ist ueber den
#                          NACHGEZOGENEN STOP definiert - und der Nutzer haelt
#                          Spot ausdruecklich ohne Stop-Loss ("aktuell auch
#                          ohne StopLoss"), laengerfristig, in Tranchen. Ein
#                          Spot-Swing waere damit eine Kombination, die er nie
#                          ausfuehrt; das Modell haette eine Aufgabe bekommen,
#                          die es in der Praxis nicht gibt.
#
#                          VORERST, nicht grundsaetzlich: setzt er kuenftig
#                          Trailing-Stops auf Spot, gehoert das Paar zurueck -
#                          die Mechanik dafuer liegt in `ausstiegsrechnung`
#                          bereits fertig.
ERLAUBTE_PAARE = {
    "spot": ("einstieg", "akkumulation"),
    "hebel": ("einstieg", "swing"),
    "absicherung": ("einstieg",),
}

# Braucht diese Kombination einen Einstiegskurs und einen STOP?
#
# Die Frage ist NICHT "gibt es ein Ziel" - das hat auch die Akkumulation, nur
# kein nahes. Die Frage ist, ob es einen einzelnen Zeitpunkt und einen Abbruch
# gibt. Bei Akkumulation nicht: ein Stop wuerde die Staffelung genau dann
# aufheben, wenn sie am guenstigsten kauft.
_MIT_KURSEN = {("spot", "akkumulation"): False}


class AuftragUngueltig(ValueError):
    """Instrument und Strategie passen nicht zusammen."""


def pruefe(instrument: str, strategie: str) -> tuple[str, str]:
    """Wirft, statt still auf einen Vorgabewert zu fallen.

    Ein stiller Rueckfall waere hier besonders teuer: er wuerde einen
    Hebel-Trade als Spot-Trade bewerten - mit denselben Fakten, aber ohne die
    Finanzierungskosten, die ihn erst teuer machen."""
    i = str(instrument or "").strip().lower()
    s = str(strategie or "").strip().lower()
    if i not in INSTRUMENTE:
        raise AuftragUngueltig(f"Instrument {instrument!r} - erlaubt {INSTRUMENTE}")
    if s not in STRATEGIEN:
        raise AuftragUngueltig(f"Strategie {strategie!r} - erlaubt {STRATEGIEN}")
    if s not in ERLAUBTE_PAARE[i]:
        raise AuftragUngueltig(
            f"{i} + {s} ist keine vorgesehene Kombination - erlaubt fuer {i}: "
            f"{ERLAUBTE_PAARE[i]}")
    return i, s


def hebel_erlaubt_fuer(strategie: str) -> bool:
    """Darf DIESE Strategie ueberhaupt gehebelt werden? (I-2, 01.09.2026)

    ⚠️ AUS DER PAAR-MATRIX, NICHT AUS EINER ZWEITEN LISTE. `ERLAUBTE_PAARE`
    ist die eine Quelle; wer hier eine eigene Aufzaehlung baute, haette die
    naechste Stelle geschaffen, an der beide auseinanderlaufen.

    ## Wozu es gebraucht wird

    `entscheidungsrechnung` bekommt bisher `hebel_handelbar` aus der GRUPPE
    (`assetklassen.hebel_handelbar`) - also die Antwort auf *„ist Hebel bei
    Krypto ueberhaupt handelbar?"*. Die zweite Haelfte der Frage fehlte:
    *„und passt er zu dieser Strategie?"*

    Fuer `akkumulation` ist die Antwort NEIN, und zwar aus einem Grund, der
    im Kopf von `ERLAUBTE_PAARE` steht: die Finanzierung kostet JEDEN Tag,
    und eine Strategie, die bewusst lange laeuft, zahlt genau diese Kosten
    am laengsten.

    ## ⚠️ Warum das der richtige Ort ist - und die Meldung nicht reichte

    Seit dem 28.08. wurde der Konflikt GEMELDET (I-2): der Lauf schrieb
    *„ACHTUNG: ETH laeuft als akkumulation, die Rechnung ergibt aber das
    Etikett 'hebel'"*. Die Begruendung fuer Melden statt Sperren lautete
    damals: *„Ein Abbruch naehme dem Kern seine Meldung."*

    **Diese Begruendung ist seit Schritt 3+4 (01.09.) hinfaellig.** Ein
    Kern-Asset hat jetzt ZWEI Zellen: die Akkumulation und die taktische.
    Der Hebel gehoert in die taktische; die Akkumulation verliert nichts,
    wenn sie ihn nicht bekommt. Das verbotene Paar muss deshalb nicht mehr
    hinterher gemeldet werden - es kann von vornherein nicht ENTSTEHEN.

    ⚠️ Die Meldung bleibt trotzdem stehen. Sie ist ab jetzt ein WAECHTER:
    schlaegt sie noch einmal an, ist etwas anderes kaputt.
    """
    return str(strategie or "").strip().lower() in ERLAUBTE_PAARE.get(
        "hebel", ())


def mit_kursen(instrument: str, strategie: str) -> bool:
    """Werden Einstiegskurs und Stop ueberhaupt gebraucht?"""
    return _MIT_KURSEN.get((instrument, strategie), True)


# Der Satz, der im Faktensatz steht. Er nennt die BEDINGUNG, unter der geurteilt
# wird - keine Aufforderung und keine Wertung (R-T3).
_SATZ_INSTRUMENT = {
    "spot": "Gehandelt wird der Wert selbst, ohne Hebel und ohne laufende "
            "Kosten.",
    "hebel": "Gehandelt wird eine gehebelte Position. Die Finanzierung faellt "
             "an JEDEM Tag an, in dem die Position offen ist, und ein "
             "Rueckschlag kann zur Zwangsaufloesung fuehren.",
    "absicherung": "Gehandelt wird ein Absicherungsinstrument. Es soll das "
                   "uebrige Portfolio abfedern, nicht selbst Gewinn erzielen.",
}
_SATZ_STRATEGIE = {
    "einstieg": "Es geht um einen einzelnen Einstieg mit einem Ziel und einem "
                "Ausstiegskurs.",
    "swing": "Die Position soll ueber mehrere Wochen gehalten und laufend "
             "nachgezogen werden.",
    "akkumulation": "Es wird ueber die Zeit gestaffelt gekauft, in der "
                    "Erwartung hoeherer Kurse auf lange Sicht. Ein fallender "
                    "Kurs beendet diese Position nicht - er verbilligt sie. "
                    "Deshalb gibt es hier keinen einzelnen Einstiegszeitpunkt "
                    "und keinen Stop; beendet wird sie erst, wenn die "
                    "Erwartung selbst nicht mehr traegt.",
}


def beschreibe(instrument: str, strategie: str) -> list[str]:
    """Zwei Saetze fuer den Faktensatz - Bedingung, nicht Anweisung.

    DIESES FELD IST EIN KONSTANTES FELD, und `finde_konstanten()` meldet es
    auch. Das ist kein Versehen und wird NICHT durch eine Ausnahme im Waechter
    stillgelegt (Gegenpruefung 12.08.):

      * Es ist konstant je LAUF, nicht ueber Laeufe hinweg. Ein Hebel-Lauf und
        ein Spot-Lauf tragen verschiedene Saetze - genau das ist der Zweck.
      * R-T6 richtet sich gegen Felder, die nicht unterscheiden KOENNEN und
        trotzdem eine Richtung nahelegen. Dieses hier soll nicht zwischen
        Assets unterscheiden; es ist die BEDINGUNG, unter der sie alle
        beurteilt werden.

    DAS RESTRISIKO IST TROTZDEM REAL und gehoert benannt: der Hebel-Satz nennt
    laufende Kosten und die Zwangsaufloesung. Beides ist wahr, aber es koennte
    JEDE Hebel-Beurteilung gleichfoermig daempfen - und eine gleichfoermige
    Daempfung sieht aus wie Vorsicht und ist keine.

    MESSPUNKT, nicht Annahme: eine gepaarte Messung auf denselben Ankern, ein
    Arm spot und einer hebel, zeigt es. Faellt die Handlungsquote im
    Hebel-Arm deutlich staerker, als die Kostenrechnung hergibt, ist der Satz
    zu stark formuliert - und dann wird der SATZ geaendert, nicht der Waechter.
    """
    i, s = pruefe(instrument, strategie)
    return [_SATZ_INSTRUMENT[i], _SATZ_STRATEGIE[s]]


def strategie_fuer(symbol: str, instrument: str, *, conn=None,
                   vorgabe: str = "einstieg", assetklasse: str | None = None,
                   nur_klassen=None) -> str:
    """Welche Strategie gilt fuer DIESES Asset? (A, 27.08.2026)

    DIE LUECKE, DIE DAS SCHLIESST. `strategie` wurde bisher LAUFWEIT vorgegeben
    (`fuehre_umlauf(strategie="einstieg")`) und an jedes Asset unveraendert
    weitergereicht. Gemessen ueber 7.294 Signale: `akkumulation` kam NULL Mal
    vor. Damit lief die Paar-Matrix nie, der Nutzer-Schalter nie, und ein
    langfristig gehaltener Spot-Bestand wurde wie ein Einzeltrade behandelt -
    samt Trailing-Stop, den es dort nicht gibt (N-11).

    DIE ZUORDNUNG KOMMT AUS DEM SCHALTER DES NUTZERS, nicht aus einer Liste
    im Code. `asset_dca_settings.dca_erlaubt` ist der Schalter, den
    `asset_schalter.py:119` schon heute fuer `strategie == "akkumulation"`
    prueft - er lief nur nie an, weil die Strategie nie so hiess.

    ⚠️ DAMIT AENDERT SICH DIE BEDEUTUNG DES SCHALTERS. In der GUI heisst er
    "Tranchen-Vorschlaege umschalten (BTC/ETH/SOL)"; fachlich hat er immer
    die Akkumulation gemeint (AZ-4: gestaffelt kaufen IST Akkumulation, und
    `betraege.py` nennt 250 EUR ausdruecklich "eine Tranche"). Wer ihn setzt,
    bekommt ab jetzt die Strategie - nicht nur einen Textvorschlag in der Mail.

    ⚠️ NUR FUER SPOT. `hebel x akkumulation` ist ausgeschlossen (Finanzierung
    kostet jeden Tag), `absicherung` kennt ohnehin nur `einstieg`. Bei jedem
    anderen Instrument bleibt es bei der Vorgabe - ohne Nachfrage an die DB.

    ⚠️ DER SCHALTER STEHT FUER 16 ASSETS AUF AN, NICHT FUER DREI. Der
    Vorgabewert `_DCA_ERLAUBT_DEFAULT_SYMBOLS` (database/db.py:1857) enthaelt
    neben BTC/ETH/SOL die am 09.08. GEHALTENEN Multi-Asset-Positionen - eine
    Nutzerentscheidung ("an fuer die gehaltenen"). Fuer diese 13 Aktien und
    ETFs bedeutet die Umstellung: kein Stop, kein Trailing, nur V1.

    `nur_klassen` begrenzt das, ohne den Schalter anzufassen: mit
    `nur_klassen={"krypto"}` gilt Akkumulation nur dort. Ohne Angabe wirkt
    der Schalter wie vom Nutzer gesetzt.

    ⚠️ ZWEI BEGRIFFE FUER "KERN" - UND SIE SIND NICHT DASSELBE (27.08.).

        `rolle: core` (config.yaml)   13 Assets   steuert COOLDOWN (8 h statt
                                                  15 h) und Budget-Allocator
        `dca_erlaubt` (DB-Schalter)    3 Assets   steuert die STRATEGIE

    Zehn Assets sind `core`, bekommen aber `einstieg`: AVAX, BNB, CANTON,
    HYPE, LINK, MORPHO, NEAR, SEI, SUI, TAO. Das ist KEIN Fehler, sondern ein
    Unterschied mit Bedeutung: sie werden langfristig GEHALTEN (fast alle sind
    gestakt), aber nicht aktiv AUFGEBAUT. Wer die Strategie aus `rolle` ableiten
    wollte, bekaeme dreizehn statt drei - und damit Positionen ohne Stop, die
    der Nutzer nie dafuer vorgesehen hat.

    EIN LESEFEHLER HEISST "VORGABE", NICHT "AKKUMULATION". Dieselbe Linie wie
    in `asset_schalter`: ein nicht lesbarer Schalter darf keine Strategie
    einschalten, die der Nutzer nicht gewaehlt hat."""
    i = str(instrument or "").strip().lower()
    if i != "spot" or conn is None:
        return vorgabe
    if nur_klassen is not None:
        if str(assetklasse or "").strip().lower() not in nur_klassen:
            return vorgabe
    try:
        import database.db as db
        if db.get_dca_erlaubt(conn, str(symbol).upper()):
            return "akkumulation"
    except Exception as exc:                                 # noqa: BLE001
        logger.warning("DCA-Schalter fuer %s nicht lesbar (%s) - Strategie "
                       "bleibt %r", symbol, exc, vorgabe)
    return vorgabe
