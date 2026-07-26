"""Deribit oeffentliche Marktdaten-Endpunkte (2026-07-26, Nutzer-Vorschlag
"Punkt 2" aus dem Regime-Persistenz-Design-Review: implizite Volatilitaet
(DVOL) + ein naeherungsweiser Options-Skew fuer BTC als vorausschauender,
marktgepreiter Fakt - anders als alle bisherigen Krypto-Indikatoren (EMA,
RSI, Fear&Greed, Funding-Rate), die entweder nachlaufend oder rein
stimmungsbasiert sind. Rein lesende oeffentliche Endpunkte, kein API-Key
noetig, kein dokumentiertes Rate-Limit fuer diese beiden Endpunkte.

`get_options_skew()` ist bewusst KEIN echter 25-Delta-Risk-Reversal - das
wuerde pro Strike einen eigenen `ticker()`-Aufruf brauchen (Greeks/Delta
stehen nur dort, nicht im guenstigen `get_book_summary_by_currency()`), also
~20-30 zusaetzliche Calls je Abruf. Stattdessen: EIN Aufruf liefert `mark_iv`
bereits fuer alle Strikes/Verfallstermine, die naechstgelegenen OTM-Strikes
zu einem festen Moneyness-Ziel (statt echtem Delta) dienen als Naeherung -
dokumentiert als Vereinfachung, nicht als exakter Marktstandard-Wert."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

BASE_URL = "https://www.deribit.com/api/v2/public"
_TIMEOUT_SECONDS = 10

# Moneyness-Naeherung fuer den Skew (siehe Modul-Docstring) - Ziel-Abstand des
# OTM-Strikes vom Spot in Prozent. Reine Definitionswahl (kein Markt-
# Schwellenwert wie z.B. die VIX-Baender), daher ohne Backtest festgelegt -
# 15% ist eine uebliche Groessenordnung fuer einen "leicht OTM"-Strike bei
# BTC-Optionen mit einigen Wochen Restlaufzeit.
_SKEW_MONEYNESS_ZIEL_PROZENT = 15.0
_SKEW_MIN_TAGE_BIS_EXPIRY = 14
_SKEW_MAX_TAGE_BIS_EXPIRY = 60


@track_api_health("deribit")
def get_volatility_index(currency: str) -> float | None:
    """DVOL (Deribit Volatility Index) - marktimplizite 30-Tage-Volatilitaet
    fuer `currency` (BTC|ETH), in Prozent p.a. Gibt den juengsten Schlusswert
    der letzten Stunde zurueck, None wenn keine Daten geliefert wurden."""
    now_ms = int(time.time() * 1000)
    response = requests.get(
        f"{BASE_URL}/get_volatility_index_data",
        params={
            "currency": currency,
            "start_timestamp": now_ms - 3_600_000,
            "end_timestamp": now_ms,
            "resolution": 60,
        },
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json().get("result", {}).get("data") or []
    if not data:
        return None
    # Format je Punkt: [timestamp, open, high, low, close] - juengster Schlusswert
    return float(data[-1][4])


@track_api_health("deribit")
def get_options_skew(currency: str) -> dict | None:
    """Naeherungsweiser Risk-Reversal (OTM-Call-IV minus OTM-Put-IV) aus dem
    naechstgelegenen Verfallstermin mit `_SKEW_MIN_TAGE_BIS_EXPIRY` bis
    `_SKEW_MAX_TAGE_BIS_EXPIRY` Tagen Restlaufzeit (siehe Modul-Docstring fuer
    die Moneyness-statt-Delta-Vereinfachung). Positiver Wert: OTM-Calls
    teurer bepreist als OTM-Puts (Markt preist tendenziell mehr Aufwaerts-
    als Abwaertsrisiko ein). Negativer Wert: umgekehrt (mehr Nachfrage nach
    Abwaerts-Absicherung, klassisches "Fear-Skew"-Muster).

    Gibt None zurueck, wenn kein passender Verfallstermin oder keine
    Optionsdaten mit beiden Seiten (Call UND Put) verfuegbar sind (P-8)."""
    response = requests.get(
        f"{BASE_URL}/get_book_summary_by_currency",
        params={"currency": currency, "kind": "option"},
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    instruments = response.json().get("result") or []
    if not instruments:
        return None

    spot = instruments[0].get("underlying_price")
    if not spot:
        return None

    now = datetime.now(timezone.utc)
    geparst = []
    for inst in instruments:
        teile = str(inst.get("instrument_name", "")).split("-")
        if len(teile) != 4:
            continue
        _, expiry_str, strike_str, option_typ = teile
        try:
            expiry = datetime.strptime(expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
            strike = float(strike_str)
        except ValueError:
            continue
        tage_bis_expiry = (expiry - now).days
        if not (_SKEW_MIN_TAGE_BIS_EXPIRY <= tage_bis_expiry <= _SKEW_MAX_TAGE_BIS_EXPIRY):
            continue
        mark_iv = inst.get("mark_iv")
        if mark_iv is None:
            continue
        geparst.append({
            "expiry": expiry, "tage": tage_bis_expiry, "strike": strike,
            "typ": option_typ, "mark_iv": mark_iv,
        })
    if not geparst:
        return None

    ziel_expiry = min(e["expiry"] for e in geparst)
    kandidaten = [e for e in geparst if e["expiry"] == ziel_expiry]

    calls = [e for e in kandidaten if e["typ"] == "C" and e["strike"] > spot]
    puts = [e for e in kandidaten if e["typ"] == "P" and e["strike"] < spot]
    if not calls or not puts:
        return None

    ziel_call_strike = spot * (1 + _SKEW_MONEYNESS_ZIEL_PROZENT / 100)
    ziel_put_strike = spot * (1 - _SKEW_MONEYNESS_ZIEL_PROZENT / 100)
    naechster_call = min(calls, key=lambda e: abs(e["strike"] - ziel_call_strike))
    naechster_put = min(puts, key=lambda e: abs(e["strike"] - ziel_put_strike))

    return {
        "tage_bis_expiry": kandidaten[0]["tage"],
        "call_strike": naechster_call["strike"],
        "call_iv": naechster_call["mark_iv"],
        "put_strike": naechster_put["strike"],
        "put_iv": naechster_put["mark_iv"],
        "skew_prozentpunkte": round(naechster_call["mark_iv"] - naechster_put["mark_iv"], 2),
        "spot": spot,
    }
