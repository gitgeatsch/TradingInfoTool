# -*- coding: utf-8 -*-
"""DIE MESSNORM — eine Grundlage, die nicht je Messung neu gewaehlt wird
(06.09.2026)

## Warum es dieses Modul gibt

**Elf Messungen in zwei Tagen haben elf Mal die Grundlage neu gewaehlt** -
Zielgroesse, Menge, Klammer, Nullpunkt, Kontrollen. Das Ergebnis war eine
Folge von "traegt / traegt nicht", die mit jeder Methodenaenderung kippte.

Nutzervorgabe 06.09.: *„stelle sicher, dass wir danach zukuenftig Regeln und
Standards haben, die eine saubere Abgrenzung erlauben und nicht jede Messung
als Zufallsergebnis traegt oder nicht traegt."*

⚠️ **Eine Norm im Dokument wird nicht befolgt - eine im Code schon.**
Vorbild ist `wahrscheinlichkeit.Beitrag.klammer="tag"`: seit dem 31.08.
wirft der Import, wenn ein Beitrag ohne Tagesklammer registriert wird.

## Die drei Fehler, gegen die dieses Modul gebaut ist

    1  FALSCHE ZIELGROESSE   "Ziel vor Stop" misst die eigene Zielregel
                             zurueck (Konzept Bewertungsstufe, 23.08.)
    2  FALSCHE MENGE         die Beitraege wirken auf 1,5 % der Anker;
                             gemessen wurde auf 100 % (F-212, 04.09.)
    3  FEHLENDE TRENNSCHAERFE  ein "traegt nicht" ohne Positivkontrolle ist
                             keine Messung, sondern das Fehlen einer

## ⚠️ Der Kern: VIER Urteile, und nur zwei sind Aussagen ueber die Welt

Bisher gab es "traegt" und "traegt nicht". Das zweite verschweigt, ob die
Messung den Effekt ueberhaupt haette finden koennen. Hier gibt es:

    TRAEGT                 Band schliesst den Nullpunkt aus
    TRAEGT NICHT           und die Positivkontrolle beweist, dass ein
                           Effekt dieser Groesse gefunden WORDEN WAERE
    KEIN BEFUND            die Trennschaerfe reicht nicht - untermaechtig

**Nur das mittlere Urteil ist eine Aussage ueber die Welt.** Das dritte ist
eine Aussage ueber die Messung, und es wird nicht mehr als Nullbefund
ausgegeben.

## Die Norm — Z bis W

| | | Quelle |
|---|---|---|
| **Z** | ZIELGROESSE, aus geschlossener Liste, passend zur Lage | Konzept Bewertungsstufe §1 |
| **M** | MENGE, mit Dosis-Wirkungs-Kurve als Pflicht | F-212 |
| **K** | KLAMMER: Kalendertag, nie gepoolt | Vorgabe 31.08., Methodik 2.86 |
| **G** | KOSTEN 0,00 % fuer jede Rangfolge | Regel 2, Konzept §4 |
| **B** | BAND: Block-Bootstrap, Block >= 3 x Horizont | Methodik 2.95 |
| **N** | NULLKONTROLLE auf derselben Struktur | F-226 |
| **P** | POSITIVKONTROLLE -> TRENNSCHAERFE | Methodik 2.88, 2.100 |
| **W** | PFLICHTANGABEN: Anker, Tage, Bloecke, Abdeckung, Hypothesen | Zielgroessen §4 |
| **L** | AUSGANGSLAGE: Instrument x Strategie x Richtung | Nutzervorgabe 06.09. |

    python messnorm.py --selbsttest
"""
from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass, field

import numpy as np

# ⚠️ ABGESICHERT (07.09.2026): `pruefe_pakete` ersetzt stdout durch einen
# Mitschnitt ohne `reconfigure`. Ein Modul, das die Suite beim IMPORT
# sprengt, ist dort nicht pruefbar - und genau dieses hier muss es sein.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                        # noqa: E402
import messe_regel_wirksamkeit as W                         # noqa: E402


# ---------------------------------------------------------------- Z
# ⚠️ GESCHLOSSENE LISTE. Wer eine neue Zielgroesse braucht, traegt sie hier
# ein - und muss dabei sagen, fuer welche Lagen sie gilt. Ein freier String
# waere genau die Beliebigkeit, gegen die dieses Modul gebaut ist.
# ⚠️⚠️⚠️ DIE MENGE — die Fehlerquelle, die dieses Projekt am oeftesten
# erwischt hat (07.09.2026, nach dem Audit 2.143).
#
# ZWEI PRINZIPIEN, BEIDE DOKUMENTIERT, BEIDE RICHTIG — und wer sie
# verwechselt, bekommt zuverlaessig das falsche Ergebnis:
#
#   P6 / F-167   "Die Messbasis ist BREITER als das Portfolio und muss es
#                sein - sonst misst man seine eigene Auswahl."
#   F-212        Beitragsurteile gehoeren auf die SELEKTIERTE Menge. Auf
#                der freien wirken die Beitraege auf 1,5 % der Anker;
#                dort liegt selbst `funding` bei -0,0003 R.
#
# **Es ist kein Widerspruch, sondern zwei verschiedene FRAGEN.** Deshalb
# ist `frageart` seit dem 07.09. Pflicht: sie bindet die Frage an die
# Menge, statt die Wahl dem Gedaechtnis zu ueberlassen.
#
# ⚠️ DIE FEHLERHISTORIE, damit sie nicht ein viertes Mal passiert:
#
#   F-167 (02.09.)  32 Watchlist-Werte importiert, wo eine Messbasis
#                   noetig war -> nur 12 Bloecke, Band deckt nicht
#   2.134 (06.09.)  `k = 2` aus 516 statt aus 40 Symbolen gewaehlt ->
#                   die Auswahl schien schaedlich, war sie nicht
#   2.143 (07.09.)  sechs von sieben Messungen auf der freien Menge ->
#                   Nullbefunde, die nichts bedeuten; eine Live-Aenderung
#                   musste zurueckgenommen werden
#
# DIE TATSAECHLICHEN GROESSEN, am 07.09. gezaehlt:
#
#   Messuniversum          516 Symbole   (`messe_eigenschaft_beitrag.lade`)
#   Watchlist               57 Eintraege - davon nur 29 im Messuniversum
#   selektiert (5 %)      ~2-3 je Tag    (oberste 5 % nach 250-Tage-Momentum)
#   Abdeckung funding      288 (56 %) · turnover 65 (13 %) · oi 115 (22 %)
FRAGEARTEN = {
    "markt": {
        "text": "Traegt diese Groesse im Markt?",
        "menge": "messuniversum",
        "begruendung": ("P6: die Messbasis muss BREITER sein als das "
                        "Portfolio - sonst misst man seine eigene Auswahl"),
    },
    "beitrag": {
        "text": "Was bewirkt dieser Beitrag im BETRIEB?",
        "menge": "selektiert",
        "begruendung": ("F-212: die Beitraege wirken erst an Trichterstufe "
                        "12, auf einer Menge, die elf Stufen vorher schon "
                        "gefiltert haben. Auf der freien Menge misst man "
                        "98,5 % Anker, an denen sie nie zum Zug kommen - "
                        "ein Nullbefund ist dort vorprogrammiert"),
    },
    "geometrie": {
        "text": "Wie soll die Geometrie stehen (Stop, Ziel, Horizont)?",
        "menge": "messuniversum",
        "begruendung": ("die Geometrie gilt fuer jeden Anker, nicht nur "
                        "fuer die ausgewaehlten - hier ist die breite "
                        "Basis richtig"),
    },
    "zaehlung": {
        "text": "Wieviele/wie oft? (deskriptiv, kein Urteil)",
        "menge": "beliebig, aber benannt",
        "begruendung": "eine Zaehlung urteilt nicht - sie muss nur sagen, "
                       "WORUEBER sie zaehlt",
    },
}


