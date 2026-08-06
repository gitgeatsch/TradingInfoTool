"""Kursreihen rekonstruieren, wo keine abrufbar ist (2026-08-06).

WOFUER. Der Abruf-Test vom 06.08. hat bestaetigt, was seit dem 20.07. in
YFINANCE_HISTORY_UNRELIABLE_TICKERS steht: fuenf gehaltene Instrumente liefern
ueber yfinance KEINE Historie, nur einen aktuellen Preis.

    OD7N GB00B15KY328.SG   WisdomTree Silver ETC
    OD7H OD7H.SG           WisdomTree Gold
    OD7C OD7C.SG           WisdomTree Copper
    OD7L JE00BN7KB334.SG   WisdomTree Natural Gas
    3QSS IE00BLRPRJ20.SG   WisdomTree Nasdaq-100 3x Daily Short

Ohne Kursreihe hat eine gehaltene Position keinen Tageswert - sie faellt aus
der Portfolio-Bewertung und damit aus Z-3 heraus. Am 06.08. fehlten dadurch
19 von 33 Symbolen.

DAS VERFAHREN. Beide Faelle folgen demselben Muster: eine REFERENZREIHE liefert
die Form, ein ANKERPREIS die Hoehe.

    ETC (ungehebelt):  wert[t] = anker x (referenz[t] / referenz[anker_tag])
    Hebelprodukt:      taegliche Rendite = faktor x Referenzrendite, verkettet

WARUM BEIM HEBELPRODUKT VERKETTET WERDEN MUSS. Ein taeglich zuruecksetzendes
(daily reset) Produkt bildet NICHT das Faktor-fache der Gesamtrendite ab,
sondern das Faktor-fache der TAGESrendite, Tag fuer Tag. Der Unterschied ist
der Volatilitaets-Drag: schwankt der Index +10 %/-10 % im Wechsel, verliert ein
3x-Short trotz seitwaerts laufendem Index. Wer ueber den Zeitraum hochrechnet
statt zu verketten, baut einen Fehler ein, der bei ruhigen Maerkten klein und
bei bewegten gross ist - also genau dann falsch, wenn es darauf ankommt.

WAS DIESE REIHEN NICHT KOENNEN, und das gehoert zu jeder Verwendung dazu:

  - ROLLKOSTEN. Futures-basierte ETCs rollen ihre Kontrakte; in Contango kostet
    das laufend. Bei Gold und Silber ist der Effekt klein, bei ERDGAS (OD7L)
    ist er notorisch gross - dort kann die Reihe ueber Wochen deutlich zu
    optimistisch sein.
  - GEBUEHREN. Verwaltungsgebuehr und Swap-Kosten fehlen, beides wirkt in
    dieselbe Richtung (Reihe zu optimistisch).
  - WECHSELKURS beim Hebelprodukt. 3QSS notiert in EUR, der Nasdaq-100 in USD -
    die FX-Bewegung fehlt in der rekonstruierten Reihe.

FOLGE: die Reihen taugen fuer KURZE Horizonte (Tage bis zwei Wochen), auf denen
Drift klein bleibt - also fuer die Outcome-Bewertung von Signalen. Sie taugen
NICHT fuer Aussagen ueber Monate. Deshalb traegt jede Zeile `quelle` und die
Bewertung kann sie ausschliessen.

NICHT VERWENDEN FUER TECHNISCHE ANALYSE. Bei den Rohstoffen liefert der
Futures-Ticker die saubere, liquide Reihe - die bleibt die richtige Grundlage
fuer Indikatoren. Bei den Hedge-Instrumenten ist Einzeltitel-Technik ohnehin
bewusst ausgeschlossen (siehe agent/hedge/pipeline.py Modul-Docstring).
"""
from __future__ import annotations

from datetime import datetime, timezone

from database.models import OhlcPoint

QUELLE_GEMESSEN = "gemessen"
QUELLE_REKONSTRUIERT = "rekonstruiert"

# Ab welcher relativen Tagesbewegung der Referenz gilt ein Punkt als
# unplausibel? Schuetzt gegen kaputte Referenzpunkte, die sich sonst
# ungebremst in die rekonstruierte Reihe fortpflanzen.
_MAX_TAGESBEWEGUNG = 0.35

