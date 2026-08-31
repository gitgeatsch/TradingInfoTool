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

STAND 31.08.2026 - ZWEI TRAGENDE BEITRAEGE, BEIDE ABGESTUFT:

    Funding-Rang im Markt    +0,82 / +1,30 / +0,12 / -0,54 / -1,70
    Turnover-Rang im Markt   +3,15 / +0,83 / +0,22 / -1,79 / -2,40

Wer diese Zahl liest, liest: "wie teuer ist dieser Wert heute, verglichen
mit den anderen".

⚠️ VORFILTER H IST AM 31.08. WEGGEFALLEN (R1). Er stand hier elf Tage mit
+4,5 Punkten und war gepoolt gemessen: +3,57 Punkte ueber die ganze
Historie, aber -1,02 [-2,18 .. +0,14] je Kalendertag. Das ist eine
LAGE-Aussage ("an welchen Tagen tritt H auf"), keine Asset-Aussage - und
Stufe 11 stellt die zweite Frage. Die Begruendung steht vollstaendig in
`wahrscheinlichkeit.BEITRAEGE`; die Marken tragen weiterhin den STOP.

⚠️ SEITHER GILT EINE REGEL, DIE DIESEN FEHLER STRUKTURELL AUSSCHLIESST:
`Beitrag.klammer` muss `"tag"` sein, damit `zustand="traegt"` erlaubt ist.
Ein gepoolt gemessener Vorsprung kommt nicht mehr in diese Zahl.

## Wofuer sie taugt und wofuer nicht

    ✔ Handlungen mit GLEICHEM CRV ordnen (welches Asset zuerst)
    ✘ Handlungen mit VERSCHIEDENEM CRV ordnen - siehe die Warnung unten
    ✘ eine SCHWELLE setzen ("ab 0,3 R handeln") - dafuer ist die Basis zu duenn
    ✘ eine Geldaussage - dafuer ist Ebene 2 zustaendig

