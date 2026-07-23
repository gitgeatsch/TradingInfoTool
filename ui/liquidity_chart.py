# -*- coding: utf-8 -*-
"""Kompakte, eigenständige Grafik zum Liquiditätszonen-Fakt (Marketmaker-
Konzept, Stufe 1, 2026-07-23) - EIN gemeinsamer Renderer für App-Detail-Panel
UND E-Mail (eingebettetes PNG), damit beide Stellen exakt dasselbe Bild
zeigen statt zweier Implementierungen, die auseinanderlaufen könnten.

Nutzt `matplotlib.figure.Figure` direkt (wie `ui/charts.py`) statt `pyplot` -
vermeidet globalen State/Thread-Sicherheitsprobleme, da dieser Renderer
sowohl aus dem Tk-Main-Thread (App) als auch aus einem Scheduler-
Hintergrund-Thread (E-Mail-Versand) aufgerufen wird."""
from __future__ import annotations

import io

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ui.formatting import format_money

_FARBE_BUYSIDE = "#378ADD"
_FARBE_SELLSIDE = "#D85A30"
_FARBE_GEFEGT = "#9a9a95"
_FARBE_PREIS = "#2c2c2a"


def _zeile(preis: float, waehrung: str, abstand_prozent: float, vorzeichen: str,
           touches: int, datum: str, bereits_gefegt: bool) -> str:
    status = "bereits gefegt" if bereits_gefegt else "noch nicht gefegt"
    return (
        f"{format_money(preis)} {waehrung} ({vorzeichen}{abstand_prozent:.1f}%)\n"
        f"{touches} Berührungen · zuletzt {datum} · {status}"
    )


def render_liquiditaetszonen_chart(
    liquiditaetszonen: dict, latest_price: float, waehrung: str = "EUR",
) -> bytes | None:
    """Baut eine kompakte PNG-Grafik (~560x260px) mit dem aktuellen Kurs und
    der nächsten Buy-/Sell-Side-Liquiditätszone, inkl. konkreter Zahlen
    (Preis+Einheit, Abstand in %, Berührungen, Datum der letzten Berührung)
    direkt als Text im Bild - kein reines Linienbild ohne Kontext. Gibt
    `None` zurück, wenn keine der beiden Zonen vorhanden ist (nichts
    Sinnvolles darzustellen, z.B. zu wenig Swing-Historie)."""
    buyside = liquiditaetszonen.get("naechste_buyside_zone")
    sellside = liquiditaetszonen.get("naechste_sellside_zone")
    if buyside is None and sellside is None:
        return None

    fig = Figure(figsize=(5.6, 2.6), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_axis_off()

    preise = [latest_price] + [z["preis"] for z in (buyside, sellside) if z is not None]
    y_min, y_max = min(preise), max(preise)
    spanne = (y_max - y_min) or (abs(latest_price) * 0.02 or 1.0)
    y_min -= spanne * 0.2
    y_max += spanne * 0.2
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0, 10)

    ax.axhline(latest_price, color=_FARBE_PREIS, linewidth=2, xmax=0.5)
    ax.text(0.2, latest_price, f"Aktueller Kurs: {format_money(latest_price)} {waehrung}",
            fontsize=9.5, color=_FARBE_PREIS, va="bottom", ha="left", fontweight="bold")

    if buyside is not None:
        gefegt = buyside["bereits_gefegt"]
        farbe = _FARBE_GEFEGT if gefegt else _FARBE_BUYSIDE
        ax.axhline(buyside["preis"], color=farbe, linewidth=1.6, linestyle=(":" if gefegt else "--"), xmax=0.5)
        ax.text(
            0.2, buyside["preis"],
            "Buy-Side-Zone: " + _zeile(buyside["preis"], waehrung, buyside["abstand_prozent"], "+",
                                        buyside["touches"], buyside["letzte_beruehrung_datum"], gefegt),
            fontsize=8.5, color=farbe, va="bottom", ha="left",
        )

    if sellside is not None:
        gefegt = sellside["bereits_gefegt"]
        farbe = _FARBE_GEFEGT if gefegt else _FARBE_SELLSIDE
        ax.axhline(sellside["preis"], color=farbe, linewidth=1.6, linestyle=(":" if gefegt else "-"), xmax=0.5)
        ax.text(
            0.2, sellside["preis"],
            "Sell-Side-Zone: " + _zeile(sellside["preis"], waehrung, sellside["abstand_prozent"], "-",
                                         sellside["touches"], sellside["letzte_beruehrung_datum"], gefegt),
            fontsize=8.5, color=farbe, va="top", ha="left",
        )

    fig.tight_layout()
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    return buf.getvalue()