ZIELGROESSEN = {
    "bewegung_r": {
        "text": "Rendite in R nach H Tagen, BARRIERENFREI",
        "gilt_fuer": "alle Lagen",
        "statistik": "median",
        "begruendung": "misst die Bewegung, nicht die eigene Zielregel",
    },
    "barriere": {
        "text": "Ziel vor Stop (CRV-Barriere)",
        "gilt_fuer": "nur Lagen, in denen ein Stop den Trade BEENDET",
        # ⚠️⚠️ MITTEL, NICHT MEDIAN (09.09.2026). Der Ausgang ist BINAER
        # (Ziel vor Stop = 0/1); der Median ist dann 0 oder 1, und die
        # Differenz fast immer exakt null - die Statistik waere entartet.
        # Eine Trefferquote ist ein MITTEL.
        "statistik": "mittel",
        "begruendung": ("blind fuer 'wieviel ist zu holen' - der "
                        "Erwartungswert ist per Konstruktion null. Zulaessig "
                        "als VERGLEICH zweier Arme unter derselben Zielregel "
                        "und dort, wo der Stop den Trade wirklich beendet."),
    },
    # ⚠️⚠️ NACHGETRAGEN AM 09.09.2026 - sie FEHLTE, obwohl die Akkumulation
    # seit dem 28.08. mit ihr gemessen wird (`messe_akkumulationsmass.py`,
    # 505 Reihen, sieben Kontrollen). Ein Zielgroessenregister, das die
    # laufende Zielgroesse einer Lage nicht kennt, kann seine Aufgabe nicht
    # erfuellen: es soll verhindern, dass eine Lage mit dem Massstab einer
    # anderen gemessen wird.
    "verbilligung": {
        "text": ("Perzentilrang der Verbilligung V(t,H) = "
                 "Mittel(Kurs[t+1..t+H]) / Kurs(t) - 1 INNERHALB der "
                 "eigenen Reihe"),
        "gilt_fuer": "nur spot x akkumulation",
        "einheit": "Rang",
        "statistik": "median",
        "begruendung": ("das Erfolgsmass, das `handelsauftrag.py` der "
                        "Akkumulation ausdruecklich gibt. Als Perzentilrang "
                        "in der EIGENEN Reihe ist die Basisrate exakt 0,500 "
                        "per Konstruktion - der Drift kann nicht als Signal "
                        "durchgehen. ⚠️ Fuer BTC, ETH und SOL traegt der "
                        "Befund NICHT (Rang -0,025 bis -0,031, p 0,72 bis "
                        "0,86) - sie sind 2,39 Standardfehler unter dem "
                        "Mittel von 505 Reihen."),
    },
}

# ⚠️ Welche Zielgroesse gehoert zu welcher Lage? Ohne diese Zuordnung wird
# eine Lage mit dem Massstab einer anderen gemessen - und der Befund traegt
# ein Etikett, das nicht zu seinem Inhalt passt.
ZIELGROESSE_JE_LAGE = {
    ("spot", "einstieg"): "bewegung_r",
    ("spot", "akkumulation"): "verbilligung",
    ("hebel", "einstieg"): "barriere",
    ("hebel", "swing"): "barriere",
    ("absicherung", "einstieg"): "bewegung_r",
}

# ⚠️⚠️ STILLGELEGTE LAGEN - nicht geloescht, sondern gesperrt (Regel G-a)
#
# Nutzervorgabe 10.09.2026: *„Swing ist keine genutzte Strategie mehr."*
#
# ⚠️ WARUM NICHT LOESCHEN: `swing` steht an fuenf Stellen in
# `pruefe_pakete` als Testfall der BETRIEBSkette (`HA.pruefe("Hebel",
# "Swing")`), und `handelsauftrag.STRATEGIEN` fuehrt es weiter. Ein
# Loeschen haette die Suite gebrochen und die Betriebskette angefasst -
# fuer eine Aenderung, die nur die MESSachse betrifft.
#
# ⚠️⚠️ Das ist die Hausregel G-a: „eine Stufe, die nichts beitraegt, wird
# NICHT geloescht, sondern stillgelegt" - mit einem Kanarienvogel, der
# anschlaegt, wenn sie doch jemand benutzt.
#
# Wer eine stillgelegte Lage misst, bekommt einen Fehler mit Begruendung -
# nicht ein stilles Ergebnis auf einer Lage, die es nicht mehr gibt.
LAGEN_STILLGELEGT = {
    ("hebel", "swing"): ("Nutzervorgabe 10.09.2026: swing ist keine "
                         "genutzte Strategie mehr. Der Eintrag in "
                         "ZIELGROESSE_JE_LAGE bleibt stehen, damit die "
                         "Betriebskette unangetastet bleibt."),
}


def stillgelegt(instrument: str, strategie: str) -> str:
    """Der Grund, wenn diese Lage stillgelegt ist - sonst leer."""
    return LAGEN_STILLGELEGT.get(
        (str(instrument or "").strip().lower(),
         str(strategie or "").strip().lower()), "")


# Lagen, in denen ein Stop den Trade beendet - nur dort ist "barriere" die
# zutreffende Zielgroesse.
ZIEHUNGEN = 5
SAAT = 20260906

