# -*- coding: utf-8 -*-
"""Die Trefferbilanz - der Entscheider (Paket 8, 12.08.2026).

WAS HIER ENTSTEHT: die Zahl fuer die E-Mail. Nicht aus dem Modell, sondern aus
der Bilanz seiner eigenen Urteile.

    Das LLM urteilt.        -> Text und Aktion. Nie eine Prozentzahl.
    Das System zaehlt mit.  -> "Wenn dieses System KAUFEN sagte bei vier
                               unabhaengigen Faktoren, traf es in X % (n = Y)."

DER NUTZERVORSCHLAG, der das Verfahren bestimmt: *"ich schlage vor, dass wir
hier mit einem Mittelwert anfangen und dann pro Signal uns anpassen."* Das ist
exakt die Schrumpfung zum Mittelwert (empirisches Bayes):

              k + m * p0
       p_hut = ----------
                n + m

    p0  Basisrate 34,0 %, gemessen ueber 19.891 Anker
    k   Treffer dieser Konstellation
    n   Faelle dieser Konstellation
    m   Gewicht des Mittelwerts, Startwert 50

    n = 0    -> 34,0 %, der Mittelwert unveraendert
    n = 20   -> vorsichtig angepasst
    n = 300  -> die Messung traegt selbst

ES GIBT KEINE SCHWELLE, DIE JEMAND SETZT. Die Kalibrierung laeuft mit jedem
neuen Ausgang mit und ist von Anfang an ehrlich: bei wenigen Faellen sagt sie
schlicht die Basisrate.

DER FILTER IST KEINE ZAHL, SONDERN EIN VERGLEICH: `p_hut` gegen den
Kosten-Breakeven. Liegt die Konstellation darunter, traegt sich der Trade
rechnerisch nicht.

WO ER SITZT: NACH dem LLM, und das Modell sieht ihn NICHT.

    Anker         eine Zahl aus dem eigenen System ist der staerkste denkbare
                  Anker (Index 0,45, Experten-Anker am staerksten)
    Zirkularitaet die Tabelle entsteht AUS den Urteilen des Modells; sie ihm
                  zurueckzugeben macht aus einer Messung eine Rueckkopplung
    Sichtbarkeit  ein VORfilter ist unsichtbar - was er wegschneidet, sieht
                  niemand. Ein NACHfilter bleibt rueckwirkend pruefbar

WAS DIESE DATEI NICHT TUT: sie verwirft nichts. Sie rechnet und beschreibt. Wer
sie anschliesst, entscheidet, was ein Unterschreiten ausloest - ein Waechter,
der selbst verwirft, macht seine eigene Wirkung unsichtbar.
"""
from __future__ import annotations

import sqlite3

# Die Basisrate, gemessen ueber 19.891 Anker (Arbeitsstand 7.25). Theoretisch
# sind es 33,3 % fuer 3 ATR Ziel gegen 1,5 ATR Stop auf einem driftfreien Pfad;
# gemessen 34,0 %. Die Naehe beider Zahlen IST der Befund - der Markt verhaelt
# sich auf dieser Aufloesung wie ein Martingal.
BASISRATE = 0.340

# Gewicht des Mittelwerts. 50 heisst: erst bei rund 50 eigenen Faellen wiegt die
# eigene Messung so schwer wie die Basisrate. Bewusst traege - eine Tabelle, die
# nach fuenf Faellen ausschlaegt, misst Rauschen.
GEWICHT_MITTELWERT = 50

CRV = 2.0                       # 3,0 ATR Ziel / 1,5 ATR Stop, = risiko.crv_minimum

# Ausgaenge: IMPORTIERT, nicht abgeschrieben.
#
# Die erste Fassung hatte sie von Hand hingeschrieben - und zwei von vier
# falsch: "stop_erreicht" statt "stop_loss_erreicht", "zeit_abgelaufen" statt
# "abgelaufen_unentschieden". `zaehle()` haette stillschweigend NICHTS
# gefunden, und das haette wie "noch keine Daten" ausgesehen statt wie ein
# Fehler. Genau die Sorte U-Boot, die dieses Projekt mehrfach bezahlt hat.
from agent.krypto.backward_tracking import (          # noqa: E402
    OUTCOME_ABGELAUFEN, OUTCOME_TAKE_PROFIT, _RESOLVED_OUTCOMES)

