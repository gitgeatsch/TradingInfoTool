"""Positionsgroesse der REGEL0 im Betrieb (Schritt 7, E-44) - reine Rechnung, keine Datenbank, kein Netz.

Startwerte stehen in ``Basisinfos/regel0_betrieb.yaml`` und sind dort jederzeit aenderbar (Nutzer 02.10.2026:
*"so bauen, dass dies einfach und flexibel angepasst werden kann"*). Die Hebelstufe kommt aus der REGEL0 und wird hier nicht veraendert.

    Einsatz      = Positionswert / Hebelstufe, begrenzt auf [einsatz_min_eur, einsatz_max_eur]
    Positionswert = Einsatz x Hebelstufe (nach der Begrenzung)
    Verlust max  = Einsatz (Liquidation) - Gebuehren sind nicht Teil der Bewertung (Regel 2), nur Information
    Richtwert    = Anzahl gleichzeitig offener REGEL0-Trades; erreicht -> Vermerk, Sperre nur wenn sperre_ab_richtwert
"""
from __future__ import annotations

import os
from dataclasses import dataclass

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEI = os.path.join(HIER, "Basisinfos", "regel0_betrieb.yaml")

# Rueckfall, falls die Datei fehlt - dieselben Startwerte wie in der Datei (E-44)
VORGABE = dict(positionswert_eur=1500.0, einsatz_min_eur=300.0, einsatz_max_eur=800.0,
               richtwert_gleichzeitig=4, sperre_ab_richtwert=False)


def lade(pfad: str | None = None) -> dict:
    """Werte aus regel0_betrieb.yaml; fehlende Schluessel aus VORGABE. Unbekannte Schluessel brechen ab (Tippfehler sichtbar)."""
    pfad = pfad or DATEI
    werte = dict(VORGABE)
    if os.path.exists(pfad):
        import yaml
        roh = yaml.safe_load(open(pfad, encoding="utf-8")) or {}
        fremd = set(roh) - set(VORGABE)
        if fremd:
            raise ValueError("regel0_betrieb.yaml: unbekannte Schluessel %s" % sorted(fremd))
        werte.update(roh)
    if not (0 < werte["einsatz_min_eur"] <= werte["einsatz_max_eur"]):
        raise ValueError("regel0_betrieb.yaml: einsatz_min_eur muss > 0 und <= einsatz_max_eur sein")
    if werte["positionswert_eur"] <= 0 or int(werte["richtwert_gleichzeitig"]) < 1:
        raise ValueError("regel0_betrieb.yaml: positionswert_eur > 0 und richtwert_gleichzeitig >= 1")
    return werte


@dataclass(frozen=True)
class Groesse:
    hebelstufe: int
    einsatz_eur: float
    positionswert_eur: float
    verlust_max_eur: float
    offen_vorher: int
    richtwert_erreicht: bool
    gesperrt: bool
    vermerk: str


def rechne(hebelstufe: int, offen_vorher: int, werte: dict | None = None) -> Groesse:
    """Einsatz und Vermerk fuer einen neuen REGEL0-Trade. ``offen_vorher`` = schon offene REGEL0-Trades."""
    w = werte if werte is not None else lade()
    if hebelstufe not in (2, 3, 5):
        raise ValueError("Hebelstufe der REGEL0 ist 2, 3 oder 5, nicht %r" % (hebelstufe,))
    einsatz = min(max(w["positionswert_eur"] / hebelstufe, w["einsatz_min_eur"]), w["einsatz_max_eur"])
    erreicht = offen_vorher >= int(w["richtwert_gleichzeitig"])
    gesperrt = erreicht and bool(w["sperre_ab_richtwert"])
    if gesperrt:
        vermerk = "GESPERRT: bereits %d REGEL0-Trades offen (Richtwert %d, Sperre an)" % (offen_vorher, w["richtwert_gleichzeitig"])
    elif erreicht:
        vermerk = "Richtwert erreicht: bereits %d REGEL0-Trades offen (Richtwert %d) - du entscheidest" % (offen_vorher, w["richtwert_gleichzeitig"])
    else:
        vermerk = ""
    return Groesse(hebelstufe, round(einsatz, 2), round(einsatz * hebelstufe, 2), round(einsatz, 2), offen_vorher, erreicht, gesperrt, vermerk)