# ============================================================================
# DER MESSSTANDARD - hier steht er, nicht in der Dokumentation
# ============================================================================
# Nutzervorgabe 08.09.2026: "jedenfalls diesen Schritt breit in die
# relevanten Dokumentationen, Messungen, Code, Basisdokumente, Regelwerke
# uebernehmen." Und frueher schon: "so einen Parameter vergesse ich in
# Kuerze und du auch - die Doku reicht bei so einer zentralen Einstellung
# nicht." Deshalb: benannt, an EINER Stelle, mit `standardzeile()`
# ausgebbar - und von `pruefe_pakete.py` bewacht.
#
# ---- Was am 08.09.2026 geaendert wurde und WARUM ---------------------------
#
# 1) NULL_ZIEHUNGEN / NULL_PERZENTIL       (Befunde 2.188 bis 2.192)
#    `null_oben` war das MAXIMUM ueber fuenf Ziehungen. Ein Maximum ist
#    kein Schaetzer: es waechst mit jeder weiteren Ziehung und hat keinen
#    Grenzwert. Auf Kunstdaten mit bekannter Wahrheit schrumpft seine
#    Streuung NICHT (0,0140 -> 0,0095 bei n = 5 bis 80), die eines
#    Perzentils schon (0,0118 -> 0,0038). Und bei fuenf Ziehungen lag das
#    Maximum UNTER dem wahren 90. Perzentil - die Latte hing zu tief.
#    ACHTUNG: Es ist NICHT strenger, sondern stabil. `schnitt` bei 10 %
#    kippte umgekehrt, von "traegt nicht" auf TRAEGT.
#
# 2) TRENNSCHAERFE_GEGEN_NULLPUNKT          (Befund 2.188-inkonsistenz)
#    Die Trennschaerfe prueft `unten > 0`, das Urteil `unten > null_oben`.
#    Zwei Massstaebe, live sichtbar in EINEM Satz an `turnover`:
#    "Wirkung +0,0639 ueber der Trennschaerfe 0,0500 R, aber ...".
#
# 3) STAERKEN                                (Befund 2.194)
#    Die Leiter endete bei 0,10, waehrend `schnitt` +0,1858 wirkt.
#    "Untermaechtig - selbst +0,10 gepflanzt nicht gefunden" war eine
#    Aussage ueber die LEITER. `messnorm_rand.py` benutzte die laengere
#    ohnehin schon - der eigene Werkzeugkasten widersprach sich.
#
# ---- WAS DAMIT NICHT ERLEDIGT IST ------------------------------------------
#
# Diese drei machen die Urteile WIDERSPRUCHSFREI, nicht SCHAERFER. Offen
# bleibt (Befund 2.198): die Positivkontrolle pflanzt in die GEMISCHTE
# Welt, deren Band breiter sein kann - dann ueberschaetzt die
# Trennschaerfe systematisch, was noetig waere. `schnitt` traegt mit
# +0,186 bei ausgewiesener Trennschaerfe 0,40. Ebenso offen: `ZIEHUNGEN`
# steckt weiter in der Positivkontrolle (4 von 5 - eine Quote mit sechs
# moeglichen Werten), und ob p90 zum Vertrauensniveau des Bandes passt.
#
# "Die Basis steht" waere deshalb eine Behauptung, kein Befund. Was sie
# rechtfertigen wuerde, ist ein Selbsttest der ganzen Anlage gegen
# bekannte Wahrheit - Fehlalarm- UND Fundquote. Der fehlt.
# ============================================================================
MESSSTANDARD_AB = "2026-09-09"
NULL_ZIEHUNGEN = 40
NULL_PERZENTIL = 90.0
TRENNSCHAERFE_GEGEN_NULLPUNKT = True
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)

# ---- DER NULLBEZUG (09.09.2026, gemessen und vom Nutzer entschieden) -------
#
# Wogegen wird geprueft? Drei Kandidaten standen zur Wahl, alle drei wurden
# gegen bekannte Wahrheit gemessen - auf ECHTEN Daten, mit Nullwelten durch
# Mischen der Raenge (`selbsttest_kriterien_echt.py`, 150 Nullwelten ueber
# DREI Basen: turnover 50 %, funding 10 %, oi_aenderung 20 %):
#
#     Bezug          Fehlalarme (Soll 2,5 %)      Fundquote
#     "null_oben"      0 / 150  =  0,0 %          34/54 =  63 %
#     "nullpunkt"      4 / 150  =  2,7 %          53/54 =  98 %   <- gewaehlt
#     "null"          42 / 150  = 28,0 %          54/54 = 100 %
#
# ⚠️ BEIDE FEHLERARTEN ZAEHLEN. Wer nur die Fehlalarme ansieht, waehlt
# immer den strengsten Bezug - und "null_oben" findet eine Wirkung von
# +0,0448 in KEINEM von sechs Faellen, waehrend `turnover` +0,0608 wirkt.
#
# ---- WARUM "nullpunkt" UND NICHT "null_oben" -------------------------------
#
# `null_oben` ist die OBERE Vertrauensgrenze einer Nullwelt, also ein
# STREUMASS. `unten > null_oben` verlangt damit zwei 95-%-Baender, die sich
# nicht ueberlappen - das entspricht etwa p < 0,005 statt p < 0,05. Die
# Unsicherheit wird zweimal gezaehlt: einmal im Band, einmal im Nullpunkt.
#
# `nullpunkt` ist das MITTEL der Nullwelten, also der VERSATZ. Den gibt es
# wirklich (+0,007 bis +0,017; auf `funding`s Nullwelten sogar +0,0139
# Wirkung ohne jeden Zusammenhang) - deshalb reicht "null" nicht.
#
#     Versatz abziehen     noetig    -> sonst 28 % Fehlalarme
#     Streuung abziehen    doppelt   -> sie steckt im Band bereits
#
# ---- ⚠️⚠️ EIN BEZUG, NICHT ZWEI --------------------------------------------
#
# Fehler 2 vom 08.09. war "zwei Massstaebe in EINEM Satz": das Urteil pruefte
# gegen `null_oben`, die Trennschaerfe gegen null. Deshalb lesen BEIDE diese
# eine Groesse. Wer sie aendert, aendert beide - das ist Absicht.
NULLBEZUG = "nullpunkt"          # "nullpunkt" | "null_oben" | "null"


def _bezug(null: dict) -> float:
    """Der Bezugspunkt aus einer Nullkontrolle — dieselbe Wahl wie `traegt`.

    ⚠️ Es gibt sie, damit Urteil und Trennschaerfe NICHT auseinanderlaufen
    koennen (Fehler 2 vom 08.09.). Wer hier etwas aendert, aendert beide.
    """
    if NULLBEZUG == "null_oben":
        return max(0.0, float(null.get("oben") or 0.0))
    if NULLBEZUG == "null":
        return 0.0
    return max(0.0, float(null.get("mittel") or 0.0))


def standardzeile() -> str:
    """Der Messstandard IN KLARTEXT - fuer jeden Messkopf und Bericht."""
    return ("Messstandard ab %s: Bezug = %s (Fehlalarme 2,7 %% bei Soll "
            "2,5 %%, Fundquote 98 %%) | Nullwelten = %.0f. Perzentil ueber "
            "%d Ziehungen | Trennschaerfe gegen denselben Bezug | "
            "gepflanzte Staerken bis %.2f R | Positivkontrolle %d Ziehungen"
            % (MESSSTANDARD_AB, NULLBEZUG, NULL_PERZENTIL, NULL_ZIEHUNGEN,
               max(STAERKEN), ZIEHUNGEN))

STOP_BEENDET = {("hebel", "einstieg"), ("hebel", "swing")}