TREFFER = (OUTCOME_TAKE_PROFIT,)
AUFGELOEST = _RESOLVED_OUTCOMES

# ABGELAUFEN ZAEHLT NICHT ALS AUFGELOEST - und das ist ein OFFENER PUNKT, kein
# Detail. `_RESOLVED_OUTCOMES` kennt nur Ziel, Stop und Liquidation; ein Signal,
# das die Zeitschranke erreicht, faellt heraus.
#
# Arbeitsstand 7.23 haelt fest, dass "keines = 0 R" eine SETZUNG ist, keine
# Messung - und dass es 15 bis 21 % aller Faelle betrifft. Wer sie weglaesst,
# hebt die Trefferquote; wer sie als Fehlschlag zaehlt, senkt sie. Beides waere
# eine Entscheidung, die diese Datei nicht treffen darf.
#
# DESHALB WERDEN SIE GEZAEHLT UND AUSGEWIESEN, nicht verrechnet: `bewerte()`
# meldet ihren Anteil, damit sichtbar ist, auf welchem Teil der Faelle die Quote
# ueberhaupt steht.


# NICHT ABSCHREIBEN - IMPORTIEREN. Diese Saetze standen hier zuerst als eigene
# Zahlen, und eine davon war falsch: Spread 0,0015 statt 0,0025 in der Quelle.
# Eine abgeschriebene Konstante ist eine Kopie, die stillschweigend veraltet -
# genau der Fall, den die Regel "immer an der Quelle pruefen" meint. Die
# autoritativen Saetze stehen seit 07.08. in `backward_tracking.py`, dort werden
# auch die Backtests damit gerechnet; jede Abweichung hier hiesse, dass Signal
# und Nachmessung mit verschiedenen Gebuehren rechnen.
from agent.krypto.backward_tracking import (          # noqa: E402
    _KOSTEN_KRYPTO_JE_SEITE, _KOSTEN_BOERSE_FIX_EUR,
    _KOSTEN_BOERSE_SPREAD_JE_SEITE)

KOSTEN_JE_SEITE = {"krypto": _KOSTEN_KRYPTO_JE_SEITE,
                   "boerse_fix_eur": _KOSTEN_BOERSE_FIX_EUR,
                   "boerse_spread": _KOSTEN_BOERSE_SPREAD_JE_SEITE}


def basisrate_fuer(crv: float = CRV, basisrate: float = BASISRATE) -> float:
    """Die Grundwahrscheinlichkeit fuer EINE Geometrie - nicht fuer alle.

    NOTWENDIG SEIT DEM STRUKTUR-ZIEL (12.08.). Solange das Ziel mechanisch bei
    CRV 2,0 lag, war die Basisrate eine Konstante. Haengt das Ziel am naechsten
    Widerstand, ist sie es nicht mehr - und ein Text, der in Abschnitt 2
    "CRV 1,4" ausweist und in Abschnitt 4 gegen die 34 % von CRV 2,0 vergleicht,
    widerspricht sich selbst. Genau daran ist die erste Fassung der Mail
    aufgefallen.

    Theoretisch gilt 1/(1+CRV). Gemessen sind es 34,0 % statt der theoretischen
    33,3 % - ein Faktor von 1,02 ueber 19.891 Anker. Dieser Faktor wird auf
    andere Geometrien uebertragen; das ist eine Annahme, aber eine kleine und
    eine sichtbare. Die Alternative waere, fuer jede CRV neu zu messen."""
    theorie_hier = 1.0 / (1.0 + max(0.0, float(crv)))
    theorie_gemessen = 1.0 / (1.0 + CRV)
    return theorie_hier * (basisrate / theorie_gemessen)


def breakeven(kosten_r: float = 0.0, crv: float = CRV) -> float:
    """Der Trefferanteil, ab dem sich der Handel nach Gebuehren traegt."""
    return (1.0 + max(0.0, kosten_r)) / (1.0 + max(0.0, float(crv)))