⚠⚠ DIE GRENZE, DIE SPOT GEGEN HEBEL AUSSCHLIESST (gefunden beim Testen,
27.08.; das Beispiel ist H, die GRENZE gilt unveraendert fuer Funding und
Turnover - auch sie sind bei CRV 2,0 gemessen). H war bei **CRV = 2,0 fest**
gemessen - `messe_marken.py:80`, woertlich
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
    klasse: str = ""

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
    def getragen_von(self) -> int:
        """Wieviele Beitraege haben tatsaechlich einen Wert geliefert?

        ⚠️ DIE FRAGE, DIE AM 31.08. GEFEHLT HAT. Ein Wert ohne jedes
        Merkmal bekommt dasselbe Potential wie einer mit gemessen
        mittelmaessigen Werten - beide landen bei rund null. Solange
        Stufe 11 nur zaehlte, war das folgenlos; seit G-6 verwirft sie,
        und dann ist der Unterschied entscheidend:

            gemessen und klein   -> zu Recht gesperrt
            gar nicht bestimmbar -> nach DATENLAGE gesperrt, nicht nach
                                    Qualitaet

        Gemessen am 31.08.: 29 von 56 Werten der Watchlist haben KEINEN
        einzigen Beitrag (alle ausser Krypto zu 100 %). Vorfilter H hatte
        dieses Problem nie - er wurde je Anker aus den Marken gerechnet
        und galt fuer jeden Wert.
        """
        return sum(1 for z in (self.beitraege or [])
                   if z.get("zustand") == "traegt")

    @property
    def erreichbar_max(self) -> float:
        """Das hoechste Potential, das bei DIESER Datenlage moeglich waere.

        ⚠️ Nur die Beitraege, die hier tatsaechlich einen Wert geliefert
        haben. Wer keinen Funding-Rang hat, kann dessen +1,30 Punkte auch
        nicht erreichen - und darf nicht daran gemessen werden.
        """
        from agent import wahrscheinlichkeit as _wk
        namen = {z.get("name") for z in (self.beitraege or [])
                 if z.get("zustand") == "traegt"}
        punkte = sum(max(b.stufen) for b in _wk.BEITRAEGE
                     if b.name in namen and b.stufen)
        q = self.basisrate + punkte / 100.0
        return q * self.crv - (1.0 - q)

    @property
    def erreichbar_voll(self) -> float:
        """Das hoechste Potential bei VOLLER Datenlage - der Bezugswert."""
        from agent import wahrscheinlichkeit as _wk
        punkte = sum(max(b.stufen) for b in _wk.BEITRAEGE
                     if b.zustand == "traegt" and b.stufen
                     and _wk._gilt(b, self.klasse, self.strategie)[0])
        q = self.basisrate + punkte / 100.0
        return q * self.crv - (1.0 - q)

    @property
    def schwelle(self) -> float:
        """⚠️⚠️ DIE SCHWELLE JE DATENLAGE (31.08.2026, Nutzerentscheidung).

        Nutzerfrage: *„Die Schwelle kann man ja vorher sauber kalibrieren je
        Beitrag bzw. Anzahl der Beitraege wird eine korrekte Schwelle
        angewendet."*

        DAS PROBLEM, das sie loest. Das Potential ist die SUMME der
        Beitragspunkte. Liegt bei einem Wert nur Funding vor und bei einem
        anderen Funding UND Turnover, summiert man ueber verschieden viele
        Summanden - und eine feste Schwelle trifft zwei verschiedene Skalen:

            nur Funding    max +0,0390 R    (36 von 43 Werten)
            beide          max +0,1335 R    ( 7 von 43 Werten)

        Eine Schwelle von 0,080 R waere fuer 36 von 43 Werten UNERREICHBAR -
        sie waeren dauerhaft gesperrt, egal wie gut ihr Funding steht. Das
        ist eine Sperre nach DATENLAGE, nicht nach Qualitaet (Regel 4).

        ⚠️ DER MITTELWERT WAR DIE FALSCHE ANTWORT und ist gemessen
        widerlegt (`messe_summe_gegen_mittel.py`, 31.08.): er benachteiligt
        die DICHTE Datenlage. Ein Wert im besten Turnover-Fuenftel (+3,15)
        und mittleren Funding (+0,12) kaeme auf +1,64 - schlechter als
        einer, der NUR Turnover hat (+3,15). Mehr Information wuerde den
        Wert senken.

        DIE KONSTRUKTION: die Schwelle ist ein ANTEIL der bei dieser
        Datenlage erreichbaren Spanne.

            schwelle = Vorgabe x (erreichbar_max / erreichbar_voll)

        Wer nur einen Beitrag hat, muss denselben ANTEIL seiner Spanne
        schaffen wie einer mit zweien. Gerechnet am Stand 31.08.:

            funding           max +0,0390 R  ->  Schwelle 0,0029 R
            turnover          max +0,0945 R  ->  Schwelle 0,0071 R
            funding+turnover  max +0,1335 R  ->  Schwelle 0,0100 R  (Vorgabe)

        ⚠️ DIE VOLLE DATENLAGE BEHAELT DIE VORGABE - sie ist der Bezug, und
        damit bleibt die Kalibrierung von `messe_schwelle_kalibrierung.py`
        gueltig.

        ⚠️ UND DER PREIS, offen benannt: ein Wert mit einem Beitrag bekommt
        dieselbe Durchlasschance wie einer mit zweien, obwohl weniger ueber
        ihn bekannt ist. Das ist eine Entscheidung fuer Erreichbarkeit und
        gegen die Gewichtung von Sicherheit - Nutzervorgabe 31.08.: *„Wir
        duerfen nicht davon ausgehen, dass wir eine 100-Prozent-Abdeckung
        der Daten haben. Das System muss genauso mit 1, 2, 3 oder mehreren
        Beitraegen arbeiten koennen."*
        """
        voll = self.erreichbar_voll
        if voll <= 0:
            return schwelle()
        anteil = max(0.0, min(1.0, self.erreichbar_max / voll))
        return schwelle() * anteil

    @property
    def traegt_hier(self) -> bool:
        """Traegt dieses Potential gegen die Schwelle SEINER Datenlage?"""
        return self.wert_r > self.schwelle

    @property
    def vermessen(self) -> bool:
        """Ist diese ASSETKLASSE ueberhaupt vermessen worden?

        ⚠️ DIE EBENE UEBER `bewertbar` - und die, die am 31.08. gefehlt hat.

        `bewertbar` fragt: hat DIESES Asset einen Wert geliefert?
        `vermessen`  fragt: gibt es fuer SEINE KLASSE ueberhaupt eine Messung?

        Der Unterschied entscheidet, ob eine Sperre begruendet ist:

            nicht vermessen  ->  wir wissen nichts. Eine Sperre waere ein
                                 FAKT ueber unseren Kenntnisstand, keine
                                 Potentialaussage (Regel 4).
            vermessen, aber
            kein Wert        ->  ein Mangel DIESES Assets. Sperre traegt.

        Gemessen am 31.08. gegen die Notebook-Produktion: mit scharfer
        Stufe 11 und ohne diese Unterscheidung lieferte die Kette **null
        Signale ueber alle fuenf Gruppen** - vier Klassen haben keinen
        einzigen registrierten Beitrag.
        """
        from agent import wahrscheinlichkeit as _wk
        return bool(_wk.vermessen(self.klasse, self.strategie))

    @property
    def bewertbar(self) -> bool:
        """Steht hinter dieser Zahl ueberhaupt eine Messung?"""
        return self.getragen_von > 0

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
           strategie: str = "einstieg",
           merkmale: dict | None = None) -> Potential:
    """Das Potential EINER Handlung - gebuehrenfrei.

    ⚠️ `gebuehr_je_seite=0.0` ist KEIN Versehen und kein Vorgabewert, den man
    spaeter fuellt. Es ist die Trennung selbst: diese Ebene kennt keine
    Gebuehren. `wahrscheinlichkeit.rechne()` verlangt das Feld, weil es dort
    beide Ebenen liefert; hier wird bewusst die gebuehrenfreie Variante
    abgerufen und NUR `quote` uebernommen.

    ⚠️ `merkmale` IST DER WEG FUER JEDEN WEITEREN BEITRAG (2e, 30.08.2026).
    H hat einen eigenen Parameter, weil er der erste war; alles danach kommt
    hier durch - `{"funding_fuenftel": 0..4, "turnover_fuenftel": 0..4}`.
    Ein fehlender Schluessel ist NICHT dasselbe wie eine 0: er fuehrt in
    `wahrscheinlichkeit.rechne()` zu "an diesem Anker nicht bestimmbar" und
    traegt null bei, statt das schlechteste Fuenftel vorzutaeuschen.

    ⚠️ `strategie` WIRD SEIT 2e MIT DURCHGEREICHT, und das ist eine
    Verhaltensaenderung ueber 2e hinaus - deshalb steht sie hier.
    `wahrscheinlichkeit._gilt()` prueft drei Achsen (Klasse, Strategie,
    Richtung), bekam aber nur die Klasse. Heute aendert das nichts: KEIN
    registrierter Beitrag schraenkt auf Strategien ein (geprueft am
    30.08.). Ohne die Durchreichung wuerde der erste strategieabhaengige
    Beitrag jedoch still fuer ALLE Strategien gelten - ein Fehler, der
    nirgends anschlaegt. Die Naht wird gelegt, solange sie folgenlos ist.
    """
    from agent import handelsauftrag as HA
    from agent import wahrscheinlichkeit as WK

    # Wirft bei unerlaubter Kombination - `hebel x akkumulation` gibt es nicht.
    instrument, strategie = HA.pruefe(instrument, strategie)
    try:
        w = WK.rechne(crv=crv, stop_relativ=stop_relativ,
                      gebuehr_je_seite=0.0, klasse=klasse, h=h,
                      strategie=strategie, merkmale=merkmale)
    except WK.WahrscheinlichkeitUnbekannt as exc:
        raise PotentialUnbekannt(str(exc)) from exc

    q, c = float(w["quote"]), float(w["crv"])
    return Potential(wert_r=q * c - (1.0 - q), quote=q,
                     basisrate=float(w["basisrate"]), crv=c,
                     zuschlag_punkte=float(w["zuschlag_punkte"]),
                     instrument=instrument, strategie=strategie,
                     beitraege=w["beitraege"], klasse=klasse)


