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
from datetime import datetime, timezone

import requests

COINMETRICS_BASE_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
COINMETRICS_FREE_METRICS = "CapMVRVCur,CapMrktCurUSD,SplyCur,PriceUSD"

# Blockchain.com Charts API: einzige kostenlose Quelle gefunden, die BTC-Preise seit
# dem Genesis-Block (2009-01-03) liefert - CoinGecko begrenzt den freien Zugriff
# explizit auf 365 Tage rueckwirkend (live per Fehlermeldung bestaetigt), Kraken/
# CoinMetrics-Community geben nur ein Fenster von ~2 Jahren bzw. ~30 Tagen. Fuer das
# BTC-Log-Regressions-Risiko-Modell (Spezifikation Kap. 8/16) noetig - mehrjaehrige
# Historie, um einen sinnvollen langfristigen Trend zu fitten. `timespan=all` liefert
# eine ausgeduennte Reihe (~alle 4 Tage ein Punkt ueber die gesamte Historie), was fuer
# einen Langfrist-Trend voellig ausreicht - keine Tagesaufloesung noetig/verfuegbar.
BLOCKCHAIN_COM_MARKET_PRICE_URL = "https://api.blockchain.info/charts/market-price"

# DefiLlama Stablecoins API: kostenlos, kein Key, gut dokumentiert - reine On-Chain-
# Token-Supply (Gesamtangebot), keine proprietaere Aggregation noetig anders als bei
# Exchange-Reserven. "Trockenpulver"-Proxy (verfuegbare Krypto-native Liquiditaet,
# Spezifikation Kap. 8/16).
DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins"

# CoinMetrics-Metrik fuer die Gesamt-Reserven (Bestand) auf Boersen wurde NICHT
# gefunden (mehrere Kandidaten-Namen probiert, alle "bad_parameter") - nur die
# Zu-/Abfluesse (FlowInExNtv/FlowOutExNtv) sind im Gratis-Tier verfuegbar. Das ist
# ohnehin das dynamischere Signal (taegliche Bewegung statt trage Bestandsgroesse).


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


@dataclass
class ExchangeFlowReading:
    date: str
    inflow_btc: float
    outflow_btc: float
    net_flow_btc: float  # positiv = mehr rein als raus (potenziell Verkaufsdruck)


def get_btc_exchange_flows(session: requests.Session | None = None) -> ExchangeFlowReading:
    """Taegliche BTC-Boersen-Zu-/Abfluesse ueber CoinMetrics Community API (kostenlos,
    kein Key). Reine Fluss-Groesse, KEIN Gesamt-Bestand - eine Metrik fuer den
    Gesamt-Bestand auf Boersen wurde im Gratis-Tier nicht gefunden (siehe Kap. 16)."""
    session = session or requests.Session()
    response = session.get(
        COINMETRICS_BASE_URL,
        params={
            "assets": "btc",
            "metrics": "FlowInExNtv,FlowOutExNtv",
            "frequency": "1d",
            "page_size": 10,
            "sort": "time",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    entry = data["data"][-1]
    inflow = float(entry["FlowInExNtv"])
    outflow = float(entry["FlowOutExNtv"])
    return ExchangeFlowReading(
        date=str(entry["time"]).split("T")[0], inflow_btc=inflow, outflow_btc=outflow,
        net_flow_btc=inflow - outflow,
    )


@dataclass
class StablecoinSupplyReading:
    date: str
    total_usd: float
    usdt_usd: float | None
    usdc_usd: float | None


def get_stablecoin_supply(session: requests.Session | None = None) -> StablecoinSupplyReading:
    """Gesamt-Marktkapitalisierung aller getrackten Stablecoins (~400) ueber
    DefiLlama, kostenlos, kein Key. "Trockenpulver"-Proxy - hoehere Summe = mehr
    verfuegbare Krypto-native Liquiditaet, die potenziell in Risiko-Assets fliessen
    koennte (nicht garantiert, nur ein grober Indikator)."""
    session = session or requests.Session()
    response = session.get(DEFILLAMA_STABLECOINS_URL, params={"includePrices": "true"}, timeout=20)
    response.raise_for_status()
    assets = response.json()["peggedAssets"]
    total = sum(a["circulating"].get("peggedUSD", 0) for a in assets)
    usdt = next((a["circulating"].get("peggedUSD") for a in assets if a["symbol"] == "USDT"), None)
    usdc = next((a["circulating"].get("peggedUSD") for a in assets if a["symbol"] == "USDC"), None)
    return StablecoinSupplyReading(
        date=datetime.now(timezone.utc).date().isoformat(),
        total_usd=float(total), usdt_usd=usdt, usdc_usd=usdc,
    )


def get_btc_full_price_history(session: requests.Session | None = None) -> list[tuple[datetime, float]]:
    """Komplette BTC-Preishistorie seit dem Genesis-Block, ~alle 4 Tage ein
    Datenpunkt. Enthaelt am Anfang (2009, kein etablierter Markt) Preis 0.0 -
    Aufrufer muss das vor einer Log-Transformation herausfiltern (log(0) undefiniert)."""
    session = session or requests.Session()
    response = session.get(
        BLOCKCHAIN_COM_MARKET_PRICE_URL, params={"timespan": "all", "format": "json"}, timeout=20
    )
    response.raise_for_status()
    data = response.json()
    return [
        (datetime.fromtimestamp(point["x"], tz=timezone.utc), float(point["y"]))
        for point in data["values"]
    ]
