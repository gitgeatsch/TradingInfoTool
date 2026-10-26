# -*- coding: utf-8 -*-
"""Die Kernwerte BTC, ETH, SOL - EINE Liste (K-4, 26.10.2026; E-148/E-150).

Nutzer 25.10.: *"vorsicht - btc und eth und sol sollen auch regel0 und hebel nutzen koennen"* ·
26.10.: *"(b) nur K-4"* - den Spot-Aufbau der Kernwerte fuehrt der Nutzer selbst per Sparplan
(monatlich ein kleiner Betrag je Asset). Die alte Spot-Kette stellt fuer sie deshalb KEINE Kauffrage mehr.

WAS DIE LISTE BEDEUTET:
    Spot     keine Zelle in der alten Rollen-Kette (`assetklassen.zellen`: gesperrte Zeile mit Grund),
             kein Rueckfall auf `strategie_fuer` (`rollen_lauf.paare_aus_zellen`); B1/B3/B4 nehmen sie
             ueber `spot_mitnahme.KERN` (= diese Liste) schon seit P14 aus.
    REGEL0   UNBERUEHRT - sie haengt an `asset_hebel_settings.hebel_pruefung_erlaubt`, nicht hier.
    Hebel    UNBERUEHRT - die Hebelzelle der Kette bleibt (taktisch: nur wenn die Rechnung einen Hebel ergibt).
    Anzeige  Bestand, G/V, Positionsfuehrung bleiben - Information ist keine Kauffrage.

⚠️ NICHT VERWECHSELN mit `rolle: core` der Watchlist (13 Werte, `assetklassen.kern_symbole`): das ist der
Vorrang in der Warteschlange, ein anderer Begriff. Und `asset_dca_settings.dca_erlaubt` ist KEIN Ausschalter:
abgeschaltet macht er aus dem Kern eine gewoehnliche Spot-Einstiegszelle MIT Stop (Voranalyse Kern-Regel §7).
"""
from __future__ import annotations

KERN = ("BTC", "ETH", "SOL")

GRUND_SPOT = ("Kernwert: kein Spot in der alten Kette - der Aufbau laeuft per Sparplan des Nutzers "
              "(K-4, E-148); REGEL0 und Hebel unberuehrt")


def ist_kern(symbol) -> bool:
    return str(symbol or "").strip().upper() in KERN
