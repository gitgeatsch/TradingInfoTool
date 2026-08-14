# -*- coding: utf-8 -*-
"""Die BERECHNUNG DER ENTSCHEIDUNG - alle Zahlen eines Handels an einer Stelle.

BENENNUNG (Nutzer, 12.08.2026): *"ich verwechsle laufend Rolle Entscheider mit
Entscheidung - u.U. sollte man 'Berechnung der Entscheidung' sagen."* Richtig,
und "Entscheider" ist ab hier abgeschafft. Es gibt das URTEIL (Rolle BC: ob
ueberhaupt, warum, was es widerlegen wuerde) und die RECHNUNG (dieses Modul:
wo, wieviel, wie lange, mit welchem Hebel). Zwei Dinge, zwei Namen.

WARUM ES DIESES MODUL GIBT. Nutzer am 12.08.: *"Wir muessen das Thema gut
abarbeiten sonst gibt es wieder Empfehlungen mit 1500 Euro und 1,5 Prozent Stop
loss."* Beide Fehler sind DERSELBE Fehler - eine Zahl ohne Herkunft und ohne
Grenze. Das Sprachmodell hat sie genannt, weil es gefragt wurde; niemand hat
geprueft, ob sie irgendwo herkommen.

Deshalb hat hier jede Zahl DREI Dinge: eine Formel, eine Quelle fuer ihre
Parameter, und ZWEI Grenzen. Eine Untergrenze allein reicht nicht - ein Stop
von 40 % ist genauso unsinnig wie einer von 1,5 %, nur faellt er niemandem auf,
weil er "vorsichtig" aussieht.

WAS DAS MODELL BEITRAEGT - UND WAS NICHT. Kapitel 11.6 der Fakten-
Entscheidungsmappe listet unter "Was das Modell NIE sieht" ausdruecklich
`Positionsgroesse, Betraege, Deckel`, `Einstieg und Stop als Zahl`
(Anchoring-Index 0,45, Experten-Anker wirken am staerksten) und
`Risikoparameter jeder Art`. Der Live-Lauf vom 12.08. hat gezeigt, warum:
gefragt nach einem Stop, nannte das Modell 1,26 % - im gemessenen Band mit
0,0 % Trefferquote ueber 9 Trades.

ES TRAEGT TROTZDEM ZWEI ZAHLEN BEI, und zwar genau die zwei, die es als URTEIL
liefert statt als Schaetzung: `umgeworfen_preis_eur` (wo die eigene Begruendung
nicht mehr traegt) und `umgeworfen_bis` (bis wann sie gelten soll). Der
Unterschied liegt in der FRAGE, nicht in der Zahl - siehe `_stop_abstand()`.
Beide werden geklemmt: ein Urteil ueber die These weiss nichts ueber das
Rauschen des Symbols.

KEIN STILLES DURCHRUTSCHEN. Fehlt eine Eingabe, kommt KEINE Empfehlung - nicht
eine geratene. `blockiert` traegt dann den Grund im Klartext. Eine Rechnung, die
bei fehlendem ATR "irgendwas" zurueckgibt, ist gefaehrlicher als gar keine.
"""
from __future__ import annotations

import math

from agent.krypto.hebel_risk_gate import max_safe_hebel

