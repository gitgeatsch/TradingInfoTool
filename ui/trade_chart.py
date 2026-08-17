# -*- coding: utf-8 -*-
"""Der geplante Trade als Bild (O-24, 14.08.2026).

WARUM NICHT DER BESTEHENDE CHART. `ui/liquidity_chart.py` zeichnet
Liquiditaetszonen und braucht dafuer das Faktum `liquiditaetszonen` - das die
Rollen-Kette nicht mehr baut. Es gehoerte zu den 34.611 Prompt-Zeichen, die der
Umbau auf 3.183 gekuerzt hat, und wiedereinzufuehren nur fuer ein Bild waere
genau der Weg zurueck, den der Umbau vermeiden sollte.

WAS STATTDESSEN GEZEICHNET WIRD: der Trade, den die Mail beschreibt. Kurs der
letzten Monate, darauf die Einstiegszone, der Stop und das Ziel - also die drei
Zahlen aus Abschnitt 2 der Mail, an ihrem Platz im Kursverlauf. Dazu die
naechsten Marken, wo sie bekannt sind.

WOFUER DAS GUT IST, und wofuer nicht. Es beantwortet die eine Frage, die aus
Zahlen allein schwer zu beantworten ist: **liegt der Stop irgendwo, wo der Kurs
schon oefter war?** Ein Stop mitten in einem Bereich, den der Kurs in den
letzten Wochen dreimal durchlaufen hat, ist ein anderer Stop als einer unter
allem, was da war - und in der Zahlenzeile sehen beide gleich aus.

Es ersetzt KEINE Analyse. Es ist die Darstellung einer bereits getroffenen
Entscheidung, nicht ihre Begruendung.

ADVISORY-ONLY UND FAIL-SOFT: gibt None zurueck, wenn irgendetwas fehlt. Eine
Mail ohne Bild ist aermer, eine Mail, die wegen eines Bildes nicht rausgeht,
ist weg (P-8).
"""
from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

# Wie viele Handelstage der Ausschnitt zeigt. Drei Monate: lang genug, dass die
# Marken einen Zusammenhang haben, kurz genug, dass die Zone nicht zu einem
# Strich zusammenschrumpft.
TAGE = 90


def render_trade_chart(*, reihe: list, index: int, rechnung: dict,
                       symbol: str, marken: list | None = None,
                       fx_eur_je_usd: float | None = None) -> bytes | None:
    """PNG des geplanten Trades - oder None.

    `reihe` sind die Kerzen, `index` der Ankertag. `rechnung` ist das Ergebnis
    von `entscheidungsrechnung.rechne()`.

    DIE WAEHRUNG IST DER STOLPERSTEIN, und er hat schon einmal zugeschlagen
    (25.07., Nutzerfund am BTC-Hebel-Signal): die Kursreihe steht in USD, die
    Rechnung in EUR. Beides ungefragt in ein Bild zu legen ergibt eine
    Grafik mit richtiger Form und falscher Skala. Deshalb wird die REIHE nach
    EUR umgerechnet, wenn der Faktor vorliegt - und ohne ihn gibt es kein Bild
    statt eines falschen."""
    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except Exception:                                        # noqa: BLE001
        return None

    try:
        hist = (reihe or [])[max(0, index + 1 - TAGE):index + 1]
        if len(hist) < 20 or not rechnung:
            return None
        # OHNE UMRECHNUNGSFAKTOR KEIN BILD - so, wie es oben steht.
        #
        # Meine erste Fassung dokumentierte genau das und rechnete trotzdem
        # mit 1.0 weiter. Das haette die Kursreihe in USD gegen Stop und Ziel
        # in EUR gezeichnet: richtige Form, falsche Skala, und niemand haette
        # es dem Bild angesehen. Es ist derselbe Fehler, den der Nutzer am
        # 25.07. am BTC-Hebel-Signal gefunden hat.
        #
        # Ein fehlendes Bild ist ein Mangel. Ein falsches Bild ist eine
        # Falschaussage - und die wiegt schwerer.
        if not fx_eur_je_usd:
            return None
        f = float(fx_eur_je_usd)
        kurse = [float(k.close) * f for k in hist]

        fig = Figure(figsize=(7.2, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(range(len(kurse)), kurse, linewidth=1.4, color="#1f77b4",
                label=f"{symbol} (EUR)")

        von = rechnung.get("einstieg_von_eur")
        bis = rechnung.get("einstieg_bis_eur")
        if von and bis:
            ax.axhspan(min(von, bis), max(von, bis), alpha=0.18,
                       color="#2ca02c", label="Einstiegszone")
        for wert, farbe, name in (
                (rechnung.get("stop_eur"), "#d62728", "Stop"),
                (rechnung.get("ziel_von_eur"), "#2ca02c", "Ziel")):
            if wert:
                ax.axhline(float(wert), color=farbe, linewidth=1.1,
                           linestyle="--", label=name)

        # DIE MARKEN NUR ALS DUENNE LINIE, ohne Beschriftung im Bild. Sie
        # stehen im Text mit Zahl und Beruehrungszahl; sie hier noch einmal zu
        # beschriften macht das Bild voll, ohne etwas hinzuzufuegen.
        for wert in (marken or []):
            try:
                ax.axhline(float(wert), color="#888888", linewidth=0.7,
                           alpha=0.6)
            except (TypeError, ValueError):
                continue

        ax.set_title(f"{symbol} - der geplante Trade", fontsize=10)
        ax.tick_params(labelsize=8)
        # DIE ZEITACHSE WAR LEER (17.08.2026, Nutzerhinweis). Hier stand
        # `ax.set_xticks([])` - das Bild zeigte einen Verlauf ohne
        # Zeitangabe, und ob er ueber zwei Wochen oder ueber ein halbes
        # Jahr laeuft, aendert alles an seiner Bedeutung.
        #
        # VIER BIS FUENF MARKEN, NICHT ALLE. Bei 120 Kerzen waeren 120
        # Datumsangaben eine schwarze Leiste; die Enden und drei Punkte
        # dazwischen sagen dasselbe und bleiben lesbar. Das Datum kommt
        # aus DERSELBEN Kerze wie der Kurs - eine zweite Zeitquelle waere
        # eine zweite Wahrheit.
        marken_x, marken_text = [], []
        schritt = max(1, (len(hist) - 1) // 4)
        for i in range(0, len(hist), schritt):
            tag = str(getattr(hist[i], "date", "") or "")[:10]
            if not tag:
                continue
            marken_x.append(i)
            # Tag und Monat reichen - das Jahr steht ohnehin im Mailkopf,
            # und vier volle Datumsangaben nebeneinander liest niemand.
            marken_text.append(f"{tag[8:10]}.{tag[5:7]}.")
        if marken_x:
            ax.set_xticks(marken_x)
            ax.set_xticklabels(marken_text, fontsize=7)
            # Wieviel Zeit das Bild ueberhaupt zeigt - die Frage, die man
            # sonst aus den Marken zusammenrechnen muesste.
            ax.set_xlabel(f"{len(hist)} Handelstage bis "
                          f"{str(getattr(hist[-1], 'date', '') or '')[:10]}",
                          fontsize=7)
        else:
            ax.set_xticks([])
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=7, loc="best", framealpha=0.85)
        fig.tight_layout()

        puffer = io.BytesIO()
        FigureCanvasAgg(fig).print_png(puffer)
        return puffer.getvalue()
    except Exception:                                        # noqa: BLE001
        logger.info("Trade-Chart fuer %s fehlgeschlagen (P-8)", symbol,
                    exc_info=True)
        return None