# ---------------------------------------------------------------------------
# DIE SCHWELLE - U-1, 30.08.2026
# ---------------------------------------------------------------------------
# Ab welchem Potential wird gehandelt? Die Zahl ist gemessen, nicht gesetzt:
# `messe_schwelle_quotengleich.py` hat sie gegen den QUOTENGLEICHEN Zufall
# geprueft (nie gegen die Gesamtmenge - der Selektionseffekt haette sie
# aufgeblaeht, Methodik 2.93).
#
#   Schwelle  Durchlass   echt minus quotengleicher Zufall
#   0,000       53,9 %    +0,1258  [+0,067 .. +0,199]   traegt
#   0,010       38,9 %    +0,1701  [+0,092 .. +0,270]   traegt
#   0,020       35,9 %    +0,1818  [+0,102 .. +0,284]   traegt
#   0,030       19,5 %    +0,1654  [+0,050 .. +0,257]   traegt
#
# ⚠️ ES GIBT KEIN OPTIMUM. Der Effekt waechst nahezu LINEAR mit der
# Sperrquote (10 % -> +0,016 · 20 % -> +0,025 · 40 % -> +0,048 · 60 % ->
# +0,071). Die Wahl ist deshalb eine ABWAEGUNG zwischen Signalzahl und
# Qualitaet - keine Messfrage, sondern eine Nutzerentscheidung.
#
# ⚠️ WAS 0,010 KONKRET VERLANGT: rund 0,33 Punkte Zuschlag. Ohne Vorfilter H
# kommen davon 9 von 25 Fuenftel-Kombinationen durch - beide Merkmale
# muessen mindestens mittelmaessig sein. Mit H kommen alle durch.
#
# KALIBRIERBAR: `Basisinfos/config.yaml` -> `bewertung: potential_schwelle_r`.
SCHWELLE_VORGABE = 0.010

