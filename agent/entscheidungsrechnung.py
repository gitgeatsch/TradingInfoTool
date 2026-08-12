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
                  umgeworfen_preis_eur: float | None = None) -> tuple[float, str]:
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

    if (isinstance(umgeworfen_preis_eur, (int, float))
            and 0 < umgeworfen_preis_eur < kurs):
        abstand = kurs - float(umgeworfen_preis_eur)
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


def rechne(*, kurs: float | None, atr: float | None, risiko_eur: float | None,
           instrument: str = "spot", betrag_wunsch_eur: float | None = None,
           topf_frei_eur: float | None = None,
           umgeworfen_preis_eur: float | None = None,
           umgeworfen_tage: int | None = None) -> dict:
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
    abstand, stop_regel = _stop_abstand(kurs, atr, umgeworfen_preis_eur)
    stop_rel = abstand / kurs

    e = {
        "einstieg_eur": round(kurs, 2),
        "einstieg_von_eur": round(kurs - GRENZEN["zone_atr"] * atr, 2),
        "einstieg_bis_eur": round(kurs + GRENZEN["zone_atr"] * atr, 2),
        "stop_eur": round(kurs - abstand, 2),
        "stop_relativ": round(stop_rel, 5),
        "stop_regel": stop_regel,
        "ziel_eur": round(kurs + GRENZEN["crv"] * abstand, 2),
        "ziel_von_eur": round(kurs + GRENZEN["crv"] * abstand
                              - GRENZEN["zone_atr"] * atr, 2),
        "ziel_bis_eur": round(kurs + GRENZEN["crv"] * abstand
                              + GRENZEN["zone_atr"] * atr, 2),
        "crv": GRENZEN["crv"],
        "haltedauer_tage": (min(int(umgeworfen_tage), GRENZEN["tage_max"])
                            if isinstance(umgeworfen_tage, int) and umgeworfen_tage > 0
                            else _haltedauer_tage(GRENZEN["crv"] * abstand, atr)),
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
    if instrument != "hebel":
        # Ohne Hebel gibt es keinen Wunsch, nur eine Rechnung: der Einsatz
        # folgt vollstaendig aus Risikobudget und Stopabstand.
        betrag = risiko_eur / stop_rel
    if topf_frei_eur is not None and betrag > float(topf_frei_eur):
        betrag, grund = float(topf_frei_eur), "Topf"
    if betrag > GRENZEN["betrag_max_eur"]:
        betrag, grund = GRENZEN["betrag_max_eur"], "Hoechstbetrag"
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
        e["liquidation_etwa_eur"] = round(kurs * (1 - 1 / hebel), 2)
    else:
        e["hebel"] = 1.0

    e["betrag_eur"] = round(betrag, 0)
    e["betrag_gedeckelt_durch"] = grund
    # Was der Handel WIRKLICH riskiert, nachdem die Deckel gegriffen haben -
    # nicht das Budget, das hineingegeben wurde.
    e["verlust_am_stop_eur"] = round(betrag * e["hebel"] * stop_rel, 2)
    e["gewinn_am_ziel_eur"] = round(betrag * e["hebel"] * GRENZEN["crv"] * stop_rel, 2)
    return e


def saetze(e: dict) -> list[str]:
    """Die Rechnung in der Form, in der sie in die E-Mail gehoert."""
    z = [f"Einstiegszone   {e['einstieg_von_eur']:,.0f} bis {e['einstieg_bis_eur']:,.0f} EUR",
         f"Stop            {e['stop_eur']:,.0f} EUR  ({100 * e['stop_relativ']:.1f} % - {e['stop_regel']})",
         f"Take-Profit     {e['ziel_von_eur']:,.0f} bis {e['ziel_bis_eur']:,.0f} EUR  "
         f"(CRV {e['crv']:.1f})",
         f"Haltedauer      etwa {e['haltedauer_tage']} Handelstage "
         f"({e.get('haltedauer_quelle', 'geschaetzt')})",
         f"Betrag          {e['betrag_eur']:,.0f} EUR"
         + (f"  - begrenzt durch {e['betrag_gedeckelt_durch']}"
            if e.get("betrag_gedeckelt_durch") else "")]
    if e["hebel"] > 1:
        z.append(f"Hebel           {e['hebel']:.1f}x  (Grenze: {e['hebel_grenze']}; "
                 f"Liquidation etwa {e['liquidation_etwa_eur']:,.0f} EUR)")
    z.append(f"Am Stop verlieren Sie {e['verlust_am_stop_eur']:,.0f} EUR, "
             f"am Ziel gewinnen Sie {e['gewinn_am_ziel_eur']:,.0f} EUR.")
    return z
