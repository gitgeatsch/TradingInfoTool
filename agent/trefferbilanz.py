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


def breakeven(kosten_r: float = 0.0, crv: float = CRV) -> float:
    """Welche Trefferquote traegt sich gerade noch?

        EW = p * CRV - (1 - p) * 1 - Kosten = 0
        =>  p = (1 + Kosten) / (1 + CRV)

    Ohne Kosten und bei CRV 2,0 sind das 33,3 % - genau die Zahl, gegen die
    dieses Projekt seit Wochen rechnet. MIT den gemessenen Krypto-Kosten von
    0,230 R sind es 41,0 %, und die Basisrate liegt bei 34,0 %.

    Diese Rechnung reproduziert also den bekannten Befund, statt ihn zu
    behaupten: brutto knapp positiv, netto negativ - die Kosten kippen das
    Vorzeichen."""
    return (1.0 + max(0.0, float(kosten_r))) / (1.0 + float(crv))


def geschrumpft(treffer: int, faelle: int,
                basisrate: float = BASISRATE,
                gewicht: int = GEWICHT_MITTELWERT) -> float:
    """Schrumpfung zum Mittelwert. Bei `faelle = 0` exakt die Basisrate."""
    n = max(0, int(faelle))
    k = min(max(0, int(treffer)), n)
    return (k + gewicht * basisrate) / (n + gewicht)


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
        band(unabhaengige_faktoren, (2, 3, 4)),
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

    aus: dict[tuple, dict] = {}
    hat_faktoren = "unabhaengige_faktoren" in spalten
    for row in conn.execute(
            "SELECT outcome_status"
            + (", unabhaengige_faktoren" if hat_faktoren else "")
            + f" FROM signals WHERE {bedingung}", werte):
        schluessel = merkmale(
            unabhaengige_faktoren=row[1] if hat_faktoren else None)
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


def bewerte(bilanz: dict, schluessel: tuple, kosten_r: float = 0.0) -> dict:
    """Die Zahlen fuer EINEN Fall - und der Satz, der daraus wird."""
    e = bilanz.get(schluessel) or {"treffer": 0, "faelle": 0, "abgelaufen": 0}
    p = geschrumpft(e["treffer"], e["faelle"])
    schwelle = breakeven(kosten_r)
    gesamt = e["faelle"] + e.get("abgelaufen", 0)
    return {"basisrate": BASISRATE, "faelle": e["faelle"],
            "treffer": e["treffer"], "wahrscheinlichkeit": p,
            "breakeven": schwelle, "traegt": p > schwelle,
            "belastbar": e["faelle"] >= GEWICHT_MITTELWERT,
            "abgelaufen": e.get("abgelaufen", 0),
            # Auf WIEVIEL der Faelle steht die Quote ueberhaupt? Ein hoher
            # Anteil abgelaufener Faelle heisst, dass die Quote nur ein
            # Bruchstueck beschreibt (Arbeitsstand 7.23: 15-21 %).
            "anteil_entschieden": (e["faelle"] / gesamt) if gesamt else None}


def satz(bewertung: dict) -> list[str]:
    """Der Entscheider-Block fuer die E-Mail - drei Zahlen und ein Urteil.

    BEI WENIGEN FAELLEN SAGT ER DAS AUCH. Ein "41 %" auf vierzehn Faellen waere
    eine erfundene Genauigkeit; die ehrliche Aussage ist dann, dass wir es noch
    nicht wissen."""
    b = bewertung
    zeilen = [
        f"Grundwahrscheinlichkeit dieser Geometrie: {100 * b['basisrate']:.0f} %",
        f"Fuer die Kosten zu schlagen sind:         {100 * b['breakeven']:.0f} %",
    ]
    if b["belastbar"]:
        zeilen.insert(1, f"Diese Konstellation traf bisher in:        "
                         f"{100 * b['wahrscheinlichkeit']:.0f} %  (n = {b['faelle']})")
        zeilen.append("--> Erwartungswert positiv." if b["traegt"]
                      else "--> Erwartungswert negativ - der Trade traegt sich "
                           "rechnerisch nicht.")
    else:
        zeilen.insert(1, f"Diese Konstellation: erst {b['faelle']} Faelle - "
                         f"keine belastbare Abweichung von der Basisrate")
        zeilen.append("--> Noch keine eigene Messung. Es gilt die Basisrate.")
    return zeilen