# ---------------------------------------------------------------------------
# R-R9: DIE SCHWELLE GEHOERT ZU EINER BEITRAGSLAGE (30.08.2026)
# ---------------------------------------------------------------------------
# Nutzervorgabe: *"mehr Beitraege, andere Kalibrierung bzw. Quote muss
# eigentlich eine feste Regel sein, sonst kippt das System."*
#
# ⚠️ WARUM DAS KEIN GUTER RAT IST, SONDERN EINE BEDINGUNG. Jeder neue
# tragende Beitrag hebt ALLE Potentialwerte an. Bei gleicher Schwelle kommen
# dadurch mehr Signale durch, ohne dass sich ihre Qualitaet geaendert haette:
#
#     heute (H + Funding + Turnover)     39 % Durchlass
#     ein Beitrag mit +1,0 Punkten mehr  77 %
#     ein Beitrag mit +2,0 Punkten mehr  89 %
#
# Ein Filter, der mit jedem Fortschritt durchlaessiger wird, hebt sich selbst
# auf. Deshalb haengt die Schwelle hier an einem FINGERABDRUCK der
# Beitragslage - aendert sich diese, faellt es auf, statt still zu wirken.
#
# ---- NEUKALIBRIERT AM 31.08.2026 (R1: H faellt) ----------------------------
#
# Zwei Kalibrierungen in zwei Tagen, und der Grund fuer die zweite ist R1:
# H ist als Beitrag weggefallen (gepoolt +3,57 Punkte, je Kalendertag
# -1,02 [-2,18 .. +0,14] - eine LAGE-Aussage, keine Asset-Aussage). Damit
# aendert sich die Beitragslage, und R-R9 verlangt eine neue Schwelle.
#
# `messe_schwelle_kalibrierung.py`, 123.465 Anker, 2.726 Kalendertage:
#
#     Schwelle   Durchlass   Gewinn gegen ohne   je verworfenem Signal
#      0,000       51,2 %         +0,0480              +0,0983
#      0,010       43,0 %         +0,0470              +0,0824     <- gilt
#      0,020       40,0 %         +0,0552              +0,0921
#      0,050       20,9 %         +0,0961              +0,1214
#      0,080       16,5 %         +0,1324              +0,1585     <- Optimum
#      0,120        2,0 %         -0,0040              -0,0041
#
# ⚠️ H's WEGFALL KOSTET 1,3 PUNKTE DURCHLASS (44,3 % -> 43,0 %). Genau die
# Groessenordnung, die `simuliere_h_varianten.py` vorhergesagt hatte
# (1,2 Punkte, 0,0016 R Ertrag). Die Schwelle bleibt deshalb bei 0,010.
#
# ⚠️ 0,080 MISST WEITERHIN BESSER (+0,1324 gegen +0,0470) UND WIRD WEITERHIN
# NICHT GESETZT. Drei Gruende, unveraendert seit dem 30.08.:
#   1. Das Optimum ist IN-SAMPLE gefunden - aus denselben Daten wie die
#      Stufen. Neun geprueste Schwellen sind ein echter Suchpreis (2.57).
#   2. 0,080 sperrt 83,5 % der Signale - eine Groessenordnung mehr als die
#      heutige Verengung, und das gehoert dem Nutzer vorgelegt.
#   3. Die Vorgabe 0,010 stammt vom Nutzer (30.08.).
#
# OFFEN: ob 0,080 ausserhalb der Stichprobe haelt.
# ---- NEUKALIBRIERT AM 31.08.2026 (P3: dritter Beitrag) --------------------
#
# `Abstand zum eigenen 200-Tage-Schnitt` ist dazugekommen - der erste
# Beitrag aus der eigenen KURSREIHE und damit der einzige, der bei jedem
# Wert wirken kann (Nutzervorgabe 31.08.: *"Krypto muss und braucht einen
# Entscheider, der bei ALLEN Assets wirkt"*).
#
# Durchlass ueber alle Rangkombinationen, gleichverteilt gerechnet:
#
#     Schwelle   zwei Beitraege   drei Beitraege
#      0,000                        48,8 %
#      0,010          44,0 %        43,2 %      <- gilt
#      0,020                        38,4 %
#      0,080                        17,6 %
#
# ⚠️ R-R9 BEFUERCHTETE, dass jeder neue Beitrag den Filter durchlaessiger
# macht. Gemessen wird er MINIMAL STRENGER (44,0 -> 43,2 %). Der Grund ist
# derselbe wie bei 2e: Rangbeitraege sind SYMMETRISCH - ihre oberen
# Fuenftel sperren, sie heben nicht nur an. Die Befuerchtung gilt fuer
# Beitraege, die nur addieren.
#
# ⚠️ DIESE ZAHLEN (44,0 -> 43,2 %) STAMMEN AUS EINER SIMULATION MIT DEM
# SCHNITTABSTAND und sind seit seinem Fall vom 31.08. abends historisch.
# Sie bleiben als Beleg fuer die Symmetrie-Aussage stehen; der geltende
# Durchlass steht in der Tabelle darueber.
# ⚠️⚠️ KORRIGIERT AM 31.08.2026 ABENDS - UND ZWAR IN ZWEI SCHRITTEN.
#
# Hier stand der Schnittabstand mit drin. Das war aus zwei Gruenden falsch:
#
#   1 Er ist am selben Abend als Beitrag GEFALLEN (Horizontlauf: bei keinem
#     Horizont trennbar, H20 -0,0221 R).
#   2 ⚠️ ER WAR NIE TEIL DER KALIBRIERUNG. `messe_schwelle_kalibrierung.
#     bewerte()` rechnet ausschliesslich mit FUNDING_STUFEN und
#     TURNOVER_STUFEN - den Schnittabstand kennt es nicht. Ich hatte ihn
#     mittags in diese Zeile geschrieben, weil er registriert war, nicht
#     weil er kalibriert war.
#
# Punkt 2 ist der schwerere: die Zeile behauptete eine Kalibrierung, die
# nie stattgefunden hat, und haette bei der naechsten R-R9-Pruefung
# faelschlich "passt" gemeldet.
#
# ✔ DIE GUTE NACHRICHT: weil die Kalibrierung den Schnittabstand nie
# enthielt, ist die Schwelle 0,010 R durch seinen Wegfall NICHT
# ungueltig geworden. Sie gilt fuer genau die Beitragslage, die jetzt
# wieder besteht.
KALIBRIERT_FUER = ("funding_fuenftel:0.82/1.30/0.12/-0.54/-1.70 "
                   "turnover_fuenftel:3.15/0.83/0.22/-1.79/-2.40")
