# -*- coding: utf-8 -*-
"""Die BERECHNUNG DES AUSSTIEGS - das Gegenstueck zur Einstiegsrechnung.

WARUM DAS DER WICHTIGSTE TEIL IST. Der groesste gemessene Befund dieser
Projektphase (04.08., 86 real bewertete Hebel-Signale):

    erreichten unterwegs >= 1 R      50,0 %
    endeten tatsaechlich im Plus     17,6 %

Die Haelfte aller Signale stand einmal bei +1 R und ging trotzdem als Verlust
aus. **Die Einstiege finden die Bewegung; zwischen Maximum und Ergebnis geht
sie verloren.** Monatelang wurde an Gates, Konfidenz und CRV-Schwellen
gemessen - an einer Stelle, die laut dieser Messung funktioniert.

DREI PRUEFUNGEN, UND NUR ZWEI DAVON SIND NEU:

  1. Trailing-Stop        `agent/krypto/ausstiegsregel.py`, seit 05.08. scharf.
                          IMPORTIERT, nicht nachgebaut - sie ist an 495
                          aufgeloesten Signalen gemessen (+0,092 R je Signal,
                          Block-Bootstrap [+0,051; +0,131], in beiden
                          Stichprobenhaelften stabil). Eine zweite Fassung
                          waere die Sorte Kopie, die still veraltet.
  2. Widerlegungspreis    NEU. Das Modell nennt bei jeder Entscheidung einen
                          Kurs, der sie als falsch erweisen wuerde
                          (`umgeworfen_preis_eur`). Die Fakten-
                          Entscheidungsmappe haelt fest, dass er "heute von
                          niemandem ausgewertet" wird (8c.2/K2). Ab hier schon.
  3. Frist                NEU. `umgeworfen_bis` - bis wann die Begruendung
                          gelten soll. 15 bis 21 % aller Faelle laufen ohne
                          Entscheidung aus (Arbeitsstand 7.23); heute merkt
                          das niemand.

DAS IST KEIN OVERRIDE DES MODELLS, SONDERN SEIN EIGENES WORT. Die Regel
"kein deterministischer Override des LLM-Werturteils" schuetzt die qualitative
Synthese. Hier wird nichts ueberschrieben: das Modell hat SELBST gesagt, unter
welcher Bedingung seine Begruendung faellt. Sie zu pruefen heisst, es beim Wort
zu nehmen - das Gegenteil eines Overrides.

WAS SICH NICHT MASCHINELL PRUEFEN LAESST, WIRD AUCH NICHT BEHAUPTET.
`umgeworfen_durch` ist Prosa ("ein Tagesschluss ueber X bei steigendem
Volumen"). Der Kurs darin ist pruefbar, die Bedingung "bei steigendem Volumen"
nicht zuverlaessig. Deshalb wird der Satz dem Nutzer GEZEIGT und nicht
stillschweigend als erfuellt oder unerfuellt behandelt.

EIN EHRLICHER VORBEHALT ZUM WIDERLEGUNGSPREIS. In der neuen Kette leitet
`entscheidungsrechnung._stop_abstand()` den Stop AUS diesem Preis ab. Wo er
unveraendert uebernommen wurde, fallen Stop und Widerlegung zusammen, und die
zweite Pruefung sagt dann nichts Eigenes. Eigenstaendig wird sie erst, wo der
Preis geklemmt wurde (zu eng, zu weit) oder wo die Position aus der alten Kette
stammt. Das wird ausgewiesen, statt eine doppelte Absicherung vorzutaeuschen.

ADVISORY-ONLY, wie die Ausstiegsregel: dieses Modul rechnet. Es fuehrt nichts
aus und schliesst keine Position.
"""
from __future__ import annotations

from datetime import date, datetime

from agent.krypto.ausstiegsregel import (
    ABSTAND_R, AUSLOESE_R, stopempfehlung, stopempfehlung_aus_mfe)

