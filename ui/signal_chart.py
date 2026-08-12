# -*- coding: utf-8 -*-
"""Ein Chart je Signal - der Plan im Kursbild (12.08.2026).

ER ERSETZT ZWEI (Umbauplan 12.6). Der alte Konfidenz-Verlauf plottete genau die
Groesse, die wegen 77,5 % vorhergesagt gegen 33,3 % gemessen gestrichen wurde -
das Verlaufsbild einer unkalibrierten Zahl ist doppelt irrefuehrend. Der alte
Zonen-Chart zeigte die Buy-Side-Zone, aber NICHT Einstieg, Stop und Ziel, also
gerade nicht das, was zu tun waere; dazu ueberlappende Beschriftungen und der
Waehrungsfehler aus 12.5 (dieselbe Zone hiess im Text 65,61 und in der Grafik
"57,05 EUR").

WAS DIESER ZEIGT: 90 Tage Kurs, darauf Einstiegszone, Stop und Ziel als Baender,
plus Widerstand und Unterstuetzung als Linien. Damit wird Abschnitt 2 der Mail
auf einen Blick pruefbar - liegt der Stop unter einer echten Marke, steht das
Ziel vor einer Mauer, ist die Zone ueberhaupt in Reichweite.

EINE WAEHRUNG, UND SIE STEHT DRAN. Der Fehler der alten Mail war nicht, dass
umgerechnet wurde - es war, dass nirgends stand, welche Einheit gemeint ist.
Alle Werte hier kommen in EUR herein und die Achse sagt es.

KEIN CHART OHNE PLAN. Fehlen Einstieg, Stop oder Ziel - etwa weil die
Empfehlung NICHTS_TUN lautet -, gibt es kein Bild. Ein Kursverlauf ohne
eingezeichneten Plan ist Dekoration, und Dekoration war der Vorwurf an den
alten Chart.
"""
from __future__ import annotations

import io

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

TAGE = 90

# Zurueckhaltende Farben - das Bild soll gelesen, nicht bestaunt werden.
FARBE_KURS = "#1f2d3d"
FARBE_ZONE = "#2e7d32"      # Einstieg: gruen
FARBE_STOP = "#c62828"      # Stop: rot
FARBE_ZIEL = "#1565c0"      # Ziel: blau
FARBE_MARKE = "#9e9e9e"


def _de(wert: float) -> str:
    return f"{float(wert):,.0f}".translate(str.maketrans(",.", ".,"))


def render_signal_chart(*, symbol: str, kurse_eur: list, datum: list | None = None,
                        einstieg_von: float | None = None,
                        einstieg_bis: float | None = None,
                        stop: float | None = None,
                        ziel_von: float | None = None,
                        ziel_bis: float | None = None,
                        widerstand: float | None = None,
                        unterstuetzung: float | None = None) -> bytes | None:
    """PNG-Bytes, oder None wenn es nichts zu zeigen gibt."""
    if not kurse_eur or len(kurse_eur) < 20:
        return None
    if einstieg_von is None or stop is None or ziel_von is None:
        # Ohne Plan kein Bild - siehe Modulkopf.
        return None

    kurse = [float(k) for k in kurse_eur][-TAGE:]
    x = list(range(len(kurse)))
    einstieg_bis = float(einstieg_bis if einstieg_bis is not None else einstieg_von)
    ziel_bis = float(ziel_bis if ziel_bis is not None else ziel_von)

    fig = Figure(figsize=(7.2, 3.4), dpi=110, facecolor="white")
    ax = fig.add_subplot(111)
    ax.plot(x, kurse, color=FARBE_KURS, linewidth=1.4, zorder=3)

    # Baender ueber die volle Breite - sie gelten ab jetzt, nicht ab damals,
    # aber ihre Hoehe ist die Aussage.
    ax.axhspan(float(einstieg_von), einstieg_bis, color=FARBE_ZONE, alpha=0.16, zorder=1)
    ax.axhspan(float(ziel_von), ziel_bis, color=FARBE_ZIEL, alpha=0.14, zorder=1)
    ax.axhline(float(stop), color=FARBE_STOP, linewidth=1.3, linestyle="--", zorder=2)

    for marke, text in ((widerstand, "Widerstand"), (unterstuetzung, "Unterstuetzung")):
        if marke:
            ax.axhline(float(marke), color=FARBE_MARKE, linewidth=1.0,
                       linestyle=":", zorder=2)
            ax.annotate(f"{text} {_de(marke)}", xy=(0, float(marke)),
                        xytext=(2, 2), textcoords="offset points",
                        fontsize=7, color=FARBE_MARKE, va="bottom")

    # BESCHRIFTUNG RECHTS AUSSERHALB DER KURVE. Der alte Chart schrieb seine
    # Etiketten mitten auf die Kurslinie, wo sie unlesbar wurden.
    rand = max(kurse + [ziel_bis, float(einstieg_von)]) - min(kurse + [float(stop)])
    ax.set_xlim(0, len(kurse) * 1.34)
    ax.set_ylim(min(kurse + [float(stop)]) - 0.04 * rand,
                max(kurse + [ziel_bis]) + 0.04 * rand)
    rechts = len(kurse) * 1.02
    for wert, farbe, text in (
            ((float(einstieg_von) + einstieg_bis) / 2, FARBE_ZONE,
             f"Einstieg {_de(einstieg_von)}-{_de(einstieg_bis)}"),
            (float(stop), FARBE_STOP, f"Stop {_de(stop)}"),
            ((float(ziel_von) + ziel_bis) / 2, FARBE_ZIEL,
             f"Ziel {_de(ziel_von)}-{_de(ziel_bis)}")):
        # LEICHT VERSETZT, nicht auf der Linie. Der alte Chart schrieb seine
        # Etiketten genau auf die Marke, die sie beschriften - dort sind sie
        # gegen jeden Hintergrund schlecht lesbar.
        ax.annotate(text, xy=(rechts, wert), xytext=(0, 4),
                    textcoords="offset points", fontsize=8, color=farbe,
                    va="center", fontweight="bold")

    ax.set_title(f"{symbol} - letzte {len(kurse)} Tage und der Plan",
                 fontsize=9, color=FARBE_KURS, loc="left")
    ax.set_ylabel("EUR", fontsize=8)
    # Deutsche Tausendertrennung auch an der Achse - "80000" gegen "80.000".
    ax.yaxis.set_major_formatter(FuncFormatter(lambda w, _: _de(w)))
    ax.tick_params(labelsize=7)
    ax.set_xticks([])
    for rand_name in ("top", "right", "bottom"):
        ax.spines[rand_name].set_visible(False)
    ax.grid(axis="y", color="#eeeeee", linewidth=0.8, zorder=0)
    fig.tight_layout()

    buf = io.BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    return buf.getvalue()
