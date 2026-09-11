# -*- coding: utf-8 -*-
"""Wieviel wird eingesetzt, und wieviel davon darf weg sein (13.08.2026).

DIE FRAGE DES NUTZERS, die dieses Modul erzwungen hat: *„was ist das Problem
genau mit meinem Betrag"* - nachdem in `rollen_lauf` `risiko_eur=75.0` und
`betrag_wunsch_eur=500.0` fest verdrahtet standen. Zahlen, die niemand
hergeleitet hatte und die jedes Signal gleich gross machten.

DIE UMPARAMETRISIERUNG IST DER KERN. Statt eines absoluten Risikobetrags steht
hier ein ANTEIL VOM EINSATZ:

    Risiko in Euro  =  Einsatz × Verlustanteil
    Hebel           =  Verlustanteil ÷ Kursverlust bis Stop

Der Hebel haengt damit am ANTEIL, nicht am Betrag: 500 oder 1.000 EUR ergeben
denselben Hebel, nur doppeltes Volumen. Einsatz und Hebel sind getrennt
einstellbar - vorher waren sie es nicht.

WARUM DAS DIE RICHTIGE GROESSE IST, in den Worten des Nutzers: *„ich setze
meist zwischen 2 und 8 Prozent - glaube aber Kursverlust und nicht
Kapitalverlust und nicht als Teil des Gesamtportfolios"*. Er beschreibt damit
zwei verschiedene Dinge, und das System braucht beide getrennt:

    2-8 % Kursverlust     der STOPABSTAND. Wird laengst gerechnet - gemessen
                          Median 5,3 %, Spanne 2,5-9,3 %. Deckt sich mit seiner
                          Einschaetzung, ohne dass jemand es abgestimmt haette.
    15-20 % vom Einsatz   der KAPITALVERLUST. Steht hier.

KEIN PORTFOLIOWERT, aus demselben Grund wie bei den Toepfen (Paket 5): ein
Prozentsatz auf ein Depot mit 60-Prozent-Positionen schrumpft genau dann, wenn
wieder gehandelt werden muesste. Der Nutzer hat es unabhaengig davon selbst
gesagt - *„nicht als Teil des Gesamtportfolios"*.

DER EINSATZ HAENGT AN DER STRATEGIE, NICHT AM INSTRUMENT. Ein Einmalkauf
schiebt keine zweite Tranche nach und darf deshalb groesser sein als ein
DCA-Schritt. Die Kette unterscheidet `einstieg` / `swing` / `akkumulation`
seit Paket 2 - hier wird die Unterscheidung endlich benutzt.
"""
from __future__ import annotations

