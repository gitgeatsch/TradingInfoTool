"""On-Chain-Metriken fuer BTC (MVRV/NUPL/Realized Price/-Cap) - Spezifikation Kap. 8/16,
Bestandsaufnahme "Krypto-typische Datentypen" 2026-07-08. Quelle: CoinMetrics
Community API (`community-api.coinmetrics.io`), kostenlos, KEIN API-Key noetig,
Rate-Limit 10 Requests/6-Sekunden-Sliding-Window (grosszuegig genug fuer gelegentliche
Abfragen).

WICHTIG: MVRV, Market Cap, Supply und Preis sind im Gratis-Tier direkt verfuegbar.
NUPL und Realized Cap/Price sind dort NICHT direkt enthalten (live geprueft,
"forbidden"-Fehler fuer bezahlte Metriken), werden hier aber aus den freien Werten
mathematisch EXAKT hergeleitet, keine Naeherung:
    MVRV = MarketCap / RealizedCap        => RealizedCap = MarketCap / MVRV
    NUPL = (MarketCap - RealizedCap) / MarketCap = 1 - RealizedCap/MarketCap
         = 1 - 1/MVRV
    RealizedPrice = RealizedCap / Supply
SOPR bleibt eine echte Luecke - braucht Transaktions-Ebene-Daten (wann wurde welcher
Output das letzte Mal bewegt), ist aus Bestandsgroessen wie MVRV NICHT herleitbar.
Kein Ersatz gefunden (2026-07-08), siehe Spezifikation Kap. 16.

Zwei andere on-chain-nahe Vorhaben aus derselben Bestandsaufnahme sind bewusst NICHT
Teil dieses Moduls: Liquidations-Heatmap (CoinGlass, kostenpflichtig, siehe
Spezifikation Kap. 16 - Register verworfener Loesungen) und Open Interest/
Long-Short-Ratio (Binance/Bybit/OKX, kostenlos, aber noch nicht implementiert -
gehoert eher zu Derivate-/Positionierungsdaten als zu On-Chain-Metriken, siehe
api/kraken.py fuer die bestehende Funding-Rate-Anbindung)."""
from __future__ import annotations

from dataclasses import dataclass

import requests

COINMETRICS_BASE_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
COINMETRICS_FREE_METRICS = "CapMVRVCur,CapMrktCurUSD,SplyCur,PriceUSD"


@dataclass
class OnChainReading:
    date: str
    price_usd: float
    market_cap_usd: float
    supply: float
    mvrv: float
    nupl: float  # hergeleitet, siehe Modul-Docstring
    realized_cap_usd: float  # hergeleitet
    realized_price_usd: float  # hergeleitet


def get_btc_onchain_snapshot(session: requests.Session | None = None) -> OnChainReading:
    """Neuester verfuegbarer Tageswert fuer BTC. Wirft bei fehlenden/kaputten
    Rohdaten eine Exception statt einen falschen abgeleiteten Wert zu berechnen
    (P-10) - der Aufrufer soll das wie jeden anderen Datenquellen-Fehler behandeln.

    Die API kennt KEINEN "order"-Parameter (live getestet - "Unsupported parameter
    'order'") - `sort=time` liefert immer aufsteigend, daher hier ein kleiner Puffer
    (page_size) und der jeweils letzte Eintrag statt page_size=1 (das haette den
    AELTESTEN Tag der gesamten Historie geliefert, nicht den neuesten)."""
    session = session or requests.Session()
    response = session.get(
        COINMETRICS_BASE_URL,
        params={
            "assets": "btc",
            "metrics": COINMETRICS_FREE_METRICS,
            "frequency": "1d",
            "page_size": 10,
            "sort": "time",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    entry = data["data"][-1]

    price = float(entry["PriceUSD"])
    market_cap = float(entry["CapMrktCurUSD"])
    supply = float(entry["SplyCur"])
    mvrv = float(entry["CapMVRVCur"])

    realized_cap = market_cap / mvrv
    nupl = 1 - (1 / mvrv)
    realized_price = realized_cap / supply

    return OnChainReading(
        date=str(entry["time"]).split("T")[0],
        price_usd=price,
        market_cap_usd=market_cap,
        supply=supply,
        mvrv=mvrv,
        nupl=nupl,
        realized_cap_usd=realized_cap,
        realized_price_usd=realized_price,
    )
