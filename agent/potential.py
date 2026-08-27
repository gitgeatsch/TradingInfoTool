# -*- coding: utf-8 -*-
"""Wieviel ist bei DIESER Handlung zu holen? (27.08.2026)

DIE NUTZERVORGABE, seit dem 25.08. mehrfach wiederholt:

    *"Wenn ein Asset ein bestimmtes POTENTIAL erreicht, soll ein Handelssignal
    kommen. Wir scheitern ausschliesslich am Potential, weil wir nur messen."*

Und die Trennung, auf der er am 27.08. bestanden hat:

    ⚠️ ZWEI EBENEN, DIE SICH NICHT UEBERSCHNEIDEN DUERFEN

    BEWERTUNG        "ist das ein guter Trade"   OHNE Gebuehren
                     -> Vorfilter, LLM, Auswahl, RANGFOLGE
    WIRTSCHAFTLICH   "rechnet es sich fuer mich" MIT Bitpanda-Satz
                     -> die Auskunft an den Nutzer, NIE ein Filter

DIESES MODUL LIEFERT AUSSCHLIESSLICH DIE ERSTE EBENE. Wer eine Zahl mit
Gebuehren braucht, nimmt `wahrscheinlichkeit.rechne()` und liest dort
`abstand_punkte` oder `erwartungswert_r`.

## Die Formel

    Potential (R) = quote * CRV - (1 - quote)

`quote` kommt aus `wahrscheinlichkeit.rechne()` - KEINE zweite Rechnung. Eine
eigene Fassung hier waere die naechste Stelle, an der zwei Zahlen
auseinanderlaufen (derselbe Grund wie bei `handelsauftrag` und `tranchen`).

## ⚠️ WAS DIESE ZAHL HEUTE WIRKLICH IST - und das gehoert in jede Deutung

DER ANTEIL AUS DER GEOMETRIE IST NULL. Die Basisrate ist `1/(1+CRV)`; setzt
man sie ein, ergibt sich exakt null:

    quote = 1/(1+CRV)  ->  Potential = CRV/(1+CRV) - 1/(1+CRV) * CRV = 0

Das ist kein Fehler, sondern der Kernbefund des Projekts: *ein Barrierensystem
auf einem driftfreien Pfad hat brutto Erwartungswert NULL - fuer JEDE
Geometrie* (theoretisch 33,3 %, gemessen 34,0 % ueber 19.891 Anker).

    ⚠️ FOLGE: Das Potential ist die SUMME DER BEITRAEGE, nichts sonst.
    Und von vier registrierten Beitraegen traegt am 27.08. genau EINER
    (Vorfilter H, +4,5 Punkte) - der bis ~19.09. im Schatten laeuft.

    Wer diese Zahl liest, liest heute im Wesentlichen: "trifft H zu?"

Das ist wenig. Es ist aber MEHR als heute, denn heute wird gar nicht
verglichen - und eine Ordnung nach einem gemessenen Merkmal ist besser als
keine. Sobald ein zweiter Beitrag traegt, wird die Zahl von selbst besser.

## Wofuer sie taugt und wofuer nicht

    ✔ Handlungen mit GLEICHEM CRV ordnen (welches Asset zuerst)
    ✘ Handlungen mit VERSCHIEDENEM CRV ordnen - siehe die Warnung unten
    ✘ eine SCHWELLE setzen ("ab 0,3 R handeln") - dafuer ist die Basis zu duenn
    ✘ eine Geldaussage - dafuer ist Ebene 2 zustaendig

⚠⚠ DIE GRENZE, DIE SPOT GEGEN HEBEL AUSSCHLIESST (gefunden beim Testen,
27.08.). H ist bei **CRV = 2,0 fest** gemessen - `messe_marken.py:80`, woertlich
*"CRV = 2,0, es gibt kein Raster"*. Der Beitrag ist ein Zuschlag in
PROZENTPUNKTEN; multipliziert mit dem jeweiligen CRV ergibt das:

    CRV 1,73 (Spot-Median)  + 4,5 Punkte  ->  +0,123 R
    CRV 2,54 (Hebel-Median) + 4,5 Punkte  ->  +0,159 R

DER HEBEL GEWINNT DAMIT REIN RECHNERISCH - nicht, weil er besser waere,
sondern weil seine Geometrie ein hoeheres CRV traegt. Ob H bei CRV 2,54
ueberhaupt +4,5 Punkte bringt, ist NICHT gemessen.

`vergleiche()` gibt Kandidaten mit verschiedenem CRV deshalb UNVERAENDERT
zurueck - ohne Reihenfolge. Wer Spot und Hebel gegeneinander stellen will,
braucht H (oder einen zweiten Beitrag) ueber ein CRV-RASTER gemessen.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class PotentialUnbekannt(RuntimeError):
    """Fehlende Eingabe. Wirft, statt zu raten - wie `wahrscheinlichkeit`."""


@dataclass
class Potential:
    """Das Potential einer Handlung, mit seiner Herkunft."""

    wert_r: float
    quote: float
    basisrate: float
    crv: float
    zuschlag_punkte: float
    instrument: str = "spot"
    strategie: str = "einstieg"
    beitraege: list = field(default_factory=list)

    @property
    def aus_geometrie(self) -> float:
        """Der Anteil, der allein aus CRV und Basisrate kommt.

        ⚠️ IST IMMER NULL, und das ist der Punkt. Die Eigenschaft existiert,
        damit es in der Ausgabe steht statt in einer Fussnote."""
        return self.basisrate * self.crv - (1.0 - self.basisrate)

    @property
    def aus_beitraegen(self) -> float:
        """Alles, was ueber die Geometrie hinausgeht - das eigentliche Mass."""
        return self.wert_r - self.aus_geometrie

    @property
    def traegt(self) -> bool:
        """⚠️ NUR eine Vorzeichenfrage, KEINE Schwelle.

        Eine Schwelle ("ab 0,3 R") waere eine Kalibrierung, fuer die die Basis
        fehlt - ein einziger tragender Beitrag."""
        return self.wert_r > 0.0

    @property
    def crv_extrapoliert(self) -> bool:
        """⚠️ Wurde der Beitrag ausserhalb seines Messpunktes angewandt?

        H IST BEI CRV = 2,0 GEMESSEN, FEST (`messe_marken.py:80`, "CRV = 2,0,
        es gibt kein Raster"). Der Beitrag +4,5 ist ein Zuschlag in
        PROZENTPUNKTEN der Trefferquote - er wird hier mit dem jeweiligen CRV
        multipliziert, und das hat eine systematische Richtung:

            CRV 1,73 + 4,5 Punkte  ->  +0,123 R
            CRV 2,54 + 4,5 Punkte  ->  +0,159 R

        ⚠️ DER HEBEL GEWINNT DAMIT REIN RECHNERISCH, weil seine Geometrie ein
        hoeheres CRV hat (Median 2,54 gegen 1,73). Ob H bei CRV 2,54 ueberhaupt
        +4,5 Punkte bringt, ist NICHT GEMESSEN.

        SOLANGE DAS SO IST, darf diese Zahl Handlungen mit VERSCHIEDENEM CRV
        nicht gegeneinander stellen - also insbesondere nicht Spot gegen
        Hebel. Innerhalb derselben Geometrie ordnet sie."""
        return abs(self.crv - 2.0) > 0.25


def rechne(*, crv: float, stop_relativ: float, klasse: str = "",
           h: bool | None = None, instrument: str = "spot",
           strategie: str = "einstieg") -> Potential:
    """Das Potential EINER Handlung - gebuehrenfrei.

    ⚠️ `gebuehr_je_seite=0.0` ist KEIN Versehen und kein Vorgabewert, den man
    spaeter fuellt. Es ist die Trennung selbst: diese Ebene kennt keine
    Gebuehren. `wahrscheinlichkeit.rechne()` verlangt das Feld, weil es dort
    beide Ebenen liefert; hier wird bewusst die gebuehrenfreie Variante
    abgerufen und NUR `quote` uebernommen."""
    from agent import handelsauftrag as HA
    from agent import wahrscheinlichkeit as WK

    # Wirft bei unerlaubter Kombination - `hebel x akkumulation` gibt es nicht.
    instrument, strategie = HA.pruefe(instrument, strategie)
    try:
        w = WK.rechne(crv=crv, stop_relativ=stop_relativ,
                      gebuehr_je_seite=0.0, klasse=klasse, h=h)
    except WK.WahrscheinlichkeitUnbekannt as exc:
        raise PotentialUnbekannt(str(exc)) from exc

    q, c = float(w["quote"]), float(w["crv"])
    return Potential(wert_r=q * c - (1.0 - q), quote=q,
                     basisrate=float(w["basisrate"]), crv=c,
                     zuschlag_punkte=float(w["zuschlag_punkte"]),
                     instrument=instrument, strategie=strategie,
                     beitraege=w["beitraege"])


def vergleiche(kandidaten: list) -> list:
    """Handlungen nach Potential ordnen, beste zuerst.

    `kandidaten` sind fertige `Potential`-Objekte. Diese Funktion RECHNET
    nichts - sie ordnet nur. Wer hier eine zweite Formel einbaute, haette zwei
    Definitionen desselben Masses.

    ⚠️ BEI GLEICHSTAND GEWINNT DIE EINFACHERE HANDLUNG. Zwei Potentiale, die
    sich auf drei Stellen gleichen, sind nicht unterscheidbar; dann ist Spot
    dem Hebel vorzuziehen, weil er keine laufenden Kosten traegt. Das ist eine
    Setzung, keine Messung - und sie steht hier, damit sie sichtbar ist.

    ⚠️ UND SIE ORDNET NICHT UEBER VERSCHIEDENE CRV HINWEG. H ist bei CRV 2,0
    gemessen; bei anderem CRV ist der Beitrag extrapoliert, und zwar mit
    systematischer Richtung zugunsten des hoeheren CRV. Wo Kandidaten
    verschiedene Geometrien haben, gibt es KEINE Reihenfolge - der Aufrufer
    bekommt sie unveraendert zurueck und muss beide melden."""
    rang = {"spot": 0, "absicherung": 1, "hebel": 2}
    crvs = {round(float(p.crv), 2) for p in kandidaten}
    if len(crvs) > 1 and any(p.crv_extrapoliert for p in kandidaten):
        return list(kandidaten)          # unveraendert - nicht vergleichbar
    return sorted(kandidaten,
                  key=lambda p: (-round(p.wert_r, 3),
                                 rang.get(p.instrument, 9)))


def saetze(p: Potential) -> list:
    """Das Potential in der Form, in der es in die Mail gehoert.

    ⚠️ DIE HERKUNFT STEHT DABEI. Eine Zahl ohne die Angabe, woraus sie
    besteht, laedt dazu ein, ihr mehr zu glauben als sie traegt - und heute
    besteht sie aus genau einem Beitrag."""
    from agent.schreibweise import de

    z = [f"Potential dieser Handlung ({p.instrument}/{p.strategie}): "
         f"{de(p.wert_r, 3)} R",
         f"   aus der Geometrie (CRV {de(p.crv, 1)}): {de(p.aus_geometrie, 3)} R"
         f"  - per Konstruktion null",
         f"   aus gemessenen Beitraegen: {de(p.aus_beitraegen, 3)} R"]
    getragen = [b for b in p.beitraege if b.get("zustand") == "traegt"]
    for b in getragen:
        z.append(f"      + {b['name']}: +{de(b['punkte'], 1)} Punkte")
    if not getragen:
        z.append("      (kein Beitrag trifft zu - das Potential ist null)")
    z.append("   ⚠️ ohne Gebuehren gerechnet - die Geldfrage steht getrennt")
    if p.crv_extrapoliert:
        z.append(f"   ⚠️ H ist bei CRV 2,0 gemessen, hier {de(p.crv, 2)} - "
                 f"der Beitrag ist EXTRAPOLIERT")
    return z