# ---------------------------------------------------------------------------
# DIE GRENZEN. Jede mit Quelle - wer eine aendert, muss die Quelle mitaendern.
GRENZEN = {
    # STOP. Der Zielwert 2,5 x ATR liegt zwischen den beiden Praxisstandards
    # (Chandelier 3 x ATR, Elder 2 x ATR) und trifft bei BTC rund 7,5 % - genau
    # den Bereich, den der Nutzer aus der Praxis nennt ("ca. 10 Prozent") und
    # den der Backtest vom 28.07. als einzigen ueber der Gewinnschwelle ausweist
    # (5-10 %: 31,2 % Trefferquote, +0,31 CRV).
    "stop_ziel_atr": 2.5,
    "stop_min_relativ": 0.025,      # RM-1b, config risiko.sl_abstand_eng_schwelle_relativ
    "stop_min_atr": 0.75,           # RM-1c, config risiko.sl_abstand_min_atr_faktor
    # OBERGRENZE - NEU, es gab bisher keine. Ein Stop von 40 % faellt durch
    # jede Untergrenze und ruiniert trotzdem die Rechnung: er macht die
    # Position winzig (Risikobudget durch grossen Nenner) und die Haltedauer
    # unbegrenzt. 25 % ist rund 8 x ATR bei Krypto - jenseits davon ist es
    # kein Stop mehr, sondern ein Verzicht auf einen.
    "stop_max_relativ": 0.25,

    "crv": 2.0,                     # risiko.crv_minimum
    "zone_atr": 0.25,               # Breite der Einstiegszone, halbe Seite

    # DIE CRV-ABSTUFUNG, aus der alten Kette uebernommen (13.08.2026) -
    # identisch zu `risiko.crv_positionsgroesse_spreizung` und `..._voll_ab`.
    # Begruendung in `_crv_faktor()`.
    "crv_spreizung": 5.0,
    "crv_voll_ab": 6.0,

    "hebel_max": 10.0,              # Bitpanda Margin: 2x-10x
    "liquidations_marge": 0.09,     # RM-11, config risiko.hebel.*_sicherheitsmarge_relativ

    # BETRAG. Die Untergrenze ist keine Vorsicht, sondern Arithmetik: bei
    # Boersengeschaeften kostet 1 EUR fix je Seite, auf 100 EUR sind das 2 %
    # Roundtrip allein aus der Fixgebuehr.
    "betrag_min_eur": 100.0,
    "betrag_max_eur": 1000.0,       # Nutzer 12.08.: "500 - max 1000 aktuell"

    # HALTEDAUER. Obergrenze aus der Ablauffrist des Backward-Trackings - was
    # laenger laeuft, wird nie ausgewertet und ist damit unmessbar.
    "tage_max": 120,
}


class RechnungBlockiert(ValueError):
    """Eine Eingabe fehlt oder eine Grenze ist verletzt - es gibt kein Ergebnis."""


def _stop_abstand(kurs: float, atr: float,
                  umgeworfen_preis_eur: float | None = None,
                  ist_short: bool = False) -> tuple[float, str]:
    """Der Stopabstand in Euro, plus die Regel, die ihn bestimmt hat.

    DIE TRADINGSTANDARDS KENNEN ZWEI SCHULEN, und die Praxis kombiniert sie:

      volatilitaetsbasiert   Chandelier Exit 3 x ATR (Le Beau), Elder 2 x ATR,
                             Van Tharp allgemein ATR-Vielfache. Vorteil: passt
                             sich dem Rauschen des Symbols an. Nachteil: kennt
                             die Struktur des Kurses nicht.
      strukturbasiert        unter das letzte Swing-Tief / die naechste
                             Unterstuetzung. Vorteil: dort ist die These
                             tatsaechlich widerlegt. Nachteil: kann beliebig
                             eng werden, wenn die Struktur nah liegt.

    Der Standard ist die KOMBINATION: an die Struktur, aber nie enger als der
    Rauschboden. Genau so ist es hier gebaut.

    UND HIER KOMMT DAS SPRACHMODELL DOCH INS SPIEL - an der einen Stelle, wo es
    hingehoert. `umgeworfen_preis_eur` ist die Antwort auf "welche einzelne
    Beobachtung wuerde deine Entscheidung als falsch erweisen". Das ist kein
    Risikoparameter, den das Modell schaetzen soll (Kapitel 11.6 verbietet das
    zu Recht) - es ist die Stelle, an der seine eigene Begruendung nicht mehr
    traegt. Die Fakten-Entscheidungsmappe sagt es selbst: *"Das ist ein Urteil,
    keine Rechnung - deshalb gehoert es zum Modell."* Und weiter: es werde
    *"heute von niemandem ausgewertet"*.

    Der Unterschied zum 1,26-%-Stop ist NICHT die Zahl, sondern die Frage. Auf
    "wo setzt du den Stop?" antwortet ein Sprachmodell mit einem Risikoparameter,
    den es nicht schaetzen kann. Auf "was widerlegt dich?" antwortet es mit
    einem Urteil ueber die eigene Begruendung - und das ist seine Aufgabe.

    ES BLEIBT GEKLEMMT. Ein Urteil ueber die These sagt nichts ueber das
    Rauschen des Symbols; liegt der Widerlegungspreis innerhalb des Rauschens,
    gilt der Rauschboden. Damit kann aus dieser Quelle kein 1,5-%-Stop werden,
    auch wenn das Modell einen nennt."""
    min_abstand = max(GRENZEN["stop_min_relativ"] * kurs,
                      GRENZEN["stop_min_atr"] * atr)
    max_abstand = GRENZEN["stop_max_relativ"] * kurs

    # BEI SHORT LIEGT DER WIDERLEGUNGSPREIS UEBER DEM KURS (Paket 13). Die
    # These "es faellt" ist widerlegt, wenn es steigt - der Abstand wird
    # deshalb andersherum gebildet. Wer das vergisst, bekommt bei jedem
    # SHORT einen negativen Abstand und faellt still auf den ATR-Stop zurueck.
    if isinstance(umgeworfen_preis_eur, (int, float)) and umgeworfen_preis_eur > 0:
        abstand = ((float(umgeworfen_preis_eur) - kurs) if ist_short
                   else (kurs - float(umgeworfen_preis_eur)))
        if abstand <= 0:
            return _stop_aus_atr(kurs, atr)
        if abstand < min_abstand:
            return min_abstand, "Widerlegungspreis lag im Rauschen - RM-1b/1c"
        if abstand > max_abstand:
            return max_abstand, f"Widerlegungspreis zu weit - Obergrenze {100 * GRENZEN['stop_max_relativ']:.0f} %"
        return abstand, "Widerlegungspreis des Modells"

    return _stop_aus_atr(kurs, atr)