# NAEHERUNGSWARNUNG. Ab wieviel des Weges vom Einstieg zum Ziel wird gewarnt?
#
# WARUM NICHT EINFACH OEFTER MAILEN. Der Nutzereinwand war, dass man vom
# erreichten Ziel erst am naechsten Morgen erfaehrt - bei einem Ruecklauf ueber
# Nacht ist das Geld dann weg. Die naheliegende Antwort waere ein engerer Takt.
# Sie ist falsch: eine Mail alle 15 Minuten wird nach zwei Tagen ignoriert, und
# selbst dann ist man nicht schneller als der Markt.
#
# DIE RICHTIGE ANTWORT IST EIN VERKAUFSAUFTRAG. Das Ziel steht im Voraus fest -
# es laesst sich bei der Boerse hinterlegen. Die Warnung sagt deshalb nicht
# "pass auf", sondern "hinterlege jetzt einen Auftrag bei X". Danach braucht es
# die Mail gar nicht mehr, und der Ruecklauf ueber Nacht ist wirkungslos.
ZIEL_NAH_ANTEIL = 0.75

# Die Empfehlungen, absteigend nach Dringlichkeit.
SCHLIESSEN = "SCHLIESSEN"
STOP_NACHZIEHEN = "STOP NACHZIEHEN"
HALTEN = "HALTEN"


def _de(wert: float, stellen: int = 2) -> str:
    """Deutsche Schreibweise. Die erste Fassung hat die ganze AUSGABEZEILE
    durch `translate` geschickt - das trifft dann auch Text, der kein Zahl ist,
    und in einer anderen Zeile stand "50,901.00 EUR" unuebersetzt daneben.
    Zwei Schreibweisen in einer Nachricht sind genau der Fehler aus 12.5."""
    return f"{float(wert):,.{stellen}f}".translate(str.maketrans(",.", ".,"))


def _als_datum(wert) -> date | None:
    if isinstance(wert, date):
        return wert
    if isinstance(wert, str) and wert.strip():
        try:
            return datetime.fromisoformat(wert.strip()[:10]).date()
        except ValueError:
            return None
    return None


