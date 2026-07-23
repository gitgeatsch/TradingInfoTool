# -*- coding: utf-8 -*-
"""Marketmaker-Konzept (Liquiditaetszonen), Stufe 1 (2026-07-23, siehe Memory
project_liquiditaetszonen_marketmaker.md): Kurse laufen oft gezielt zu Punkten,
an denen viele Stop-Loss-/Pending-Orders clustern (Swing-Extrema), holen dort
die Liquiditaet ab ("Stop-Hunt"/"Liquidity Sweep") und drehen erst danach.

Stufe 1 ist BEWUSST nur Transparenz/Kontext, KEIN aktiver Deckel - kein
automatisches Verschieben von Entry/CRV/Hebel basierend auf Zonen. Gleiche
Philosophie wie der Schwerpunkte-Stufe-1-Rollout: erst sichtbar machen, Wirkung
erst spaeter und nur mit echten Daten kalibrieren. Krypto Spot+Hebel only (24/7-
Markt + hoher Retail-/Hebel-Anteil, klassische Marketmaker-Dynamik-Annahme) -
NICHT fuer Aktien/Rohstoffe/Hedge/Themen-ETF verdrahtet."""
from __future__ import annotations

from indicators.calculations import TechnicalSnapshot


def liquiditaetszonen_fakt(
    snapshot: TechnicalSnapshot, latest_price: float | None, config: dict | None,
) -> dict | None:
    """Baut den Fakt fuer build_facts()/build_hebel_facts(): naechste Buy-/
    Sell-Side-Zone samt Abstand in %, ob latest_price innerhalb der Naehe-
    Warnschwelle einer noch nicht gefegten Zone liegt. None, wenn das Feature
    per config deaktiviert ist, keine Zonen berechnet werden konnten (z.B. zu
    wenig Swing-Historie) oder kein aktueller Preis vorliegt."""
    cfg = (config or {}).get("liquiditaetszonen", {})
    if not cfg.get("aktiv", True):
        return None

    pools = snapshot.liquidity_zones
    if not pools.available or latest_price is None or latest_price <= 0:
        return None

    min_beruehrungen = cfg.get("min_beruehrungen", 2)
    naehe_schwelle = cfg.get("naehe_warnschwelle_relativ", 0.01)

    buyside_kandidaten = [
        z for z in pools.value["buyside"] if z.touches >= min_beruehrungen and z.price > latest_price
    ]
    sellside_kandidaten = [
        z for z in pools.value["sellside"] if z.touches >= min_beruehrungen and z.price < latest_price
    ]
    naechste_buyside = min(buyside_kandidaten, key=lambda z: z.price) if buyside_kandidaten else None
    naechste_sellside = max(sellside_kandidaten, key=lambda z: z.price) if sellside_kandidaten else None

    def _zu_dict(zone) -> dict | None:
        if zone is None:
            return None
        return {
            "preis": zone.price,
            "touches": zone.touches,
            "letzte_beruehrung_datum": zone.letzte_beruehrung_datum,
            "bereits_gefegt": zone.bereits_gefegt,
            "abstand_prozent": round(abs(zone.price - latest_price) / latest_price * 100, 2),
        }

    buyside_dict = _zu_dict(naechste_buyside)
    sellside_dict = _zu_dict(naechste_sellside)

    # Bei sehr enger Range koennen beide Seiten gleichzeitig in der
    # Naehe-Warnschwelle liegen - die naehere Zone gewinnt (nur EINE
    # "in_naehe_ungefegter_zone"-Warnung, kein widerspruechlicher Doppel-Fakt).
    in_naehe_ungefegter_zone = False
    seite = None
    if (
        buyside_dict is not None and not naechste_buyside.bereits_gefegt
        and buyside_dict["abstand_prozent"] / 100 <= naehe_schwelle
    ):
        in_naehe_ungefegter_zone = True
        seite = "buyside"
    if (
        sellside_dict is not None and not naechste_sellside.bereits_gefegt
        and sellside_dict["abstand_prozent"] / 100 <= naehe_schwelle
        and (seite is None or sellside_dict["abstand_prozent"] < buyside_dict["abstand_prozent"])
    ):
        in_naehe_ungefegter_zone = True
        seite = "sellside"

    return {
        "naechste_buyside_zone": buyside_dict,
        "naechste_sellside_zone": sellside_dict,
        "in_naehe_ungefegter_zone": in_naehe_ungefegter_zone,
        "seite": seite,
    }
