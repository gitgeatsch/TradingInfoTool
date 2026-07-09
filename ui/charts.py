"""Chart-Fenster je Asset: Preis + Indikatoren (U-3, Spezifikation Kap. 7).

Naeherungs-Indikatoren (Volatilitaet, Swing-Punkte) sind IMMER als solche
gekennzeichnet - siehe indicators/calculations.py fuer die Begruendung (P-2/P-10).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import database.db as db
import ui.theme as theme
from api.kraken import KRAKEN_PAIR_MAP
from indicators.calculations import build_technical_snapshot, latest_value
from ui.formatting import format_money, is_history_stale


class ChartWindow(tk.Toplevel):
    def __init__(self, parent, db_conn_factory, asset):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._asset = asset
        self._currency = tk.StringVar(value="eur")

        self.title(f"{asset.symbol} — {asset.name}")
        self.geometry("1000x820")

        self._build_controls()
        self._build_figure()
        self._reload()

    def _build_controls(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=8)

        ttk.Label(toolbar, text="Währung:").pack(side="left")
        ttk.Radiobutton(
            toolbar, text="EUR", variable=self._currency, value="eur", command=self._reload
        ).pack(side="left", padx=(4, 0))
        ttk.Radiobutton(
            toolbar, text="USD", variable=self._currency, value="usd", command=self._reload
        ).pack(side="left")

        self._staleness_label = ttk.Label(toolbar, text="", foreground=theme.stale_color())
        self._staleness_label.pack(side="left", padx=(16, 0))

    def _build_figure(self) -> None:
        self._figure = Figure(figsize=(9, 7), dpi=100)
        self._ax_price, self._ax_rsi, self._ax_macd = self._figure.subplots(
            3, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1, 1]}
        )
        self._canvas = FigureCanvasTkAgg(self._figure, master=self)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._volatility_label = ttk.Label(self, text="", foreground=theme.info_color())
        self._volatility_label.pack(fill="x", padx=8)

        self._unavailable_label = ttk.Label(
            self, text="", foreground=theme.info_color(), wraplength=980, justify="left"
        )
        self._unavailable_label.pack(fill="x", padx=8, pady=(0, 8))

    def _apply_chart_theme(self) -> None:
        """Dark-Mode-Politur fuers Chart (Nutzer-Idee 2026-07-09, "Charts
        mitziehen"): Flaechen-/Text-/Gitterfarben passend zum aktiven Theme. Bei
        jedem Render neu gesetzt, da Axes.clear() die Flaechenfarbe zuruecksetzt.
        Einzelne Indikator-/Kurvenfarben (tab:blue, tab:orange, ...) bleiben
        unveraendert - die sind auf beiden Hintergruenden ausreichend lesbar."""
        facecolor = theme.chart_facecolor()
        text_color = theme.chart_price_line_color()
        grid_color = theme.chart_grid_color()

        self._figure.patch.set_facecolor(facecolor)
        for ax in (self._ax_price, self._ax_rsi, self._ax_macd):
            ax.set_facecolor(facecolor)
            ax.tick_params(colors=text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            for spine in ax.spines.values():
                spine.set_color(grid_color)

    def _reload(self) -> None:
        currency = self._currency.get()
        conn = self._db_conn_factory()
        try:
            history = db.get_price_history(conn, self._asset.coingecko_id)
            last_date = db.get_last_history_date(conn, self._asset.coingecko_id)
            ohlc_history = []
            if self._asset.symbol in KRAKEN_PAIR_MAP:
                ohlc_history = db.get_ohlc_history(conn, self._asset.symbol, currency.upper())
        finally:
            conn.close()

        if is_history_stale(last_date):
            age_text = f"letzter Tag: {last_date}" if last_date else "keine Daten vorhanden"
            self._staleness_label.config(text=f"⚠ Historie veraltet ({age_text})")
        else:
            self._staleness_label.config(text="")

        if not history:
            self._render_no_data()
            return

        dates = np.array([p.date for p in history])
        closes = np.array(
            [(p.price_usd if currency == "usd" else p.price_eur) for p in history],
            dtype=float,
        )
        # Zeilen ohne Preis in der gewählten Währung ausfiltern (P-10: keine Lücken
        # silently interpolieren).
        valid_mask = ~np.isnan(closes)
        dates = dates[valid_mask]
        closes = closes[valid_mask]

        if len(closes) == 0:
            self._render_no_data()
            return

        self._render_chart(dates, closes, currency, ohlc_history)

    def _render_no_data(self) -> None:
        for ax in (self._ax_price, self._ax_rsi, self._ax_macd):
            ax.clear()
        self._apply_chart_theme()
        self._ax_price.text(
            0.5,
            0.5,
            "Keine historischen Daten verfügbar",
            ha="center",
            va="center",
            color=theme.chart_price_line_color(),
            transform=self._ax_price.transAxes,
        )
        self._canvas.draw()
        self._volatility_label.config(text="")
        self._unavailable_label.config(text="")

    def _render_chart(
        self, dates: np.ndarray, closes: np.ndarray, currency: str, ohlc_history: list
    ) -> None:
        currency_label = currency.upper()
        unavailable_notes: list[str] = []

        # Echte OHLC-Daten von Kraken bevorzugen (35/41 Assets, siehe api/kraken.py) -
        # nur fuer ATR und Swing-Punkte, die Preislinie selbst bleibt CoinGecko-basiert
        # (Waehrungs-Umschalter/Kontinuitaet unveraendert). Fehlt Kraken-Abdeckung,
        # bleibt die Naeherung aus Phase 2 die einzige Quelle (P-10: klar gekennzeichnet).
        # Geteilte Logik mit agent/pipeline.py, siehe indicators/calculations.py.
        snapshot = build_technical_snapshot(closes, dates, ohlc_history)

        for ax in (self._ax_price, self._ax_rsi, self._ax_macd):
            ax.clear()
        self._apply_chart_theme()

        x = mdates.datestr2num(dates)
        self._ax_price.plot(
            x, closes, label=f"Preis ({currency_label})", color=theme.chart_price_line_color(), linewidth=1,
        )

        for period, color in ((20, "tab:blue"), (50, "tab:orange"), (200, "tab:green")):
            result = snapshot.ema[period]
            if result.available:
                self._ax_price.plot(x, result.value, label=f"EMA-{period}", color=color, linewidth=1)
            else:
                unavailable_notes.append(f"EMA-{period}: nicht verfügbar ({result.reason})")

        bb = snapshot.bollinger
        if bb.available:
            self._ax_price.plot(
                x, bb.value["upper"], label="Bollinger oben", color="grey", linestyle="--", linewidth=0.8
            )
            self._ax_price.plot(
                x, bb.value["lower"], label="Bollinger unten", color="grey", linestyle="--", linewidth=0.8
            )
        else:
            unavailable_notes.append(f"Bollinger Bands: nicht verfügbar ({bb.reason})")

        swing = snapshot.swing
        swing_label = snapshot.swing_label
        swing_indicator_name = (
            "Swing-Punkte/Support-Resistance/Fibonacci"
            if snapshot.swing_source == "real"
            else "Swing-Punkte/Support-Resistance/Fibonacci (Näherung)"
        )

        if swing.available:
            # date_to_x basiert auf der (CoinGecko-)Preislinie - Swing-Punkte, deren Datum
            # dort nicht existiert (z.B. Kraken-Historie beginnt frueher), werden beim
            # Zeichnen uebersprungen statt einen KeyError zu werfen.
            date_to_x = {d: x[i] for i, d in enumerate(dates)}
            high_points = [(date_to_x[d], p) for d, p in swing.value["highs"] if d in date_to_x]
            low_points = [(date_to_x[d], p) for d, p in swing.value["lows"] if d in date_to_x]
            high_x = [px for px, _ in high_points]
            high_prices = [p for _, p in high_points]
            low_x = [px for px, _ in low_points]
            low_prices = [p for _, p in low_points]

            if high_prices:
                self._ax_price.scatter(
                    high_x, high_prices, marker="v", color="red", s=25, label=swing_label, zorder=5
                )
            if low_prices:
                self._ax_price.scatter(low_x, low_prices, marker="^", color="green", s=25, zorder=5)

            sr = snapshot.support_resistance
            if sr.available:
                for level in sr.value:
                    self._ax_price.axhline(
                        level["price"], color="purple", linestyle=":", linewidth=0.6, alpha=0.5
                    )

            if snapshot.fibonacci is not None:
                for ratio, price in snapshot.fibonacci.items():
                    self._ax_price.axhline(price, color="goldenrod", linestyle=":", linewidth=0.5, alpha=0.4)
        else:
            unavailable_notes.append(f"{swing_indicator_name}: nicht verfügbar ({swing.reason})")

        self._ax_price.set_ylabel(f"Preis ({currency_label})")
        self._ax_price.legend(loc="upper left", fontsize=7, labelcolor=theme.chart_price_line_color())
        self._ax_price.set_title(f"{self._asset.symbol} — {self._asset.name}")

        rsi_result = snapshot.rsi
        if rsi_result.available:
            self._ax_rsi.plot(x, rsi_result.value, color="tab:purple", linewidth=1)
            self._ax_rsi.axhline(70, color="red", linestyle="--", linewidth=0.6)
            self._ax_rsi.axhline(30, color="green", linestyle="--", linewidth=0.6)
            self._ax_rsi.set_ylim(0, 100)
            self._ax_rsi.set_ylabel("RSI-14")
        else:
            unavailable_notes.append(f"RSI-14: nicht verfügbar ({rsi_result.reason})")

        macd_result = snapshot.macd
        if macd_result.available:
            self._ax_macd.plot(x, macd_result.value["macd"], label="MACD", color="tab:blue", linewidth=1)
            self._ax_macd.plot(x, macd_result.value["signal"], label="Signal", color="tab:orange", linewidth=1)
            self._ax_macd.bar(x, macd_result.value["histogram"], color="grey", alpha=0.4, width=0.8)
            self._ax_macd.legend(loc="upper left", fontsize=7, labelcolor=theme.chart_price_line_color())
            self._ax_macd.set_ylabel("MACD")
        else:
            unavailable_notes.append(f"MACD: nicht verfügbar ({macd_result.reason})")

        locator = mdates.AutoDateLocator()
        self._ax_macd.xaxis.set_major_locator(locator)
        self._ax_macd.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        self._ax_macd.set_xlabel("Datum")
        self._figure.autofmt_xdate()

        atr_result = snapshot.atr
        atr_label = snapshot.atr_label
        if atr_result.available:
            latest_vol = latest_value(atr_result)
            self._volatility_label.config(
                text=f"{atr_label}: {format_money(latest_vol)} {currency_label}/Tag"
            )
        else:
            self._volatility_label.config(text="")
            unavailable_notes.append(f"{atr_label}: nicht verfügbar ({atr_result.reason})")

        self._figure.tight_layout()
        self._canvas.draw()

        if unavailable_notes:
            self._unavailable_label.config(text="Nicht verfügbar: " + " | ".join(unavailable_notes))
        else:
            self._unavailable_label.config(text="")