def bewerte(*, einstieg: float | None, stop_original: float | None,
            kurs_aktuell: float | None,
            hoechstkurs: float | None = None, mfe_r: float | None = None,
            stop_aktuell: float | None = None, ist_short: bool = False,
            umgeworfen_preis_eur: float | None = None,
            ziel: float | None = None,
            umgeworfen_bis=None, umgeworfen_durch: str | None = None,
            heute=None, ausloese_r: float = AUSLOESE_R,
            abstand_r: float = ABSTAND_R) -> dict | None:
    """Alle drei Pruefungen fuer EINE gehaltene Position.

    Entweder `hoechstkurs` (guenstigster Kurs seit Eroeffnung) oder `mfe_r`
    (hoechster Buchgewinn in R) - das Backward-Tracking fuehrt letzteren seit
    dem 02.08. bei jedem Lauf fort, auch fuer offene Signale.

    None, wenn Einstieg oder Originalstop fehlen: ohne sie gibt es kein R und
    damit keine der drei Aussagen."""
    if not einstieg or einstieg <= 0 or stop_original is None:
        return None
    risiko = (stop_original - einstieg) if ist_short else (einstieg - stop_original)
    if risiko <= 0:
        return None

    if mfe_r is not None:
        empf = stopempfehlung_aus_mfe(einstieg, stop_original, mfe_r, ist_short,
                                      stop_aktuell, ausloese_r, abstand_r)
    elif hoechstkurs is not None:
        empf = stopempfehlung(einstieg, stop_original, hoechstkurs, ist_short,
                              stop_aktuell, ausloese_r, abstand_r)
    else:
        empf = None

    e = {"risiko_eur": risiko,
         "stand_r": (((einstieg - kurs_aktuell) if ist_short else
                      (kurs_aktuell - einstieg)) / risiko)
                    if kurs_aktuell else None,
         "mfe_r": empf.mfe_r if empf else mfe_r,
         "trailing_aktiv": bool(empf and empf.aktiv),
         "stop_empfohlen": empf.stop_empfohlen if empf and empf.aktiv else None,
         "gesicherte_r": empf.gesicherte_r if empf and empf.aktiv else None,
         "trailing_begruendung": empf.begruendung if empf else None,
         "umgeworfen_durch": umgeworfen_durch,
         # IN PROZENT, NICHT NUR IN R. Nutzer am 12.08. zu den Kosten: "damit
         # fange ich nichts an" - dasselbe gilt hier. R ist eine interne
         # Einheit; Prozent versteht jeder und ist waehrungsfrei.
         "stand_prozent": ((einstieg - kurs_aktuell) if ist_short
                           else (kurs_aktuell - einstieg)) / einstieg
                          if kurs_aktuell else None,
         "mfe_prozent": (risiko * float(mfe_r) / einstieg
                         if mfe_r is not None else None)}

    # 1a. NAEHERT SICH DER KURS DEM ZIEL?
    e["ziel"] = ziel
    e["weg_zum_ziel"] = None
    e["ziel_in_reichweite"] = False
    if ziel and kurs_aktuell and abs(ziel - einstieg) > 1e-12:
        anteil = (kurs_aktuell - einstieg) / (ziel - einstieg)
        e["weg_zum_ziel"] = anteil
        # Nur nach OBEN warnen: ein Anteil ueber 1,0 hiesse, das Ziel ist
        # schon durchlaufen - dann greift die Nachlese, nicht die Warnung.
        e["ziel_in_reichweite"] = bool(ZIEL_NAH_ANTEIL <= anteil < 1.0)

    # 1b. IST DER NACHGEZOGENE STOP SCHON UNTERSCHRITTEN?
    #
    # GEFUNDEN AN DER FERTIGEN MAIL, nicht am Modul. Dort stand "Stop auf
    # 59.100 EUR nachziehen" neben einem Kurs von 58.000 - die Position waere
    # laengst ausgestoppt gewesen. Der Trailing-Stop rechnet aus dem HOECHSTEN
    # erreichten Kurs; faellt der Kurs danach unter die nachgezogene Marke,
    # ist sie nicht mehr eine Empfehlung fuer morgen, sondern ein Ereignis von
    # gestern.
    #
    # Die Ausstiegsregel selbst kann das nicht wissen - sie bekommt den
    # aktuellen Kurs gar nicht, sie ist reine Stop-Arithmetik. Die Pruefung
    # gehoert also hierher und nirgendwo sonst.
    e["stop_bereits_unterschritten"] = bool(
        e["stop_empfohlen"] is not None and kurs_aktuell
        and (kurs_aktuell >= e["stop_empfohlen"] if ist_short
             else kurs_aktuell <= e["stop_empfohlen"]))

    # 2. WIDERLEGUNGSPREIS. Bei LONG faellt die These, wenn der Kurs DARUNTER
    # schliesst; bei SHORT darueber.
    e["falsifiziert"] = False
    e["falsifikator_eigenstaendig"] = None
    if (isinstance(umgeworfen_preis_eur, (int, float)) and umgeworfen_preis_eur > 0
            and kurs_aktuell):
        getroffen = (kurs_aktuell >= umgeworfen_preis_eur if ist_short
                     else kurs_aktuell <= umgeworfen_preis_eur)
        e["umgeworfen_preis_eur"] = float(umgeworfen_preis_eur)
        e["falsifiziert"] = bool(getroffen)
        # SAGT ER ETWAS EIGENES? Wo der Stop aus diesem Preis abgeleitet wurde,
        # fallen beide zusammen und die Pruefung ist keine zweite Absicherung.
        e["falsifikator_eigenstaendig"] = (
            abs(float(umgeworfen_preis_eur) - float(stop_original)) > 1e-6)

    # 3. FRIST.
    bis = _als_datum(umgeworfen_bis)
    jetzt = _als_datum(heute) or date.today()
    e["frist"] = bis.isoformat() if bis else None
    e["frist_abgelaufen"] = bool(bis and jetzt > bis)

    # DIE EMPFEHLUNG. Reihenfolge ist Dringlichkeit, nicht Wichtigkeit:
    # eine gefallene These beendet den Handel, ein nachgezogener Stop nicht.
    gruende = []
    if e["stop_bereits_unterschritten"]:
        gruende.append(
            f"Der nachgezogene Stop bei {_de(e['stop_empfohlen'])} EUR liegt "
            f"BEREITS hinter dem aktuellen Kurs ({_de(kurs_aktuell)} EUR). Die "
            f"Position haette danach schliessen muessen - die Marke ist kein "
            f"Vorschlag fuer morgen, sondern ein Ereignis von gestern.")
    if e["falsifiziert"]:
        gruende.append(
            f"Der Kurs hat den Preis erreicht, bei dem das Modell seine eigene "
            f"Begruendung fuer widerlegt erklaert hat "
            f"({_de(e['umgeworfen_preis_eur'])} EUR)."
            + ("" if e["falsifikator_eigenstaendig"] else
               " Er entspricht dem Stop - beide sagen dasselbe."))
    if e["frist_abgelaufen"]:
        gruende.append(
            f"Die Begruendung galt bis {e['frist']} und ist abgelaufen. Das "
            f"heisst nicht, dass die Position falsch ist - es heisst, dass der "
            f"Grund, sie zu halten, nicht mehr belegt ist.")
    if e["ziel_in_reichweite"] and not e["falsifiziert"] and not e["stop_bereits_unterschritten"]:
        gruende.append(
            f"Der Kurs hat {100 * e['weg_zum_ziel']:.0f} % des Weges zum Ziel "
            f"({_de(ziel)}) zurueckgelegt. HINTERLEGEN SIE JETZT EINEN "
            f"VERKAUFSAUFTRAG DORT - dann brauchen Sie keine Mail mehr, und "
            f"ein Ruecklauf ueber Nacht kostet nichts.")
    if e["trailing_aktiv"]:
        gruende.append(e["trailing_begruendung"])
        # BEI GENAU +1 R SICHERT DER NACHGEZOGENE STOP NULL - er steht dann
        # exakt auf dem Einstand. Das IST der Breakeven-Lock, der am 01.08.
        # gemessen und verworfen wurde (kostet 63 % der Gewinner). Die Regel
        # bleibt trotzdem unveraendert: ihre +0,092 R sind MIT diesem Randfall
        # gemessen, und wer ihn herausnimmt, hat die Messung entwertet. Er
        # wird benannt, nicht wegdefiniert.
        if e["gesicherte_r"] is not None and abs(e["gesicherte_r"]) < 0.01:
            gruende.append(
                "Bei genau +1 R steht der nachgezogene Stop auf dem Einstand - "
                "er sichert noch nichts, er begrenzt nur den Verlust auf null. "
                "Erst darueber sichert jedes weitere R mit.")

    grund_empfehlung = (
        SCHLIESSEN if (e["falsifiziert"] or e["stop_bereits_unterschritten"])
        else STOP_NACHZIEHEN if e["trailing_aktiv"] else HALTEN)
    # Die abgelaufene Frist steht MIT in der Ueberschrift. In der ersten
    # Fassung stand sie nur unter den Gruenden - eine Position, deren
    # Begruendung abgelaufen ist, sah dort aus wie jede andere.
    e["empfehlung"] = (f"{grund_empfehlung} · FRIST ABGELAUFEN"
                       if e["frist_abgelaufen"] and grund_empfehlung != SCHLIESSEN
                       else grund_empfehlung)
    e["gruende"] = gruende
    return e


