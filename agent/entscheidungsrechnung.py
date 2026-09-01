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
from agent.schreibweise import de

# ---------------------------------------------------------------------------
# DIE GRENZEN. Jede mit Quelle - wer eine aendert, muss die Quelle mitaendern.
GRENZEN = {
    # STOP. Der Zielwert 2,5 x ATR liegt zwischen den beiden Praxisstandards
    # (Chandelier 3 x ATR, Elder 2 x ATR) und trifft bei BTC rund 7,5 % - genau
    # den Bereich, den der Nutzer aus der Praxis nennt ("ca. 10 Prozent") und
    # den der Backtest vom 28.07. als einzigen ueber der Gewinnschwelle ausweist
    # (5-10 %: 31,2 % Trefferquote, +0,31 CRV).
    "stop_ziel_atr": 2.5,
    # ⚠️⚠️ VON 0,025 AUF 0,050 ANGEHOBEN (31.08.2026, Nutzerentscheidung).
    #
    # ⚠️ DIE BEGRUENDUNG IST NEU GEORDNET (01.09.2026, Nutzerhinweis:
    # *"Du musst sauber zwischen der neutralen Bewertung und der Rechnung
    # im eMail trennen - zwei verschiedene Bereiche."*). Sie stand vorher
    # vollstaendig in Gebuehrensprache - Bitpanda-Satz, Breakeven,
    # Wirtschaftlichkeit. Das las sich, als sei die Kostenrechnung das
    # Kriterium fuer eine GEOMETRIEgrenze gewesen. Der tragende Grund ist
    # ein anderer, und er kommt jetzt zuerst.
    #
    # ---- DER NEUTRALE GRUND: ein Stop im Rauschen misst nichts ----
    #
    # Ein Stop hat genau eine Aufgabe: er soll sagen, dass die Annahme
    # falsch war. Liegt er innerhalb der normalen Tagesspanne, sagt sein
    # Ausloesen nichts ueber die Annahme - er wird von einem beliebigen
    # Tick getroffen. Der Ausstieg ist dann ein Zufall, kein Befund.
    #
    # Krypto-Werte der Watchlist tragen eine mittlere Tagesspanne um 5 %.
    # Ein Stop bei 2,5 % liegt damit bei rund 0,5 ATR - INNERHALB dessen,
    # was ein ereignisloser Tag ohnehin durchlaeuft. Genau diese Grenze
    # zieht `stop_min_atr` (0,75 ATR) bereits relativ; `stop_min_relativ`
    # ist ihr absoluter Zwilling fuer Werte mit ungewoehnlich enger ATR,
    # bei denen der relative Boden allein zu tief laege.
    #
    # ⚠️ Das ist eine Aussage ueber die KONSTRUKTION des Trades, nicht
    # ueber sein Potential. Sie bewertet nicht, ob dieser Einstieg gut
    # ist - sie sorgt dafuer, dass sein Ausgang ueberhaupt eine Aussage
    # traegt. Die Bewertung selbst bleibt davon unberuehrt: bei
    # `gebuehr_je_seite=0.0` ist der Breakeven `1/(1+CRV)` und damit fuer
    # JEDE Stopweite gleich (gemessen 01.09.: 0,3333 bei 2,5 / 5 / 20 %,
    # Potential identisch +0,1191 R). Die Stopweite kann das Potential
    # also gar nicht verschieben.
    #
    # ---- NACHRANGIG, UND NUR FUER DEN MAILTEXT: die Wirtschaftlichkeit --
    #
    # ⚠️ Was jetzt folgt, ist KEIN Grund fuer diese Grenze, sondern eine
    # Folge davon - und sie gehoert auf die Mailebene, wo mit echten
    # Saetzen gerechnet wird. Sie steht hier, weil sie die Groessenordnung
    # anschaulich macht, nicht weil sie die Zahl bestimmt haette.
    #
    # Bei Stop 2,5 % und Bitpanda 1,5 % je Seite kostet die Runde 3,0 % -
    # mehr, als der Stop ueberhaupt verlieren darf. Der Breakeven im
    # Mailtext springt damit auf 73,3 %. Beim Standardsatz 0,30 % je Seite
    # sind es 0,6 % Runde und 36,0 % Breakeven - dieselbe Geometrie, eine
    # ganz andere Wirtschaftlichkeit. Genau deshalb darf diese Rechnung
    # die Grenze nicht setzen: sie haengt am Anbieter, die Geometrie nicht.
    #
    # ---- DIE WIRKUNG, gemessen an 2.297 echten Rollen-Signalen ----
    #
    #     Stops <= 2,6 % (an der Klemme)   233 Signale   10,1 %
    #     Signale mit Hebel > 5            105
    #     hoechster Hebel                  10,00  (= hebel_max)
    #
    # WIRKUNG DER ANHEBUNG, an denselben Daten gerechnet:
    #
    #     betroffen        698 von 2.297 (30,4 %) - KEINES faellt weg,
    #                      sie bekommen einen weiteren Stop
    #     Hebel > 5        105 -> 0
    #     hoechster Hebel  10,00 -> 4,11
    #     Breakeven (BP)   64,6 % -> 53,3 %
    #     Etikett          110 Signale wechseln von hebel auf spot
    #
    # ⚠️ EIN HEBELDECKEL WAERE DER FALSCHE GRIFF (S6d, 22.08.): er senkt
    # das Risiko nicht, er vergroessert die Nominale. Die Stopweite greift
    # an der richtigen Stelle - `hebel = verlustanteil / stop_rel`.
    #
    # ⚠️ UND DIE EHRLICHE EINSCHRAENKUNG: auch bei 5 % traegt sich der
    # Trade rechnerisch nicht (53,3 % noetig, 27,8 % gemessen). Die
    # Untergrenze repariert die GEOMETRIE, nicht die Trefferquote.
    #
    # ⚠️ ZWEI GROESSEN, EIN WERT. `config risiko.sl_abstand_eng_schwelle_-
    # relativ` ist fachlich etwas anderes - die WARNSCHWELLE der alten
    # Hebel-Kette ("dieser Stop ist eng"). Sie zieht mit, damit beide nicht
    # auseinanderlaufen; die Pruefung erzwingt das. Folge: die Warnung
    # greift kuenftig strukturell nie mehr, weil kein Stop mehr darunter
    # liegen kann - und das ist richtig so.
    "stop_min_relativ": 0.05,       # RM-1b, config risiko.sl_abstand_eng_schwelle_relativ
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
    "crv_spreizung": 1.0,      # STILLGELEGT 15.08.2026 - siehe
                               # _crv_faktor(). 5.0 war an 298 Signalen der
                               # ALTEN Kette gemessen, als das Ziel mechanisch
                               # bei CRV 2,0 lag. Seit dem Struktur-Ziel
                               # (12.08.) faellt das CRV aus dem Chart, und die
                               # Abstufung kuerzte damit fast jede Empfehlung
                               # pauschal auf ein Fuenftel. 1.0 = ohne Wirkung.
    # ⚠️ NEU GEEICHT AUF 3,0 (23.08.2026) - vorher 6,0.
    #
    # DIE 6,0 WAR FUER DIE ALTE VERTEILUNG RICHTIG. Gemessen an der
    # Produktionsdatenbank:
    #
    #     alte Kette   Median 2,25   90 % 4,00   max 15,50   >= 6,0: 3 %
    #     Rollen-Kette Median 2,29   90 % 2,79   max  3,00   >= 6,0: 0 %
    #
    # Die MEDIANE sind fast gleich - die SPITZE fehlt. Seit dem Struktur-Ziel
    # (12.08.) faellt das CRV aus dem Chart statt mechanisch bei 2,0 zu
    # liegen, und die Zone ist begrenzt: die Verteilung endet bei 3,0.
    #
    # ⚠️ MIT voll_ab = 6,0 ERREICHT KEIN EINZIGES SIGNAL DIE VOLLE GROESSE.
    # Beim Median-CRV waeren es rund 26 % - genau das "kuerzte fast jede
    # Empfehlung pauschal auf ein Fuenftel", das am 15.08. zur Stilllegung
    # gefuehrt hat.
    #
    # 3,0 BILDET DIE URSPRUENGLICHE ABSICHT NACH: dort erreichen 5 % die volle
    # Groesse, damals waren es 3 %. Nicht die Abstufung war falsch, sondern
    # ihre Eichung.
    #
    # ⚠️ WIRKUNGSLOS, SOLANGE `crv_spreizung` auf 1,0 steht. Die Eichung ist
    # die Vorbereitung, nicht die Inbetriebnahme - das ist eine eigene
    # Entscheidung des Nutzers.
    "crv_voll_ab": 3.0,

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


def _boeden(kurs: float, atr: float, k: float,
            marke_preis: float | None = None,
            umgeworfen_preis_eur: float | None = None,
            ist_short: bool = False) -> dict:
    """Die Untergrenzen des Stopabstands, benannt - DIE EINE STELLE.

    S5 des Umbauplans Kapitel 90 (18.08.2026). Drei Boeden, der weiteste
    gewinnt:

        Rauschen    max(2,5 % Kurs, k x ATR)  - unter dem Rauschen ist jeder
                                                Stop eine Frage der Zeit
        Struktur    Marke +- 0,25 ATR         - jenseits des Niveaus, nicht
                                                darauf
        These       Widerlegungspreis         - wo das Modell seine eigene
                                                Begruendung fuer erledigt haelt

    Das ist die Kombination, die `_stop_abstand`s Docstring seit jeher als
    Standard beschreibt. Gebaut war bis heute nur der erste Boden, und der zu
    niedrig: 0,75 ATR wird in 57,3 % der Faelle binnen fuenf Handelstagen vom
    blossen Rauschen getroffen (26.910 Anker).

    VON `_stop_abstand` UND `dimensioniere` GEMEINSAM BENUTZT. Zwei Rechnungen
    an zwei Orten sind der Fehler, an dem in diesem Projekt schon einmal Werte
    auseinandergelaufen sind (Umbauplan 70.4)."""
    aus = {"Rauschen": max(GRENZEN["stop_min_relativ"] * kurs,
                           float(k) * atr)}
    if isinstance(marke_preis, (int, float)) and marke_preis > 0:
        # JENSEITS der Marke, nicht darauf. Wer genau auf das Niveau geht,
        # wird von jedem Test des Niveaus ausgestoppt. Dieselbe Breite, die
        # die Zielrechnung VOR den Widerstand legt - keine neue Groesse.
        ab = ((float(marke_preis) - kurs) if ist_short
              else (kurs - float(marke_preis))) + GRENZEN["zone_atr"] * atr
        if ab > 0:
            aus["Struktur"] = ab
    if isinstance(umgeworfen_preis_eur, (int, float)) and umgeworfen_preis_eur > 0:
        # BEI SHORT LIEGT DER WIDERLEGUNGSPREIS UEBER DEM KURS (Paket 13).
        ab = ((float(umgeworfen_preis_eur) - kurs) if ist_short
              else (kurs - float(umgeworfen_preis_eur)))
        if ab > 0:
            aus["These"] = ab
    return aus


def _stop_abstand(kurs: float, atr: float,
                  umgeworfen_preis_eur: float | None = None,
                  ist_short: bool = False,
                  min_atr: float | None = None,
                  marke_preis: float | None = None) -> tuple[float, str]:
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
    # SEIT S5 DREI BOEDEN, DER WEITESTE GEWINNT (18.08.2026).
    #
    # Vorher kannte diese Funktion zwei Quellen: den Widerlegungspreis und den
    # Rauschboden. Die Marken unter dem Kurs sah sie NIE - der Docstring oben
    # zitiert die strukturbasierte Schule und baute sie nicht.
    #
    # `min_atr=None` heisst weiterhin: es gilt die Vorgabe aus GRENZEN.
    _k = GRENZEN["stop_min_atr"] if min_atr is None else float(min_atr)
    boeden = _boeden(kurs, atr, _k, marke_preis, umgeworfen_preis_eur,
                     ist_short)
    max_abstand = GRENZEN["stop_max_relativ"] * kurs

    # DER ALTE RUECKFALL BLEIBT UNTERGRENZE, wenn das Modell nichts sagt.
    # Ohne ihn bekaeme ein Signal ohne Widerlegungspreis bei k < 2,5 ploetzlich
    # einen ENGEREN Stop als vorher - eine Verschlechterung durch die
    # Hintertuer, und zwar genau dort, wo ohnehin am wenigsten bekannt ist.
    if "These" not in boeden:
        boeden["ATR-Rueckfall"] = _stop_aus_atr(kurs, atr)[0]

    regel = max(boeden, key=boeden.get)
    abstand = boeden[regel]
    _deckel = 100 * GRENZEN["stop_max_relativ"]
    if abstand > max_abstand:
        return max_abstand, "Obergrenze {:.0f} %".format(_deckel)
    if regel == "These":
        return abstand, "Widerlegungspreis des Modells"
    if regel == "Struktur":
        return abstand, "jenseits der naechsten Marke"
    if regel == "ATR-Rueckfall":
        return abstand, _stop_aus_atr(kurs, atr)[1]
    return abstand, "Rauschboden RM-1b/1c"


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
    # ':g' schrieb "2.5 x ATR" - die einzige englische Zahl, die nach der
    # Vereinheitlichung noch in der Mail stand (17.08.2026).
    return ziel, f"{de(GRENZEN['stop_ziel_atr'], 1)} x ATR"


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
        # ⚠️ NICHT MEHR "kein Widerstand in Reichweite" (17.08.2026).
        # Der Deckel wird seit heute NICHT mehr angewandt (Begruendung in
        # `marken_saetze`), also bekommt diese Funktion keinen Widerstand
        # mehr uebergeben. Der alte Text behauptete dann, es gebe keinen -
        # direkt ueber einer Liste von vier Marken. Was hier gilt, ist
        # schlicht die Rechnung.
        return ziel_mech, GRENZEN["crv"], "mechanisch, 2x Risiko"

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


def _runde_kurs(wert: float | None) -> float | None:
    """Einen KURS runden - auf signifikante Stellen, nicht auf Cent.

    DER DEFEKT, DEN DAS BEHEBT (14.08.2026, in der Gegenpruefung gefunden).
    Jeder Kurs dieser Rechnung lief durch `round(x, 2)`. Fuer BTC ist das
    richtig; fuer alles unter einem Euro vernichtet es die Geometrie:

        KAS   Kurs 0,02428   ->  Zone 0,02 bis 0,02, Stop 0,02, Ziel 0,03
        PLUME Kurs 0,0119    ->  Zone 0,01 bis 0,01, Stop 0,01

    Einstieg, Stop und Ziel fallen auf denselben Wert zusammen. Die Zone hat
    keine Breite mehr, der Stop liegt auf dem Einstieg, und das CRV, das
    daneben steht, gehoert zu einer Rechnung, die es so nicht mehr gibt.

    ICH HABE DAS HEUTE FRUEH FALSCH BERICHTET. Zur PLUME-Mail schrieb ich, die
    Rechnung sei richtig gewesen und nur die Darstellung habe sie vernichtet.
    Das stimmte nur zur Haelfte: `_eur()` hat die Anzeige zerstoert, aber die
    Werte waren vorher schon auf Cent gerundet. Der Formatierer machte den
    Schaden sichtbar, verursacht hat ihn diese Zeile.

    BETRAEGE BLEIBEN BEI ZWEI STELLEN. Ein Einsatz von 160,00 EUR ist ein
    Eurobetrag, kein Kurs - dort sind Cent die richtige Genauigkeit.

    Sechs signifikante Stellen, weil die Zonenbreite bei kleinen Kursen in der
    fuenften oder sechsten steht: bei 0,0119 EUR sind 0,25 ATR rund 0,0002."""
    if wert is None:
        return None
    import math as _m

    w = abs(float(wert))
    if w == 0:
        return 0.0
    stellen = max(2, min(10, 6 - 1 - int(_m.floor(_m.log10(w)))))
    return round(float(wert), stellen)


def _crv_faktor(crv: float, instrument: str,
                kostenklasse: str = "krypto") -> float:
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
    # UND NUR KRYPTO - nachgetragen am 14.08.2026 (O-26).
    #
    # Die Messung lief auf 298 KRYPTO-Spot-Signalen. Die Abstufung galt aber
    # fuer JEDES `instrument == "spot"`, also auch fuer Aktien, Rohstoffe und
    # Themen-ETF. Dort ist die Kostenstruktur eine andere: 1 EUR fix je Seite
    # statt 1,5 % vom Betrag. Bei einer Tranche von 400 EUR heisst das:
    #
    #     CRV 6,0   ->  400 EUR   Kosten 1,00 %
    #     CRV 3,0   ->  160 EUR   Kosten 1,75 %
    #     CRV 2,0   ->   80 EUR   Kosten 3,00 %
    #
    # Bei Krypto bleibt die Quote konstant - Kosten und Betrag skalieren
    # gemeinsam. An der Boerse VERDREIFACHT die Abstufung sie: sie macht den
    # Trade genau dann teuer, wenn das Modell am wenigsten ueberzeugt ist. Das
    # ist die Umkehrung dessen, wofuer sie gemessen wurde.
    #
    # Eine Abstufung fuer boersengehandelte Werte braucht eine eigene Messung
    # oder eine Untergrenze. Bis dahin gilt die Regel dort, wo sie gemessen
    # wurde.
    #
    # IM BETRIEB AENDERT SICH HEUTE NICHTS: `rollen_kette.aktiv_fuer` steht
    # auf ["krypto"]. Der Fehler waere erst beim Zuschalten der uebrigen
    # Klassen aufgetreten - und dann als schleichende Kostenquote, nicht als
    # Absturz.
    if (instrument != "spot" or kostenklasse != "krypto"
            or spreizung <= 1.0 or voll_ab <= GRENZEN["crv"]):
        return 1.0
    spanne = max(0.0, min(1.0, (crv - GRENZEN["crv"]) / (voll_ab - GRENZEN["crv"])))
    sockel = 1.0 / spreizung
    return sockel + (1.0 - sockel) * spanne


# Die Mindestgroesse JE KOSTENKLASSE (15.08.2026).
#
# GEMESSEN, NICHT GESETZT. Kosten in R bei 5 % Stop:
#
#     Betrag      Krypto     Boerse
#         25       0,600      1,700
#        100       0,600      0,500
#        400       0,600      0,200
#
# KRYPTO IST BETRAGSUNABHAENGIG - 1,5 % je Seite kuerzen sich heraus. Eine
# Mindestgroesse aus Gebuehrengruenden hat dort GAR KEINE Grundlage; die 100
# EUR stammen aus der Boersenlogik und galten dort mit, weil niemand sie
# getrennt hat. Was bei Krypto bleibt, ist eine praktische Untergrenze: unter
# 25 EUR lohnt der Aufwand nicht, aber das ist eine Aussage ueber den Menschen,
# nicht ueber die Gebuehren.
#
# AN DER BOERSE bleibt es bei 100 EUR. Der Wert wird NICHT angehoben, obwohl
# die Kostenquote dort erst ab rund 250 EUR ertraeglich wird - eine strengere
# Grenze wuerde mehr Empfehlungen verschwinden lassen, und das ist die Richtung,
# aus der wir gerade kommen. Die Kostenzahl steht stattdessen in der Mail.
BETRAG_MIN_JE_KOSTENKLASSE = {"krypto": 25.0, "boerse": 100.0}


def betrag_min_eur(kostenklasse: str = "krypto") -> float:
    """Die kleinste sinnvolle Positionsgroesse fuer diese Kostenklasse."""
    return BETRAG_MIN_JE_KOSTENKLASSE.get(
        str(kostenklasse or "").strip().lower(), GRENZEN["betrag_min_eur"])


def rechne(*, kurs: float | None, atr: float | None, risiko_eur: float | None,
           instrument: str = "spot", betrag_wunsch_eur: float | None = None,
           topf_frei_eur: float | None = None,
           cash_frei_eur: float | None = None,
           umgeworfen_preis_eur: float | None = None,
           umgeworfen_tage: int | None = None,
           widerstand: tuple[float, int] | None = None,
           kostenklasse: str = "krypto",
           # DIE ANLAGEKLASSE - NUR FUER DEN TRICHTER (19.08.2026).
           # Sie steuert KEINE Rechnung, nur die Wahl der gemessenen
           # Trichterfaktoren: Krypto schwankt anders als ein ETF, und
           # ein Faktor fuer alle war fuer jede Klasse falsch (93 A/A2).
           # Leer heisst Rueckfall, und die Mail sagt das dann auch.
           assetklasse: str = "",
           ist_short: bool = False,
           stop_min_atr: float | None = None,
           marke_stop_eur: float | None = None,
           hebel_handelbar: bool | None = None,
           risikobudget_hart: bool = False) -> dict:
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
    abstand, stop_regel = _stop_abstand(kurs, atr, umgeworfen_preis_eur,
                                        ist_short, stop_min_atr,
                                        marke_stop_eur)
    stop_rel = abstand / kurs
    ziel, crv, ziel_regel = _ziel(kurs, abstand, atr, widerstand, ist_short)

    e = {
        "ist_short": bool(ist_short),
        # DER ATR GEHOERT INS ERGEBNIS (19.08.2026). Der Trichter braucht
        # ihn, und ihn dort neu zu bestimmen waere die zweite Stelle, an der
        # zwei Rechnungen auseinanderlaufen koennen (Umbauplan 70.4).
        "atr": float(atr),
        "assetklasse": str(assetklasse or ""),
        # S2 (18.08.2026): die Marke auf der STOPSEITE - unten bei LONG,
        # oben bei SHORT. Sie wird HIER NOCH NICHT BENUTZT; der Stop
        # kennt sie erst ab S5. Reine Durchreichung, damit die Verkabelung
        # steht und einzeln pruefbar ist.
        #
        # NICHT ueber `widerstand` - der geht an `_ziel()` und wuerde den
        # am 17.08. verworfenen Widerstandsdeckel reaktivieren.
        "marke_stop_eur": (float(marke_stop_eur)
                           if isinstance(marke_stop_eur, (int, float))
                           and marke_stop_eur > 0 else None),
        "einstieg_eur": _runde_kurs(kurs),
        "einstieg_von_eur": _runde_kurs(kurs - GRENZEN["zone_atr"] * atr),
        "einstieg_bis_eur": _runde_kurs(kurs + GRENZEN["zone_atr"] * atr),
        "stop_eur": _runde_kurs(kurs - (-abstand if ist_short else abstand)),
        "stop_relativ": round(stop_rel, 5),
        "stop_regel": stop_regel,
        "ziel_eur": _runde_kurs(ziel),
        "ziel_von_eur": _runde_kurs(ziel - GRENZEN["zone_atr"] * atr),
        "ziel_bis_eur": _runde_kurs(ziel + GRENZEN["zone_atr"] * atr),
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
    # ⚠️ A5 (23.08.2026): DIE ABSTUFUNG FRAGT DAS ERGEBNIS, NICHT DEN LAUF.
    #
    # `_crv_faktor` gilt ausdruecklich NUR FUER SPOT - die Messung vom 03.08.
    # fand beim Hebel die GEGENLAEUFIGE Antwort (Gate SQN +3,25 gegen +1,25
    # fuer jede Groessen-Variante). Sie fragte aber `instrument`, und das
    # heisst fuer Krypto seit S6b immer "spot": eingeschaltet wuerde sie
    # damit auch jedes Hebel-Signal kuerzen - gegen ihre eigene Messung.
    #
    # DAS ETIKETT VORAB, aus dem WUNSCHBETRAG. An dieser Stelle traegt
    # `betrag` noch den Wunsch, keinen Deckel - damit ist die Groesse
    # dieselbe wie in `dimensioniere()`, wo `hebel_noetig = verlustanteil /
    # stop_rel` gar keinen Betrag kennt. Das endgueltige Etikett faellt
    # weiter unten nach allen Deckeln an; hier geht es nur um die Frage
    # "Spot oder Hebel", und die haengt am Stopabstand, nicht am Deckel.
    _handelbar = (bool(hebel_handelbar) if hebel_handelbar is not None
                  else instrument == "hebel")
    _noetig_vorab = (risiko_eur / (betrag * stop_rel)
                     if betrag and stop_rel else 0.0)
    _etikett_vorab = ("hebel" if _handelbar
                      and (_noetig_vorab > 1.0 or ist_short) else "spot")
    _faktor = _crv_faktor(crv, _etikett_vorab, kostenklasse)
    if _faktor < 1.0:
        betrag, grund = betrag * _faktor, f"CRV-Abstufung ({crv:.2f})"
    e["crv_groessenfaktor"] = round(_faktor, 3)
    # TOPF UND CASH AENDERN DEN BETRAG NICHT MEHR (15.08.2026).
    #
    # DIE TRENNLINIE, auf die sich der Nutzer und ich geeinigt haben:
    #
    #     Das System bemisst den EINZELNEN TRADE.
    #     Die Aufteilung des PORTFOLIOS bemisst der Nutzer.
    #
    # Stop, Positionsgroesse aus Risiko und Hebel aus Liquidationsabstand
    # folgen aus dem Trade allein - dafuer braucht es kein Portfoliowissen.
    # Topf und Cash-Reserve brauchen es sehr wohl, und zwar Wissen, das dieses
    # System NICHT HAT: ob der Nutzer die Empfehlungen von gestern ausgefuehrt
    # hat. Es kennt seinen Bestand (Bitpanda-Sync), nicht seine Absicht.
    #
    # WAS DAS IN DER PRAXIS ANRICHTETE: der Hebel-Topf zaehlte EMPFEHLUNGEN.
    # Ein einziges Signal (LINK, 500 EUR) fuellte den 500er-Topf, und ab da
    # bekam jedes weitere Hebel-Symbol Betrag 0 - blockiert NACH dem
    # Modellaufruf, ohne Zeile, also ohne Cooldown. 802 Modellaufrufe fuer 47
    # Urteile an einem Tag.
    #
    # Die Zahlen bleiben und wandern in die MAIL, als Lagebild. Der Nutzer:
    # "Deckel laufen nur als Info fuer den User mit im eMail."
    if topf_frei_eur is not None:
        e["topf_frei_eur"] = round(float(topf_frei_eur), 2)
        e["topf_wuerde_ueberschreiten"] = betrag > float(topf_frei_eur)
    if cash_frei_eur is not None:
        e["cash_frei_eur"] = round(float(cash_frei_eur), 2)
        e["cash_wuerde_ueberschreiten"] = betrag > float(cash_frei_eur)
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
    _min = betrag_min_eur(kostenklasse)
    e["betrag_min_eur"] = _min
    if (betrag < _min and grund and grund.startswith("CRV-Abstufung")
            and float(betrag_wunsch_eur or 0) >= _min):
        betrag = _min
        grund = f"{grund}, auf Mindestgroesse angehoben"
    if betrag < _min:
        # DIE EINZIGE HARTE GRENZE, die uebrig bleibt - und sie ist eine
        # Eigenschaft des TRADES, nicht des Portfolios: unter dieser Groesse
        # frisst die Gebuehr das Risikobudget. Deshalb darf sie bleiben.
        raise RechnungBlockiert(
            f"Betrag {betrag:.0f} EUR unter der Mindestgroesse {_min:.0f} EUR "
            f"fuer die Kostenklasse {kostenklasse!r}")

    # ⚠️ A1 (23.08.2026): DIE HANDELBARKEIT ENTSCHEIDET, NICHT DER LAUF.
    #
    # Hier stand `if instrument == "hebel"`. Seit S6b laeuft Krypto nur noch
    # mit `instrument="spot"` - die Bedingung war nie wieder wahr, und damit
    # ergab JEDE Rechnung Hebel 1,0. Gemessen am Export: 22.08. bis 11:30
    # (zwei Laeufe) 97 Signale mit 55 Hebelspalten, ab 11:30 (ein Lauf) 16
    # Signale mit NULL.
    #
    # ⚠️ UND DAS ETIKETT KOMMT AUS DER ZAHL, wie in `dimensioniere()`:
    #
    #     etikett = "hebel", wenn ein Hebel NOETIG ist (oder es ein SHORT ist)
    #
    # DAMIT AENDERT SICH EINE ENTSCHEIDUNG VOM 15.08., und das gehoert
    # benannt. Damals galt: "die Spalte entscheidet sich am Instrument statt
    # am Wert" - weil ein echter Hebel-Trade, dessen sicherer Faktor auf 1,0
    # faellt (KAITO 9,9 %, CAT 17,4 % Stop), sonst als Spot in der Datenbank
    # landete. Das Instrument war der verlaessliche Marker, WEIL ES ZWEI
    # LAEUFE GAB. Mit einem Lauf gibt es diesen Marker nicht mehr, und ein
    # Signal, das keinen Hebel BRAUCHT, ist auch keines. Die Entscheidung ist
    # damit durch S6b ueberholt, nicht durch mich umgestossen.
    #
    # RUECKFALL FUER DIE ALTEN KETTEN: ohne Angabe gilt weiter das Instrument.
    # `hebel_analyst` und Verwandte rufen unveraendert - dort gibt es beide
    # Laeufe noch, und dort ist das Instrument weiterhin eindeutig.
    # `_handelbar` steht schon oben (A5) - eine zweite Rechnung waere eine
    # zweite Wahrheit ueber dieselbe Frage.
    hebel_noetig = risiko_eur / (betrag * stop_rel) if betrag and stop_rel else 0.0
    e["hebel_noetig"] = round(hebel_noetig, 2)
    e["hebel_handelbar"] = _handelbar
    # ⚠️ SHORT IST IMMER GEHEBELT - Spot kann nicht leerverkauft werden.
    # ⚠️ DAS ETIKETT HAENGT AM WUNSCH, NICHT AM DECKEL (23.08.2026).
    #
    # DER FEHLER, DEN DAS VERHINDERT - sichtbar geworden, als die Eichung von
    # `voll_ab` geprueft wurde: `hebel_noetig` rechnet mit dem GEDECKELTEN
    # Betrag. Kuerzt die CRV-Abstufung ihn (800 -> 320 EUR), steigt
    # `hebel_noetig` von 0,6 auf 1,5 - und aus einem SPOT-Trade wird ein
    # HEBEL-Trade, allein weil die Position kleiner wurde. Das ist eine
    # Rueckkopplung, kein Befund.
    #
    # ⚠️ SIE TRITT ERST AUF, WENN DIE ABSTUFUNG EINGESCHALTET WIRD (heute
    # steht `crv_spreizung` auf 1,0). Deshalb faellt sie jetzt auf, nicht
    # spaeter im Betrieb.
    #
    # OB EIN TRADE GEHEBELT IST, ist eine Eigenschaft seiner GEOMETRIE -
    # Verlustanteil gegen Stopabstand. Genau das rechnet `dimensioniere()`
    # als `verlustanteil / stop_rel`, ganz ohne Betrag. `_noetig_vorab` oben
    # ist dieselbe Groesse, aus dem Wunschbetrag.
    e["etikett"] = ("hebel" if _handelbar
                    and (_noetig_vorab > 1.0 or ist_short) else "spot")
    if e["etikett"] == "hebel":
        sicher = max_safe_hebel(100 * stop_rel, GRENZEN["liquidations_marge"])
        # DER BETRAG FOLGT DEM RISIKOBUDGET, NICHT DER HEBEL DEM BETRAG
        # (15.08.2026).
        #
        # `max(1.0, ...)` war als Untergrenze gedacht und war eine
        # STILLSCHWEIGENDE UMDEUTUNG: faellt der noetige Faktor unter 1, heisst
        # das, die UNGEHEBELTE Position riskiert schon mehr als das Budget
        # hergibt. Die Untergrenze hat den Ueberschuss nicht beseitigt, sondern
        # verschwiegen - der Trade riskierte dann mehr als erlaubt.
        #
        # WARUM NICHT ABSAGEN. Das war meine erste Fassung, und die eigene
        # Pruefung 10 hat sie gestoppt: dort liegt der noetige Faktor bei 0,99.
        # Ein Prozent Ueberschuss ist ein Rundungsrand, keine Pathologie - und
        # ein Urteil dafuer wegzuwerfen waere genau das Einschraenken, das
        # nichts besser macht. Bei KAITO waren es 0,67; beide Faelle brauchen
        # dieselbe Antwort, und die lautet: den Betrag kleiner machen.
        #
        # DANACH IST DER HEBEL GENAU 1,0 - und das wird jetzt auch so
        # geschrieben und gesagt. Vorher fiel diese Zeile durch
        # `signal_abbildung`s Filter `hebel > 1.0` und landete als SPOT in der
        # Datenbank: ausserhalb von Hebel-Cooldown und Hebel-Topf, mit dem
        # Mailbetreff "EROEFFNEN (Hebel)". Mail und Datenbank widersprachen
        # sich; das ist seit heute am Instrument entschieden.
        if hebel_noetig < 1.0:
            betrag = risiko_eur / stop_rel
            if betrag < _min:
                raise RechnungBlockiert(
                    f"Betrag {betrag:.0f} EUR unter der Mindestgroesse "
                    f"{_min:.0f} EUR - das Risikobudget "
                    f"({risiko_eur:.0f} EUR bei {100 * stop_rel:.1f} % Stop) "
                    f"traegt hier keine handelbare Groesse")
            grund = "Risikobudget (Hebel 1,0 - kein Hebel moeglich)"
            hebel_noetig = 1.0
        hebel = max(1.0, min(hebel_noetig, sicher, GRENZEN["hebel_max"]))
        e["hebel"] = round(hebel, 1)
        # ⚠️ DIESELBE VERDREHUNG WIE IN `dimensioniere` (dort am 22.08.
        # gefunden): `hebel <= hebel_noetig` ist bei LONG immer wahr, weil
        # `hebel` aus einem min() ueber `hebel_noetig` kommt - die beiden
        # anderen Zweige waren toter Code.
        if hebel >= hebel_noetig - 1e-9:
            e["hebel_grenze"] = "Risikobudget"
        elif sicher <= GRENZEN["hebel_max"] + 1e-9 and hebel <= sicher + 1e-9:
            e["hebel_grenze"] = "RM-11 Liquidationsabstand"
        else:
            e["hebel_grenze"] = "Hoechsthebel"
        # Bei SHORT liegt die Liquidation UEBER dem Einstieg.
        e["liquidation_etwa_eur"] = round(
            kurs * (1 + 1 / hebel) if ist_short else kurs * (1 - 1 / hebel), 2)
    else:
        e["hebel"] = 1.0
        # HARTES BUDGET AUCH OHNE HEBEL (28.08.2026).
        #
        # ⚠️ DIE KORREKTUR GAB ES SEIT DEM 15.08. - aber nur im Hebel-Zweig
        # darueber, und der wird bei weitem Stop nie betreten. Ihre Begruendung
        # gilt hier woertlich genauso: "faellt der noetige Faktor unter 1,
        # heisst das, die UNGEHEBELTE Position riskiert schon mehr als das
        # Budget hergibt. Die Untergrenze hat den Ueberschuss nicht beseitigt,
        # sondern VERSCHWIEGEN."
        #
        # GEMESSEN, wie oft das eintritt: 768 von 1.033 Einstiegssignalen seit
        # dem 19.08. (74,3 %) haben einen rechnerischen Faktor unter 1,0. Das
        # Budget wurde im Median um 46 % ueberschritten, im Maximum um 480 %.
        #
        # ⚠️ WAS DAS NICHT LOEST: Hebel entstehen dadurch keine. Der Faktor
        # bleibt 1,0; nur die Groesse wird kleiner. Beides - fehlender Hebel
        # und Budgetueberschreitung - hat dieselbe Ursache (der Stop ist
        # weiter als der Verlustanteil), aber nur die zweite ist eine
        # Korrektur. Die erste waere eine Entscheidung.
        #
        # ⚠️ UND DER STOP BLEIBT EINE RECHENGROESSE, keine Order (siehe
        # `risiko_quelle` oben): bei Spot gibt es bei Bitpanda keine
        # Stop-Order. Der Betrag am Budget auszurichten macht das Budget
        # trotzdem wieder zu einer Grenze - ohne diese Zeile ist es nur ein
        # Etikett auf einer Zahl, die aus etwas anderem folgt.
        # ⚠️⚠️ DAS IST C2, KEINE KORREKTUR - und ich hatte es als Korrektur
        # ausgegeben. Die eigene Suite hat es gestoppt (Paket Q, 14.08.):
        #
        #     "Bei Spot OHNE Stop-Order gibt es keine Groesse, die aus dem
        #      Stop folgen koennte."
        #     "Tranche 800 -> Betrag 4.800. Dort stand 960, wo der Nutzer 800
        #      gesagt hatte - der Betrag haette am Stopabstand gehangen statt
        #      an seiner Entscheidung."
        #
        # `Umbauplan_Gesamtsystem_12_08.md` fuehrt C2 als "festes Risiko oder
        # fester Betrag - offen, GELDFRAGE". Wer den Betrag aus dem Budget
        # ableitet, entscheidet sie.
        #
        # DESHALB EIN SCHALTER, UND SEINE VORGABE AENDERT NICHTS. Eingeschaltet
        # haelt das Budget bei jeder Stopweite (gemessen an 1.033 Einstiegen:
        # 74,3 % ueberschreiten es heute, im Median um 46 %). Ausgeschaltet
        # bleibt der Betrag die Entscheidung des Nutzers - und der Ueberschuss
        # wird wenigstens BENANNT statt verschwiegen.
        if hebel_noetig and 0.0 < hebel_noetig < 1.0 and not risikobudget_hart:
            # NICHT STILL: der Ueberschuss steht in der Rechnung, auch wenn
            # der Betrag unangetastet bleibt. Das war der eigentliche Fehler -
            # nicht die Groesse, sondern das Schweigen darueber.
            e["budget_ueberschritten_um"] = round(
                (betrag * stop_rel) / risiko_eur - 1.0, 3)
        if hebel_noetig and 0.0 < hebel_noetig < 1.0 and risikobudget_hart:
            _knapp = risiko_eur / stop_rel
            if _knapp < _min:
                # KEIN ABBRUCH - dieselbe Linie wie im Hebel-Zweig, wo ein
                # Prozent Ueberschuss "ein Rundungsrand, keine Pathologie"
                # heisst. Unter der Mindestgroesse bleibt der alte Betrag
                # stehen UND der Ueberschuss wird benannt, statt ihn
                # stillschweigend zu tragen.
                e["budget_ueberschritten_um"] = round(
                    (betrag * stop_rel) / risiko_eur - 1.0, 3)
            else:
                betrag = _knapp
                grund = "Risikobudget (ungehebelt zu gross)"

    e["betrag_eur"] = round(betrag, 0)
    e["betrag_gedeckelt_durch"] = grund
    # DAS RISIKO ERST JETZT, NACH ALLEN DECKELN (14.08.).
    #
    # Die erste Fassung rechnete es aus dem Betrag VOR der CRV-Abstufung: in
    # der Pruefung stand "Risiko 100 EUR auf 400 EUR bei 5 % Stop" - das waeren
    # 25 %, und niemand haette gesehen, dass die Zahl zu einer Groesse gehoert,
    # die es nicht mehr gibt. `verlust_am_stop_eur` war die ganze Zeit richtig,
    # weil es den Endbetrag nimmt; die beiden haetten sich widersprochen.
    # ⚠️ DAS ETIKETT, NICHT DER LAUF (28.08.2026, I-1). Hier stand
    # `instrument != "hebel"` - und `instrument` ist seit S6b immer "spot".
    # Damit wurde `risiko_eur` AUCH bei Hebel-Signalen ueberschrieben, und
    # zwar OHNE den Hebel: bei Hebel 1,6 und 500 EUR stand `risiko_eur` auf
    # 18,75 waehrend `verlust_am_stop_eur` 30,00 sagte. Dieselbe Groesse,
    # zwei Zahlen - genau der Fehler aus Umbauplan 12.5.
    if e["etikett"] != "hebel":
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


# Wieviele Marken die Mail hoechstens auflistet. Nutzerentscheidung
# 17.08.2026: die drei naechsten. Gemessen liegen bis zu sieben zwischen
# Kurs und Ziel - alle zu nennen waere eine Liste, die niemand liest.
MARKEN_IN_DER_MAIL = 3

# Der Erlaeuterungstext unter der Markenliste. Nutzerwunsch 17.08.2026:
# "mit sinnvollem Ergaenzungstext zur Nutzung (vorerst temporaer)".
#
# Er sagt DREI Dinge, und jedes davon beantwortet eine Nutzerfrage:
#   - was eine Marke ist (frueher gedrehte Preise, dort liegen Auftraege)
#   - was die Zahl bedeutet (mehr Umkehrpunkte = eher wieder)
#   - was das Ziel NICHT ist (keine Prognose, sondern eine Bedingung)
_MARKEN_ERKLAERUNG = (
    "  Was das heisst: an diesen Preisen hat der Kurs frueher gedreht - "
    "dort liegen Auftraege.",
    "  Je mehr Umkehrpunkte, desto eher passiert es wieder; "
    "'durchbrochen' heisst, die",
    "  Marke hat zuletzt nicht gehalten. Das Ziel ist GERECHNET, nicht "
    "vorhergesagt: es",
    "  sagt, wie weit der Kurs laufen muesste, damit sich der Trade traegt.",
)


def marken_saetze(e: dict, marken: list | None,
                  liquiditaetszonen: bool = False) -> list[str]:
    """Die Marken auf dem Weg zum Ziel - genannt, nicht angewandt.

    ⚠️ WARUM SIE NICHT DECKELN (gemessen 17.08.2026). Ein frueherer Bau
    liess die naechste Marke das Ziel begrenzen. Ergebnis: bei 44 von 44
    Symbolen gedeckelt, 98 % unter CRV 0,5, Median 0,21. Der Grund ist
    strukturell - zwischen Kurs und einem 2R-Ziel liegen im Median DREI
    Wendepunkte, bei FLOKI 143 im ganzen Chart. Auf Tagesfraktalen ist
    immer eine Marke im Weg; ein Deckel darauf hiesse "es gibt nie ein
    2R-Ziel".

    Also: das Ziel bleibt gerechnet, die Marken stehen daneben. Kein
    stiller Deckel und keine stille Behauptung, es gaebe keinen
    Widerstand.

    `liquiditaetszonen` nur fuer Krypto Spot und Hebel - die Bezeichnung
    traegt eine Deutung (Stop-Hunt, Marketmaker), die am 23.07.2026
    ausdruecklich auf diese beiden begrenzt wurde. Die Marken selbst gibt
    es ueberall; nur der Name ist begrenzt."""
    if not marken or not e.get("ziel_bis_eur"):
        return []
    von = min(float(e["einstieg_bis_eur"]), float(e["ziel_bis_eur"]))
    bis = max(float(e["einstieg_bis_eur"]), float(e["ziel_bis_eur"]))
    im_weg = [m for m in marken
              if von < float(m.get("preis_eur") or 0) <= bis]
    if not im_weg:
        return ["  Bis zum Ziel liegt keine Marke im Weg."]
    gezeigt = im_weg[:MARKEN_IN_DER_MAIL]
    # "liegen 1 Marke" stand in der ersten Fassung.
    wie_viele = (f"liegen {len(im_weg)} Marken" if len(im_weg) > 1
                 else "liegt 1 Marke")
    kopf = ("  Auf dem Weg dorthin " + wie_viele
            + (" (Liquiditaetszonen)" if liquiditaetszonen else "")
            + (", die " + str(len(gezeigt)) + " naechsten:"
               if len(im_weg) > len(gezeigt) else ":"))
    z = [kopf]
    for m in gezeigt:
        teile = []
        if m.get("nach_unten_gedreht"):
            teile.append(str(m["nach_unten_gedreht"]) + "x nach unten gedreht")
        if m.get("gehalten"):
            teile.append(str(m["gehalten"]) + "x gehalten")
        z.append("    " + preis(m["preis_eur"]) + " EUR  +"
                 + _eur(m["abstand_atr"], 1) + " Schwankungsbreiten - "
                 + str(m["beruehrungen"]) + " Umkehrpunkte")
        z.append("      (" + ", ".join(teile) + ")"
                 + (", zuletzt " + str(m["letzte_beruehrung"])
                    if m.get("letzte_beruehrung") else "")
                 + (" - seither durchbrochen" if m.get("gefegt") else ""))
    return z + list(_MARKEN_ERKLAERUNG)


def saetze(e: dict, marken: list | None = None,
           liquiditaetszonen: bool = False) -> list[str]:
    """Die Rechnung in der Form, in der sie in die E-Mail gehoert."""
    z = [f"Einstiegszone   {preis(e['einstieg_von_eur'])} bis {preis(e['einstieg_bis_eur'])} EUR",
         f"Stop            {preis(e['stop_eur'])} EUR  ({_eur(100 * e['stop_relativ'], 1)} % - {e['stop_regel']})",
         f"Take-Profit     {preis(e['ziel_von_eur'])} bis {preis(e['ziel_bis_eur'])} EUR  "
         f"(CRV {_eur(e['crv'], 1)} - {e['ziel_regel']})"]
    z += marken_saetze(e, marken, liquiditaetszonen)

    # ⚠️ DER TRICHTER (19.08.2026, Kapitel 93 A). Die einzige Aussage ueber
    # die ZUKUNFT, die dieses System belegen kann - und sie sagt nur, WIE
    # WEIT, nicht wohin. Die Groesse einer Bewegung ist prognostizierbar,
    # die Richtung nicht.
    #
    # Sie steht NACH Stop und Ziel, weil sie die dortigen Zahlen einordnet:
    # ein Stop innerhalb der ueblichen Schwankung wird vom Zufall getroffen,
    # ein Ziel jenseits davon in der Zeit nicht erreicht.
    if not e["crv_erreicht"]:
        z.append(f"                !! Der Weg bis dorthin traegt nur CRV "
                 f"{_eur(e['crv'], 1)}, verlangt sind {_eur(GRENZEN['crv'], 1)}")
    z += [
         # "etwa 1 Handelstage" stand in einer echten Mail.
         f"Haltedauer      etwa {e['haltedauer_tage']} "
         f"{'Handelstag' if e['haltedauer_tage'] == 1 else 'Handelstage'} "
         f"({e.get('haltedauer_quelle', 'geschaetzt')})",
         f"Betrag          {_eur(e['betrag_eur'])} EUR"
         + (f"  - begrenzt durch {e['betrag_gedeckelt_durch']}"
            if e.get("betrag_gedeckelt_durch") else "")]
    # ⚠️ DIE ZEILE STEHT IMMER DA, AUCH BEI 1,0 (19.08.2026).
    #
    # Bis heute erschien sie nur bei `hebel > 1`. Seit S5 kommt in vier von
    # fuenf Faellen 1,0 heraus - und eine Mail OHNE Hebelzeile sieht aus wie
    # eine, bei der die Angabe vergessen wurde, nicht wie eine, bei der es
    # keinen Hebel gibt. Nutzerfund an einer echten AKT-Mail: Betreff
    # "EROEFFNEN (Hebel)", im Koerper kein Hebel.
    #
    # Dasselbe Muster wie `uebersprungen` bei Rolle G: das Fehlen einer
    # Zeile ist keine Aussage, sondern eine Luecke.
    if e["hebel"] > 1:
        z.append(f"Hebel           {_eur(e['hebel'], 1)}x  (Grenze: {e['hebel_grenze']}; "
                 f"Liquidation etwa {preis(e['liquidation_etwa_eur'])} EUR)")
    elif e.get("instrument") == "hebel" or e.get("hebel") is not None:
        z.append("Hebel           1,0x  - kein Hebel noetig, der Betrag "
                 "folgt dem Risikobudget")
    z.append(f"Am Stop verlieren Sie {_eur(e['verlust_am_stop_eur'])} EUR, "
             f"am Ziel gewinnen Sie {_eur(e['gewinn_am_ziel_eur'])} EUR.")
    # DER TRICHTER STEHT NACH DEN SECHS HANDELSPARAMETERN (20.08.2026).
    #
    # Er stand zuerst zwischen Take-Profit und Haltedauer und hat damit den
    # Block zerschnitten, den der Nutzer am 17.08. ausdruecklich zusammen
    # und fett sehen wollte: Einstiegszone, Stop, TP, Haltedauer, Betrag,
    # Hebel. Sieben Zeilen dazwischen machen aus einer Tabelle eine Suche.
    try:
        from agent import trichter as _TR
        z += _TR.saetze(e.get("einstieg_eur"), e.get("atr"),
                        stop_relativ=e.get("stop_relativ"),
                        ziel_relativ=(
                            (e.get("ziel_eur") - e.get("einstieg_eur"))
                            / e.get("einstieg_eur")
                            if e.get("ziel_eur") and e.get("einstieg_eur")
                            else None),
                        klasse=e.get("assetklasse"))
    except Exception:                                        # noqa: BLE001
        pass

    # DIE LAGE - Information, kein Eingriff (15.08.2026).
    #
    # Topf und Cash aendern den Betrag nicht mehr; sie stehen hier, damit der
    # Nutzer die Portfolioentscheidung treffen kann, die das System nicht
    # treffen darf. Es kennt seinen Bestand, nicht seine Absicht.
    lage = []
    if e.get("topf_frei_eur") is not None:
        lage.append(f"Im Topf frei    {_eur(e['topf_frei_eur'])} EUR"
                    + ("   !! diese Position wuerde ihn ueberschreiten"
                       if e.get("topf_wuerde_ueberschreiten") else ""))
    if e.get("cash_frei_eur") is not None:
        lage.append(f"Cash frei       {_eur(e['cash_frei_eur'])} EUR"
                    + ("   !! reicht fuer diese Position nicht"
                       if e.get("cash_wuerde_ueberschreiten") else ""))
    if lage:
        z += [""] + lage + [
            "Diese Zahlen begrenzen die Empfehlung NICHT - sie setzen voraus,",
            "dass Sie die uebrigen Empfehlungen dieses Laufs nicht ausfuehren."]
    if e.get("betrag_min_eur"):
        z.append(f"Kleinste sinnvolle Groesse hier: "
                 f"{_eur(e['betrag_min_eur'])} EUR "
                 + ("(Krypto: die Gebuehr ist prozentual, der Betrag kuerzt "
                    "sich heraus)" if e["betrag_min_eur"] <= 50 else
                    "(Boerse: 1 EUR fix je Seite - kleiner lohnt nicht)"))
    return z


# ---------------------------------------------------------------------------
# STUFE 0 DES PLANS (Umbauplan Kapitel 88, Fassung 2, 18.08.2026)
# ---------------------------------------------------------------------------


class Dimension(dict):
    """Das Ergebnis von `dimensioniere` - ein dict mit Namen."""


def dimensioniere(*, kurs: float, atr: float, k: float, verlustanteil: float,
                  einsatz_eur: float, marke_preis: float | None = None,
                  umgeworfen_preis_eur: float | None = None,
                  ist_short: bool = False, hebel_handelbar: bool = True,
                  mindestgroesse_eur: float = 0.0) -> Dimension:
    """Stop, Betrag, Hebel und Etikett - REIN, ohne DB, Uhr oder Netz.

    DIE EINE STELLE fuer die Dimensionierung. Zwei Aufrufer: die Messung
    (`messe_dimensionierung.py`) und spaeter die Produktion. Zwei Rechnungen
    an zwei Orten sind der Fehler, an dem in diesem Projekt schon einmal
    Werte auseinandergelaufen sind (Umbauplan 70.4).

    DREI BOEDEN, DER WEITESTE GEWINNT:

        Rauschen    k x ATR             - unter dem Rauschen ist jeder Stop
                                          eine Frage der Zeit, nicht der These
        Struktur    Marke +- 0,25 ATR   - jenseits des Niveaus, nicht darauf
        These       Widerlegungspreis   - wo das Modell seine Begruendung
                                          fuer erledigt haelt

    Das ist die Kombination, die `_stop_abstand`s Docstring seit jeher als
    Standard beschreibt; gebaut war bisher nur der erste Boden, und der zu
    niedrig (0,75 ATR - gemessen 56,7 % Rauschtreffer in fuenf Tagen).

    UND DER HEBEL FAELLT AN, er wird nicht gewaehlt:

        Hebel = Verlustanteil / Stopabstand

    Daraus folgt `Hebel > 1  <=>  Stop < Verlustanteil`. Die Spot/Hebel-Grenze
    IST der Verlustanteil - das ist der Befund, der die Erstfassung des Plans
    widerlegt hat.

    ⚠️ SHORT ERZWINGT HEBEL. Spot kann bei Bitpanda nicht short; die Richtung
    ist damit selbst ein Hebelkriterium - eine Tatsache, keine Prognose.

    ⚠️ NIE `None`. Fuer jede Eingabe kommt ein Ergebnis oder eine benannte
    Ausnahme. Eine Funktion, die still nichts liefert, waere genau die
    Bauform, die den Deadloop erzeugt hat.
    """
    for name, wert in (("Kurs", kurs), ("ATR", atr), ("Einsatz", einsatz_eur)):
        if not wert or float(wert) <= 0:
            raise RechnungBlockiert(f"{name} fehlt oder ist nicht positiv")
    if not 0 < float(verlustanteil) < 1:
        raise RechnungBlockiert(
            f"Verlustanteil {verlustanteil!r} liegt nicht zwischen 0 und 1")
    kurs, atr, einsatz_eur = float(kurs), float(atr), float(einsatz_eur)
    verlustanteil = float(verlustanteil)

    # DIESELBE STELLE WIE `_stop_abstand` (S5). Vorher stand die
    # Boden-Rechnung hier ein zweites Mal.
    boeden = _boeden(kurs, atr, k, marke_preis, umgeworfen_preis_eur,
                     ist_short)

    regel = max(boeden, key=boeden.get)
    abstand = boeden[regel]
    deckel = GRENZEN["stop_max_relativ"] * kurs
    if abstand > deckel:
        abstand, regel = deckel, "Obergrenze"
    stop_rel = abstand / kurs

    risiko_eur = verlustanteil * einsatz_eur
    hebel_noetig = verlustanteil / stop_rel
    sicher = max_safe_hebel(100 * stop_rel, GRENZEN["liquidations_marge"])

    if hebel_handelbar and (hebel_noetig > 1.0 or ist_short):
        etikett = "hebel"
        hebel = max(1.0, min(hebel_noetig, sicher, GRENZEN["hebel_max"]))
        betrag = einsatz_eur if hebel >= hebel_noetig - 1e-9 else risiko_eur / (hebel * stop_rel)
        # ⚠️ DIE BEDINGUNG WAR VERDREHT (22.08.2026, gefunden bei S6d).
        #
        # Hier stand `if hebel <= hebel_noetig + 1e-9`. Da `hebel` aus einem
        # min() ueber hebel_noetig kommt, ist das bei LONG IMMER wahr - die
        # beiden anderen Zweige waren toter Code. Ueber 18 geprueften
        # Kombinationen kam ausschliesslich "Risikobudget" heraus, auch bei
        # Stop 2,5 %, wo hebel_noetig 12,0 betraegt und der Hoechsthebel auf
        # 10,0 deckelt.
        #
        # RICHTIG HERUM: "Risikobudget" heisst, die Rechnung hat bekommen, was
        # sie brauchte. Liegt der Hebel DARUNTER, hat ein Deckel gebunden -
        # und welcher, ist genau die Auskunft, fuer die das Feld da ist.
        #
        # ⚠️ NIEMAND LIEST DAS FELD BISHER - deshalb ist es nie aufgefallen.
        # Das ist der Grund, es jetzt zu reparieren und nicht spaeter: die
        # erste Auswertung, die es benutzt, waere sonst falsch.
        if hebel >= hebel_noetig - 1e-9:
            gebunden = "Risikobudget"
        elif sicher <= GRENZEN["hebel_max"] + 1e-9 and hebel <= sicher + 1e-9:
            gebunden = "RM-11 Liquidationsabstand"
        else:
            gebunden = "Hoechsthebel"
    else:
        # KEIN HEBEL NOETIG (oder keiner handelbar): der Betrag folgt dem
        # Risikobudget. Ihn bei `einsatz_eur` zu lassen hiesse, mehr zu
        # riskieren als erlaubt - genau die stillschweigende Umdeutung, die
        # am 15.08. aus `max(1.0, ...)` entfernt wurde.
        etikett = "spot"
        hebel = 1.0
        betrag = min(einsatz_eur, risiko_eur / stop_rel)
        gebunden = ("Risikobudget" if risiko_eur / stop_rel < einsatz_eur
                    else "Einsatzwunsch")

    weg = GRENZEN["crv"] * abstand
    return Dimension({
        "stop_rel": stop_rel, "stop_eur": abstand, "stop_regel": regel,
        "boeden": {n: v / kurs for n, v in boeden.items()},
        "betrag_eur": betrag, "hebel": hebel, "etikett": etikett,
        "hebel_noetig": hebel_noetig, "hebel_sicher": sicher,
        "gebunden_durch": gebunden, "risiko_eur": risiko_eur,
        "tage": _haltedauer_tage(weg, atr),
        "unter_mindestgroesse": bool(mindestgroesse_eur
                                     and betrag < float(mindestgroesse_eur)),
        "hebel_handelbar": bool(hebel_handelbar),
    })
