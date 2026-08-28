# -*- coding: utf-8 -*-
"""Die Lage-Bewertung der Akkumulation - Entscheidung B+C (28.08.2026).

⚠️ DIESES MODUL SPERRT NICHTS. Es rechnet den Abstand zum eigenen 200-Schnitt,
ordnet ihn einem gemessenen Band zu und gibt eine Erwartung zurueck. Kein
Signal wird verhindert. Dieselbe Bauform wie `agent/vorfilter.py`, und aus
demselben Grund: der Befund steht nicht auf den Reihen, auf die er hier trifft.

WAS GEMESSEN IST (`messe_akkumulationsmass.py`, 28.08.2026, 505 lueckenlose
Krypto-Reihen ueber neun Jahre). Zielgroesse ist die VERBILLIGUNG - das
Erfolgsmass, das `handelsauftrag.py` der Akkumulation ausdruecklich gibt:

    V(t,H) = Mittel(Kurs[t+1 .. t+H]) / Kurs(t) - 1

Gewertet wird der Perzentilrang von V INNERHALB der eigenen Reihe. Die
Basisrate ist damit exakt 0,500 per Konstruktion - der Drift kann nicht als
Signal durchgehen. Sieben Kontrollen bestanden, darunter Negativkontrolle
(-0,0008 bei Null +-0,0007), Positivkontrolle (+0,4242) und der Log-Test
gegen Jensen (identisch).

⚠️⚠️ UND DIE EINSCHRAENKUNG, DIE DIESES MODUL BESTIMMT: fuer BTC, ETH und SOL
traegt der Befund NICHT.

    505 Reihen   Rang +0,0283   p 0,000
    BTC          Rang -0,0251   p 0,723
    ETH          Rang -0,0308   p 0,810
    SOL          Rang -0,0291   p 0,855

Kein n=3-Rauschen: die Streuung je Symbol ist 0,0397, die Kernwerte liegen
2,39 Standardfehler unter dem Mittel, und von 505 Symbolen sind nur 14,3 %
negativ - alle drei Kernwerte darunter. Nach Gesamtentwicklung gefuenftelt ist
der Vorsprung konstant (+0,024 bis +0,033), es liegt also nicht am Anstieg.

DIE FOLGE, und sie ist unbequem: `spot x akkumulation` ist heute genau auf
BTC/ETH/SOL freigeschaltet. Der Befund hat damit **keinen Anwendungsort, an
dem er gilt** - und deshalb steht hier eine Zahl mit Vorbehalt statt einer
Regel.

    Entscheidung B   der Kern bekommt KEINEN Verbilligungssatz als
                     Begruendung. Er wird akkumuliert, weil der Nutzer ihn
                     fuer ueberlebensfaehig haelt - das ist eine
                     Anlageentscheidung, kein Timing, und sie braucht kein
                     Signalmass.
    Entscheidung C   die Ausschlussseite wird berechnet und GEZEIGT, aber sie
                     sperrt nicht. Fuer den Kern ist sie unbelegt.

⚠️ WAS SICH AM 28.08. AN C GEAENDERT HAT, NACH DER GEGENPRUEFUNG. Die erste
Fassung von C lautete "fuer den Kern nur die Ausschlussseite nutzen" - mit der
Begruendung, sie greife dort am haeufigsten (24,5 % der Tage). Das war ein
Fehlschluss: Haeufigkeit ist kein Beleg. Nachgemessen zeigt das Band ueber
+30 % bei den Kernwerten teils die GEGENRICHTUNG (BTC +0,0112 / ETH +0,0423 /
SOL +0,0605 auf H=90). Eine Bremse darauf zu bauen waere genau die "Bremse
ohne Potentialaussage", an der dieses Projekt schon 79 % seines Trichters
verloren hat.

✔ WAS DIE GEGENPRUEFUNG DAFUER GEKLAERT HAT - offene Frage 2 aus
`Befund_Lage_27_08.md`: die Ausschlussregel war dort NUR "innerhalb tief
gefallener Assets" gemessen. Sie gilt auch ausserhalb:

    > +30 %, NICHT tief gefallen   Rang -0,0924 (H=90) / -0,1450 (H=365)
                                   363 bzw. 329 Reihen

Damit ist sie breiter belegt als zuvor - nur eben nicht fuer die drei Werte,
auf die sie heute traefe.

DIE KENNLINIE IST MONOTON ueber alle neun Baender und auf beiden Horizonten -
das ist der Grund, sie stetig zu fuehren statt als Schalter. Ein Schalter auf
"unter dem Schnitt" feuert an 68,5 % aller Tage und mischt das beste Band
(+0,0960) mit einem der schlechtesten (-0,0651).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Die Werte, die keinen Verbilligungssatz bekommen (Entscheidung B).
#
# ⚠️ DIESE LISTE IST EIN MESSERGEBNIS, KEINE MEINUNG. Sie steht hier und nicht
# in der Konfiguration, weil ihre Aenderung eine MESSUNG voraussetzt: ein Wert
# gehoert hier hinein, wenn sein Rang nachweislich nicht traegt - nicht, wenn
# jemand ihn fuer besonders haelt.
OHNE_BELEG = ("BTC", "ETH", "SOL")

# Die gemessene Kennlinie (H = 90 Tage, 505 Reihen).
#
# ⚠️ H=90 UND NICHT H=365, obwohl der Vorsprung dort groesser ist (+0,0514
# gegen +0,0283). Der laengere Horizont hat bei 3.292 Tagen Achse nur rund
# neun unabhaengige Fenster; H=90 hat 36. Die vorsichtigere Zahl ist die, die
# in eine Mail gehoert.
#
#           (untere Grenze, obere Grenze, Rang, Median-Verbilligung)
BAENDER = (
    (-9.99, -0.40, +0.0960, +0.0606),
    (-0.40, -0.25, +0.0197, +0.0218),
    (-0.25, -0.15, -0.0305, -0.0117),
    (-0.15, -0.075, -0.0605, -0.0381),
    (-0.075, 0.0, -0.0651, -0.0464),
    (0.0, +0.075, -0.0755, -0.0549),
    (+0.075, +0.15, -0.0822, -0.0605),
    (+0.15, +0.30, -0.0895, -0.0633),
    (+0.30, +9.99, -0.1508, -0.1179),
)


def abstand_zum_schnitt(kurse) -> float | None:
    """Kurs gegen den eigenen 200-Tage-Schnitt, als Anteil.

    ⚠️ LIEST NUR VERGANGENHEIT - dieselbe Form wie in der Messung
    (`messe_akkumulation.anteil_der_regel`): das Fenster endet beim aktuellen
    Tag einschliesslich, der Schnitt sind dessen letzte 200 Werte. Wer hier
    einen Tag weiter greift, misst etwas anderes als gemessen wurde."""
    if not kurse:
        return None
    # ⚠️ ZWEI FORMATE, UND DAS WAR EIN ECHTER FEHLER (28.08.2026). Die erste
    # Fassung las `float(k)` - in der Kette stehen dort aber KERZEN mit
    # `.close`, kein Zahlenstrom. Der Aufruf haette einen TypeError geworfen,
    # den das `try/except` an der Naht stillschweigend geschluckt haette:
    # fail-soft ist fail-silent. Gefunden, weil das Format nachgesehen und
    # nicht angenommen wurde.
    werte: list[float] = []
    for k in kurse:
        if k is None:
            continue
        roh = getattr(k, "close", k)
        try:
            wert = float(roh)
        except (TypeError, ValueError):
            continue
        if wert > 0:
            werte.append(wert)
    if len(werte) < 200:
        return None
    schnitt = sum(werte[-200:]) / 200.0
    if schnitt <= 0:
        return None
    return werte[-1] / schnitt - 1.0


def bewerte(symbol: str, kurse) -> dict | None:
    """Die Lage-Bewertung fuer eine Akkumulation. Gibt None, wenn unbekannt.

    ⚠️ `belegt=False` IST NICHT `belegt=None`. Fuer BTC/ETH/SOL ist gemessen,
    dass es NICHT traegt - das ist etwas anderes als "nie geprueft". Ein
    Merkmal, das man kennt, darf nicht aussehen wie eines, das fehlt (dieselbe
    Unterscheidung wie `h = None` gegen `h = False` im Vorfilter)."""
    ab = abstand_zum_schnitt(kurse)
    if ab is None:
        return None
    for unten, oben, rang, hoehe in BAENDER:
        if unten <= ab < oben:
            break
    else:
        return None
    return {
        "abstand": ab,
        "rang": rang,
        "verbilligung": hoehe,
        "belegt": str(symbol or "").upper() not in OHNE_BELEG,
        "band": (unten, oben),
    }


def saetze(symbol: str, kurse) -> list[str]:
    """Die Zeilen fuer die Mail. Leer, wenn nichts zu sagen ist.

    ⚠️ DIE ZAHL STEHT NIE OHNE IHREN VERGLEICH. "+6,1 % Verbilligung" allein
    waere wieder der Drift, den die Rangbildung gerade herausrechnet - die
    Aussage lebt ausschliesslich von "gegenueber einem beliebigen Tag derselben
    Reihe"."""
    b = bewerte(symbol, kurse)
    if b is None:
        return []
    prozent = ("%+.1f" % (100 * b["abstand"])).replace(".", ",")
    z = ["Lage         %s %% zum eigenen 200-Tage-Schnitt" % prozent]

    if not b["belegt"]:
        # ENTSCHEIDUNG B: kein Verbilligungssatz fuer den Kern.
        # KEIN WARNZEICHEN IN DER MAILZEILE: keine einzige Zeile dieses
        # Projekts traegt eines - geprueft ueber vorfilter, wahrscheinlichkeit,
        # drift und ausstiegsrechnung (0 Treffer). Emojis kommen auf der
        # Windows-Konsole als Escape-Folge an; das Wort tut es in jedem
        # Encoding.
        z.append("             ACHTUNG: fuer %s ist die Verbilligung NICHT belegt "
                 "(Rang -0,03 bei p > 0,7) - dieser Wert wird gehalten, weil "
                 "er ueberleben soll, nicht weil der Zeitpunkt guenstig ist"
                 % str(symbol).upper())
        return z

    erwartung = ("%+.1f" % (100 * b["verbilligung"])).replace(".", ",")
    if b["verbilligung"] >= 0:
        z.append("             Erwartung %s %% guenstiger als ein beliebiger "
                 "Tag dieser Reihe (Median ueber 90 Tage, 505 Reihen)"
                 % erwartung)
    else:
        # ENTSCHEIDUNG C: die Ausschlussseite wird GEZEIGT, nicht erzwungen.
        z.append("             ACHTUNG: Erwartung %s %% - von dieser Lage aus war der "
                 "Kauf TEURER als ein beliebiger Tag dieser Reihe "
                 "(Median ueber 90 Tage, 505 Reihen)" % erwartung)
    return z
