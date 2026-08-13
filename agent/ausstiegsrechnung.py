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
         "umgeworfen_durch": umgeworfen_durch}

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

    grund_empfehlung = (SCHLIESSEN if e["falsifiziert"] else
                        STOP_NACHZIEHEN if e["trailing_aktiv"] else HALTEN)
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