# Alle Werte am 13.08.2026 vom Nutzer festgelegt. Wer sie aendert, aendert sie
# in `config.yaml` unter `risiko.rollen_kette` - hier stehen nur die Vorgaben.
#
#   spot.akkumulation   250   *"deine Annahme einer Tranche ist mit 200-250
#                             ganz gut"* - oberes Ende
#   spot.einstieg       800   *"wuerde bei Einmalkauf eher 500 bis 800
#                             ansetzen"* - oberes Ende, weil ein Einmalkauf
#                             keine zweite Tranche nachschiebt
#   spot.swing            -   GESTRICHEN 14.08. Es war die einzige geratene
#                             Zahl hier, und das Paar gibt es nicht mehr:
#                             Swing ist ueber einen nachgezogenen Stop
#                             definiert, den der Nutzer auf Spot nicht setzt.
#   hebel.*            1000   *"bei Hebel wuerde ich eher 500 nehmen"*, spaeter
#                             *"eine Hebelposition vorerst 1000"*
VORGABE_EINSATZ_EUR: dict[str, dict[str, float]] = {
    # `swing` FEHLT HIER BEWUSST (14.08.): das Paar spot x swing ist in
    # `handelsauftrag.ERLAUBTE_PAARE` gestrichen, weil Swing ueber einen
    # nachgezogenen Stop definiert ist und der Nutzer Spot ohne Stop haelt.
    # Ein Betrag fuer ein unmoegliches Paar waere eine Zahl ohne Bedeutung -
    # und ausgerechnet die einzige, die ich geraten hatte.
    # ⚠️ 800 IST EIN VORLAEUFIGER WERT (Nutzervorgabe 23.08.2026).
    #
    # Seit S6b laeuft Krypto mit EINEM Lauf, und `einsatz_eur` geht in
    # `dimensioniere()` HINEIN, waehrend der Hebel DARAUS anfaellt
    # (`verlustanteil / stop_rel`). Er kann also nicht vom Ergebnis abhaengen:
    # die alte Aufteilung 800 (spot) / 1.000 (hebel) ist technisch nicht mehr
    # darstellbar, es gibt genau eine Zahl je Gruppe und Strategie.
    #
    # ⚠️ UND DIE 1.000 WAR NIE EIN STANDARDWERT, sondern die Obergrenze -
    # `entscheidungsrechnung.GRENZEN["betrag_max_eur"]`, hergeleitet aus
    # *"500 - max 1000 aktuell"*. Der Hebel-Pfad hat sie nur als Zielgroesse
    # benutzt. Deshalb ist 800 der Ausgangspunkt und nicht 1.000.
    #
    # WANN SIE STEIGEN DARF - und das ist eine MESSBARE Bedingung, kein
    # Gefuehl: erst wenn die Trefferquote den Breakeven
    # `(1 + Kosten) / (1 + CRV)` ueber eine belastbare Zahl von Faellen
    # schlaegt. Heute liegt sie bei 27,8 % gegen eine Basisrate von 33,3 %
    # (Kapitel 141) - eine groessere Position waere dort ein groesserer
    # Fehler, keine Verbesserung. Traegt die Auswahl, gehoert die Zahl nach
    # oben geprueft, bis zur Obergrenze und danach ueber sie hinaus.
    "spot": {"einstieg": 800.0, "akkumulation": 250.0},
    "hebel": {"einstieg": 1000.0, "swing": 1000.0, "akkumulation": 1000.0},
    # Die Absicherung bemisst sich am abzusichernden Exposure, nicht an einem
    # Wunschbetrag (siehe `toepfe.einsatz_fuer_absicherung`). Der Wert hier ist
    # nur die Rueckfallgroesse, wenn kein Exposure bekannt ist.
    "absicherung": {"einstieg": 500.0, "swing": 500.0, "akkumulation": 500.0},
}

# Wieviel vom EINSATZ darf im schlechtesten Fall verloren gehen.
#
# *"Verlust Margin ca. 15 -20 Prozent bin mir aber nicht sicher"* - unteres Ende
# genommen, weil eine zu grosse Zahl hier direkt den Hebel hochtreibt.
#
# BEI SPOT OHNE STOP-ORDER IST DAS KEINE ORDER, SONDERN EINE RECHENGROESSE. Der
# Nutzer haelt Spot *"aktuell auch ohne StopLoss"* - der Wert bestimmt dort nur
# die Groesse, nicht eine Verkaufsanweisung.
VORGABE_VERLUSTANTEIL: dict[str, float] = {
    "spot": 0.15,
    "hebel": 0.15,
    "absicherung": 0.15,
}


class BetragUnbekannt(ValueError):
    """Kein Einsatz fuer dieses Paar - wirft, statt still 500 zu nehmen."""


def _cfg(config: dict | None, name: str) -> dict:
    """Eine Einstellung der Rollen-Kette - aus BEIDEN moeglichen Orten.

    DIE FALLE, DIE DAS BEHEBT (14.08.2026). Dieses Modul las unter
    `risiko.rollen_kette.*`, alle uebrigen Leser der Kette unter
    `rollen_kette.*` an oberster Stelle:

        rollen_job     aktiv_fuer, betriebsart      -> rollen_kette.*
        rollen_lauf    verkauf_mailt                -> rollen_kette.*
        wiederholung   cooldown_stunden_je_gruppe   -> rollen_kette.*
        betraege       einsatz_eur, verlustanteil   -> risiko.rollen_kette.*

    UND `risiko.rollen_kette` GIBT ES IN DER config.yaml NICHT. Wer den Einsatz
    fuer Aktien setzen wollte, haette ihn naheliegenderweise unter
    `rollen_kette:` eingetragen - dorthin, wo `aktiv_fuer` und `betriebsart`
    schon stehen - und es waere WIRKUNGSLOS geblieben. Ohne Fehlermeldung, denn
    ein fehlender Schluessel ist hier legitim.

    Gefunden bei der Nutzerfrage nach `verkauf_mailt`, also beim Nachsehen fuer
    eine Erklaerung - nicht beim Bauen. Genau dafuer ist "immer an der Quelle
    pruefen" da.

    OBERSTE STELLE GEWINNT, weil dort alles andere steht. Der alte Ort bleibt
    lesbar: eine bestehende Einstellung soll nicht durch das Aufraeumen
    ausfallen."""
    c = config or {}
    oben = (c.get("rollen_kette") or {}).get(name) or {}
    unten = ((c.get("risiko") or {}).get("rollen_kette") or {}).get(name) or {}
    return {**unten, **oben}


