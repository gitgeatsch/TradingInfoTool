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