def kosten_r_aus_stop(einstieg: float, stop: float, klasse: str = "krypto",
                      position_eur: float | None = None) -> float | None:
    """Die Kosten in R fuer DIESES Signal - aus seinem eigenen Stopabstand.

    DER LIVE-LAUF VOM 12.08. HAT GEZEIGT, WARUM DAS NOETIG IST. Das Modell
    waehlte fuer BTC einen Stop von 1.000 EUR auf 55.500 - das sind 1,80 % und
    nur 0,60 ATR. Die Folge:

        Stopabstand          stop_rel   Kosten in R   Breakeven
        1.000 EUR (Modell)      1,80 %       1,67 R      88,8 %
        2.516 EUR (1,5 ATR)     4,53 %       0,66 R      55,4 %
        7.000 EUR              12,61 %       0,24 R      41,3 %

    Bei 1.000 EUR verschlingen die Gebuehren MEHR ALS DIE GANZE CHANCE - der
    Trade ist rechnerisch unmoeglich, bevor irgendeine Marktmeinung ins Spiel
    kommt. Und der Stopabstand ist die einzige Groesse, die das entscheidet.

    EINE KLASSENKONSTANTE WAERE HIER FALSCH. Die dokumentierten -0,230 R fuer
    Krypto gelten fuer einen Stop um 13 %; auf 1,8 % sind es 1,67 R. Wer den
    Klassenwert nimmt, rechnet fuer dieses Signal um das Siebenfache zu
    guenstig.

    ANDERS ALS DIE TREFFERQUOTE IST DAS KEIN SCHAETZWERT: die Gebuehren stehen
    fest, der Stopabstand steht im Signal. Diese Zahl ist gerechnet, nicht
    kalibriert."""
    if not einstieg or not stop or einstieg <= 0 or stop >= einstieg:
        return None
    stop_rel = (einstieg - stop) / einstieg
    if klasse == "krypto":
        kosten_rel = 2.0 * KOSTEN_JE_SEITE["krypto"]
    else:
        # Boerse: Fixgebuehr je Seite plus Spread. Die Fixgebuehr macht die
        # Kosten positionsgroessen-ABHAENGIG - sie kuerzt sich nicht heraus.
        groesse = float(position_eur) if position_eur else 500.0
        kosten_rel = (2.0 * KOSTEN_JE_SEITE["boerse_fix_eur"] / groesse
                      + 2.0 * KOSTEN_JE_SEITE["boerse_spread"])
    return kosten_rel / stop_rel


def geschrumpft(treffer: int, faelle: int,
                basisrate: float = BASISRATE,
                gewicht: int = GEWICHT_MITTELWERT) -> float:
    """Schrumpfung zum Mittelwert. Bei `faelle = 0` exakt die Basisrate."""
    n = max(0, int(faelle))
    k = min(max(0, int(treffer)), n)
    return (k + gewicht * basisrate) / (n + gewicht)


def _prozent(wert):
    """Perzentil 0..1 auf die 0..100-Skala, die `merkmale()` erwartet.

    `faktenblock.werte_aus_reihe()` liefert einen ANTEIL (0,74), die Grenzen in
    `merkmale()` sind PROZENTE (25, 50, 75). Ohne diese Zeile faenden alle
    Werte im untersten Band - und die Tabelle saehe gefuellt aus, waehrend sie
    nur eine Spalte breit waere."""
    return None if wert is None else float(wert) * 100.0


def _band_grob(wert):
    """Anteil in drei Baender: unten / mitte / oben. Als Text, weil dieser
    Platz im Schluessel bisher `gleichlauf` trug und dort Etiketten standen -
    eine Zahl daneben waere beim Lesen einer alten Tabelle nicht zu
    unterscheiden."""
    if wert is None:
        return None
    w = float(wert)
    return "vol_hoch" if w >= 0.75 else ("vol_tief" if w < 0.25 else "vol_mitte")