def saetze(e: dict) -> list[str]:
    """Der Ausstiegsblock fuer die E-Mail."""
    if not e:
        return []
    z = [f"Empfehlung   {e['empfehlung']}"]
    if e.get("stand_r") is not None:
        z.append(f"Stand        {e['stand_r']:+.2f} R"
                 + (f", hoechster Buchgewinn {e['mfe_r']:+.2f} R"
                    if e.get("mfe_r") is not None else ""))
    if e.get("stop_empfohlen") is not None:
        z.append(f"Stop         auf {_de(e['stop_empfohlen'])} EUR nachziehen "
                 f"- sichert {e['gesicherte_r']:+.2f} R")
    elif e.get("mfe_r") is not None and not e.get("trailing_aktiv"):
        z.append(f"Stop         unveraendert - der Trailing-Stop loest erst ab "
                 f"+{AUSLOESE_R:.1f} R aus")
    for g in e.get("gruende", []):
        z.append(f"  {g}")
    if e.get("umgeworfen_durch"):
        # NICHT MASCHINELL GEPRUEFT, und das steht dabei.
        z += ["", f"Selbst zu pruefen: {e['umgeworfen_durch']}",
              "  Diese Bedingung hat das Modell genannt; sie enthaelt mehr als "
              "einen Kurs und wird deshalb nicht automatisch ausgewertet."]
    return z