@dataclass(frozen=True)
class Lage:
    """Instrument x Strategie x Richtung — Pflichtfeld jeder Messung.

    ⚠️ Nutzervorgabe 06.09.: *„das sind unterschiedliche Ausgangslagen,
    welche nicht unsauber vermischt werden sollten - zumindest bei Hebel."*

    Gemessen am 06.09.: `instrument='hebel'` hat es in der neuen Kette NIE
    gegeben (3.513 spot, 11 absicherung, 0 hebel), und SHORT ist nie
    gefeuert. Der Hebel entsteht INNERHALB von spot x einstieg. Deshalb
    traegt jede Hebel-Aussage die Markierung `simuliert=True`.
    """
    instrument: str
    strategie: str
    richtung: str = "long"
    simuliert: bool = False

    def __post_init__(self) -> None:
        from agent import handelsauftrag as HA
        erlaubt = HA.ERLAUBTE_PAARE.get(self.instrument)
        if not erlaubt:
            raise ValueError("unbekanntes Instrument: %r" % self.instrument)
        if self.strategie not in erlaubt:
            raise ValueError("%s + %s ist keine vorgesehene Kombination"
                             % (self.instrument, self.strategie))
        if self.richtung not in ("long", "short"):
            raise ValueError("Richtung muss long oder short sein")
        if self.richtung == "short":
            # ⚠️ SHORT IST OFFEN (Nutzerhinweis 06.09.). Null Signale in der
            # Produktion, Zielgroesse ungeklaert. Kein stiller Durchlauf.
            raise ValueError(
                "SHORT ist noch nicht geklaert - null Signale in der "
                "Produktion, Zielgroesse offen. Erst festlegen, dann messen.")

    @property
    def stop_beendet(self) -> bool:
        return (self.instrument, self.strategie) in STOP_BEENDET

    def __str__(self) -> str:
        return "%s x %s x %s%s" % (self.instrument, self.strategie,
                                   self.richtung,
                                   " (simuliert)" if self.simuliert else "")


@dataclass(frozen=True)
class Protokoll:
    """DER WEG, nicht das Ergebnis — hier passieren die Fehler.

    ⚠️ Nutzerhinweis 06.09.: *„zur Urteilslogik gehoert nicht nur das
    Ergebnis, sondern der Weg dorthin, wo die eigentlichen Fehler
    passieren."*

    Beleg aus zwei Tagen: KEIN einziger Fehler war im Ergebnis sichtbar.
    Jeder erzeugte eine plausible Zahl.

        gepoolt statt Tagesklammer   ->  12,4 Punkte auf einem Nulleffekt
        Nullpunkt aus EINER Ziehung  ->  eine saubere Kurve
        Maximum statt Streuungsmass  ->  ein "strengerer" Test
        Pflanzung auf echte Daten    ->  eine gute Trennschaerfe
        Kunstwelt nach Rohwert       ->  ein bestandener Selbsttest

    Deshalb traegt jeder Befund seinen Weg mit sich, und die Norm prueft
    ihn - nicht nur die Zahl am Ende.
    """
    wirkung_funktion: str            # welche Funktion die Wirkung rechnete
    band_funktion: str               # welche das Band rechnete
    null_konstruktion: str           # wie der Nullpunkt entstand
    null_ziehungen: int
    positiv_konstruktion: str        # wie die Positivkontrolle entstand
    positiv_ziehungen: int
    positiv_treffer: dict            # {staerke: gefunden in x von n}
    blocklaenge: int
    saat: int
    # ⚠️ NACHGETRAGEN 06.09. (Schritt 4a, Gegenpruefung G1). Der Docstring
    # von `_block` verlangte seit dem Bau: *"die Blocklaenge wird je
    # Messung NACHGEPRUEFT, nicht angenommen. Wer sie nur setzt, hat sie
    # geraten."* `pruefe()` setzte sie - und rief `pruefe_block()` nie auf.
    # Die Norm dokumentierte ihre eigene Regel und hielt sie nicht ein.
    # Folgenlos geblieben (alle 18 gepruefte Zellen lagen zwischen -0,053
    # und +0,087 bei Grenze 0,15), aber genau deshalb faellt so etwas nicht
    # auf.
    block_ak: float = float("nan")   # Autokorrelation beim Blockabstand
    block_ok: bool = True

    def __post_init__(self) -> None:
        # ⚠️ BEKANNTE FALSCHE WEGE WERDEN ABGELEHNT, nicht nur vermerkt.
        if "gemischt" not in self.positiv_konstruktion:
            raise ValueError(
                "die Positivkontrolle muss in die GEMISCHTE Welt pflanzen. "
                "Auf die echten Daten gepflanzt misst sie Effekt PLUS "
                "Pflanzung - die Trennschaerfe faellt dann zu gut aus "
                "(06.09. gemessen: eine Welt mit 0,05 R wurde als "
                "'traegt nicht bis 0,02 R' gemeldet).")
        if self.null_ziehungen < 3 or self.positiv_ziehungen < 3:
            raise ValueError(
                "eine Ziehung ist kein Nullpunkt (Methodik 2.104). Die "
                "Basislinie wandert je Saat um denselben Betrag wie die "
                "gesuchten Effekte - gemessen -0,0055 bis +0,0010.")

    def zeilen(self) -> list:
        return [
            "  Wirkung ueber   %s" % self.wirkung_funktion,
            "  Band ueber      %s · Block %d" % (self.band_funktion,
                                                 self.blocklaenge),
            "  Nullpunkt       %s · %d Ziehungen" % (self.null_konstruktion,
                                                     self.null_ziehungen),
            "  Positivkontr.   %s · %d Ziehungen" % (self.positiv_konstruktion,
                                                     self.positiv_ziehungen),
            "  gefunden        %s" % " · ".join(
                "%.2f R: %d/%d" % (k, v, self.positiv_ziehungen)
                for k, v in sorted(self.positiv_treffer.items())),
            "  Blockpruefung   AK %.4f beim Abstand %d -> %s"
            % (self.block_ak, self.blocklaenge,
               "lang genug" if self.block_ok else "⚠️ ZU KURZ"),
            "  Saat            %d" % self.saat,
        ]