def _stop_aus_atr(kurs: float, atr: float) -> tuple[float, str]:
    """Der Stopabstand in Euro, plus die Regel, die ihn bestimmt hat.

    Reihenfolge: erst der Zielwert aus dem ATR, dann nach unten und oben
    beschnitten. Die Untergrenze ist die STRENGERE von RM-1b und RM-1c, also
    der GROESSERE geforderte Abstand - das war am 12.08. schon einmal falsch
    herum gebaut."""
    ziel = GRENZEN["stop_ziel_atr"] * atr
    min_abstand = max(GRENZEN["stop_min_relativ"] * kurs,
                      GRENZEN["stop_min_atr"] * atr)
    max_abstand = GRENZEN["stop_max_relativ"] * kurs

    if ziel < min_abstand:
        return min_abstand, "RM-1b/1c: Untergrenze"
    if ziel > max_abstand:
        return max_abstand, f"Obergrenze {100 * GRENZEN['stop_max_relativ']:.0f} % des Kurses"
    return ziel, f"{GRENZEN['stop_ziel_atr']:g} x ATR"


def _ziel(kurs: float, abstand: float, atr: float,
          widerstand: tuple[float, int] | None = None,
          ist_short: bool = False) -> tuple[float, float, str]:
    """Der Zielkurs, die daraus folgende CRV und die Regel dahinter.

    WARUM NICHT EINFACH 2 R. Ein mechanisches 2-R-Ziel weiss nichts davon, ob
    auf dem Weg dorthin eine Marke liegt, an der schon dreimal verkauft wurde.
    Der Praxisstandard setzt das Ziel KURZ UNTER den naechsten Widerstand -
    dort stehen die Verkaufsauftraege, und wer die letzten Cent mitnehmen will,
    bekommt gar nichts. `_niveaus()` liefert diese Marken samt Zahl der
    Beruehrungen; ein dreimal bestaetigtes Niveau ist etwas anderes als ein
    einmaliger Wendepunkt.

    UND DANN KANN DAS GESCHAEFT DARAN SCHEITERN. Liegt der Widerstand so nah,
    dass davor keine 2,0 mehr uebrig bleiben, ist der Aufbau nicht schlecht
    beschrieben - er ist arithmetisch zu klein. Das wird AUSGEWIESEN, nicht
    stillschweigend auf 2,0 hochgerechnet: `crv` traegt dann den echten Wert
    und `crv_erreicht` ist False. Ein Ziel, das hinter einer Mauer liegt, ist
    kein Ziel.

    Liegt der Widerstand jenseits des mechanischen Ziels, bleibt es beim
    mechanischen - dann steht die Mauer nicht im Weg."""
    richtung = -1.0 if ist_short else 1.0
    ziel_mech = kurs + richtung * GRENZEN["crv"] * abstand
    if not widerstand:
        return ziel_mech, GRENZEN["crv"], "kein Widerstand in Reichweite"

    preis, beruehrungen = float(widerstand[0]), int(widerstand[1])
    # Bei SHORT ist die Marke im Weg eine UNTERSTUETZUNG, und sie liegt
    # zwischen Ziel und Kurs - also andersherum eingeklammert.
    dazwischen = (ziel_mech < preis < kurs) if ist_short else (kurs < preis < ziel_mech)
    if not dazwischen:
        return ziel_mech, GRENZEN["crv"], "naechster Widerstand liegt dahinter"

    # Kurz DAVOR aussteigen, nicht daran. Ein Viertel Schwankungsbreite ist
    # dieselbe Breite wie die Einstiegszone - keine neue Groesse.
    ziel = preis - richtung * GRENZEN["zone_atr"] * atr
    crv = richtung * (ziel - kurs) / abstand if abstand > 0 else 0.0
    # BEI SHORT IST DIE MARKE IM WEG EINE UNTERSTUETZUNG. Sie "Widerstand" zu
    # nennen waere nicht nur unsauber - es waere die falsche Richtung: ein
    # Widerstand liegt ueber dem Kurs, diese Marke liegt darunter.
    marke = "der Unterstuetzung" if ist_short else "dem Widerstand"
    return ziel, crv, (f"vor {marke} bei {_eur(preis)} EUR "
                       f"({beruehrungen}-mal beruehrt)")


