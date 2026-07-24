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
# 2026-07-23, Nutzer-Fund: war "#9a9a95" (Kontrast nur ~2,7:1 auf Weiss) - bei
# realer Browser-/E-Mail-Client-Darstellung (Skalierung, Client-Rendering)
# praktisch unsichtbar, obwohl in einer isolierten PNG-Ansicht noch erkennbar.
# Nachgedunkelt auf WCAG-AA-Kontrast (~4,6:1), bleibt gegenueber den aktiven
# Buy-/Sell-Side-Farben weiterhin sichtbar "gedaempft".
_FARBE_GEFEGT = "#6e6e69"
_FARBE_PREIS = "#2c2c2a"
# 2026-07-23, Nutzer-Wunsch: echte Kursverlauf-Linie statt nur der beiden
# Zonen-Referenzlinien ("ich rede von... was eine Chartlinie zu sehen").
# Eigene, von Buy-/Sell-Side/Preis-Linie klar unterscheidbare Akzentfarbe.
_FARBE_KURSVERLAUF = "#9c1458"
# 2026-07-24, Nutzer-Wunsch (Kombianzeige): zweite, klar unterscheidbare
# Referenzlinie fuer den LIVE nachgeladenen Kurs, zusaetzlich zum am
# Analysezeitpunkt eingefrorenen Kurs (siehe render_liquiditaetszonen_chart()-
# Docstring). Gruen, um sich bewusst von den bestehenden Farben (Blau/Orange/
# Grau/Dunkelgrau/Magenta) abzuheben.
_FARBE_LIVE_PREIS = "#1a7a4c"
# Ab dieser relativen Abweichung wird die Live-Linie ueberhaupt erst
# gezeichnet - darunter waeren beide Linien optisch ununterscheidbar
# (unnoetiges Rauschen im ohnehin kompakten Chart).
_LIVE_PREIS_MINDESTABWEICHUNG_RELATIV = 0.001

# 2026-07-23, Nutzer-Wunsch: statischer, IMMER GLEICHER Erklaersatz (keine
# Signal-spezifische Interpretation - die uebernimmt bereits das LLM in der
# eigenen Kurz-/Langbegruendung, siehe hebel_analyst.py Regel 17). Erklaert
# nur die Begrifflichkeit ("Beruehrungen"/"gefegt"/"ungefegt"), bewusst ohne
# jede Wertung zur aktuellen Situation - bleibt damit neutral im Sinne des
# Stufe-1-Designs (reine Transparenz, kein Deckel).
_ERKLAERUNG = (
    "Berührungen = frühere Kursreaktionen an dieser Zone · gefegt = bereits "
    "durchbrochen (kein akutes Warnsignal mehr) · ungefegt = noch aktiv "
    "(möglicher Stop-Hunt vor einer Bewegung)"
)


def _zeile(preis: float, waehrung: str, abstand_prozent: float, vorzeichen: str,
           touches: int, datum: str, bereits_gefegt: bool, seither_erreicht: bool = False) -> str:
    status = "bereits gefegt" if bereits_gefegt else "noch nicht gefegt"
    zeile = (
        f"{format_money(preis)} {waehrung} ({vorzeichen}{abstand_prozent:.1f}%)\n"
        f"{touches} Berührungen · zuletzt {datum} · {status}"
    )
    # 2026-07-24, Nutzer-Fund: der eingefrorene "noch nicht gefegt"-Status gilt
    # nur zum Analysezeitpunkt - hat der seither nachgeladene Live-Kurs die
    # Zone inzwischen erreicht/durchbrochen, wird das HIER zusaetzlich vermerkt
    # (der eingefrorene Status selbst bleibt unveraendert stehen, siehe
    # render_liquiditaetszonen_chart()-Docstring: historisch korrekt, nicht
    # rueckwirkend ueberschrieben).
    if seither_erreicht:
        zeile += "\n⚠ seit der Analyse bereits erreicht (aktueller Kurs)"
    return zeile


def _zone_seither_erreicht(zone: dict | None, seite: str, live_preis: float | None) -> bool:
    if zone is None or live_preis is None or zone.get("bereits_gefegt"):
        return False
    zone_preis = zone["preis"]
    if seite == "buyside":
        return live_preis >= zone_preis
    return live_preis <= zone_preis


