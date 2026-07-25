# -*- coding: utf-8 -*-
"""Kompakte, eigenständige Grafik zum Signal-Stabilitäts-Fakt (2026-07-25,
echter NEAR/LINK-Fund, siehe agent/krypto/signal_stabilitaet.py Modul-
Docstring) - EIN gemeinsamer Renderer für App-Detail-Panel UND E-Mail
(eingebettetes PNG), exakt nach demselben Muster wie ui/liquidity_chart.py
(Figure/FigureCanvasAgg statt pyplot - thread-sicher, sowohl aus dem Tk-
Main-Thread als auch aus einem Scheduler-Hintergrund-Thread aufrufbar)."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

_FARBE_STABIL = "#1a7a4c"
_FARBE_INSTABIL = "#c0392b"
# Echter Kategoriewechsel (Aufbau<->Abbau<->Neutral, siehe agent/krypto/
# signal_stabilitaet.py Modul-Docstring) - deutlich, durchgezogen, gleiche
# Warnfarbe wie _FARBE_INSTABIL (das IST der Grund fuer "instabil").
_FARBE_KATEGORIEWECHSEL = "#c0392b"
# Reine Tier-Feinjustierung INNERHALB derselben Kategorie (z.B. Teilverkauf
# <-> Schliessen) - bewusst deutlich zurueckhaltender (heller, duenner,
# gepunktet), kein Warncharakter.
_FARBE_TIER_WECHSEL = "#c2c2bd"
_FARBE_TEXT = "#2c2c2a"


def _kurzzeit(iso_timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%H:%M")
    except ValueError:
        return iso_timestamp[:16].replace("T", " ")


def render_signal_stabilitaet_chart(signal_stabilitaet: dict) -> bytes | None:
    """Baut eine kompakte PNG-Grafik (~560x220px) mit dem Konfidenzverlauf der
    letzten Bewertungszyklen (chronologisch aufsteigend, siehe `verlauf` im
    Fakt) als Linie, gefaerbt nach `stabil` (gruen) vs. instabil (rot).
    Markiert echte Kategoriewechsel (Aufbau<->Abbau<->Neutral, siehe
    agent/krypto/signal_stabilitaet.py Modul-Docstring) mit einer deutlichen
    durchgezogenen roten Linie, reine Tier-Feinjustierungen innerhalb
    derselben Kategorie (z.B. Teilverkauf<->Schliessen) nur mit einer duennen,
    hellen gepunkteten Linie - bewusst unterschiedlich gewichtet, damit der
    Nutzer echte Meinungswechsel von blosser Intensitaets-Feinjustierung
    unterscheiden kann. Gibt `None` zurueck, wenn weniger als 2 Punkte
    vorhanden sind (nichts Sinnvolles darzustellen - deckt sich mit dem
    `None`-Fall von signal_stabilitaet_fakt() selbst, ist hier nur eine
    defensive zweite Pruefung fuer den Fall aelterer/manipulierter
    facts_json-Daten ohne `kategorie`-Feld)."""
    verlauf = signal_stabilitaet.get("verlauf") or []
    if len(verlauf) < 2:
        return None

    konfidenzen = [p["konfidenz_pct"] for p in verlauf]
    kategorien = [p.get("kategorie") for p in verlauf]
    farbe = _FARBE_STABIL if signal_stabilitaet.get("stabil") else _FARBE_INSTABIL

    fig = Figure(figsize=(5.6, 2.3), dpi=100, facecolor="white")
    ax = fig.add_subplot(111, facecolor="white")

    x = range(len(konfidenzen))
    ax.plot(
        x, konfidenzen, color=farbe, linewidth=1.8, marker="o", markersize=4,
        solid_capstyle="round", solid_joinstyle="round", zorder=5,
    )
    # 2026-07-25, Nutzer-Wunsch: konkreter %-Wert direkt über jedem Punkt,
    # damit man den Verlauf nicht erst aus der Y-Achse ablesen muss.
    for xi, yi in zip(x, konfidenzen):
        ax.annotate(
            f"{yi:.0f}", (xi, yi), textcoords="offset points", xytext=(0, 7),
            ha="center", fontsize=7, color=_FARBE_TEXT, zorder=6,
        )

    for i in range(1, len(kategorien)):
        if kategorien[i] is None or kategorien[i - 1] is None:
            continue
        if kategorien[i] != kategorien[i - 1]:
            ax.axvline(i - 0.5, color=_FARBE_KATEGORIEWECHSEL, linewidth=1.6, linestyle="-", zorder=2)
        elif verlauf[i]["action"] != verlauf[i - 1]["action"]:
            ax.axvline(i - 0.5, color=_FARBE_TIER_WECHSEL, linewidth=0.8, linestyle=":", zorder=1)

    ax.set_ylim(0, 100)
    ax.set_xlim(-0.3, len(konfidenzen) - 0.7)
    ax.set_xticks(list(x))
    ax.set_xticklabels([_kurzzeit(p["datum"]) for p in verlauf], fontsize=7, rotation=30, ha="right")
    ax.set_ylabel("Konfidenz %", fontsize=8, color=_FARBE_TEXT)
    ax.tick_params(axis="y", labelsize=7, colors=_FARBE_TEXT)
    ax.tick_params(axis="x", colors=_FARBE_TEXT)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    titel = "Signal-Stabilität: stabil" if signal_stabilitaet.get("stabil") else "Signal-Stabilität: instabil"
    ax.set_title(titel, fontsize=10.5, color=farbe, fontweight="bold", loc="left")

    fig.text(
        0.015, 0.015, signal_stabilitaet.get("einordnung", ""), fontsize=6.5,
        color=_FARBE_TEXT, ha="left", va="bottom", wrap=True,
    )

    fig.tight_layout(rect=(0, 0.16, 1, 1))
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    return buf.getvalue()