def merkmale(*, unabhaengige_faktoren=None, vola_perzentil=None,
             spanne_perzentil=None, gleichlauf=None) -> tuple:
    """Der Schluessel, unter dem gezaehlt wird.

    BEWUSST GROB. Jedes Merkmal wird in wenige Baender gelegt, denn eine
    Tabelle mit tausend Zellen hat in jeder Zelle drei Faelle - und drei Faelle
    tragen keine Quote. Lieber vier Baender mit je hundert Faellen.

    NUR WAS ZUM SIGNALZEITPUNKT FESTSTAND. Kein Ausgang, keine spaetere
    Erkenntnis - sonst waere die Tabelle ein Blick in die Zukunft und jede
    Quote daraus wertlos.

    `None` bleibt `None` und wird zu einem eigenen Band. Fehlende Angaben
    stillschweigend in ein Nachbarband zu schieben hiesse, Faelle zu zaehlen,
    die dort nicht hingehoeren."""
    def band(wert, grenzen):
        if wert is None:
            return None
        for i, g in enumerate(grenzen):
            if float(wert) < g:
                return i
        return len(grenzen)

    return (
        # 0-1, 2, 3, 4+ - die Praxisliteratur nennt drei bis vier unabhaengige
        # Faktoren als Bereich fuer einen tragfaehigen Aufbau.
        #
        # DIE FAKTORZAHL IST HIER RAUS (15.1, 13.08.) - der Parameter bleibt,
        # damit Aufrufer sich nicht aendern muessen, aber er geht NICHT in den
        # Schluessel ein. Sie wird weiter auf der Signalzeile mitgeschrieben.
        #
        # DREI GRUENDE, in der Reihenfolge ihres Gewichts:
        #
        # 1. SIE WIEDERHOLT DIE ENTSCHEIDUNG. Ueber 20 echte Urteile nimmt sie
        #    nur zwei Werte an (2 und 3); Faktorzahl 3 bedeutete in 82 % einen
        #    Einstieg, Faktorzahl 2 in 0 %. Ein Merkmal, das die Ausgabe des
        #    Primaermodells wiederholt, trennt keine Marktlagen, sondern
        #    Entscheidungen, die schon gefallen sind.
        # 2. SIE HALBIERT JEDE ZELLE. Gemessen an 42 echten Symbolen belegen
        #    die drei Familien 17 Zellen. Ein binaeres viertes Merkmal macht
        #    daraus bis zu 34 - jede Zelle fuellt sich halb so schnell, und
        #    `belastbar` verlangt 50 Faelle.
        # 3. DER PLAN WOLLTE SIE DETERMINISTISCH AUS DEN FAMILIEN RECHNEN
        #    (Kap. 15.1). Seit die Familien SELBST die anderen drei Plaetze
        #    sind, waere das eine vierte Achse, die von den ersten dreien
        #    vollstaendig bestimmt ist - mehr Zellen, keine Information.
        #
        # Ob sie ZUSAETZLICH zu den Familien etwas traegt, ist jetzt messbar,
        # weil beides auf der Signalzeile steht. Vorher war die Frage nicht
        # einmal stellbar.
        band(vola_perzentil, (25, 50, 75)),
        band(spanne_perzentil, (25, 50, 75)),
        gleichlauf,
    )