# ---------------------------------------------------------------------------
# DIE SAMMEL-MAIL fuer alle offenen Positionen (13.08.2026).
#
# NUTZEREINWAND: *"bekomme heute schon ein Stop-nachziehen-Mail mit vielen
# Werten, das macht es unuebersichtlich."* Die alte Fassung listet je Position
# eine Zeile dieser Art:
#
#     SOL        SHORT (hebel, seit 2026-08-05)
#         stand bei 10.63 R - Stop von 145.2 auf 132.8 nachziehen, sichert 9.63 R
#
# Vier Zahlen, zwei davon in einer internen Einheit, kein Satz. Vier Aenderungen:
#
#   1. NACH DRINGLICHKEIT GRUPPIERT, nicht nach Buchgewinn sortiert. Der
#      groesste ungesicherte Gewinn ist nicht automatisch der dringendste Fall -
#      eine faellige Position ist es immer.
#   2. PROZENT STATT R. Dieselbe Begruendung wie bei den Kosten am 12.08.
#   3. EIN SATZ JE POSITION statt einer Wertereihe. Was ist zu tun, an welcher
#      Marke, und was steht auf dem Spiel.
#   4. WAS NICHTS BRAUCHT, STEHT IN EINER ZEILE. Wer zwoelf Positionen haelt,
#      soll nicht zwoelf Absaetze lesen, um die zwei zu finden, die zaehlen.
GRUPPEN = ((SCHLIESSEN, "JETZT SCHLIESSEN"),
           (STOP_NACHZIEHEN, "STOP NACHZIEHEN"))


def _prozent(wert: float | None, stellen: int = 1) -> str:
    return "-" if wert is None else f"{100 * wert:+.{stellen}f} %".replace(".", ",")


def _kurs(wert: float | None, waehrung: str = "USD") -> str:
    if wert is None:
        return "-"
    stellen = 2 if abs(wert) < 100 else 0
    return f"{wert:,.{stellen}f}".translate(str.maketrans(",.", ".,")) + f" {waehrung}"


def _in_eur(e: dict, wert: float | None) -> float | None:
    """USD-Zone in EUR. None, wenn der Faktor fehlt - lieber keine Zahl als
    eine in der falschen Waehrung. Genau das war der Fehler der alten
    Hebel-Mail (Umbauplan 12.5)."""
    faktor = e.get("eur_je_usd")
    return None if wert is None or not faktor else float(wert) * float(faktor)