def _haltedauer_tage(weg: float, atr: float) -> int:
    """Geschaetzte Handelstage bis zum Ziel.

    ES IST EINE SCHAETZUNG, KEIN MESSWERT, und sie steht auf einer Annahme, die
    dieses Projekt anderswo bewusst NICHT macht: driftfreier Pfad. Auf einem
    solchen waechst die zurueckgelegte Strecke mit der WURZEL der Zeit, die
    Zeit also mit dem QUADRAT der Strecke. Fuenf Tagesschwankungen Weg heissen
    rund 25 Tage, nicht fuenf.

    Warum trotzdem: die Zahl entscheidet bei Hebel ueber die Finanzierung und
    damit ueber die halbe Kostenrechnung. Eine ausgewiesene Schaetzung ist
    besser als ein stillschweigendes "ein paar Tage". Sie gehoert gegen die
    eigenen Reihen nachgerechnet - offener Punkt."""
    if atr <= 0:
        return GRENZEN["tage_max"]
    return int(min(GRENZEN["tage_max"], max(1, round((weg / atr) ** 2))))


def _crv_faktor(crv: float, instrument: str) -> float:
    """Wieviel der vollen Groesse bei diesem CRV - stufenlos von 1/Spreizung
    bei CRV 2,0 auf 1,0 bei CRV 6,0.

    AUS DER ALTEN KETTE UEBERNOMMEN, und zwar als EINZIGE ihrer
    Positionsgroessen-Regeln. Der Grund ist eine Messung an 298 Spot-Signalen,
    die in `risk_gate.py` dokumentiert ist:

        SQN           +0,63  ->  +1,36
        Summe         +9,8 R ->  +23,1 R
        Rueckschlag   36,3 R ->  27,1 R

    Besseres Ergebnis bei KLEINEREM Risiko. Vor der Abstufung bekamen ein CRV
    von 2,5 und eines von 6,0 dieselbe Groesse.

    NUR SPOT, und das ist keine Nachlaessigkeit. Dieselbe Untersuchung fand
    beim Hebel die GEGENLAEUFIGE Antwort (Gate behalten, SQN +3,25 gegen +1,25
    fuer jede Groessen-Variante). Sie dort anzuwenden hiesse, eine Messung
    gegen ihr eigenes Ergebnis zu uebertragen.

    SICHER DURCH BAUFORM: der Faktor ist hoechstens 1,0, kann also nur
    verkleinern. Eine Ueberexposition ist ausgeschlossen, nicht bloss
    unwahrscheinlich. Abschalten ueber `crv_spreizung = 1.0`."""
    spreizung, voll_ab = GRENZEN["crv_spreizung"], GRENZEN["crv_voll_ab"]
    # NUR SPOT - ausdruecklich, nicht "alles ausser Hebel" (14.08.2026).
    #
    # Die erste Fassung fragte `instrument == "hebel"` ab und traf damit auch
    # die ABSICHERUNG: 500 EUR waeren bei CRV 2,0 auf 100 geschrumpft. Das ist
    # in zweifacher Hinsicht falsch. Die Messung lief an 298 SPOT-Signalen, nie
    # an Absicherungen. Und eine Absicherung bemisst sich am abzusichernden
    # Exposure (`toepfe.einsatz_fuer_absicherung`), nicht an einem CRV - eine
    # auf ein Fuenftel gekuerzte Absicherung schuetzt ein Fuenftel dessen, was
    # sie soll. Das ist das Gegenteil einer Sicherheitsmassnahme.
    #
    # Eine Ausschlussliste faengt nur, was jemand vorhergesehen hat; eine
    # Einschlussliste nur, was jemand gemessen hat. Hier ist die zweite richtig.
    if instrument != "spot" or spreizung <= 1.0 or voll_ab <= GRENZEN["crv"]:
        return 1.0
    spanne = max(0.0, min(1.0, (crv - GRENZEN["crv"]) / (voll_ab - GRENZEN["crv"])))
    sockel = 1.0 / spreizung
    return sockel + (1.0 - sockel) * spanne