@dataclass(frozen=True)
class Befund:
    """Ein Messergebnis, das ohne seine Kontrollen nicht entstehen kann."""
    kandidat: str
    lage: Lage
    zielgroesse: str
    menge: str
    # Ergebnis
    wirkung: float
    unten: float
    oben: float
    # Kontrollen — Pflicht
    nullpunkt: float
    null_unten: float
    null_oben: float
    trennschaerfe: float | None          # kleinste GEFUNDENE gepflanzte Staerke
    # ⚠️ EINHEITEN (06.09., vom Vorabtest des Randmassstabs gefunden).
    #
    # `urteil` vergleicht `wirkung` gegen `trennschaerfe`. Solange beide in
    # R stehen, geht das auf. Beim Randmassstab steht `wirkung` aber in
    # ANTEILSPUNKTEN, waehrend gepflanzt wird in R - der Vergleich war
    # sinnlos (0,0008 Anteilspunkte gegen 0,05 R) und haette jedes Urteil
    # verfaelscht.
    #
    # Regel ab jetzt: `trennschaerfe` steht IMMER in der Einheit von
    # `wirkung`. Die gepflanzte Staerke in R - die einzige Groesse, die
    # ZWISCHEN den Massstaeben vergleichbar ist - steht in
    # `trennschaerfe_in_r`.
    trennschaerfe_in_r: float | None = None
    gepflanzt: tuple = ()
    # ⚠️ SEIT 07.09. PFLICHT (technisch mit Vorgabe, inhaltlich erzwungen
    # in `__post_init__`). Sie bindet die FRAGE an die MENGE - ohne sie war
    # die Wahl eine Gedaechtnisleistung, und die ist dreimal misslungen
    # (F-167, 2.134, 2.143).
    frageart: str = ""
    # Pflichtangaben
    n_anker: int = 0
    n_tage: int = 0
    n_bloecke: int = 0
    abdeckung_symbole: int = 0
    hypothesen: int = 1
    klammer: str = "tag"
    kosten_je_seite: float = 0.0
    protokoll: Protokoll | None = None

    def __post_init__(self) -> None:
        if not self.frageart:
            raise ValueError(
                "kein Befund ohne FRAGEART (seit 07.09.2026, Methodik "
                "2.143). Erlaubt: %s. Sie bindet die Frage an die Menge - "
                "ohne sie war die Wahl eine Gedaechtnisleistung, und die "
                "ist dreimal misslungen (F-167, 2.134, 2.143)."
                % ", ".join(FRAGEARTEN))
        if self.frageart not in FRAGEARTEN:
            raise ValueError("unbekannte Frageart: %r - erlaubt: %s"
                             % (self.frageart, ", ".join(FRAGEARTEN)))
        if self.frageart == "beitrag" and self.menge in ("frei", "messuniversum"):
            raise ValueError(
                "⚠️⚠️ BEITRAGSURTEIL AUF DER FREIEN MENGE. F-212: die "
                "Beitraege wirken dort auf 1,5 %% der Anker, und selbst "
                "`funding` liegt bei -0,0003 R. Ein Nullbefund ist "
                "vorprogrammiert. Benutze `messnorm_auswahl.pruefe_auswahl()` "
                "mit menge='5%%' - das Modul gibt es seit dem 06.09. "
                "(Menge war %r)" % self.menge)
        if self.zielgroesse not in ZIELGROESSEN:
            raise ValueError("unbekannte Zielgroesse: %r" % self.zielgroesse)
        if self.zielgroesse == "barriere" and not self.lage.stop_beendet:
            raise ValueError(
                "Zielgroesse 'barriere' ist fuer %s nicht zulaessig - dort "
                "beendet kein Stop den Trade. Sie misst dann die eigene "
                "Zielregel zurueck (Konzept Bewertungsstufe, 23.08.)."
                % self.lage)
        if self.klammer != "tag":
            raise ValueError("nur die Tagesklammer ist zulaessig (31.08.)")
        if self.kosten_je_seite != 0.0:
            raise ValueError("jede Rangfolge rechnet gebuehrenfrei (Regel 2)")
        # ⚠️ DIE KONTROLLEN SIND PFLICHT, NICHT OPTION.
        if self.protokoll is None:
            raise ValueError(
                "kein Befund ohne PROTOKOLL - der Weg gehoert zum Urteil, "
                "weil dort die Fehler passieren (Nutzervorgabe 06.09.)")
        if not self.gepflanzt:
            raise ValueError(
                "ohne Positivkontrolle kein Befund - ein 'traegt nicht' "
                "ohne Trennschaerfe ist keine Messung, sondern das Fehlen "
                "einer (Methodik 2.88, 2.100)")

    @property
    def traegt(self) -> bool:
        return self.unten > self.bezugswert

    @property
    def bezugswert(self) -> float:
        """Wogegen geprueft wird — EINE Groesse fuer Urteil UND Trennschaerfe.

        ⚠️ Gemessen am 09.09.2026 auf echten Daten (150 Nullwelten, drei
        Basen): `nullpunkt` trifft mit 2,7 % Fehlalarmen den Sollwert von
        2,5 % und findet 98 % der gepflanzten Effekte. `null_oben` macht
        0 % Fehlalarme, findet aber nur 63 % - es zaehlt die Unsicherheit
        doppelt. `null` macht 28 % Fehlalarme.
        """
        if NULLBEZUG == "null_oben":
            return max(0.0, self.null_oben)
        if NULLBEZUG == "null":
            return 0.0
        return max(0.0, self.nullpunkt)

    @property
    def urteil(self) -> str:
        """VIER Urteile — und nur zwei davon sind Aussagen ueber die Welt.

        ⚠️ DER KERN DIESES MODULS. Bisher gab es "traegt" und "traegt
        nicht", und das zweite verschwieg, ob die Messung den Effekt
        ueberhaupt haette finden koennen. Hier gilt:

            TRAEGT              Band schliesst den Nullpunkt aus
            TRAEGT NICHT BIS X  die Positivkontrolle hat X gefunden, die
                                Messung sieht nichts -> Effekte ab X sind
                                AUSGESCHLOSSEN. Eine echte Aussage.
            NICHT TRENNBAR      die Wirkung liegt ueber X, aber das Band
                                schliesst die Null ein - zu unpraezise
            KEIN BEFUND         zu wenige Bloecke, oder selbst die groesste
                                gepflanzte Staerke wurde nicht gefunden.
                                Eine Aussage ueber die MESSUNG, nicht ueber
                                die Welt - und sie wird nicht als
                                Nullbefund ausgegeben.

        ⚠️ Der Unterschied zwischen "TRAEGT NICHT BIS X" und "KEIN BEFUND"
        ist genau der, den zwei Tage lang gefehlt hat.
        """
        if self.n_bloecke < 20:
            return ("KEIN BEFUND - nur %d Bloecke, das Band deckt nicht "
                    "(bei 5 Bloecken 19,5 %% Fehlalarme statt 5 %%)"
                    % self.n_bloecke)
        # ⚠️ Ein zu kurzer Block macht das Band ZU ENG - dann waere ein
        # "TRAEGT" ein Scheinbefund. Das wiegt schwerer als zu wenige
        # Bloecke und steht deshalb direkt daneben.
        if self.protokoll is not None and not self.protokoll.block_ok:
            return ("KEIN BEFUND - Block %d zu kurz, Autokorrelation %.3f "
                    "(Grenze 0,15). Das Band waere zu eng."
                    % (self.protokoll.blocklaenge, self.protokoll.block_ak))
        # `traegt` STEHT VOR der Untermacht-Abfrage (2.193, 08.09.2026).
        # Vorher stand die None-Abfrage davor und verdeckte echte Befunde:
        # `schnitt` bei 20 % hatte Wirkung +0,1858 und `traegt` = True,
        # ausgegeben wurde "KEIN BEFUND". Eine zu kurze Leiter entwertet
        # einen NULLbefund - einen POSITIVEN nicht. Das Band schliesst den
        # Nullpunkt aus oder es tut es nicht; die Positivkontrolle aendert
        # daran nichts.
        # Die beiden Abfragen DAVOR (zu wenige Bloecke, Block zu kurz)
        # bleiben vorn - die entwerten das Band SELBST.
        if self.traegt:
            return "TRAEGT"
        if self.trennschaerfe is None:
            return ("KEIN BEFUND - untermaechtig: selbst %+.2f R gepflanzt "
                    "wurde nicht gefunden" % max(self.gepflanzt))
        einheit = ZIELGROESSEN[self.zielgroesse].get("einheit", "R")
        if abs(self.wirkung) < self.trennschaerfe:
            # ⚠️ `trennschaerfe` ist das GEMESSENE Niveau - nur so ist der
            # Vergleich mit `wirkung` zulaessig (Fehler 5). Die gepflanzte
            # Staerke steht daneben, sonst ist die Schranke nicht
            # nachvollziehbar.
            return ("TRAEGT NICHT bis %.4f %s%s (Effekte ab dieser Groesse "
                    "sind ausgeschlossen)"
                    % (self.trennschaerfe, einheit,
                       ("" if self.trennschaerfe_in_r is None
                        else " = %.2f gepflanzt" % self.trennschaerfe_in_r)))
        return ("NICHT TRENNBAR - Wirkung %+.4f ueber der Trennschaerfe "
                "%.4f %s, aber das Band schliesst die Null ein"
                % (self.wirkung, self.trennschaerfe, einheit))

    def zeile(self) -> str:
        return ("%-16s %-28s %-11s %-6s %+8.4f R [%+.4f .. %+.4f] · "
                "Null %+.4f · Trennsch. %s · %d Tage/%d Bl. · %d Sym · %s"
                % (self.kandidat, str(self.lage), self.zielgroesse, self.menge,
                   self.wirkung, self.unten, self.oben, self.nullpunkt,
                   ("%.4f" % self.trennschaerfe) if self.trennschaerfe
                   else "KEINE", self.n_tage, self.n_bloecke,
                   self.abdeckung_symbole, self.urteil))