# Abweichungen je GRUPPE (14.08.). Leer heisst: es gilt der Wert des
# Instruments - und das ist der Normalfall.
#
# WARUM NICHT FUER JEDE GRUPPE EIN EIGENER WERT: der Nutzer hat Betraege fuer
# Krypto genannt, nicht fuer Aktien. Sie einfach zu uebernehmen waere eine
# Zahl mit falscher Herkunft; sie zu erfinden waere schlimmer. Der Haken haengt
# hier bereit, gefuellt wird er, wenn jemand ihn fuellen kann.
#
# ROHSTOFFE UND THEMEN-ETF haben allerdings eine BOERSEN-FIXGEBUEHR (1 EUR je
# Seite). Bei einer 250-EUR-Tranche sind das 0,8 % allein an Fixkosten - der
# Breakeven liegt dort ueber fuenf Prozentpunkte hoeher als bei 1.000 EUR
# (gemessen in `trefferbilanz.kosten_r_aus_stop`). Eine kleine Tranche ist dort
# also teurer als bei Krypto, wo sich der Betrag herauskuerzt.
# O-17: WOHER DIE 800 KOMMEN - und woher NICHT (14.08.2026).
#
# Die 800 sind von Krypto uebernommen, nicht fuer die Boerse entschieden. Der
# Nutzer hat Betraege fuer Krypto genannt (Tranche 200-250, Hebel 1.000); fuer
# Aktien, Rohstoffe und Themen-ETF gibt es keine Angabe.
#
# WAS DIE KOSTEN DAZU SAGEN, bei 5 % Stop und 1 EUR fix je Seite:
#
#     Betrag    Fixkostenanteil   Gesamtkosten   in R
#      250 EUR         0,80 %         1,30 %     0,260
#      400 EUR         0,50 %         1,00 %     0,200
#      800 EUR         0,25 %         0,75 %     0,150
#    1.000 EUR         0,20 %         0,70 %     0,140
#
# Die Kurve wird ab etwa 800 EUR flach - der Sprung von 250 auf 800 halbiert
# die Kosten in R, der von 800 auf 1.500 spart nur noch 0,023 R. 800 liegt
# also am Knick, und das ist ein Argument, aber KEINE Entscheidung: wieviel
# Geld in eine einzelne Aktie geht, ist eine Risikofrage und gehoert dem
# Nutzer.
#
# UEBERSCHREIBBAR unter `rollen_kette.einsatz_eur_je_gruppe`
# (seit 14.08. auch dort - vorher las dieses Modul als EINZIGES unter
# `risiko.rollen_kette.*`, einem Ort, den es in der config.yaml nicht gibt),
# damit die
# Entscheidung eine Konfigurationszeile ist und kein Codeeingriff.
VORGABE_EINSATZ_JE_GRUPPE: dict[str, dict[str, float]] = {
    "aktien": {"einstieg": 800.0, "akkumulation": 400.0},
    "rohstoffe": {"einstieg": 800.0, "akkumulation": 400.0},
    "themen_etf": {"einstieg": 800.0, "akkumulation": 400.0},
}


