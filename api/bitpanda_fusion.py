# -*- coding: utf-8 -*-
"""LESENDER ZUGANG ZU BITPANDA FUSION - offene Orders (Schritt 61, Stufe 1.3).

⚠️ WARUM. Die neue Public API sagt, WIE VIEL Cash gebunden ist (gesamt minus
verfuegbar, 16.09.: 3.467,27 - 560,00 = 2.907,27 EUR), aber nicht WORIN. Das
Geld liegt in Fusion-Limit-Orders (Befund 2.455-cash-gesperrt), und nur Fusion
nennt sie: Anzahl, Betrag, aelteste. Genau das braucht die Mailzeile (F4):
,reicht nur, wenn Sie offene Orders aufloesen (10 Orders, aelteste vom 04.06.)'.

EIGENER SCHLUESSEL `FUSION_API_KEY` (nur Lesen, gueltig bis 15.09.2027), Kopf
`x-api-key`. Live geprueft 16.09.2026: `GET /account/orders?status=open` liefert
`{"data": [...], "meta": {"limit", "hasNextPage", "nextCursor"}}`; je Order
`pair`, `side`, `type`, `status`, `pricedIn`, `amount`, `filledAmount`,
`createdAt`. 10 offene Kauforders, Summe 2.900,00 EUR - 7,27 EUR unter dem
gebundenen Betrag der Public API (vermutlich reservierte Gebuehren).

⚠️ FUSION IST ZUSATZ, NICHT QUELLE. Den gebundenen BETRAG liefert die Public
API; faellt Fusion aus oder fehlt der Schluessel, bleibt der Betrag richtig, nur
die Details fehlen. Kein Schreibzugriff, keine Orderfunktion.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from database.api_health import track_api_health
from geheimnisse import maskiere

logger = logging.getLogger(__name__)

BASIS_URL = "https://api.fusion.bitpanda.com/v1"
ZEITLIMIT_SEKUNDEN = 20
MAX_SEITEN = 20


class FusionFehler(RuntimeError):
    """Fehler beim Lesen - Text bereits maskiert."""


@dataclass(frozen=True)
class OffeneOrders:
    anzahl: int
    kauf_eur: float
    aelteste: str | None       # ISO-Zeitpunkt der aeltesten offenen Order
    paare: tuple               # z.B. ("BTC-EUR", "ETH-EUR")


def _zahl(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


@track_api_health("bitpanda_fusion")
def _hole(pfad: str, api_key: str, params: dict | None = None) -> dict:
    try:
        r = requests.get(BASIS_URL + pfad, headers={"x-api-key": api_key},
                         params=params or {}, timeout=ZEITLIMIT_SEKUNDEN)
    except requests.RequestException as exc:
        raise FusionFehler("Fusion %s nicht erreichbar: %s"
                           % (pfad, maskiere(str(exc).replace(api_key, "***")))) from None
    if r.status_code == 401:
        raise FusionFehler("Fusion: Zugang abgelehnt (401) - Schluessel ungueltig oder abgelaufen")
    if r.status_code >= 400:
        raise FusionFehler("Fusion %s antwortete %d: %s"
                           % (pfad, r.status_code, maskiere(r.text[:200].replace(api_key, "***"))))
    try:
        return r.json()
    except ValueError:
        raise FusionFehler("Fusion %s lieferte keine lesbare Antwort" % pfad) from None


def offene_orders(api_key: str) -> OffeneOrders:
    """Offene Orders mit EUR-Preisbezug; `kauf_eur` = noch nicht ausgefuehrter
    Betrag der KAUF-Orders (das ist gebundenes Cash - Verkaufsorders binden Coins)."""
    orders = []
    cursor = None
    for _ in range(MAX_SEITEN):
        params = {"status": "open"}
        if cursor:
            params["cursor"] = cursor
        js = _hole("/account/orders", api_key, params)
        orders.extend(js.get("data") or [])
        meta = js.get("meta") or {}
        neu = meta.get("nextCursor")
        if not meta.get("hasNextPage") or not neu or neu == cursor:
            break
        cursor = neu
    kauf = [o for o in orders if str(o.get("side", "")).lower() == "buy"
            and str(o.get("pricedIn", "")).upper() == "EUR"]
    zeiten = sorted(str(o["createdAt"]) for o in kauf if o.get("createdAt"))
    return OffeneOrders(
        anzahl=len(kauf),
        kauf_eur=round(sum(max(0.0, _zahl(o.get("amount")) - _zahl(o.get("filledAmount"))) for o in kauf), 2),
        aelteste=zeiten[0] if zeiten else None,
        paare=tuple(sorted({str(o.get("pair")) for o in kauf if o.get("pair")})))