def _block(horizont: int) -> int:
    """Der Block muss laenger sein als die ABHAENGIGKEIT - gemessen, nicht
    gesetzt (06.09.2026).

    ⚠️ `messe_regel_wirksamkeit` rechnet `max(90, 3 x HORIZONT)`. Der Boden
    von 90 Tagen ist eine SETZUNG, keine Messung - und er macht den einzigen
    vergleichbaren Marktabschnitt unmessbar:

        2024-2026 sind rund 960 Kalendertage
        Block 90 -> 10 Bloecke   unter der Grenze von 20, fuer JEDE Menge

    Nachgemessen (Autokorrelation der Tageswirkung, `schnitt50`):

        H     lag 1   lag 5   lag 10  lag 15  lag 30
         5    0,634   0,037  -0,032  -0,004  -0,024    weg nach 5 Tagen
        10    0,702   0,319   0,004  -0,020  -0,101    weg nach 10
        20    0,733   0,486   0,247   0,109  -0,064    weg nach 30

    **Die Abhaengigkeit reicht genau so weit wie der Horizont** - wie die
    Theorie ueberlappender Fenster es verlangt. `3 x Horizont` ist damit
    dreifach konservativ; der Boden von 90 ist es nicht, er ist willkuerlich.

    ⚠️ ABER: die Blocklaenge wird je Messung NACHGEPRUEFT (`pruefe_block`),
    nicht angenommen. Wer sie nur setzt, hat sie geraten.
    """
    return max(15, 3 * int(horizont))


def pruefe_block(d: dict, block: int, grenze: float = 0.15) -> dict:
    """Ist der Block laenger als die ABHAENGIGKEIT? — je Messung belegt.

    Gibt die Autokorrelation der Tageswirkung beim Abstand `block` zurueck.
    Liegt sie ueber `grenze`, ist der Block zu kurz und das Band zu eng.
    """
    tage = sorted(d)
    if len(tage) < block + 30:
        return {"lag": block, "ak": float("nan"), "ok": False,
                "grund": "zu wenige Tage fuer die Pruefung"}
    x = np.array([d[t] for t in tage], float)
    a, b = x[:-block], x[block:]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return {"lag": block, "ak": 0.0, "ok": True, "grund": "keine Streuung"}
    ak = float(np.corrcoef(a, b)[0, 1])
    return {"lag": block, "ak": ak, "ok": abs(ak) <= grenze,
            "grund": ("Abhaengigkeit abgeklungen" if abs(ak) <= grenze
                      else "⚠️ Block ZU KURZ - das Band waere zu eng")}