def einsatz_eur(instrument: str, strategie: str,
                config: dict | None = None, gruppe: str | None = None) -> float:
    """Der gewuenschte Einsatz fuer DIESES Paar aus Instrument und Strategie.

    WIRFT BEI EINEM UNBEKANNTEN PAAR, statt auf einen Vorgabewert zu fallen.
    Ein stiller Rueckfall waere genau der Fehler, den `handelsauftrag.pruefe()`
    eine Ebene hoeher verhindert: ein Paar, das niemand vorgesehen hat, soll
    auffallen und nicht mit 500 EUR weiterlaufen."""
    i, s = str(instrument or "").strip().lower(), str(strategie or "").strip().lower()
    g = str(gruppe or "").strip().lower()
    ueber = _cfg(config, "einsatz_eur")
    # REIHENFOLGE: Instrument-Vorgabe, dann Gruppen-Vorgabe, dann Konfiguration
    # je Instrument, zuletzt je Gruppe. Das Spezifischere gewinnt, und die
    # Konfiguration gewinnt immer gegen den Code.
    tabelle = {**VORGABE_EINSATZ_EUR.get(i, {}),
               **VORGABE_EINSATZ_JE_GRUPPE.get(g, {}),
               **(ueber.get(i) or {}),
               **((_cfg(config, "einsatz_eur_je_gruppe") or {}).get(g) or {})}
    if s not in tabelle:
        raise BetragUnbekannt(
            f"kein Einsatz fuer {instrument!r}/{strategie!r} - bekannt: "
            f"{sorted(VORGABE_EINSATZ_EUR)} x {sorted(VORGABE_EINSATZ_EUR['spot'])}")
    return float(tabelle[s])


def stop_min_atr(config: dict | None = None) -> float | None:
    """Der ATR-Faktor des Rauschbodens - oder None, wenn nichts gesetzt ist.

    S1 DES UMBAUPLANS KAPITEL 90 (18.08.2026). Bisher war der Wert eine feste
    Zahl in `entscheidungsrechnung.GRENZEN` und damit nur durch eine
    Codeaenderung zu bewegen. Der gleichnamige Schluessel
    `risiko.sl_abstand_min_atr_faktor` steuert die ALTEN Pipelines und wird
    von der Rollen-Kette nicht gelesen - wer ihn drehte, aenderte hier nichts.

    GIBT None STATT EINES VORGABEWERTS. Die Vorgabe steht an genau einer
    Stelle (`GRENZEN["stop_min_atr"]`); sie hier zu wiederholen hiesse,
    dieselbe Zahl an zwei Orten zu pflegen - der Fehler aus Umbauplan 70.4.

    ⚠️ DIESER SCHALTER AENDERT DAS VERHALTEN DER KETTE. Ohne Eintrag in der
    Konfiguration bleibt alles, wie es war; mit Eintrag verschiebt sich der
    Stop und damit Betrag, Hebel und Etikett jedes Signals."""
    # `_cfg` liefert ein dict; hier steht ein Skalar. Beide Pfade werden
    # gelesen, damit der Schluessel dort stehen darf, wo der Nutzer ihn
    # vermutet - dieselbe Falle wie am 14.08. beim Einsatz.
    _q = config or {}
    roh = ((_q.get("rollen_kette") or {}).get("stop_min_atr")
           if isinstance(_q.get("rollen_kette"), dict) else None)
    if roh is None:
        roh = (((_q.get("risiko") or {}).get("rollen_kette") or {})
               .get("stop_min_atr"))
    wert = roh if isinstance(roh, (int, float)) else None
    if wert is None:
        return None
    if not 0 < float(wert) <= 10:
        raise BetragUnbekannt(
            f"stop_min_atr {wert!r} liegt ausserhalb (0, 10] - ein Faktor "
            f"auf die Schwankungsbreite, keine Prozentzahl")
    return float(wert)