def render_liquiditaetszonen_chart(
    liquiditaetszonen: dict, latest_price: float, waehrung: str = "EUR",
    live_preis: float | None = None,
) -> bytes | None:
    """Baut eine kompakte PNG-Grafik (~560x280px) mit dem Kurs zum
    Analysezeitpunkt, der nächsten Buy-/Sell-Side-Liquiditätszone (inkl.
    konkreter Zahlen: Preis+Einheit, Abstand in %, Berührungen, Datum der
    letzten Berührung direkt als Text im Bild) UND - wenn im Fakt vorhanden
    (`kursverlauf`, 2026-07-23, Nutzer-Wunsch nach einer echten Chart-Linie
    statt nur der beiden Zonen-Referenzlinien) - dem tatsächlichen
    Kursverlauf als Linie. Gibt `None` zurück, wenn keine der beiden Zonen
    vorhanden ist (nichts Sinnvolles darzustellen, z.B. zu wenig
    Swing-Historie).

    `latest_price` (2026-07-24 umbenannt/klargestellt, siehe Nutzer-Diskussion:
    "veralteter Chart" vs. echter Blick in die Zukunft) ist der Kurs, der
    BEREITS im `facts_json` dieses Signals eingebettet ist (`facts["preis"][
    "eur"/"usd"]`) - exakt derselbe Zeitpunkt wie `kursverlauf` und die
    Zonen-"gefegt"-Flags, damit der Chart in sich konsistent bleibt (kein
    Live-Preis, der nicht zum Ende der Kurslinie passt).

    `live_preis` (NEU, 2026-07-24, Kombianzeige) - optional zusätzlich der
    JETZT nachgeladene Live-Kurs. Wird nur als eigene zweite Referenzlinie
    gezeichnet, wenn er sich relevant vom Analysezeitpunkt-Kurs unterscheidet
    (`_LIVE_PREIS_MINDESTABWEICHUNG_RELATIV`) - macht sichtbar, ob/wie weit
    sich der Kurs seit der Analyse bewegt hat, UND ob eine noch "ungefegte"
    Zone seitdem bereits erreicht/durchbrochen wurde (reine Zusatz-Information,
    der eingefrorene historische Status selbst wird nie überschrieben - siehe
    `_zone_seither_erreicht()`). Ohne `live_preis` (z.B. E-Mail-Versand direkt
    nach Signal-Erstellung, kein sinnvoller Unterschied zu erwarten) bleibt
    das Verhalten unverändert bei einer einzigen Preislinie.

    Rückwärtskompatibel: bereits VOR diesem Nachtrag erzeugte Signale haben
    kein `kursverlauf` im gespeicherten `facts_json` - in dem Fall bleibt die
    Grafik exakt beim alten schematischen Layout (Referenzlinien nur über die
    linke Hälfte), kein Fehler, keine leere/kaputte Grafik."""
    buyside = liquiditaetszonen.get("naechste_buyside_zone")
    sellside = liquiditaetszonen.get("naechste_sellside_zone")
    if buyside is None and sellside is None:
        return None

    kursverlauf = liquiditaetszonen.get("kursverlauf") or []
    kurs_preise = [p["preis"] for p in kursverlauf]
    hat_kursverlauf = len(kurs_preise) >= 2

    # Hintergrund explizit weiss+opak fixieren (2026-07-23, Nutzer-Fund: in der
    # E-Mail wirkte die Grafik "ohne Linien/Beschriftung") - unabhaengig von
    # jedem ambienten matplotlib-rcParams-Zustand des aufrufenden Prozesses
    # (Notebook-Scheduler-Thread vs. App-Hauptthread), niemals implizit vom
    # Default abhaengig.
    fig = Figure(figsize=(5.6, 3.0), dpi=100, facecolor="white")
    ax = fig.add_subplot(111, facecolor="white")
    ax.set_axis_off()

    preise = [latest_price] + [z["preis"] for z in (buyside, sellside) if z is not None] + kurs_preise
    if live_preis is not None:
        preise.append(live_preis)
    y_min, y_max = min(preise), max(preise)
    spanne = (y_max - y_min) or (abs(latest_price) * 0.02 or 1.0)
    y_min -= spanne * 0.2
    y_max += spanne * 0.2
    ax.set_ylim(y_min, y_max)

    # Referenzlinien liefen bisher nur ueber die linke Haelfte (xmax=0.5,
    # Achsen-Bruchteil, unabhaengig von den Datenkoordinaten) - mit einer
    # echten Kursverlauf-Linie sollen sie wie in einem echten Chart ueber die
    # VOLLE Breite laufen. Ohne Kursverlauf (Rueckwaertskompatibilitaet)
    # bleibt das alte schematische 0-10-Layout mit Halbbreite unveraendert.
    if hat_kursverlauf:
        x_max_data = len(kurs_preise) - 1
        ax.set_xlim(0, x_max_data)
        linien_xmax = 1.0
    else:
        ax.set_xlim(0, 10)
        linien_xmax = 0.5

    # Kleiner vertikaler Puffer (2026-07-23, Nutzer-Fund: Sell-Side-Label
    # ueberlappte seine eigene gestrichelte/gepunktete Linie, weil va="top"
    # den Text OHNE Abstand direkt an der Linie verankerte - anders als
    # Buy-Side/Kurs mit va="bottom", die dadurch schon einen natuerlichen
    # Abstand hatten). Schiebt Buy-Side-/Kurs-Text nach oben, Sell-Side-Text
    # nach unten weg von der jeweiligen Linie.
    puffer = spanne * 0.04

    ax.axhline(latest_price, color=_FARBE_PREIS, linewidth=2, xmax=linien_xmax)
    # 2026-07-23, Nutzer-Fund: bei eng beieinander liegenden Zonen/Kurs
    # ueberlappte das Kurs-Label mit den Zonen-Labels, da alle drei auf
    # derselben linken Seite (x=0.2) standen und sich bei geringem
    # Preisabstand vertikal nicht mehr trennen liessen. Rechts einordnen
    # (ueber eine "Blend"-Transform: x als Achsen-Bruchteil unabhaengig vom
    # Datenbereich, y weiterhin am echten Kurswert) trennt es raeumlich von
    # den links stehenden Zonen-Labels, auch wenn die Preise nahe beieinander
    # liegen.
    ax.text(
        0.98, latest_price + puffer, f"Kurs zum Analysezeitpunkt: {format_money(latest_price)} {waehrung}",
        fontsize=9.5, color=_FARBE_PREIS, va="bottom", ha="right", fontweight="bold",
        transform=ax.get_yaxis_transform(),
    )

    # Kombianzeige (2026-07-24, Nutzer-Wunsch): zweite Referenzlinie fuer den
    # LIVE nachgeladenen Kurs, nur wenn er sich spuerbar vom Analysezeitpunkt-
    # Kurs unterscheidet - sonst waeren beide Linien optisch identisch und nur
    # Rauschen.
    zeigt_live_preis = (
        live_preis is not None and latest_price
        and abs(live_preis - latest_price) / abs(latest_price) > _LIVE_PREIS_MINDESTABWEICHUNG_RELATIV
    )
    if zeigt_live_preis:
        ax.axhline(live_preis, color=_FARBE_LIVE_PREIS, linewidth=1.6, linestyle="--", xmax=linien_xmax)
        ax.text(
            0.98, live_preis - puffer, f"Aktueller Kurs (jetzt): {format_money(live_preis)} {waehrung}",
            fontsize=9.5, color=_FARBE_LIVE_PREIS, va="top", ha="right", fontweight="bold",
            transform=ax.get_yaxis_transform(),
        )

    if buyside is not None:
        gefegt = buyside["bereits_gefegt"]
        farbe = _FARBE_GEFEGT if gefegt else _FARBE_BUYSIDE
        # Gepunktete Linien (gefegt) brauchen etwas mehr Strichbreite als
        # gestrichelte/durchgezogene, da ein Punktmuster pro Laengeneinheit
        # weniger sichtbare "Tinte" traegt (sonst bei Skalierung kaum sichtbar).
        ax.axhline(buyside["preis"], color=farbe, linewidth=(2.2 if gefegt else 1.6),
                   linestyle=(":" if gefegt else "--"), xmax=linien_xmax)
        ax.text(
            0.2, buyside["preis"] + puffer,
            "Buy-Side-Zone: " + _zeile(
                buyside["preis"], waehrung, buyside["abstand_prozent"], "+",
                buyside["touches"], buyside["letzte_beruehrung_datum"], gefegt,
                seither_erreicht=_zone_seither_erreicht(buyside, "buyside", live_preis),
            ),
            fontsize=8.5, color=farbe, va="bottom", ha="left",
        )

    if sellside is not None:
        gefegt = sellside["bereits_gefegt"]
        farbe = _FARBE_GEFEGT if gefegt else _FARBE_SELLSIDE
        ax.axhline(sellside["preis"], color=farbe, linewidth=(2.2 if gefegt else 1.6),
                   linestyle=(":" if gefegt else "-"), xmax=linien_xmax)
        ax.text(
            0.2, sellside["preis"] - puffer,
            "Sell-Side-Zone: " + _zeile(
                sellside["preis"], waehrung, sellside["abstand_prozent"], "-",
                sellside["touches"], sellside["letzte_beruehrung_datum"], gefegt,
                seither_erreicht=_zone_seither_erreicht(sellside, "sellside", live_preis),
            ),
            fontsize=8.5, color=farbe, va="top", ha="left",
        )

    if hat_kursverlauf:
        ax.plot(
            range(len(kurs_preise)), kurs_preise, color=_FARBE_KURSVERLAUF,
            linewidth=1.4, solid_capstyle="round", solid_joinstyle="round", zorder=5,
        )

    fig.text(0.015, 0.015, _ERKLAERUNG, fontsize=6.5, color=_FARBE_GEFEGT,
              ha="left", va="bottom", wrap=True)

    fig.tight_layout(rect=(0, 0.07, 1, 1))
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    return buf.getvalue()
