# -*- coding: utf-8 -*-
"""Die EINE Stelle, an der die Eingabe fuer die Rollen entsteht.

WARUM ES DIESE DATEI GIBT (12.08.2026). Bis hierher baute jedes Messskript die
Eingabe selbst zusammen - `pruefe_rollenkette`, `messe_degradierung`,
`messe_faktorzahl`, `messe_dritter_faktor`, `messe_abgleich_alt_neu`,
`messe_marktphasen`. Sechs Stellen mit demselben Aufbau.

Das hatte zwei Folgen, beide belegt:

  * Die Finanzierungsrate war gebaut (Faktenmappe 12.9) und liess sich trotzdem
    nicht "anschliessen" - es gab keinen Ort dafuer. Sie haette in sechs
    Skripte einzeln eingesetzt werden muessen.
  * Zwei Skripte riefen die Marktbreite mit `mit_bezug=False` auf, zwei mit
    `True`. Der Kalibrierungssatz, der die Zuspitzung eindaemmen soll, fehlte
    also in der Haelfte aller Messungen - unbemerkt (Arbeitsstand 7.14).

Wer die Eingabe aendern will, aendert sie hier. Wer sie an sechs Stellen
aendert, aendert sie an fuenf.

WAS HIER NICHT HINEINGEHOERT: Netzwerkaufrufe im Zweifel. `finanzierung` wird
als fertige Zusammenfassung uebergeben, nicht hier geholt - sonst haengt eine
Beschreibung an einer Boersen-API und faellt mit ihr aus. Der Aufrufer holt und
entscheidet, was bei einem Ausfall geschieht.
"""
from __future__ import annotations

import numpy as np


def baue_lagebild_eingabe(reihen: dict, datum: str) -> dict:
    """Eingabe fuer das Lagebild. MIT historischem Bezug, immer.

    `mit_bezug=True` ist hier nicht optional: der Satz "in X % der Faelle war
    dieser Anteil niedriger" ist die einzige Kalibrierung, die das Modell vor
    einer Zuspitzung schuetzt. Zwei Messungen liefen ohne ihn, und in genau
    einer davon wurde aus einem knapp durchschnittlichen Wert eine "extreme
    Schieflage"."""
    from agent.marktbreite import beschreibe_marktbreite
    return {"marktlage": beschreibe_marktbreite(reihen, datum, mit_bezug=True)}


def baue_befund_eingabe(*, symbol: str, reihe: list, index: int,
                        kurs_eur: float, atr: float,
                        menge: float | None = None,
                        einstand_eur: float | None = None,
                        finanzierung: dict | None = None,
                        lagebild: dict | None = None) -> dict:
    """Eingabe fuer Befund und Entscheidung - alle Bloecke an einer Stelle."""
    from agent.lagebeschreibung import beschreibe_lage
    aus = {"asset": symbol,
           "stand": beschreibe_lage(symbol=symbol, reihe=reihe, index=index,
                                    kurs_eur=kurs_eur, atr=atr, menge=menge,
                                    einstand_eur=einstand_eur,
                                    finanzierung=finanzierung)}
    if lagebild:
        aus["marktlage_beurteilung"] = {"traegt": lagebild.get("traegt"),
                                        "lage": lagebild.get("lage")}
    return aus


def hole_finanzierung(symbol: str, datum: str, session=None,
                      zwischenspeicher: dict | None = None) -> dict | None:
    """Finanzierungsrate zum ANKERTAG, kausal abgeschnitten.

    FAIL-SOFT UND STILL: Faellt die Boerse aus oder kennt sie das Symbol nicht,
    kommt None zurueck und der Block entfaellt. Das ist richtig so - ein Satz
    "keine Finanzierungsdaten" waere fuer alle Aktien, ETF und Rohstoffe
    identisch und damit ein konstantes Feld (B10).

    ABER: der Aufrufer muss zaehlen, wie oft None kam. Ein stiller Ausfall, den
    niemand zaehlt, ist genau das U-Boot, das dieses Projekt mehrfach bezahlt
    hat. `zwischenspeicher` dient zugleich der Taktung - dieselbe Kombination
    wird nur einmal geholt."""
    from datetime import datetime, timezone
    schluessel = (symbol, datum[:10])
    if zwischenspeicher is not None and schluessel in zwischenspeicher:
        return zwischenspeicher[schluessel]
    ergebnis = None
    try:
        from api.derivatives import get_funding_history, summarize_funding
        ende = int(datetime.fromisoformat(datum[:10]).replace(
            tzinfo=timezone.utc).timestamp() * 1000)
        ergebnis = summarize_funding(
            get_funding_history(f"{symbol}USDT", 100, session, ende))
    except Exception:                                            # noqa: BLE001
        ergebnis = None
    if zwischenspeicher is not None:
        zwischenspeicher[schluessel] = ergebnis
    return ergebnis


def pruefe_lagebild(ausgabe: dict, eingabe: dict) -> dict:
    """Der Waechter auf der NAHT zwischen den Rollen (R-T8).

    Die bestehenden Waechter pruefen EINGABEN. Die Ausgabe des Lagebilds ist die
    Eingabe der Entscheidung - und wurde nie geprueft. Belegt am 11.08.: aus
    "8 % ueber der 50-Tage-Linie, in 46 % der Faelle war dieser Anteil
    niedriger" wurde "extreme Schieflage mit starkem Abwaertsdruck", und dieser
    Satz erreichte die Entscheidung als Beleg mit Gewicht HOCH.

    VERMERKEN, NICHT ABLEHNEN. Eine Ablehnung erzeugt eine Wiederholung und am
    Ende kein Signal - derselbe Deadloop an anderer Stelle (R-A5). Und den Text
    umzuschreiben waere schlimmer: dann stuende dort ein Satz, den niemand
    verantwortet. Der Verstoss wird gezaehlt und sichtbar gemacht; was daraus
    folgt, ist eine Entscheidung des Nutzers, keine des Waechters."""
    from agent.waechter_zuspitzung import pruefe
    text = " ".join(str(v) for v in (ausgabe.get("lage"), *(ausgabe.get("belege") or [])))
    ergebnis = pruefe(text, eingabe.get("marktlage") or [])
    if ergebnis.get("verstoss"):
        ausgabe["_zuspitzung"] = (
            f"unbelegte Gradbehauptung {ergebnis['hart']} - {ergebnis['grund']}")
    return ergebnis