def _absatz(e: dict, waehrung: str = "EUR") -> list[str]:
    # Datum lesbar, nicht technisch: "seit 01.08." statt "seit 2026-08-01".
    seit = str(e.get("seit", ""))
    if len(seit) == 10 and seit[4] == "-":
        seit = f"{seit[8:10]}.{seit[5:7]}."
    # RICHTUNG NUR, WO ES EINE WAHL GIBT. "LONG, spot" ist doppelt gemoppelt -
    # eine Spot-Position kann gar nicht short sein (Nutzerfund 13.08.).
    tier = e.get("tier", "?")
    art = (f"{e.get('richtung','?')} mit Hebel" if tier == "hebel"
           else "Spot" if tier == "spot" else str(tier))
    # WELCHES SIGNAL MELDET HIER? (14.08.2026)
    #
    # NUTZERFRAGE: *"btc hat drei signale produziert 1x verkaufen 1x kaufen und
    # dann 1x verkaufen - diese ueberschneiden sich und ich habe keine Ahnung
    # 'wo und welches der Signale' jetzt z.B. schliessen meldet."*
    #
    # Das Beispiel war fiktiv, der Fall ist es nicht: am 14.08. hatten DBPK und
    # OD7L je FUENF offene Signale, 3QSS vier, MON und OD7C drei. Der Kopf
    # dieses Absatzes nannte bis heute nur Symbol, Art und Datum - drei
    # Absaetze zum selben Symbol unterschieden sich damit im Tagesdatum, sonst
    # in nichts.
    #
    # ZWEI KENNZEICHEN, weil sie verschiedene Fragen beantworten: der EINSTIEG
    # sagt dem Leser, welche seiner Positionen gemeint ist ("die von 61.200"),
    # die NUMMER macht es eindeutig, wenn zwei Signale denselben Einstieg
    # haben. Die Nummer allein waere technisch und unbrauchbar, der Einstieg
    # allein mehrdeutig.
    kennung = []
    if e.get("entry") is not None:
        kennung.append(f"Einstieg {_kurs(_in_eur(e, e['entry']), waehrung)}")
    if e.get("signal_id") is not None:
        kennung.append(f"{'Hebel' if e.get('ist_hebel') else 'Spot'}-Signal "
                       f"#{e['signal_id']}")
    kopf = (f"  {e['symbol']:<6} {art}, seit {seit or '?'}"
            + (" - " + ", ".join(kennung) if kennung else ""))
    z = [kopf]
    if e.get("stop_bereits_unterschritten"):
        z.append(f"      Der nachgezogene Stop bei {_kurs(_in_eur(e, e['stop_empfohlen']), waehrung)} "
                 f"haette greifen muessen - der Kurs steht bei "
                 f"{_kurs(_in_eur(e, e.get('kurs_usd')), waehrung)}.")
    if e.get("falsifiziert"):
        z.append(f"      Der Kurs hat die Marke erreicht, bei der das Modell seine "
                 f"eigene Begruendung fuer widerlegt erklaerte "
                 f"({_kurs(_in_eur(e, e.get('umgeworfen_preis_eur')), waehrung)}).")
    if e.get("ziel_in_reichweite"):
        z.append(f"      {100 * e['weg_zum_ziel']:.0f} % des Weges zum Ziel "
                 f"({_kurs(_in_eur(e, e.get('ziel')), waehrung)}) sind "
                 f"zurueckgelegt - Verkaufsauftrag dort hinterlegen.")
    if e.get("stop_empfohlen") is not None and not e.get("stop_bereits_unterschritten"):
        z.append(f"      Stop auf {_kurs(_in_eur(e, e['stop_empfohlen']), waehrung)} nachziehen.")
    if e.get("frist_abgelaufen"):
        _f = str(e.get("frist") or "")
        if len(_f) == 10 and _f[4] == "-":
            _f = f"{_f[8:10]}.{_f[5:7]}.{_f[:4]}"
        z.append(f"      Die Begruendung galt bis {_f} und ist abgelaufen.")
    if e.get("stand_prozent") is not None:
        hoch = e.get("mfe_prozent")
        z.append(f"      Stand {_prozent(e['stand_prozent'])}"
                 + (f", hoechster Buchgewinn {_prozent(hoch)}"
                    if hoch is not None else ""))
    return z