# Standard-Fenster: gut zwei Handelsjahre. Deckt jede Outcome-Bewertung mit
# Reserve ab und haelt die Drift-Akkumulation in Grenzen (siehe rekonstruiere()).
MAX_PUNKTE_STANDARD = 520


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def rekonstruiere(
    symbol: str,
    currency: str,
    referenz: list[dict],
    anker_preis: float,
    anker_datum: str | None = None,
    faktor: float = 1.0,
    invers: bool = False,
    max_punkte: int | None = MAX_PUNKTE_STANDARD,
) -> list[OhlcPoint]:
    """Reihe fuer `symbol` aus einer Referenzreihe und einem Ankerpreis.

    `referenz` ist eine nach Datum sortierte Liste mit mindestens `date` und
    `close`. `anker_datum` ist der Tag, an dem `anker_preis` gilt - ohne Angabe
    der letzte Referenztag.

    `faktor`/`invers` beschreiben ein taeglich zuruecksetzendes Hebelprodukt:
    faktor=3.0, invers=True ergibt einen 3x-Short. Bei faktor=1.0 und
    invers=False (Standard, der ungehebelte ETC-Fall) ist das Ergebnis
    mathematisch identisch zur einfachen Verhaeltnisrechnung - die Verkettung
    laeuft trotzdem, damit es nur EINEN Codepfad gibt.

    Der Ankertag traegt exakt `anker_preis` - das ist die Pruefgroesse, an der
    sich die Rekonstruktion messen laesst.

    `max_punkte` begrenzt das Fenster auf die juengsten N Referenztage. Das ist
    kein Sparzwang, sondern folgt aus dem Verfahren: die Referenzreihen reichen
    Jahrzehnte zurueck (^NDX bis 1985), die Instrumente existieren erst seit
    wenigen Jahren, und die nicht modellierte Drift (Roll, Gebuehren, FX)
    akkumuliert mit jedem Tag rueckwaerts. Eine Reihe bis 1985 waere lang,
    billig und falsch. None hebt die Grenze auf - nur fuer Tests gedacht.
    """
    reihe = [p for p in referenz if p.get("close")]
    reihe.sort(key=lambda p: p["date"])
    if max_punkte and len(reihe) > max_punkte:
        reihe = reihe[-max_punkte:]
    if len(reihe) < 2 or not anker_preis or anker_preis <= 0:
        return []
    tage = [p["date"] for p in reihe]
    ziel = anker_datum if anker_datum in tage else tage[-1]
    anker_index = tage.index(ziel)

    # Tagesrenditen der Referenz, unplausible Spruenge uebersprungen
    werte: dict[str, float] = {ziel: float(anker_preis)}

    def schritt(von_close: float, nach_close: float) -> float | None:
        if not von_close:
            return None
        r = nach_close / von_close - 1.0
        if abs(r) > _MAX_TAGESBEWEGUNG:
            return None
        eigen = r * faktor * (-1.0 if invers else 1.0)
        return max(-0.95, eigen)          # ein Produkt kann nicht negativ werden

    # vorwaerts ab dem Anker
    for i in range(anker_index + 1, len(reihe)):
        s = schritt(reihe[i - 1]["close"], reihe[i]["close"])
        vorher = werte.get(reihe[i - 1]["date"])
        if s is None or vorher is None:
            continue
        werte[reihe[i]["date"]] = vorher * (1.0 + s)
    # rueckwaerts vor den Anker
    for i in range(anker_index, 0, -1):
        s = schritt(reihe[i - 1]["close"], reihe[i]["close"])
        nachher = werte.get(reihe[i]["date"])
        if s is None or nachher is None or (1.0 + s) <= 0:
            continue
        werte[reihe[i - 1]["date"]] = nachher / (1.0 + s)

    jetzt = _jetzt()
    punkte = []
    for p in reihe:
        w = werte.get(p["date"])
        if w is None or w <= 0:
            continue
        # Hoch/Tief der Referenz anteilig uebertragen - die Tagesspanne des
        # Basiswerts ist die beste verfuegbare Naeherung. Bei einem inversen
        # Produkt kehren sich Hoch und Tief um.
        c = p["close"]
        hoch_rel = (p.get("high") or c) / c if c else 1.0
        tief_rel = (p.get("low") or c) / c if c else 1.0
        if invers:
            hoch_rel, tief_rel = (2.0 - tief_rel), (2.0 - hoch_rel)
        punkte.append(OhlcPoint(
            symbol=symbol, currency=currency, date=p["date"],
            open=w, high=max(w, w * hoch_rel), low=min(w, w * tief_rel),
            close=w, volume=0.0, fetched_at=jetzt,
        ))
    return punkte


def ankertag_abweichung(punkte: list[OhlcPoint], anker_preis: float,
                        anker_datum: str) -> float | None:
    """Pflicht-Pruefgroesse: am Ankertag muss die Reihe den Ankerpreis EXAKT
    treffen. Weicht sie ab, stimmt die Verkettung nicht."""
    for p in punkte:
        if p.date == anker_datum:
            return abs(p.close - anker_preis) / anker_preis
    return None