def rechne(*, kurs: float | None, atr: float | None, risiko_eur: float | None,
           instrument: str = "spot", betrag_wunsch_eur: float | None = None,
           topf_frei_eur: float | None = None,
           cash_frei_eur: float | None = None,
           umgeworfen_preis_eur: float | None = None,
           umgeworfen_tage: int | None = None,
           widerstand: tuple[float, int] | None = None,
           ist_short: bool = False) -> dict:
    """Alle Zahlen eines Einstiegs aus drei Eingaben: Kurs, ATR, Risikobudget.

    `risiko_eur` ist der Betrag, den DIESER eine Handel im schlechtesten Fall
    kosten darf - nicht ein Prozentsatz. Bewusst absolut, aus demselben Grund
    wie bei den Toepfen (Paket 5): ein Prozentsatz auf ein Portfolio, das 70 %
    im Minus steht, schrumpft genau dann, wenn er gebraucht wird.

    `betrag_wunsch_eur` ist die gewuenschte Positionsgroesse. Sie bestimmt
    zusammen mit dem Risikobudget den HEBEL - nicht umgekehrt. Das entspricht
    der Denkweise des Nutzers ("der Betrag ca. 500") und macht die einzige
    Groesse, die er im Kopf hat, zur Eingabe statt zur Ausgabe."""
    fehlt = [n for n, w in (("Kurs", kurs), ("ATR", atr),
                            ("Risikobudget", risiko_eur)) if not w or w <= 0]
    if fehlt:
        raise RechnungBlockiert(f"{', '.join(fehlt)} fehlt - keine Empfehlung")

    kurs, atr, risiko_eur = float(kurs), float(atr), float(risiko_eur)
    abstand, stop_regel = _stop_abstand(kurs, atr, umgeworfen_preis_eur, ist_short)
    stop_rel = abstand / kurs
    ziel, crv, ziel_regel = _ziel(kurs, abstand, atr, widerstand, ist_short)

    e = {
        "ist_short": bool(ist_short),
        "einstieg_eur": round(kurs, 2),
        "einstieg_von_eur": round(kurs - GRENZEN["zone_atr"] * atr, 2),
        "einstieg_bis_eur": round(kurs + GRENZEN["zone_atr"] * atr, 2),
        "stop_eur": round(kurs - (-abstand if ist_short else abstand), 2),
        "stop_relativ": round(stop_rel, 5),
        "stop_regel": stop_regel,
        "ziel_eur": round(ziel, 2),
        "ziel_von_eur": round(ziel - GRENZEN["zone_atr"] * atr, 2),
        "ziel_bis_eur": round(ziel + GRENZEN["zone_atr"] * atr, 2),
        "crv": round(crv, 2),
        "crv_erreicht": crv >= GRENZEN["crv"] - 1e-9,
        "ziel_regel": ziel_regel,
        "haltedauer_tage": (min(int(umgeworfen_tage), GRENZEN["tage_max"])
                            if isinstance(umgeworfen_tage, int) and umgeworfen_tage > 0
                            else _haltedauer_tage(ziel - kurs, atr)),
        "haltedauer_quelle": ("Frist des Modells"
                              if isinstance(umgeworfen_tage, int) and umgeworfen_tage > 0
                              else "geschaetzt aus Weg und Schwankung"),
        "risiko_eur": round(risiko_eur, 2),
    }

    # BETRAG UND HEBEL HAENGEN ZUSAMMEN: Risiko = Betrag x Hebel x Stopabstand.
    # Zwei der drei sind vorgegeben (Risiko als Budget, Betrag als Wunsch), der
    # dritte folgt. Bei Spot ist der Hebel per Definition 1, dann folgt der
    # BETRAG aus dem Risiko - dort gibt es keinen Wunsch, nur eine Rechnung.
    # ERST DIE DECKEL, DANN DER HEBEL. Andersherum gebaut blieb nach einem
    # greifenden Topf-Deckel das halbe Risikobudget ungenutzt (38 statt 75 EUR),
    # weil der Hebel auf den WUNSCHBETRAG gerechnet worden war und danach
    # niemand mehr nachzog. Der Deckel begrenzt den EINSATZ; wieviel Risiko auf
    # diesem Einsatz liegt, entscheidet danach der Hebel.
    betrag = float(betrag_wunsch_eur) if betrag_wunsch_eur else GRENZEN["betrag_min_eur"] * 5
    grund = None
    # BEI SPOT IST DER WUNSCH DIE ANTWORT, NICHT DIE RECHNUNG (14.08.2026).
    #
    # Hier stand: "Ohne Hebel gibt es keinen Wunsch, nur eine Rechnung: der
    # Einsatz folgt vollstaendig aus Risikobudget und Stopabstand." Das ist die
    # Lehrbuchantwort - und sie setzt eine STOP-ORDER voraus.
    #
    # DER NUTZER HAELT SPOT OHNE STOP-LOSS ("aktuell auch ohne StopLoss"),
    # laengerfristig, in Tranchen. Ohne Stop gibt es keine Groesse, die aus ihm
    # folgen koennte - die Tranche IST die Eingabe, und die 250 bzw. 800 EUR
    # sind genau das, was er investieren will.
    #
    # GEFUNDEN IM ERSTEN LAUF UEBER DEN ECHTEN JOB, an einer Mail:
    #     Tranche 800 -> Risiko 800 x 15 % = 120 -> Betrag 120 / 2,5 % = 4.800
    #     -> CRV-Abstufung x 0,2 = 960 EUR
    # In der Mail stand 960, wo der Nutzer 800 gesagt hatte - und bei 4 % Stop
    # waeren es 600 gewesen. Der Betrag haette am Stopabstand gehangen statt an
    # seiner Entscheidung.
    #
    # DAS RISIKO FOLGT JETZT UMGEKEHRT: Betrag x Stopabstand. Bei einer Position
    # ohne Stop-Order ist es ohnehin eine Rechengroesse, keine Order.
    if instrument != "hebel":
        # Der WERT folgt erst nach den Deckeln - siehe unten. Hier steht nur,
        # dass er folgt und nicht vorgegeben ist.
        e["risiko_quelle"] = "folgt aus Betrag und Stopabstand"
    # DIE CRV-ABSTUFUNG ZUERST, dann die Deckel. Sie beschreibt, wieviel der
    # Aufbau VERDIENT; Topf und Hoechstbetrag, wieviel er BEKOMMEN darf. Zwei
    # verschiedene Fragen, und die zweite gehoert nach der ersten.
    _faktor = _crv_faktor(crv, instrument)
    if _faktor < 1.0:
        betrag, grund = betrag * _faktor, f"CRV-Abstufung ({crv:.2f})"
    e["crv_groessenfaktor"] = round(_faktor, 3)
    if topf_frei_eur is not None and betrag > float(topf_frei_eur):
        betrag, grund = float(topf_frei_eur), "Topf"
    # RM-4 MIT EIGENEM GRUND, nicht in den Topf hineingerechnet. Beide
    # begrenzen, aber aus verschiedenen Anlaessen - waeren sie ein Wert, sagte
    # die Notiz "Topf", wo in Wahrheit das Geld fehlt.
    if cash_frei_eur is not None and betrag > float(cash_frei_eur):
        betrag, grund = float(cash_frei_eur), "Cash-Reserve (RM-4)"
    if betrag > GRENZEN["betrag_max_eur"]:
        betrag, grund = GRENZEN["betrag_max_eur"], "Hoechstbetrag"
    # DIE ABSTUFUNG DARF NICHT ZUM STILLEN FILTER WERDEN (14.08.2026).
    #
    # Gerechnet an der Akkumulations-Tranche von 250 EUR: bei CRV 2,0 macht die
    # CRV-Abstufung daraus 50 EUR - unter der Mindestgroesse, also
    # `RechnungBlockiert`. Damit waere JEDES Tranchen-Signal unter CRV 4,0
    # lautlos verschwunden, und in den gemessenen Laeufen lagen die meisten CRV
    # bei genau 2,0.
    #
    # Ein Deckel, der ein Signal ganz zum Verschwinden bringt, ist kein Deckel
    # mehr, sondern ein Veto - und ein unsichtbares dazu. Deshalb wird auf die
    # Mindestgroesse ANGEHOBEN statt abgebrochen: die Empfehlung geht raus, in
    # der kleinsten Groesse, die sich rechnet. Die Richtung der Abstufung bleibt
    # erhalten, ihr unteres Ende ist nur abgeschnitten.
    #
    # ABGEBROCHEN WIRD WEITERHIN, wenn schon der WUNSCH zu klein war - dann hat
    # niemand eine Abstufung angewandt, sondern es ist schlicht zu wenig Geld.
    if (betrag < GRENZEN["betrag_min_eur"]
            and grund and grund.startswith("CRV-Abstufung")
            and float(betrag_wunsch_eur or 0) >= GRENZEN["betrag_min_eur"]):
        betrag = GRENZEN["betrag_min_eur"]
        grund = f"{grund}, auf Mindestgroesse angehoben"
    if betrag < GRENZEN["betrag_min_eur"]:
        raise RechnungBlockiert(
            f"Betrag {betrag:.0f} EUR unter der Mindestgroesse "
            f"{GRENZEN['betrag_min_eur']:.0f} EUR - bei dieser Groesse frisst "
            f"die Fixgebuehr das Risikobudget")

    if instrument == "hebel":
        hebel_noetig = risiko_eur / (betrag * stop_rel)
        sicher = max_safe_hebel(100 * stop_rel, GRENZEN["liquidations_marge"])
        hebel = max(1.0, min(hebel_noetig, sicher, GRENZEN["hebel_max"]))
        e["hebel"] = round(hebel, 1)
        e["hebel_grenze"] = (
            "Risikobudget" if hebel <= hebel_noetig + 1e-9
            else ("RM-11 Liquidationsabstand" if sicher < GRENZEN["hebel_max"]
                  else "Hoechsthebel"))
        # Bei SHORT liegt die Liquidation UEBER dem Einstieg.
        e["liquidation_etwa_eur"] = round(
            kurs * (1 + 1 / hebel) if ist_short else kurs * (1 - 1 / hebel), 2)
    else:
        e["hebel"] = 1.0

    e["betrag_eur"] = round(betrag, 0)
    e["betrag_gedeckelt_durch"] = grund
    # DAS RISIKO ERST JETZT, NACH ALLEN DECKELN (14.08.).
    #
    # Die erste Fassung rechnete es aus dem Betrag VOR der CRV-Abstufung: in
    # der Pruefung stand "Risiko 100 EUR auf 400 EUR bei 5 % Stop" - das waeren
    # 25 %, und niemand haette gesehen, dass die Zahl zu einer Groesse gehoert,
    # die es nicht mehr gibt. `verlust_am_stop_eur` war die ganze Zeit richtig,
    # weil es den Endbetrag nimmt; die beiden haetten sich widersprochen.
    if instrument != "hebel":
        e["risiko_eur"] = round(betrag * stop_rel, 2)
    # Was der Handel WIRKLICH riskiert, nachdem die Deckel gegriffen haben -
    # nicht das Budget, das hineingegeben wurde.
    e["verlust_am_stop_eur"] = round(betrag * e["hebel"] * stop_rel, 2)
    e["gewinn_am_ziel_eur"] = round(betrag * e["hebel"] * crv * stop_rel, 2)
    return e