def verlustanteil(instrument: str, config: dict | None = None) -> float:
    """Welcher Anteil des Einsatzes darf im schlechtesten Fall weg sein.

    ⚠️ DIES IST DIE SPOT/HEBEL-GRENZE DER NEUEN KETTE (18.08.2026), auch
    wenn der Name das nicht sagt. Es gilt `Hebel = Verlustanteil /
    Stopabstand`, also `Hebel > 1 <=> Stop < Verlustanteil`. Bei 15 % ist
    praktisch jedes Geschaeft ein Hebelgeschaeft, unabhaengig davon, wie
    der Stop gesetzt wird.

    NICHT ZU VERWECHSELN mit `config.yaml::risiko_pro_trade_prozent` und
    `risiko_pro_trade_prozent_hebel`. Die beiden Schluessel steuern die
    ALTEN Pipelines (risk_gate.py, hebel_risk_gate.py) und werden von der
    Rollen-Kette nicht gelesen. Sie sagen 1 bzw. 2 %, hier stehen 15 % -
    wer das eine liest und das andere meint, irrt um den Faktor fuenf."""
    i = str(instrument or "").strip().lower()
    ueber = _cfg(config, "verlustanteil")
    wert = ueber.get(i, VORGABE_VERLUSTANTEIL.get(i))
    if wert is None:
        raise BetragUnbekannt(f"kein Verlustanteil fuer {instrument!r}")
    return float(wert)


def risiko_eur(instrument: str, strategie: str, config: dict | None = None,
               gruppe: str | None = None) -> float:
    """Der Euro-Betrag, den dieser Handel hoechstens kosten darf.

    DIE EINE STELLE, an der aus Anteil und Einsatz ein Betrag wird. Ihn
    anderswo noch einmal zu rechnen hiesse, die Beziehung zwischen beiden an
    zwei Orten zu pflegen."""
    return (einsatz_eur(instrument, strategie, config, gruppe)
            * verlustanteil(instrument, config))


# ---------------------------------------------------------------------------
# H-2 / K1 - DER HEBEL AUS DER WAHRSCHEINLICHKEIT (Paket B, 11.09.2026)
# ---------------------------------------------------------------------------
# Nutzerauftrag 28.08./05.09.: *"die Wahrscheinlichkeit auf positive Risiko
# und Chance soll auch den Hebel dynamisch erzeugen"*, Zielzone 2-5x.
# Nutzerentscheidung 11.09. (Paket B): unter 2x Spot, harte Grenze 5x bis zur
# Trennschaerfe, Quote unkalibriert, Spot-Betrag UNVERAENDERT (N-38).
#
#     risiko  = r(q) x Kapital          r(q) = halbes Kelly, geklammert
#     nominal = risiko / Stopabstand     der Stop bestimmt nur die GROESSE
#     hebel   = nominal / Hebelnenner    faellt an, wird nicht gewaehlt
#
# ⚠️ HEUTE STAND HIER `hebel = verlustanteil / stop_rel` (Befund 2.174-ist):
# der Hebel kam aus der GEOMETRIE, die Quote ging nicht ein. Genau das war
# die Luecke zum Auftrag.
#
# ⚠️ WARUM EINE KLAMMER (Anforderungen N-39): bei CRV 2 liegt der Nullpunkt
# exakt bei q = 33,3 %; ein Prozentpunkt Fehler in q verschiebt die Nominale
# um Tausende. Solange die Trennschaerfe nicht gemessen ist (A1), setzt das
# Band die Grenzen, nicht die Formel.
#
# ⚠️ AUS, bis Schritt 19 die Hebelverteilung simuliert hat - der Plan
# verlangt die Simulation VOR dem Scharfschalten. Umschalten in
# `config.yaml` unter `rollen_kette.hebel_aus_quote.aktiv`.
HEBEL_AUS_QUOTE_VORGABE: dict = {
    "aktiv": False,
    "r_min": 0.005,            # 0,50 % des Kapitals (N-39)
    "r_max": 0.0125,           # 1,25 % des Kapitals (N-39)
    "hebelnenner_eur": 500.0,  # Nutzer 05.09.: "500 ok als Basiswert"
    "hebel_ab": 2.0,           # Nutzer 05.09.: "ein Hebel unter 2 ist kein Hebel"
    "hebel_grenze": 5.0,       # Nutzer 11.09.: Deckel 5x bis zur Trennschaerfe
    "aggregat_anteil": 0.03,   # Nutzer 11.09.: alle Hebelrisiken zusammen
                               # hoechstens 3 % des Kapitals (H-5, hebel_aggregat)
}