def zaehle(conn: sqlite3.Connection, quelle_kette: str | None = "rollen") -> dict:
    """Treffer und Faelle je Konstellation, aus AUFGELOESTEN Signalen.

    Nur was einen Ausgang hat. Ein offenes Signal traegt keine Information
    ueber seinen Ausgang - es mitzuzaehlen hiesse, Unentschiedenes als
    Misserfolg zu buchen.

    `quelle_kette` trennt alte und neue Kette. Sie in einen Topf zu werfen waere
    der klassische Fehler: die alte Kette hatte andere Fakten, andere Prompts
    und ein anderes Aktionsvokabular - ihre Quote sagt nichts ueber diese."""
    spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    if "outcome_status" not in spalten:
        return {}
    stati = list(AUFGELOEST) + [OUTCOME_ABGELAUFEN]
    bedingung = "outcome_status IN ({})".format(",".join("?" for _ in stati))
    werte = list(stati)
    if quelle_kette and "quelle_kette" in spalten:
        bedingung += " AND quelle_kette = ?"
        werte.append(quelle_kette)

    # DIE DREI GEMESSENEN FAMILIEN FUELLEN DIE UEBRIGEN PLAETZE (13.08.).
    #
    # Bis heute fuellte diese Funktion EINEN der vier Plaetze - die Faktorzahl,
    # und von der ist gemessen, dass sie die Entscheidung nur wiederholt. Die
    # drei Familien rechnet `faktenblock.werte_aus_reihe()` ohnehin je Asset zum
    # Signalzeitpunkt; sie standen bisher nur im Mailtext und waren danach weg.
    #
    # `schwankung` -> `vola`, `momentum` -> `spanne`: die Plaetze des
    # Schluessels heissen aelter als die Familien. Umbenennen wuerde jeden
    # bestehenden Schluessel ungueltig machen, also bleibt der Name und die
    # Zuordnung steht hier - beim `momentum_perzentil` ist "spanne" ohnehin
    # naeher an dem, was gemessen wird (Rueckgang vom Hoechststand).
    optional = [s for s in ("unabhaengige_faktoren", "schwankung_perzentil",
                            "momentum_perzentil", "volumen_perzentil")
                if s in spalten]

    aus: dict[tuple, dict] = {}
    for row in conn.execute(
            "SELECT outcome_status"
            + "".join(f", {s}" for s in optional)
            + f" FROM signals WHERE {bedingung}", werte):
        hat = dict(zip(optional, row[1:]))
        schluessel = merkmale(
            vola_perzentil=_prozent(hat.get("schwankung_perzentil")),
            spanne_perzentil=_prozent(hat.get("momentum_perzentil")),
            # VOLUMEN AUF DEN VIERTEN PLATZ, der bisher `gleichlauf` hiess und
            # nie gefuellt wurde. Ein Band statt des Rohwerts, damit der
            # Schluessel grob bleibt - vier Merkmale mit je vier Baendern sind
            # schon 256 Zellen.
            gleichlauf=_band_grob(hat.get("volumen_perzentil")))
        e = aus.setdefault(schluessel,
                           {"treffer": 0, "faelle": 0, "abgelaufen": 0})
        if row[0] == OUTCOME_ABGELAUFEN:
            # Mitgezaehlt, aber NICHT als Fall - siehe die Begruendung oben.
            e["abgelaufen"] += 1
            continue
        e["faelle"] += 1
        if row[0] in TREFFER:
            e["treffer"] += 1
    return aus


def bewerte(bilanz: dict, schluessel: tuple, kosten_r: float = 0.0,
            crv: float = CRV) -> dict:
    """Die Zahlen fuer EINEN Fall - und der Satz, der daraus wird.

    `crv` (12.08.): seit das Ziel am naechsten Widerstand haengt, ist die
    Geometrie nicht mehr fuer jedes Signal dieselbe. Basisrate UND Breakeven
    muessen derselben folgen, sonst widersprechen sich die Abschnitte."""
    e = bilanz.get(schluessel) or {"treffer": 0, "faelle": 0, "abgelaufen": 0}
    basis = basisrate_fuer(crv)
    p = geschrumpft(e["treffer"], e["faelle"], basisrate=basis)
    schwelle = breakeven(kosten_r, crv)
    gesamt = e["faelle"] + e.get("abgelaufen", 0)
    return {"basisrate": basis, "crv": crv, "faelle": e["faelle"],
            "treffer": e["treffer"], "wahrscheinlichkeit": p,
            "breakeven": schwelle, "traegt": p > schwelle,
            "belastbar": e["faelle"] >= GEWICHT_MITTELWERT,
            "abgelaufen": e.get("abgelaufen", 0),
            # Auf WIEVIEL der Faelle steht die Quote ueberhaupt? Ein hoher
            # Anteil abgelaufener Faelle heisst, dass die Quote nur ein
            # Bruchstueck beschreibt (Arbeitsstand 7.23: 15-21 %).
            "anteil_entschieden": (e["faelle"] / gesamt) if gesamt else None}


def _de(wert: float, stellen: int = 1) -> str:
    """Komma statt Punkt - siehe signal_mail.eur()."""
    return f"{wert:,.{stellen}f}".translate(str.maketrans(",.", ".,"))