def _eur(wert: float, stellen: int = 0) -> str:
    """Deutsche Schreibweise - siehe signal_mail.eur() fuer die Begruendung."""
    return f"{wert:,.{stellen}f}".translate(str.maketrans(",.", ".,"))


def preis(wert: float) -> str:
    """Ein KURS in deutscher Schreibweise - mit so vielen Stellen, wie er
    braucht.

    DER FUND, DER DIESE FUNKTION ERZWUNGEN HAT (14.08.2026, erste echte
    Produktionsmail, PLUME bei 0,0119 EUR):

        Einstiegszone   0 bis 0 EUR
        Stop            0 EUR  (5,5 % - ...)
        Take-Profit     0 bis 0 EUR

    Die Rechnung war richtig, die Darstellung hat sie vernichtet. `_eur()`
    hatte eine FESTE Stellenzahl - null fuer Kurse, zwei im Kopf der Mail. Bei
    einem Wert unter einem Cent bleibt davon nichts uebrig, und der Nutzer
    bekommt eine Kaufempfehlung ohne Einstieg, ohne Stop und ohne Ziel.

    DASS ES NIEMANDEM AUFFIEL, hat einen Grund: die Zahlen im Urteilstext
    stammen vom Modell und werden NICHT durch diesen Formatierer geschickt -
    dort stand korrekt "Widerstand bei 0.0119 EUR". In derselben Mail. Zwei
    Zahlenwege, einer davon kaputt.

    DIE REGEL: mindestens vier signifikante Stellen, hoechstens acht
    Nachkommastellen, und nie weniger als zwei. Ein Bitcoin-Kurs bleibt damit
    "61.234,50", ein Sub-Cent-Wert wird "0,011900" statt "0".

    NICHT NUR EIN KRYPTO-THEMA: dieselbe Falle trifft jeden Wert unter einem
    Euro, also auch Small Caps und jeden Cent-Wert im Aktienteil."""
    import math as _m

    w = abs(float(wert))
    if w >= 1.0 or w == 0:
        # Ab einem Euro sind zwei Stellen die gewohnte Schreibweise - mehr
        # waere Genauigkeit, die niemand braucht ("2,340 EUR" liest sich falsch).
        stellen = 2
    else:
        # Darunter zaehlen SIGNIFIKANTE Stellen, nicht Nachkommastellen: bei
        # 0,0119 sind vier davon fuenf Nachkommastellen, bei 0,000043 acht.
        stellen = min(8, 4 - 1 - int(_m.floor(_m.log10(w))))
    return f"{float(wert):,.{stellen}f}".translate(str.maketrans(",.", ".,"))


