"""Backtesting-Engine (2026-07-17, Vorbereitung fuer Selbstverifikations-Vision
Schritt 3-4, siehe Basisinfos/Regelwerksmanual.md Kap. 7 "Nachtrag ... Backtesting-
Engine" + Plandatei swift-napping-muffin). Simuliert die bestehenden,
deterministischen Regel-Bausteine (Indikator-Konfluenz, CRV-Mindestschwelle Z-2,
Stop-Loss-Abstand RM-5) rueckwirkend gegen die bereits gespeicherte Kurshistorie
(`price_history_ohlc`), um synthetische, aufgeloeste Handelsergebnisse zu erzeugen.
Groesster bisheriger Engpass fuer Schritt 3 war schlicht zu wenig Zeit fuer genug
echte, aufgeloeste Signale (Wochen bis Monate) - diese Engine ersetzt Warten durch
Nachrechnen bereits vorhandener Jahre an Kurshistorie.

**Bewusste Grenzen (P-10, keine Ueberzeugungskraft vortaeuschen, die nicht da ist):**

- Der eigentliche LLM-Entscheidungsschritt (`agent/krypto/analyst.py::
  call_groq_for_signal`) wird NICHT nachgebildet - weder reproduzierbar noch
  budgetneutral, wenn er fuer Jahre Historie mal Tage aufgerufen wuerde. Ersetzt
  durch eine einfache, deterministische Konfluenz-Regel (`_confluence_entry_signal`),
  die dieselbe "kein Signal aus einem einzelnen Indikator"-Philosophie nutzt
  (Kap. 6, confluence_pflicht; `indicators.calculations.summarize_confluence`),
  aber NICHT die multi-faktorielle Bewertungstiefe der echten KI-Empfehlung
  ersetzt. Diese Engine testet also primaer die Kalibrierung der RISIKO-Regel-
  Parameter (`CRV_MINIMUM`, `STOP_LOSS_ATR_MULTIPLE` aus `risk_gate.py`), NICHT
  die Qualitaet der LLM-Urteilsbildung selbst.
- Regime-Erhebung ist vereinfacht (nur BTC-Trend/EMA, `_simplified_btc_regime`) -
  Fear&Greed-/BTC-Dominanz-Historie liegt erst seit 2026-07-07 vor
  (`macro_snapshot`, nur wenige Zeilen), MVRV/NUPL ist ein Live-only-Wert ohne
  gespeicherte Historie. Absichtlich EIGENE Zustandsnamen
  (`bulle_technisch`/`baer_technisch`/`seitwaerts_technisch`/`unbekannt`), NICHT
  die echten `determine_regime()`-Zustaende - um nie den Eindruck zu erwecken,
  dies sei mit dem echten, mehrfaktoriellen Live-Regime gleichwertig.
- Nur Spot, kein Hebel - die Hebel-Trigger-Erzeugung (`hebel_screening.py`)
  braucht Open-Interest-Aenderungs-Historie, die aktuell nur ein einzelnes
  13-Minuten-Fenster (2026-07-14) umfasst - fachlich nicht backtestbar.
- Kein Lookahead-Bias bei der SIGNAL-ERZEUGUNG: an jedem simulierten Tag werden
  Indikatoren/Regime nur aus Daten bis einschliesslich diesem Tag berechnet
  (siehe die `[: idx + 1]`-Slices in `run_backtest`). Die ERGEBNIS-Aufloesung
  (Take-Profit/Stop-Loss) darf danach die tatsaechliche Zukunft nutzen - genau
  wie beim echten Backward-Tracking (`agent/krypto/backward_tracking.py`), das
  ebenfalls erst im Nachhinein prueft.
- Einstiege sind FLANKEN-GETRIGGERT (nur beim Wechsel non-bullish -> bullish),
  nicht bei jedem Tag mit bullishem Bias - sonst wuerde ein einzelner mehrwoechiger
  Aufwaertstrend als viele, stark korrelierte "unabhaengige" Trades gezaehlt und
  die Stichprobe faelschlich aufblaehen (derselbe Overfitting-/Stichproben-
  Risikopunkt wie in der Machbarkeitsanalyse, Abschnitt 1).

Reine Analysefunktion, kein Seiteneffekt auf Live-Verhalten - schreibt nichts in
`signals`/`hebel_signals`, liefert nur ein eigenes strukturiertes `BacktestReport`.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field

import numpy as np

import database.db as db
from agent.krypto.risk_gate import CRV_MINIMUM, STOP_LOSS_ATR_MULTIPLE
from indicators.calculations import build_technical_snapshot, latest_value, summarize_confluence

# EMA-200 + kleiner Puffer, siehe build_technical_snapshot()s Standard-ema_periods.
MIN_LOOKBACK_TAGE = 210
# Gleicher Wert wie backward_tracking.abgelaufen_nach_tagen (Basisinfos/config.yaml).
DEFAULT_MAX_HALTEDAUER_TAGE = 90


@dataclass
class BacktestTrade:
    symbol: str
    entry_date: str
    entry_price: float
    stop_loss: float
    take_profit: float
    stop_methode: str
    regime_technisch: str
    exit_date: str | None
    exit_price: float | None
    outcome: str  # "take_profit" | "stop_loss" | "abgelaufen_unentschieden" | "offen_am_ende_der_historie"
    realized_crv: float | None


@dataclass
class BacktestReport:
    symbol: str
    start_date: str
    end_date: str
    tage_geprueft: int = 0
    trades: list[BacktestTrade] = field(default_factory=list)

    @property
    def anzahl_entschieden(self) -> int:
        return sum(1 for t in self.trades if t.outcome in ("take_profit", "stop_loss"))

    @property
    def win_rate(self) -> float | None:
        entschieden = self.anzahl_entschieden
        if entschieden == 0:
            return None
        treffer = sum(1 for t in self.trades if t.outcome == "take_profit")
        return treffer / entschieden

    @property
    def avg_realized_crv(self) -> float | None:
        werte = [t.realized_crv for t in self.trades if t.realized_crv is not None]
        if not werte:
            return None
        return sum(werte) / len(werte)

    @property
    def max_drawdown_crv(self) -> float | None:
        """Maximaler Ruecksetzer der KUMULIERTEN CRV-Kurve (nicht Euro/Prozent - die
        tatsaechliche Positionsgroesse wird in diesem vereinfachten Backtest nicht
        simuliert). Werte <= 0, je naeher an 0 desto besser."""
        werte = [t.realized_crv for t in self.trades if t.realized_crv is not None]
        if not werte:
            return None
        kumuliert = np.cumsum(werte)
        peak = np.maximum.accumulate(kumuliert)
        return float((kumuliert - peak).min())

    def regime_breakdown(self) -> dict[str, dict]:
        """Trefferquote/CRV getrennt je `regime_technisch` - direkte Antwort auf die
        in der Machbarkeitsanalyse aufgeworfene Frage ('gilt das nur im
        Bullenmarkt?'), Abschnitt 1 der Plandatei."""
        ergebnis: dict[str, dict] = {}
        for regime in sorted({t.regime_technisch for t in self.trades}):
            gruppe = [t for t in self.trades if t.regime_technisch == regime]
            entschieden = [t for t in gruppe if t.outcome in ("take_profit", "stop_loss")]
            crv_werte = [t.realized_crv for t in entschieden if t.realized_crv is not None]
            ergebnis[regime] = {
                "anzahl_trades": len(gruppe),
                "anzahl_entschieden": len(entschieden),
                "win_rate": (
                    sum(1 for t in entschieden if t.outcome == "take_profit") / len(entschieden)
                    if entschieden else None
                ),
                "avg_realized_crv": sum(crv_werte) / len(crv_werte) if crv_werte else None,
            }
        return ergebnis


def _last_index_le(sorted_dates: list[str], date: str) -> int | None:
    """Groesster Index i mit sorted_dates[i] <= date (ISO-Datumsstrings sortieren
    lexikographisch = chronologisch). None, wenn kein solcher Index existiert."""
    i = bisect.bisect_right(sorted_dates, date) - 1
    return i if i >= 0 else None


def _simplified_btc_regime(btc_snapshot, btc_closes: np.ndarray) -> str:
    """Vereinfachtes, NUR technisches Pendant zu regime.py::determine_regime()s
    BTC-Trend-Baustein - bewusst eigene Zustandsnamen (siehe Modul-Docstring)."""
    ema50 = latest_value(btc_snapshot.ema[50])
    ema200 = latest_value(btc_snapshot.ema[200])
    if ema50 is None or ema200 is None or len(btc_closes) == 0:
        return "unbekannt"
    close = float(btc_closes[-1])
    if close < ema50:
        return "baer_technisch"
    if close > ema50 > ema200:
        return "bulle_technisch"
    return "seitwaerts_technisch"


def _compute_entry_zone(snapshot, entry_price: float) -> tuple[float | None, float | None, str]:
    """Stop-Loss bevorzugt ueber ATR (RM-5-Konvention, `STOP_LOSS_ATR_MULTIPLE`
    aus `risk_gate.py`, dieselbe Zahl wie im echten Risk-Gate), sonst Fallback auf
    den naechsten Support-Level unterhalb des Entry-Preises. Take-Profit exakt auf
    `CRV_MINIMUM` (Z-2) skaliert - so testet die spaetere Auswertung direkt, ob
    dieser Schwellenwert in der Praxis haelt, statt ihn a priori grosszuegiger
    anzusetzen."""
    atr_value = latest_value(snapshot.atr)
    if atr_value is not None and atr_value > 0:
        stop_loss = entry_price - STOP_LOSS_ATR_MULTIPLE * atr_value
        methode = f"{STOP_LOSS_ATR_MULTIPLE}x ATR ({snapshot.atr_label})"
    elif snapshot.support_resistance.available and snapshot.support_resistance.value:
        unter_preis = [lvl["price"] for lvl in snapshot.support_resistance.value if lvl["price"] < entry_price]
        if not unter_preis:
            return None, None, "kein Stop-Loss ableitbar (kein ATR, kein Support unterhalb)"
        stop_loss = max(unter_preis)
        methode = "naechster Support-Level (Fallback ohne ATR)"
    else:
        return None, None, "kein Stop-Loss ableitbar (kein ATR, keine Support-Level)"

    if stop_loss >= entry_price:
        return None, None, "abgeleiteter Stop-Loss liegt nicht unter Entry"

    take_profit = entry_price + CRV_MINIMUM * (entry_price - stop_loss)
    return stop_loss, take_profit, methode


def _resolve_trade(
    ohlc_history: list,
    entry_idx: int,
    symbol: str,
    entry_date: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    stop_methode: str,
    regime_technisch: str,
    max_haltedauer_tage: int,
    end_idx: int,
) -> BacktestTrade:
    """Tag-fuer-Tag-Aufloesung wie `backward_tracking.py::check_signal_outcome()` -
    trifft ein einzelner Tag beide Zonen, gewinnt IMMER Stop-Loss (Z-1,
    konservativ: ohne Tick-Daten keine Annahme ueber die Innertages-Reihenfolge)."""
    letzter_moeglicher_idx = min(entry_idx + max_haltedauer_tage, end_idx)
    for i in range(entry_idx + 1, letzter_moeglicher_idx + 1):
        row = ohlc_history[i]
        if row.low <= stop_loss:
            crv = (row.low - entry_price) / (entry_price - stop_loss)
            return BacktestTrade(
                symbol, entry_date, entry_price, stop_loss, take_profit, stop_methode,
                regime_technisch, row.date, row.low, "stop_loss", crv,
            )
        if row.high >= take_profit:
            crv = (row.high - entry_price) / (entry_price - stop_loss)
            return BacktestTrade(
                symbol, entry_date, entry_price, stop_loss, take_profit, stop_methode,
                regime_technisch, row.date, row.high, "take_profit", crv,
            )

    outcome = (
        "offen_am_ende_der_historie"
        if letzter_moeglicher_idx >= end_idx and letzter_moeglicher_idx - entry_idx < max_haltedauer_tage
        else "abgelaufen_unentschieden"
    )
    return BacktestTrade(
        symbol, entry_date, entry_price, stop_loss, take_profit, stop_methode,
        regime_technisch, None, None, outcome, None,
    )


def run_backtest(
    conn,
    symbol: str,
    currency: str = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
    max_haltedauer_tage: int = DEFAULT_MAX_HALTEDAUER_TAGE,
    btc_ohlc_history: list | None = None,
) -> BacktestReport:
    """Simuliert die Konfluenz-/CRV-Entry-Regel Tag fuer Tag gegen die gespeicherte
    `price_history_ohlc`-Historie eines einzelnen Symbols. `btc_ohlc_history` kann
    von aussen durchgereicht werden (Performance: bei einem Mehrsymbol-Lauf nur
    einmal statt pro Symbol laden), sonst wird sie selbst geladen."""
    ohlc_history = db.get_ohlc_history(conn, symbol, currency)
    if len(ohlc_history) < MIN_LOOKBACK_TAGE + 1:
        return BacktestReport(
            symbol=symbol, start_date=start_date or "", end_date=end_date or "",
        )

    dates_all = [p.date for p in ohlc_history]
    closes_all = np.array([p.close for p in ohlc_history], dtype=float)

    if btc_ohlc_history is None:
        btc_ohlc_history = ohlc_history if symbol == "BTC" else db.get_ohlc_history(conn, "BTC", currency)
    btc_dates_all = [p.date for p in btc_ohlc_history]
    btc_closes_all = np.array([p.close for p in btc_ohlc_history], dtype=float)

    start_idx = MIN_LOOKBACK_TAGE
    if start_date:
        gefunden = next((i for i, d in enumerate(dates_all) if d >= start_date), len(dates_all))
        start_idx = max(start_idx, gefunden)
    end_idx = len(dates_all) - 1
    if end_date:
        gefunden_end = _last_index_le(dates_all, end_date)
        if gefunden_end is not None:
            end_idx = min(end_idx, gefunden_end)

    report = BacktestReport(
        symbol=symbol,
        start_date=dates_all[start_idx] if start_idx <= end_idx else (start_date or ""),
        end_date=dates_all[end_idx] if end_idx >= 0 else (end_date or ""),
    )
    if start_idx > end_idx:
        return report

    war_bullish = False
    idx = start_idx
    while idx <= end_idx:
        report.tage_geprueft += 1
        as_of_date = dates_all[idx]
        closes_slice = closes_all[: idx + 1]
        dates_slice = np.array(dates_all[: idx + 1])
        ohlc_slice = ohlc_history[: idx + 1]

        snapshot = build_technical_snapshot(closes_slice, dates_slice, ohlc_slice)
        confluence = summarize_confluence(snapshot, float(closes_slice[-1]))
        ist_bullish = confluence.overall_bias == "bullish"

        # Flanken-Trigger (siehe Modul-Docstring): nur beim Wechsel non-bullish ->
        # bullish, nicht bei jedem Tag mit bullishem Bias.
        if ist_bullish and not war_bullish:
            btc_idx = _last_index_le(btc_dates_all, as_of_date)
            regime_technisch = "unbekannt"
            if btc_idx is not None and btc_idx >= MIN_LOOKBACK_TAGE:
                btc_snapshot = build_technical_snapshot(
                    btc_closes_all[: btc_idx + 1], np.array(btc_dates_all[: btc_idx + 1]),
                    btc_ohlc_history[: btc_idx + 1],
                )
                regime_technisch = _simplified_btc_regime(btc_snapshot, btc_closes_all[: btc_idx + 1])

            entry_price = float(closes_slice[-1])
            stop_loss, take_profit, stop_methode = _compute_entry_zone(snapshot, entry_price)
            if stop_loss is not None and take_profit is not None:
                trade = _resolve_trade(
                    ohlc_history, idx, symbol, as_of_date, entry_price, stop_loss, take_profit,
                    stop_methode, regime_technisch, max_haltedauer_tage, end_idx,
                )
                report.trades.append(trade)

        war_bullish = ist_bullish
        idx += 1

    return report


def run_backtest_batch(conn, symbols: list[str], currency: str = "USD", **kwargs) -> dict[str, BacktestReport]:
    """Mehrsymbol-Lauf - laedt die BTC-Historie (fuer `_simplified_btc_regime`) nur
    einmal, statt pro Symbol neu."""
    btc_ohlc_history = db.get_ohlc_history(conn, "BTC", currency)
    return {
        symbol: run_backtest(conn, symbol, currency, btc_ohlc_history=btc_ohlc_history, **kwargs)
        for symbol in symbols
    }