def pruefe(kandidat: str, je_tag: dict, *, lage: Lage, zielgroesse: str,
           menge: str, rng, frageart: str = "", horizont: int = 20,
           staerken: tuple = STAERKEN, hypothesen: int = 1,
           oben_sperren: bool = True, still: bool = True) -> Befund:
    """DIE eine Messung. Alles andere ruft sie.

    ⚠️ Sie benutzt `messe_regel_wirksamkeit.wirkung()` und
    `messe_bewertungskennzahl.urteil_tage()` — dieselben Funktionen, mit
    denen F-212 gerechnet und reproduziert wurde. Keine Nachbildung.
    """
    if zielgroesse not in ZIELGROESSEN:
        raise ValueError("unbekannte Zielgroesse: %r" % zielgroesse)
    block = _block(horizont)

    def _band(d, titel):
        if still:
            import io
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                return M.urteil_tage(titel, d, rng, block)
        return M.urteil_tage(titel, d, rng, block)

    d, _anteil, _g, _u = W.wirkung(je_tag, oben_sperren)
    haupt = _band(d, kandidat)
    if haupt is None:
        raise ValueError("zu wenige Tage fuer ein Band (%d)" % len(d))
    bp = pruefe_block(d, block)          # ⚠️ belegt, nicht angenommen

    # ⚠️ MEHRERE ZIEHUNGEN, NICHT EINE (06.09., gemessen).
    # Die Basislinie wandert je Saat zwischen -0,0055 und +0,0010 - also um
    # denselben Betrag wie die gesuchten Effekte. Eine Ziehung ist kein
    # Nullpunkt (Methodik 2.104).
    nullwerte, nullunten, nulloben = [], [], []
    for z in range(NULL_ZIEHUNGEN):
        n0, _a, _g2, _u2 = W.wirkung(
            je_tag, oben_sperren, mische=np.random.default_rng(SAAT + z))
        nb = _band(n0, "null %d" % z)
        if nb:
            nullwerte.append(nb["mittel"])
            nullunten.append(nb["unten"])
            nulloben.append(nb["oben"])
    # PERZENTIL, NICHT MAXIMUM (2.188). Siehe Kopf dieses Moduls.
    null = {"mittel": float(np.mean(nullwerte)) if nullwerte else 0.0,
            "unten": (float(np.percentile(nullunten, 100.0 - NULL_PERZENTIL))
                      if nullunten else 0.0),
            "oben": (float(np.percentile(nulloben, NULL_PERZENTIL))
                     if nulloben else 0.0)}

    # ⚠️ DIE TRENNSCHAERFE: die KLEINSTE gepflanzte Staerke, die gefunden
    # wird. Sie ist die eigentliche Neuerung - ohne sie ist "traegt nicht"
    # nicht von "haetten wir gar nicht sehen koennen" zu unterscheiden.
    # ⚠️⚠️ ZWEI SKALEN, NICHT EINE (Fehler 5, 08.09.2026).
    #
    # `s` ist die GEPFLANZTE Staerke. Die Anlage MISST davon aber nur
    # (1 - GRENZE) = 20 %: gesenkt werden die oberen 20 %, und
    # `median(alle)` verschiebt sich nur um diesen Anteil - `median(frei)`
    # gar nicht. An echten Daten nachgemessen: 20,3 / 20,1 / 19,6 / 19,2 %
    # fuer s = 0,05 / 0,10 / 0,20 / 0,40.
    #
    # `urteil` vergleicht `wirkung` (gemessen) mit `trennschaerfe`. Stand
    # dort die gepflanzte Zahl, war der Vergleich um Faktor 5 daneben und
    # der Satz "Effekte ab X sind ausgeschlossen" schlicht falsch.
    #
    #     trennschaerfe        das GEMESSENE Niveau -> mit `wirkung` vergleichbar
    #     trennschaerfe_in_r   die gepflanzte Staerke -> nachvollziehbar
    #
    # `messnorm_rand.py` trennt beide seit jeher so; hier wurde es
    # nachgezogen.
    trennschaerfe, trennschaerfe_in_r = None, None
    treffer = {}
    for s in sorted(staerken):
        # ⚠️ IN DIE GEMISCHTE WELT PFLANZEN (06.09., von der Gegenpruefung
        # gefunden).
        #
        # Die erste Fassung pflanzte auf die ECHTEN Daten obendrauf. Steckt
        # im Kandidaten schon ein Effekt, misst die Kontrolle dann
        # `Effekt + Pflanzung` statt der Pflanzung allein - und die
        # Trennschaerfe faellt zu gut aus. Sichtbar wurde es an einer
        # Kunstwelt mit 0,03 R Effekt: die Norm meldete "traegt nicht bis
        # 0,02 R", also eine Schranke UNTER dem tatsaechlich vorhandenen
        # Effekt. Ein Widerspruch in sich.
        #
        # `mische` zerstoert das echte Signal, `pflanze` legt ein bekanntes
        # hinein. Erst dann beantwortet die Zahl die Frage, die sie stellen
        # soll: haette diese Anlage einen Effekt DIESER Groesse gefunden?
        gefunden, werte = 0, []
        for z in range(ZIEHUNGEN):
            misch_rng = np.random.default_rng(SAAT + 1000 * z + int(s * 1000))
            p, _a2, _g3, _u3 = W.wirkung(je_tag, oben_sperren,
                                         mische=misch_rng, pflanze=s)
            pb = _band(p, "pflanze %.2f/%d" % (s, z))
            if pb:
                werte.append(pb["mittel"])
            # DERSELBE MASSSTAB WIE DAS URTEIL (2.188-inkonsistenz).
            latte = _bezug(null)
            if pb and pb["unten"] > latte:
                gefunden += 1
        treffer[s] = gefunden
        # ⚠️ MEHRHEIT, NICHT EIN TREFFER. Bei einer Ziehung entscheidet die
        # Saat - gemessen wanderte die Basislinie um den Betrag des
        # gesuchten Effekts.
        if trennschaerfe is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            trennschaerfe_in_r = s
            trennschaerfe = float(np.mean(werte)) if werte else None

    n_anker = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    return Befund(
        frageart=frageart,
        kandidat=kandidat, lage=lage, zielgroesse=zielgroesse, menge=menge,
        wirkung=haupt["mittel"], unten=haupt["unten"], oben=haupt["oben"],
        nullpunkt=null["mittel"], null_unten=null["unten"],
        null_oben=null["oben"], trennschaerfe=trennschaerfe,
        trennschaerfe_in_r=trennschaerfe_in_r,
        gepflanzt=tuple(sorted(staerken)), n_anker=n_anker,
        n_tage=haupt["tage"], n_bloecke=max(1, haupt["tage"] // block),
        abdeckung_symbole=syms, hypothesen=hypothesen,
        protokoll=Protokoll(
            wirkung_funktion="messe_regel_wirksamkeit.wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt",
            null_ziehungen=ZIEHUNGEN,
            positiv_konstruktion="in die gemischte Welt gepflanzt, "
                                 "auf die Gesperrten",
            positiv_ziehungen=ZIEHUNGEN, positiv_treffer=treffer,
            blocklaenge=block, saat=SAAT,
            block_ak=float(bp.get("ak", float("nan"))),
            block_ok=bool(bp.get("ok", True))))


# ------------------------------------------------------------- Selbsttest
def _welt(rng, tage=2400, syms=40, effekt=0.0):
    # ⚠️ 2400 TAGE, NICHT 900 (06.09., der Selbsttest hat es gefunden).
    # Der Block ist 3 x Horizont = 90 Tage; 900 Tage ergeben 10 Bloecke, und
    # bei unter 20 verweigert die Norm das Urteil - zu Recht (bei 5 Bloecken
    # 19,5 % Fehlalarme statt 5 %). Die Kunstwelt muss also mindestens so
    # gross sein wie die echte Anforderung, sonst prueft der Test die Norm
    # gar nicht, sondern nur ihre Schutzschwelle.
    """Kunstwelt: die obersten 20 % nach Kennzahl sind um `effekt` schlechter."""
    # ⚠️ NACH DEM RANG PFLANZEN, NICHT NACH DEM ROHWERT (06.09., von der
    # Gegenpruefung gefunden).
    #
    # Erste Fassung pflanzte auf `k >= 0.80`. `wirkung` sperrt aber nach dem
    # RANG innerhalb des Tages (`rang(w) >= GRENZE`). Bei 40 Symbolen fallen
    # beide Gruppen nur teilweise zusammen - der gepflanzte Effekt verduennt
    # sich, und die Kunstwelt prueft etwas anderes als das Werkzeug tut.
    # Sichtbar wurde es daran, dass eine Welt mit 0,03 R Effekt als "traegt
    # nicht bis 0,02 R" gemeldet wurde: eine Schranke UNTER dem vorhandenen
    # Effekt.
    je_tag = {}
    grenze = int(round(syms * 0.80))
    for t in range(tage):
        ks = [float(rng.random()) for _ in range(syms)]
        rs = [float(rng.normal(0, 1.0)) for _ in range(syms)]
        ordnung = sorted(range(syms), key=lambda i: ks[i])
        z = []
        for platz, i in enumerate(ordnung):
            r = rs[i] - (effekt if platz >= grenze else 0.0)
            z.append({"sym": "S%02d" % i, "kennzahl": ks[i], "in_r": r})
        je_tag["t%04d" % t] = z
    return je_tag


def selbsttest() -> bool:
    print("=" * 96)
    print("SELBSTTEST DER MESSNORM")
    print("=" * 96)
    ok = True
    L = Lage("spot", "einstieg")

    # 1 — die Lage
    print("\n1. Die AUSGANGSLAGE wird erzwungen")
    for inst, strat, erw in (("spot", "einstieg", True),
                             ("hebel", "akkumulation", False),
                             ("quatsch", "einstieg", False)):
        try:
            Lage(inst, strat)
            got = True
        except ValueError:
            got = False
        gut = got is erw
        ok &= gut
        print("   %-24s -> %-9s %s" % ("%s x %s" % (inst, strat),
                                       "erlaubt" if got else "abgelehnt",
                                       "OK" if gut else "✖"))
    try:
        Lage("spot", "einstieg", richtung="short")
        ok = False
        print("   short                    -> erlaubt   ✖ (muss abgelehnt werden)")
    except ValueError:
        print("   short                    -> abgelehnt OK")

    # ein gueltiges Protokoll, damit die anderen Pruefungen isoliert greifen
    def _prot(**aend):
        werte = dict(
            wirkung_funktion="messe_regel_wirksamkeit.wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt", null_ziehungen=5,
            positiv_konstruktion="in die gemischte Welt gepflanzt",
            positiv_ziehungen=5, positiv_treffer={0.02: 5},
            blocklaenge=90, saat=1)
        werte.update(aend)
        return Protokoll(**werte)

    def _befund(**aend):
        werte = dict(kandidat="x", lage=L, frageart="markt",
                     zielgroesse="bewegung_r", menge="frei",
                     wirkung=0.0, unten=0.0, oben=0.0,
                     nullpunkt=0.0, null_unten=0.0, null_oben=0.0,
                     trennschaerfe=0.02, gepflanzt=(0.02,), protokoll=_prot())
        werte.update(aend)
        return Befund(**werte)

    # 2 — die Zielgroesse an der Lage
    print("")
    print("2. 'barriere' nur, wo ein Stop den Trade beendet")
    for lage, erw in ((Lage("spot", "akkumulation"), False),
                      (Lage("hebel", "einstieg", simuliert=True), True)):
        try:
            _befund(lage=lage, frageart="markt", zielgroesse="barriere")
            got = True
        except ValueError:
            got = False
        ok &= got is erw
        print("   %-36s -> %-9s %s"
              % (lage, "erlaubt" if got else "abgelehnt",
                 "OK" if got is erw else "✖"))

    # 3 — DER WEG wird geprueft, nicht nur das Ergebnis
    #
    # ⚠️ Nutzerhinweis 06.09.: *„zur Urteilslogik gehoert nicht nur das
    # Ergebnis, sondern der Weg dorthin, wo die eigentlichen Fehler
    # passieren."* Jeder dieser sechs Irrwege hat am 05./06.09. eine
    # plausible Zahl erzeugt - keiner war am Ergebnis erkennbar.
    print("")
    print("3. Der WEG wird geprueft - sechs bekannte Irrwege")
    # ⚠️ TRAEGE, nicht vorgebaut: das Protokoll lehnt einen Irrweg schon bei
    # der eigenen Konstruktion ab. Wer die Faelle vorher baut, faellt beim
    # AUFBAU des Tests durch statt im Test.
    faelle = (
        ("ohne Protokoll", lambda: _befund(protokoll=None)),
        ("ohne Positivkontrolle",
         lambda: _befund(gepflanzt=(), trennschaerfe=None)),
        ("Pflanzung auf ECHTE Daten",
         lambda: _befund(protokoll=_prot(
             positiv_konstruktion="auf die echten Daten"))),
        ("Nullpunkt aus EINER Ziehung",
         lambda: _befund(protokoll=_prot(null_ziehungen=1))),
        ("mit Gebuehren gerechnet", lambda: _befund(kosten_je_seite=0.015)),
        ("gepoolt statt Tagesklammer", lambda: _befund(klammer="gepoolt")),
    )
    for name, bauen in faelle:
        try:
            bauen()
            ok = False
            print("   %-30s -> DURCHGELASSEN  ✖" % name)
        except ValueError:
            print("   %-30s -> abgelehnt      OK" % name)

    # 4 — die drei Urteile an Kunstwelten
    print("\n4. Die DREI Urteile")
    rng = np.random.default_rng(20260906)
    faelle = (("klarer Effekt +0,10 R", 0.10),
              ("kein Effekt", 0.0))
    for name, eff in faelle:
        b = pruefe("kunst", _welt(rng, effekt=eff), lage=L, frageart="markt",
                   zielgroesse="bewegung_r", menge="frei", rng=rng)
        print("   %-24s %+7.4f R · Trennsch. %s · %s"
              % (name, b.wirkung,
                 ("%.2f" % b.trennschaerfe) if b.trennschaerfe else "KEINE",
                 b.urteil))
        # ⚠️ DIE WIRKUNG IST KOMPRIMIERT. `wirkung` rechnet
        # median(frei) - median(alle); ein Effekt auf den obersten 20 %
        # verschiebt den Gesamtmedian nur zu einem Bruchteil. Geprueft wird
        # deshalb das URTEIL, nicht die Hoehe.
        if eff > 0 and b.urteil != "TRAEGT":
            ok = False
            print("      ✖ ein gepflanzter Effekt muss gefunden werden")
        if eff == 0 and b.urteil == "TRAEGT":
            ok = False
            print("      ✖ ohne Effekt darf nichts tragen")
        if eff == 0 and not b.urteil.startswith("TRAEGT NICHT"):
            ok = False
            print("      ✖ ohne Effekt muss eine SCHRANKE herauskommen, "
                  "kein Achselzucken")

    # 5 — untermaechtig wird als KEIN BEFUND ausgewiesen
    print("\n5. Wenige Tage -> KEIN BEFUND statt 'traegt nicht'")
    b = pruefe("kunst_kurz", _welt(rng, tage=200), lage=L, frageart="markt",
               zielgroesse="bewegung_r", menge="frei", rng=rng)
    gut = b.urteil.startswith("KEIN BEFUND")
    ok &= gut
    print("   %d Tage / %d Bloecke -> %s  %s"
          % (b.n_tage, b.n_bloecke, b.urteil, "OK" if gut else "✖"))

    print()
    print("=" * 96)
    print("SELBSTTEST %s" % ("BESTANDEN" if ok else "✖ FEHLGESCHLAGEN"))
    print("=" * 96)
    return ok


if __name__ == "__main__":
    sys.exit(0 if selbsttest() else 1)