def saetze(e: dict) -> list[str]:
    """Die Rechnung in der Form, in der sie in die E-Mail gehoert."""
    z = [f"Einstiegszone   {preis(e['einstieg_von_eur'])} bis {preis(e['einstieg_bis_eur'])} EUR",
         f"Stop            {preis(e['stop_eur'])} EUR  ({_eur(100 * e['stop_relativ'], 1)} % - {e['stop_regel']})",
         f"Take-Profit     {preis(e['ziel_von_eur'])} bis {preis(e['ziel_bis_eur'])} EUR  "
         f"(CRV {_eur(e['crv'], 1)} - {e['ziel_regel']})"]
    if not e["crv_erreicht"]:
        z.append(f"                !! Der Weg bis dorthin traegt nur CRV "
                 f"{_eur(e['crv'], 1)}, verlangt sind {_eur(GRENZEN['crv'], 1)}")
    z += [
         f"Haltedauer      etwa {e['haltedauer_tage']} Handelstage "
         f"({e.get('haltedauer_quelle', 'geschaetzt')})",
         f"Betrag          {_eur(e['betrag_eur'])} EUR"
         + (f"  - begrenzt durch {e['betrag_gedeckelt_durch']}"
            if e.get("betrag_gedeckelt_durch") else "")]
    if e["hebel"] > 1:
        z.append(f"Hebel           {_eur(e['hebel'], 1)}x  (Grenze: {e['hebel_grenze']}; "
                 f"Liquidation etwa {preis(e['liquidation_etwa_eur'])} EUR)")
    z.append(f"Am Stop verlieren Sie {_eur(e['verlust_am_stop_eur'])} EUR, "
             f"am Ziel gewinnen Sie {_eur(e['gewinn_am_ziel_eur'])} EUR.")
    return z