"""Die Beitragslage, fuer die SCHWELLE_VORGABE kalibriert wurde.

⚠️ WIRD BEI JEDER AENDERUNG AN `wahrscheinlichkeit.BEITRAEGE` MITGEZOGEN -
und zwar zusammen mit einer NEUEN Kalibrierung, nicht davor und nicht danach.
Der Ablauf steht in `Regelwerksmanual.md` R-R9, das Verfahren in
`Test_und_Verifikationsmethodik.md` 2.93.
"""


def beitragslage() -> str:
    """Fingerabdruck der heute TRAGENDEN Beitraege.

    Nur `traegt` zaehlt - ein Beitrag im Zustand `null` oder `noch_nicht`
    verschiebt keine Potentialwerte und braucht deshalb keine Neukalibrierung.
    """
    from agent import wahrscheinlichkeit as WK
    teile = []
    for b in WK.BEITRAEGE:
        if b.zustand != "traegt":
            continue
        if b.stufen:
            teile.append("%s:%s" % (b.merkmal or b.name,
                                    "/".join("%.2f" % x for x in b.stufen)))
        else:
            teile.append("%s:%.1f" % (b.merkmal or b.name, b.punkte))
    return " ".join(sorted(teile))


def kalibrierung_gilt() -> tuple[bool, str]:
    """Passt die Schwelle noch zur Beitragslage? (R-R9)

    Rueckgabe `(gilt, lage)`. Wer `False` bekommt, hat einen Beitrag
    veraendert, ohne die Schwelle nachzuziehen - die Durchlassquote ist dann
    eine andere als die kalibrierte, ohne dass es jemand entschieden haette.
    """
    lage = beitragslage()
    return lage == KALIBRIERT_FUER, lage


def schwelle() -> float:
    """Die geltende Potentialschwelle - aus der Konfiguration, sonst Vorgabe.

    ⚠️ Wird bei JEDEM Aufruf gelesen, nicht beim Import gecacht. Wer die Zahl
    in `config.yaml` aendert, soll nicht neu starten muessen - das ist der
    Unterschied zwischen "kalibrierbar" und "konfigurierbar".
    """
    try:
        import config as _cfg
        wert = (_cfg.load_config() or {}).get("bewertung", {})             .get("potential_schwelle_r")
        if wert is not None:
            return float(wert)
    except Exception:                                        # noqa: BLE001
        pass
    return SCHWELLE_VORGABE


def traegt(wert_r: float, grenze: float | None = None) -> bool:
    """Reicht dieses Potential fuer eine Empfehlung?

    ⚠️ STRIKT GROESSER. Genau null heisst "kein Beitrag traegt" - und das ist
    der Regelfall, nicht die Ausnahme. Ein Barrierensystem auf driftfreiem
    Pfad hat Erwartungswert null; wer null durchlaesst, empfiehlt ohne Grund.
    """
    return float(wert_r) > (schwelle() if grenze is None else float(grenze))


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