def satz(bewertung: dict, einstieg=None, stop=None,
         einsatz_eur=None, klasse: str = "krypto") -> list[str]:
    """Der Entscheider-Block fuer die E-Mail.

    IN EURO UND PROZENT, NICHT IN R. Nutzereinwand 12.08.: *"Kosten in 2,77 R -
    damit fange ich nichts an."* Zu Recht: R ist eine interne Einheit. Der
    Nutzer sieht einen Einsatz in Euro und einen Stop in Prozent; in diesen
    Groessen muss die Aussage stehen.

    Die Rechnung dahinter ist dieselbe, nur ausgesprochen:

        Gebuehren 3 % vom Einsatz, Stop 1,3 % entfernt
        -> die Gebuehren sind mehr als doppelt so gross wie das ganze Risiko

    BEI WENIGEN FAELLEN SAGT ER DAS AUCH. Ein "41 %" auf vierzehn Faellen waere
    erfundene Genauigkeit. Die Fallzahl entscheidet aber NUR, ob wir eine
    konstellations-eigene Quote behaupten - nicht, ob wir vergleichen duerfen.
    Die Basisrate steht auf 19.891 Ankern."""
    b = bewertung
    zeilen = []

    # Zuerst das Konkrete, wenn wir es haben: was kostet der Trade, gemessen
    # an dem, was er riskiert.
    if einstieg and stop and einstieg > stop > 0:
        stop_pct = 100.0 * (einstieg - stop) / einstieg
        gebuehr_pct = (100.0 * 2 * KOSTEN_JE_SEITE["krypto"] if klasse == "krypto"
                       else 100.0 * (2 * KOSTEN_JE_SEITE["boerse_fix_eur"]
                                     / float(einsatz_eur or 500.0)
                                     + 2 * KOSTEN_JE_SEITE["boerse_spread"]))
        zeilen.append(f"Ihr Stop liegt {_de(stop_pct)} % unter dem Einstieg - "
                      f"so viel riskieren Sie.")
        zeilen.append(f"Kauf und Verkauf zusammen kosten {_de(gebuehr_pct)} % "
                      f"des Einsatzes"
                      + (f", bei {einsatz_eur:.0f} EUR also rund "
                         f"{gebuehr_pct / 100 * float(einsatz_eur):.0f} EUR."
                         if einsatz_eur else "."))
        verhaeltnis = gebuehr_pct / stop_pct
        zeilen.append(
            f"Die Gebuehren sind damit {_de(verhaeltnis)}-mal so gross wie Ihr "
            f"Risiko." if verhaeltnis >= 1 else
            f"Die Gebuehren fressen {100 * verhaeltnis:.0f} % Ihres Risikos auf.")
        zeilen.append("")

    zeilen.append(f"Von hundert solchen Einstiegen erreichen erfahrungsgemaess "
                  f"{100 * b['basisrate']:.0f} das Ziel vor dem Stop.")
    if b["belastbar"]:
        zeilen.append(f"In genau dieser Konstellation waren es bisher "
                      f"{100 * b['wahrscheinlichkeit']:.0f} von hundert "
                      f"({b['faelle']} Faelle).")
    else:
        zeilen.append(f"Fuer genau diese Konstellation liegen erst "
                      f"{b['faelle']} eigene Faelle vor - zu wenige fuer eine "
                      f"eigene Zahl.")
    zeilen.append(f"Damit sich der Trade nach Gebuehren traegt, muessten es "
                  f"{100 * b['breakeven']:.0f} von hundert sein.")

    if b["breakeven"] >= 1.0:
        zeilen.append("--> DAS KANN NICHT AUFGEHEN. Selbst wenn JEDER Einstieg "
                      "sein Ziel erreichte, blieben die Gebuehren groesser als "
                      "der Gewinn. Ein weiterer Stop wuerde helfen, ein "
                      "engerer macht es schlimmer.")
    elif b["traegt"]:
        zeilen.append("--> Traegt sich."
                      + ("" if b["belastbar"] else " Gemessen an der "
                         "Erfahrungsrate - eine eigene Zahl gibt es noch nicht."))
    else:
        zeilen.append(f"--> Traegt sich NICHT: "
                      f"{100 * b['wahrscheinlichkeit']:.0f} erreichen das Ziel, "
                      f"noetig waeren {100 * b['breakeven']:.0f}."
                      + ("" if b["belastbar"] else " Gemessen an der "
                         "Erfahrungsrate; eine eigene Zahl gibt es noch nicht."))
    if b.get("abgelaufen"):
        zeilen.append(f"    ({b['abgelaufen']} weitere Faelle liefen ohne "
                      f"Entscheidung aus - die Quote steht auf "
                      f"{100 * (b['anteil_entschieden'] or 0):.0f} % der Faelle)")
    return zeilen