def hebel_aus_quote_einstellungen(config: dict | None = None) -> dict:
    """Die Einstellungen der Hebelrechnung - Vorgabe, von `config.yaml`
    (`rollen_kette.hebel_aus_quote`) ueberschrieben."""
    return {**HEBEL_AUS_QUOTE_VORGABE, **_cfg(config, "hebel_aus_quote")}


def hebelrechnung(*, quote: float, crv: float, kapital_eur: float,
                  stop_rel: float, einstellungen: dict | None = None,
                  kapital_satz: str = "",
                  hebel_sicher: float | None = None,
                  aggregat: dict | None = None) -> dict:
    """Der Hebel aus der Wahrscheinlichkeit - REIN, ohne DB, Uhr oder Netz.

    ⚠️ OHNE POSITIVE ERWARTUNG KEIN HEBEL. Ist das volle Kelly <= 0, sagt
    die Formel: nicht setzen. Die Untergrenze der Klammer wird dann NICHT
    angewandt - sonst entstuende aus einer negativen Erwartung ein
    Mindestrisiko und bei engem Stop ein Hebelgeschaeft. Die Bewertungs-
    schwelle sperrt solche Faelle ohnehin; diese Funktion verlaesst sich
    nicht darauf.

    ⚠️ WIRFT BEI FALSCHER EINGABE, statt zu raten - dieselbe Linie wie
    `einsatz_eur()`.

    Rueckgabe: kelly, kelly_halb, r, klammer, risiko_eur, nominal_eur,
    hebel_roh, hebel (gedeckelt), ist_hebel, grenze_greift und `saetze` -
    die Herleitung in EUR fuer die Mail."""
    from agent.schreibweise import de as _de

    e = {**HEBEL_AUS_QUOTE_VORGABE, **(einstellungen or {})}
    try:
        q, c = float(quote), float(crv)
        kap, stop = float(kapital_eur), float(stop_rel)
    except (TypeError, ValueError) as exc:
        raise BetragUnbekannt(f"Hebelrechnung ohne Zahl: {exc}") from exc
    if not 0.0 < q < 1.0:
        raise BetragUnbekannt(f"Quote {quote!r} liegt nicht zwischen 0 und 1")
    if c <= 0 or kap <= 0 or stop <= 0:
        raise BetragUnbekannt(
            f"CRV {crv!r}, Kapital {kapital_eur!r} und Stop {stop_rel!r} "
            f"muessen positiv sein")
    r_min, r_max = float(e["r_min"]), float(e["r_max"])
    nenner, ab = float(e["hebelnenner_eur"]), float(e["hebel_ab"])
    grenze = float(e["hebel_grenze"])

    kelly = (q * (1.0 + c) - 1.0) / c
    halb = kelly / 2.0
    aus = {"quote": q, "crv": c, "kapital_eur": kap, "stop_rel": stop,
           "kelly": kelly, "kelly_halb": halb, "r": 0.0, "klammer": "",
           "risiko_eur": 0.0, "nominal_eur": 0.0, "hebel_roh": 0.0,
           "hebel": 1.0, "ist_hebel": False, "grenze_greift": False,
           "hebelnenner_eur": nenner, "hebel_ab": ab,
           "hebel_grenze": grenze, "hebel_sicher": None,
           "liquidation_greift": False, "risiko_vor_aggregat_eur": 0.0,
           "aggregat_greift": False, "aggregat": aggregat, "saetze": []}
    kopf = ("Hebel aus der Wahrscheinlichkeit: Trefferquote %s %% bei CRV %s"
            % (_de(100 * q, 1), _de(c, 1)))
    if kelly <= 0:
        aus["saetze"] = [kopf + " - keine positive Erwartung (halbes Kelly "
                         "%s %%), daher kein Hebel"
                         % _de(100 * halb, 2, vorzeichen=True)]
    else:
        r = min(max(halb, r_min), r_max)
        klammer = ("Obergrenze" if halb > r_max
                   else "Untergrenze" if halb < r_min else "")
        risiko_voll = r * kap
        # ⚠️⚠️ H-5 (11.09.2026): DER AGGREGAT-DECKEL. Alle offenen
        # Hebelrisiken zusammen hoechstens `aggregat_anteil` des Kapitals
        # (`hebel_aggregat.aggregat`). Er BEGRENZT: dieser Trade bekommt
        # hoechstens das freie Restrisiko. Faellt der Hebel dadurch unter
        # `hebel_ab`, wird es Spot - die Paket-B-Regel gilt unveraendert.
        # Ohne `aggregat` (Aufrufer ohne Portfolioblick, Simulation) wie bisher.
        frei = (None if aggregat is None
                else max(0.0, float(aggregat.get("frei_eur") or 0.0)))
        risiko = risiko_voll if frei is None else min(risiko_voll, frei)
        agg_greift = bool(frei is not None and risiko < risiko_voll - 1e-9)
        nominal = risiko / stop
        roh = nominal / nenner
        # ⚠️ DER LIQUIDATIONSABSTAND ZAEHLT MIT (Gegenpruefung 11.09.): was
        # `rechne()` spaeter auf RM-11 deckelt, muss schon hier gelten - sonst
        # hiesse es ,Hebel', und die Rechnung ergaebe weniger.
        sicher = float(hebel_sicher) if hebel_sicher else None
        moeglich = min(roh, sicher) if sicher else roh
        ist = moeglich >= ab - 1e-9
        aus.update(r=r, klammer=klammer, risiko_eur=risiko,
                   nominal_eur=nominal, hebel_roh=roh, ist_hebel=ist,
                   hebel=(min(moeglich, grenze) if ist else 1.0),
                   hebel_sicher=sicher,
                   grenze_greift=bool(ist and moeglich > grenze + 1e-9),
                   liquidation_greift=bool(ist and sicher
                                           and roh > sicher + 1e-9
                                           and sicher < grenze),
                   risiko_vor_aggregat_eur=risiko_voll,
                   aggregat_greift=agg_greift)
        zeile2 = ("   bei %s %% Stop: %s EUR Positionswert / %s EUR Einsatz "
                  "= %sx" % (_de(100 * stop, 1), _de(nominal, 0),
                             _de(nenner, 0), _de(roh, 1)))
        if not ist and agg_greift:
            zeile2 += (" - nach dem Aggregat-Deckel unter %sx, daher Spot mit "
                       "dem gewohnten Betrag" % _de(ab, 1))
        elif not ist and sicher and roh >= ab - 1e-9:
            zeile2 += (" - der Liquidationsabstand erlaubt nur %sx, daher "
                       "Spot mit dem gewohnten Betrag" % _de(sicher, 1))
        elif not ist:
            zeile2 += (" - unter %sx, daher Spot mit dem gewohnten Betrag"
                       % _de(ab, 1))
        elif aus["liquidation_greift"]:
            zeile2 += (" -> der Liquidationsabstand erlaubt hoechstens %sx"
                       % _de(sicher, 1))
        elif aus["grenze_greift"]:
            zeile2 += (" -> Grenze %sx (bis die Trennschaerfe gemessen ist)"
                       % _de(grenze, 1))
        aus["saetze"] = [
            kopf + " -> halbes Kelly %s %% -> Risiko %s %%%s von %s EUR "
            "Kapital = %s EUR" % (_de(100 * halb, 2), _de(100 * r, 2),
                                  (" (%s)" % klammer) if klammer else "",
                                  _de(kap, 0), _de(risiko_voll, 0))]
        # H-5: DER STAND DES AGGREGAT-DECKELS - zwischen dem Risiko aus r(q)
        # und der Positionsgroesse, denn er steht auch in der Rechnung dazwischen.
        if aggregat is not None:
            _az = "   " + str(aggregat.get("satz")
                              or "Aggregat-Deckel: frei %s EUR" % _de(frei, 0))
            if agg_greift:
                _az += (" -> dieser Trade traegt %s statt %s EUR"
                        % (_de(risiko, 0), _de(risiko_voll, 0))
                        if risiko > 0 else " -> ausgeschoepft")
            aus["saetze"].append(_az)
        aus["saetze"].append(zeile2)
    if kapital_satz and "⚠️" in kapital_satz:
        aus["saetze"].append("   " + kapital_satz)
    return aus