def sammel_mail(alle: list, geprueft: int | None = None,
                waehrung: str = "EUR",
                ziel_erreicht: list | None = None) -> tuple[str, str] | None:
    """(Betreff, Text) - oder None, wenn nichts zu melden ist.

    ZWEI WELTEN, UND SIE WERDEN GETRENNT. Nutzerfund 13.08.: *"Diese Aktionen
    sind teilweise fiktiv."* Genau so ist es. `signals` enthaelt EMPFEHLUNGEN,
    nicht Positionen - von 45 Signal-Symbolen lagen 28 gar nicht im Bestand.
    Fuer die waere "SCHLIESSEN" eine Anweisung fuer etwas, das es nicht gibt.

        IHR BESTAND       `holdings` / `hebel_positions` - hier ist die
                          Empfehlung eine Handlung
        SIGNALVERFOLGUNG  offene Signale ohne Bestand - hier ist sie ein
                          MESSPUNKT. Die These ist gefallen, gekauft wurde nie

    UND NUR DER BESTAND LOEST EINE MAIL AUS. Wer fuer eine nie eroeffnete
    Position geweckt wird, hoert nach der dritten Mail auf hinzusehen.

    WAS "SCHLIESSEN" NICHT HEISST - Nutzerfrage 13.08.: *"Wenn da steht jetzt
    schliessen, ist das Gewinnzone erreicht?"* NEIN, im Gegenteil. Wer sein
    Ziel erreicht, wird vom Backward-Tracking als `take_profit` aufgeloest und
    ist dann nicht mehr offen - er taucht hier NIE auf. Diese Mail meldet
    ausschliesslich: Gewinn geht zurueck, These gefallen, oder Frist vorbei.
    Der Satz steht auch im Kopf der Mail."""
    # NICHT AN `alle` ABBRECHEN. Die erste Fassung stieg hier aus, wenn es
    # keine offene Position gab - und schnitt damit genau den Fall ab, fuer
    # den diese Mail gebaut wurde: ein erreichtes Ziel OHNE weitere offene
    # Position haette keine Nachricht ergeben. Die einzige Nachricht mit Geld
    # darin waere die einzige gewesen, die nicht verschickt wird.
    alle = list(alle or [])
    bestand = [e for e in alle if e.get("ist_bestand")]
    verfolgung = [e for e in alle if not e.get("ist_bestand")]

    def gruppiere(liste):
        nach = {k: [e for e in liste
                    if e["empfehlung"].split(" · ")[0] == k] for k, _ in GRUPPEN}
        rest = [e for e in liste
                if e["empfehlung"].split(" · ")[0] not in dict(GRUPPEN)]
        return nach, rest

    nach, rest = gruppiere(bestand)
    faellig = len(nach[SCHLIESSEN])
    _nah_vorab = {id(e) for e in bestand if e.get("ziel_in_reichweite")
                  and e["empfehlung"].split(" · ")[0] != SCHLIESSEN}
    nachziehen = len([e for e in nach[STOP_NACHZIEHEN] if id(e) not in _nah_vorab])
    abgelaufen = [e for e in rest if e.get("frist_abgelaufen")]
    ziel_erreicht = list(ziel_erreicht or [])
    if (not faellig and not nachziehen and not abgelaufen and not ziel_erreicht
            and not any(e.get("ziel_in_reichweite") for e in bestand)):
        return None

    teile = []
    # DAS ERREICHTE ZIEL ZUERST - es ist die einzige gute Nachricht hier und
    # die einzige, bei der Geld auf dem Tisch liegt.
    if ziel_erreicht:
        teile.append(f"{len(ziel_erreicht)} Ziel erreicht")
    if _nah_vorab:
        teile.append(f"{len(_nah_vorab)} nah am Ziel")
    if faellig:
        teile.append(f"{faellig} faellig")
    if nachziehen:
        teile.append(f"{nachziehen} Stop nachziehen")
    if abgelaufen and not teile:
        teile.append(f"{len(abgelaufen)} Begruendung abgelaufen")
    betreff = "TradingInfoTool: " + ", ".join(teile)

    zeilen = [
        "Diese Mail meldet NUR Handlungsbedarf bei bestehenden Positionen.",
        "Ein erreichtes Kursziel steht GANZ OBEN - dort liegt Geld auf dem "
        "Tisch, das Sie selbst holen muessen.",
        "Alles hier ist eine EMPFEHLUNG; es wird nichts ausgefuehrt.",
        ""]
    if ziel_erreicht:
        zeilen += [f"ZIEL ERREICHT - VERKAUFEN ({len(ziel_erreicht)})",
                   "  Diese Positionen haben ihr Kursziel erreicht und liegen "
                   "noch im Depot. Das System verbucht sie als erledigt - "
                   "verkauft wird dadurch nichts.", ""]
        for e in ziel_erreicht:
            crv = e.get("crv")
            am = str(e.get("am", ""))
            if len(am) == 10 and am[4] == "-":
                am = f"{am[8:10]}.{am[5:7]}."
            art = ("mit Hebel" if e.get("tier") == "hebel" else "Spot")
            zeilen += [f"  {e['symbol']:<6} {art}, Ziel erreicht am {am or '?'}"
                       + (f" - das {_de(crv, 1)}-fache des eingesetzten Risikos"
                          if crv else "")]
        zeilen.append("")
    # JEDE POSITION GENAU EINMAL. Die Naehe zum Ziel ist die handlungsnaehere
    # Aussage - dort steht ein Auftrag an, nicht nur eine Marke. Der
    # Stop-Hinweis laeuft im selben Absatz mit, siehe `_absatz()`.
    nah = [e for e in bestand if e.get("ziel_in_reichweite")
           and e["empfehlung"].split(" · ")[0] != SCHLIESSEN]
    _nah_ids = {id(e) for e in nah}
    if nah:
        zeilen += [f"ZIEL IN REICHWEITE ({len(nah)})",
                   "  Hinterlegen Sie jetzt einen Verkaufsauftrag beim "
                   "Zielkurs. Danach brauchen Sie diese Mail nicht mehr - und "
                   "ein Ruecklauf ueber Nacht kostet nichts.", ""]
        for e in nah:
            zeilen += _absatz(e, waehrung) + [""]
    for schluessel, titel in GRUPPEN:
        gruppe = [e for e in nach[schluessel] if id(e) not in _nah_ids]
        if not gruppe:
            continue
        zeilen += [f"{titel} ({len(gruppe)})", ""]
        for e in gruppe:
            zeilen += _absatz(e, waehrung) + [""]
    if abgelaufen:
        zeilen += [f"BEGRUENDUNG ABGELAUFEN ({len(abgelaufen)})",
                   "  Kein Handlungszwang - aber der Grund, diese Positionen zu "
                   "halten, ist nicht mehr belegt.", ""]
        for e in abgelaufen:
            zeilen += _absatz(e, waehrung) + [""]
    ruhig = [e for e in rest if not e.get("frist_abgelaufen")
             and not e.get("ziel_in_reichweite")]
    if ruhig:
        zeilen += [f"OHNE HANDLUNGSBEDARF ({len(ruhig)})",
                   "  " + ", ".join(f"{e['symbol']} {_prozent(e.get('stand_prozent'))}"
                                    for e in ruhig), ""]

    # DIE SIGNALVERFOLGUNG ZULETZT UND ALS SOLCHE BENANNT.
    v_nach, v_rest = gruppiere(verfolgung)
    v_faellig = v_nach[SCHLIESSEN]
    if v_faellig:
        zeilen += [f"SIGNALVERFOLGUNG - KEIN BESTAND ({len(v_faellig)})",
                   "  Hier ist nichts zu tun: diese Positionen wurden nie "
                   "eroeffnet. Die These ist gefallen, und das wird gezaehlt, "
                   "damit die Trefferquote stimmt.",
                   "  " + ", ".join(e["symbol"] for e in v_faellig), ""]

    zeilen += ["-" * 68,
               "Warum der Ausstieg zaehlt: die Haelfte aller Signale stand "
               "unterwegs einmal im Gewinn - nur 17,6 % endeten dort. "
               "(86 real bewertete Signale, 04.08.)",
               "Taeglich um 07:15, nach dem Backward-Tracking um 6:00.",
               "Abschalten: config.yaml risiko.ausstieg_trailing_ausloese_r auf 0."]
    return betreff, chr(10).join(zeilen)
