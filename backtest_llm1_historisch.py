"""Historischer Backtest fuer LLM1: welche Prompt-Variante entscheidet besser?

DIE FRAGE, die alle bisherigen LLM-Messungen NICHT beantworten konnten. Das
Drei-Arm-Verfahren (messe_prompt_nebeneffekte.py) zeigt, ob sich eine
Entscheidung AENDERT - nicht, ob sie BESSER wird. Dafuer braucht es
Ergebnisse, und die schienen erst in Wochen zu entstehen.

NUTZER-EINWAND (04.08.), und er trifft: die Ergebnisse liegen laengst vor -
in der Kurshistorie. 748 Tage, alle drei Marktphasen. Man kann LLM1 an einen
historischen Zeitpunkt stellen, beide Varianten fragen und danach nachsehen,
was tatsaechlich passiert ist.

    "historische bekannte Daten - beide Varianten an die LLM1 - haetten sie
     in unserem Fenster korrekt ein bestimmtes Level nach oben oder unten
     erreicht"

DER AUFBAU

    1. Ankerpunkt (Symbol, Datum) aus der Historie waehlen
    2. Faktensatz NUR aus Daten bis einschliesslich diesem Tag bauen
    3. LLM1 mit Variante A und B fragen - es setzt Richtung UND Zonen selbst
    4. Die SELBST GESETZTEN Zonen gegen den tatsaechlichen weiteren Verlauf
       simulieren -> R-Multiple
    5. Varianten vergleichen

DER ENTSCHEIDENDE UNTERSCHIED ZU ALLEM BISHERIGEN: bewertet wird die
Entscheidung des Modells an ihrem eigenen Massstab. Nicht ein fester
mechanischer Trade, sondern die Zonen, die das Modell selbst fuer richtig
hielt. Ein Modell, das gute Zonen setzt, gewinnt hier - eines, das nur
zuversichtlich klingt, nicht.

KEIN VORAUSSCHAUEN. `_reihe_bis()` schneidet die Kursreihe hart am Ankertag
ab, BEVOR irgendein Indikator gerechnet wird. Ohne das waere der ganze
Backtest wertlos, und der Fehler waere in den Ergebnissen nicht zu sehen -
sie saehen nur verdaechtig gut aus.

ANREICHERUNG NACH DEM ERSTEN LAUF (04.08.). Der erste Faktensatz war so
duenn, dass das Modell in 36 von 36 Faellen eroeffnete - im Betrieb sagt es
zu 65 % HALTEN. Ohne Gegenindikatoren fehlt ihm der Grund zurueckzuhalten,
und der Backtest mass dadurch ZONENQUALITAET statt SELEKTIVITAET. Ergaenzt
wurden deshalb, alles rein kursbasiert und damit fuer die vollen 748 Tage
verfuegbar: Konfluenz (im Betrieb Pflicht-Pruefpunkt und Ausloeser des
Positionsgroessen-Deckels bei "gemischt"), Fibonacci, Liquiditaetszonen und
der BTC-Relativwert ueber 30 Tage.

WAS WEITERHIN FEHLT: Funding-Rate, Open Interest, Fear&Greed und
Long-Konten-Anteil. Sie liegen in der DB (macro_snapshot,
open_interest_snapshot, beide taeglich), sind aber noch nicht im Export -
und sie reichen nur bis Juli 2026 zurueck, waehrend die Kurshistorie 748 Tage
umfasst. Daraus folgt ein Zielkonflikt, der bewusst zugunsten der Reichweite
entschieden ist: lange Fenster mit kursbasierten Fakten schlagen kurze
Fenster mit vollstaendigen. Fuer den VERGLEICH zweier Varianten ist das
unkritisch (beide bekommen denselben Satz), fuer eine Aussage ueber die
absolute Guete waere es das nicht.

Lauf: python -u backtest_llm1_historisch.py [--n 12] [--w 3]
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import statistics
import sys
from dataclasses import dataclass

import numpy as np

from agent.krypto.backward_tracking import (
    gap_bewusster_fill, kosten_kontext_fuer_prompt,
)
from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from indicators.calculations import (
    build_technical_snapshot, latest_value, summarize_confluence,
)

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
logger = logging.getLogger(__name__)

HORIZONT = 14          # Bewertungsfenster in Tagen, wie im Backward-Tracking
VORLAUF_MIN = 210      # genug fuer EMA200
WARTE_SEKUNDEN = 1.5
VERSUCHE = 4

# Die zweite Variante: Chain-of-Thought ausweiten. Einziges Verfahren mit
# universell positivem Befund in der systematischen Auswertung (arXiv
# 2604.23178). Bewusst kurz und ohne Zahlenbeispiel (Anker-Kollaps, siehe
# project_konfidenz_prompt_fixes).
COT_ZUSATZ = """

ARBEITSWEISE (vor der Antwort, in dieser Reihenfolge):
a) Nenne die zwei Fakten, die am staerksten FUER deine These sprechen.
b) Nenne die zwei Fakten, die am staerksten DAGEGEN sprechen.
c) Erst danach entscheide `action` und lege `confidence_pct` fest.
Diese Abwaegung fliesst in `gegenargument` und `short_reasoning` ein; gib sie
nicht als eigenes Feld aus."""

VARIANTEN = {
    "A unveraendert": SYSTEM_PROMPT,
    "B erweiterte CoT": SYSTEM_PROMPT + COT_ZUSATZ,
}


@dataclass
class Kerze:
    date: str
    open: float
    high: float
    low: float
    close: float
    # UMSATZ (10.08.2026). Er stand die ganze Zeit in der Exportdatei - 7.690 von
    # 7.690 Punkten fuehren ihn - und wurde hier weggeworfen. Die Praxisliteratur
    # nennt ihn als einen der zentralen Bestaetigungsfaktoren: institutionelle
    # Akkumulation zeigt sich als stetiger Umsatz ueber mehrere Sitzungen, nicht
    # als ein einzelner Ausbruchstag.
    #
    # Mit Vorgabewert, damit die zweite Stelle, die Kerzen baut, unveraendert
    # bleibt - und weil `None` etwas anderes heisst als `0.0`: nicht vorhanden
    # gegen tatsaechlich kein Handel.
    volume: float | None = None


def _arg(name: str, default: int) -> int:
    if name in sys.argv:
        try:
            return int(sys.argv[sys.argv.index(name) + 1])
        except (IndexError, ValueError):
            pass
    return default


def lade_reihen_aus_db(db: str = "data/tradinginfotool.db",
                       nur_taeglich: bool = True) -> dict[str, list[Kerze]]:
    """Kursreihen direkt aus der Datenbank - ohne den 125-MB-JSON-Umweg.

    ANLASS (11.08.2026): `lade_reihen()` scheiterte mit MemoryError. Ursache war
    nicht die Datei, sondern der freie Speicher - ein Browser hielt 22 von 34 GB.
    Eine 125-MB-JSON braucht beim Parsen ein Vielfaches davon als
    Python-Objekte; die Datenbank liefert dieselben Zeilen zeilenweise.

    Die Exportdatei bleibt der Weg fuer Notebook-Analysen. Fuer alles, was auf
    diesem Rechner laeuft, ist die DB die primaere Quelle und war es immer -
    der JSON-Umweg stammt daher, dass die ersten Backtests am Notebook liefen.

    WAEHRUNG: eine je Symbol, USD bevorzugt, EUR als Rueckfall (11.08.2026).

    Vorher stand hier `where currency='USD'`. Das war fuer Krypto, Aktien und
    Rohstoffe richtig - und machte die GESAMTE Assetklasse ETF unsichtbar:

        3QSS EUR 522 · CEBS EUR 793 · DBPK EUR 4160 (ab 2010) · EXH3 EUR 4722
        (ab 2008) · ISOC EUR 3647 · VVMX EUR 1236 · X136 EUR 157

    Die Daten waren da, tief und reichlich; der Filter hat sie weggeschnitten.
    `beschreibe_lage()` bekam fuer sieben Assets nichts und die Kette
    uebersprang sie stumm - ununterscheidbar von "kein Signal".

    WARUM NICHT EINFACH DEN FILTER ENTFERNEN: Krypto liegt in BEIDEN Waehrungen
    (44 USD, 35 EUR). Ohne Auswahl kaemen dort zwei Reihen ineinander verwoben
    heraus - jeder Tag doppelt, mit verschiedenen Kursen. Deshalb genau eine
    Waehrung je Symbol.

    WER DIE WAEHRUNG BRAUCHT, muss sie erfragen koennen: `waehrung_je_symbol()`.
    Eine EUR-Reihe darf nicht noch einmal nach EUR umgerechnet werden."""
    import sqlite3
    c = sqlite3.connect(db)
    q = ("select symbol, currency, date, open, high, low, close, volume "
         "from price_history_ohlc where currency in ('USD','EUR') "
         "and close is not null and high is not null and low is not null "
         "order by symbol, currency, date")
    je_waehrung: dict[tuple[str, str], list[Kerze]] = {}
    for sym, cur, datum, o, h, l, cl, v in c.execute(q):
        je_waehrung.setdefault((sym, cur), []).append(
            Kerze(str(datum)[:10], float(o if o is not None else cl),
                  float(h), float(l), float(cl),
                  None if v is None else float(v)))
    reihen: dict[str, list[Kerze]] = {}
    for sym in {s for s, _ in je_waehrung}:
        for cur in ("USD", "EUR"):          # Reihenfolge = Vorrang
            if (sym, cur) in je_waehrung:
                reihen[sym] = je_waehrung[(sym, cur)]
                break
    return nur_tageskerzen(reihen, "DB") if nur_taeglich else reihen


def nur_tageskerzen(reihen: dict, quelle: str = "") -> dict:
    """Entfernt Reihen, die keine Tageskerzen sind - und sagt WELCHE.

    Der Wächter gehoert an JEDEN Ladepfad, nicht nur an einen. Am 11.08. hat
    eine Laengenschranke (`len(c) < 250`) die Vier-Tage-Kerzen zufaellig
    abgefangen, weil sie nur 24 Stueck waren. Das ist Glueck, kein Schutz:
    lieferte eine Quelle je 300 Vier-Tage-Kerzen, gingen sie ungehindert ein.

    STILL VERWERFEN WAERE DER GLEICHE FEHLER wie das stumme Ueberspringen
    fehlender Assets - deshalb wird jede entfernte Reihe genannt."""
    grob = {s: m for s, m in granularitaet_je_symbol(reihen).items() if m > 1}
    if grob:
        namen = ", ".join(f"{s} ({m}d)" for s, m in sorted(grob.items()))
        logger.warning("%s%d Reihe(n) sind KEINE Tageskerzen und werden nicht "
                       "geladen: %s", f"{quelle}: " if quelle else "",
                       len(grob), namen)
    return {s: r for s, r in reihen.items() if s not in grob}


def granularitaet_je_symbol(reihen: dict) -> dict[str, int]:
    """Median-Abstand zwischen zwei Kerzen, in Tagen. 1 = Tageskerzen.

    WOZU (Befund 11.08.2026). `price_history_ohlc` mischt Quellen mit
    verschiedener Granularitaet, ohne es zu vermerken. Der CoinGecko-Rueckfall
    liefert fuer sieben Symbole VIER-TAGE-Kerzen - 24 Stueck ueber 92 Tage,
    Abstand ausnahmslos 4 -, und sie liegen neben Krakens Tageskerzen in
    derselben Tabelle. Jeder "20-Tage"-Indikator rechnet dort ueber 80
    Kalendertage: ATR, gleitende Durchschnitte, Swing-Erkennung, die
    60-Tage-Bewegung. Nichts stuerzt ab, alles ist verschoben.

    WARUM MESSEN STATT EINE SPALTE. Eine Granularitaetsspalte muesste jeder
    Leser beachten - und wer sie vergisst, rechnet weiter falsch. Ein Feld, das
    man beachten MUSS, ist selbst eine Falle. Der Abstand steht dagegen in den
    Daten selbst: er ist immer da, gilt fuer jede kuenftige Quelle und kann
    nicht vergessen werden.

    WARUM DER MEDIAN. Tageskerzen von Aktien haben ueber das Wochenende Luecken
    von drei Tagen; der Median bleibt trotzdem 1. Ein Mittelwert waere dadurch
    verschoben, ein Minimum blind fuer eine ueberwiegend grobe Reihe."""
    from datetime import date
    aus: dict[str, int] = {}
    for sym, reihe in reihen.items():
        if len(reihe) < 3:
            aus[sym] = 0          # nicht bestimmbar
            continue
        tage = [date.fromisoformat(k.date[:10]) for k in reihe]
        abstaende = sorted((tage[i + 1] - tage[i]).days
                           for i in range(len(tage) - 1))
        aus[sym] = abstaende[len(abstaende) // 2]
    return aus


def waehrung_je_symbol(db: str = "data/tradinginfotool.db") -> dict[str, str]:
    """In welcher Waehrung liefert `lade_reihen_aus_db()` dieses Symbol?

    Dieselbe Vorrangregel, an EINER Stelle. Wer das anderswo nachbaut, baut
    frueher oder spaeter eine andere Regel - und dann rechnet eine Stelle um,
    wo die andere es schon getan hat."""
    import sqlite3
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    vorhanden: dict[str, set] = {}
    for sym, cur in c.execute(
            "select distinct symbol, currency from price_history_ohlc "
            "where currency in ('USD','EUR') and close is not null"):
        vorhanden.setdefault(sym, set()).add(cur)
    return {s: ("USD" if "USD" in w else "EUR") for s, w in vorhanden.items()}


def lade_reihen(nur_taeglich: bool = True) -> dict[str, list[Kerze]]:
    """Kursreihen aus der Notebook-Exportdatei.

    `nur_taeglich` (11.08.2026) verwirft Reihen, die keine Tageskerzen sind -
    derselbe Waechter wie in `lade_reihen_aus_db()`. Er gehoert an BEIDE
    Ladepfade: die Messskripte lesen ueber diesen hier, und dort hat bisher nur
    die Laengenschranke `len(c) < 250` zufaellig geschuetzt.

    NICHT geaendert wurde der Waehrungsfilter (nur USD). In der Datenbank war er
    ein Defekt - er machte die ETF-Klasse unsichtbar. Hier waere seine Aenderung
    etwas anderes: sie veraenderte die GRUNDGESAMTHEIT der 8.441-Faelle-Messung
    und machte deren Ergebnis unvergleichbar. Wer ihn anfasst, misst danach
    etwas anderes - und muss das wissen und begruenden."""
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    reihen: dict[str, list[Kerze]] = {}
    for q in ("preishistorie_signal_symbole", "preishistorie_ueberholte_symbole"):
        for s, rr in ((d.get(q) or {}).get("preishistorie_je_symbol") or {}).items():
            g = [p for p in (rr or []) if p.get("currency") == "USD"
                 and p.get("close") and p.get("high") and p.get("low")]
            if len(g) > len(reihen.get(s, [])):
                reihen[s] = [Kerze(str(p["date"])[:10], float(p.get("open") or p["close"]),
                                   float(p["high"]), float(p["low"]), float(p["close"]),
                                   None if p.get("volume") is None else float(p["volume"]))
                             for p in sorted(g, key=lambda x: str(x["date"])[:10])]
    return nur_tageskerzen(reihen, "Export") if nur_taeglich else reihen


def _reihe_bis(reihe: list[Kerze], index: int) -> list[Kerze]:
    """Alles BIS EINSCHLIESSLICH `index`. Der harte Schnitt gegen Vorausschau."""
    return reihe[:index + 1]


def baue_historische_fakten(sym: str, reihe: list[Kerze], i: int,
                            btc: list[Kerze] | None) -> dict | None:
    """Faktensatz aus Daten bis Tag i - kein einziger Wert von danach."""
    hist = _reihe_bis(reihe, i)
    if len(hist) < VORLAUF_MIN:
        return None
    closes = np.array([k.close for k in hist], dtype=float)
    dates = np.array([k.date for k in hist])
    snap = build_technical_snapshot(closes, dates, hist)

    def w(res):
        """Letzter Wert eines Indikators - auch wenn er mehrere Reihen fuehrt.

        MACD und Bollinger liefern ein dict von Reihen (macd/signal/histogram
        bzw. upper/middle/lower), kein einzelnes Array. latest_value() erwartet
        ein Array und wirft dort einen TypeError - das hat den ersten Lauf
        abgebrochen. Hier wird das dict aufgeloest, damit die Fakten dieselbe
        Aussage tragen wie im Betrieb."""
        if res is None or not getattr(res, "available", False):
            return None
        wert = res.value
        if isinstance(wert, dict):
            raus = {}
            for name, reihe in wert.items():
                try:
                    v = latest_value(type(res)(reihe, True))
                except Exception:
                    v = None
                if v is not None and math.isfinite(float(v)):
                    raus[name] = round(float(v), 6)
            return raus or None
        try:
            v = latest_value(res)
        except Exception:
            return None
        return None if v is None else round(float(v), 6)

    # BTC-Trend historisch: EMA-Staffel am selben Tag, nicht der heutige Wert
    btc_trend = "nicht verfügbar"
    if btc:
        bhist = [k for k in btc if k.date <= hist[-1].date]
        if len(bhist) >= 210:
            bc = np.array([k.close for k in bhist], dtype=float)
            from indicators.calculations import ema as _ema
            e20, e50, e200 = (latest_value(_ema(bc, p)) for p in (20, 50, 200))
            if None not in (e20, e50, e200):
                if e20 > e50 > e200:
                    btc_trend = "aufwärts (EMA20 > EMA50 > EMA200)"
                elif e20 < e50 < e200:
                    btc_trend = "abwärts (EMA20 < EMA50 < EMA200)"
                else:
                    btc_trend = "gemischt"

    # ANREICHERUNG (2026-08-04, zweiter Lauf). Der erste Faktensatz war so
    # duenn, dass das Modell in 36 von 36 Faellen eroeffnete - im Betrieb sagt
    # es zu 65 % HALTEN. Ohne Gegenindikatoren fehlt ihm der Grund
    # zurueckzuhalten, und der Backtest mass dadurch Zonenqualitaet statt
    # Selektivitaet. Alles Folgende ist REIN KURSBASIERT und damit fuer die
    # vollen 748 Tage rekonstruierbar - kein Makro-Wert, der die
    # Vergleichbarkeit auf wenige Wochen einschraenken wuerde.
    konf = summarize_confluence(snap, hist[-1].close)

    # BTC-Relativwert: Vorsprung/Rueckstand gegenueber BTC ueber 30 Tage.
    # Im Betrieb ein eigener Faktenblock, hier aus denselben Kursen abgeleitet.
    btc_rel = None
    if btc and len(hist) > 31:
        bh = [k for k in btc if k.date <= hist[-1].date]
        if len(bh) > 31:
            eig = hist[-1].close / hist[-31].close - 1.0
            ref = bh[-1].close / bh[-31].close - 1.0
            btc_rel = {"vorsprung_30t_prozentpunkte": round((eig - ref) * 100, 2)}

    return {
        "asset": {"symbol": sym, "name": sym, "rolle": "historischer Backtest"},
        "preis": {"usd": round(hist[-1].close, 8), "aktualisiert_vor_min": 0},
        "technische_analyse": {
            "ema": {str(p): w(r) for p, r in snap.ema.items()},
            "macd": w(snap.macd), "rsi_14": w(snap.rsi),
            "bollinger": w(snap.bollinger), "atr": w(snap.atr),
            "atr_perzentil": w(snap.atr_percentile),
            "support_resistance": w(snap.support_resistance),
            "fibonacci": snap.fibonacci,
            # Der wichtigste Zusatz: die Konfluenz ist im Betrieb ein
            # Pflicht-Pruefpunkt (Regel 13/22) und loest bei "gemischt" einen
            # Positionsgroessen-Deckel aus. Sie fehlte bisher komplett.
            "confluence": {
                "gesamttendenz": konf.overall_bias,
                "bullish": konf.bullish_count,
                "bearish": konf.bearish_count,
                "neutral": konf.neutral_count,
                "nicht_verfuegbar": konf.unavailable_count,
            },
        },
        "liquiditaetszonen": w(snap.liquidity_zones),
        "btc_relativwert": btc_rel,
        "regime": {"wert": "nicht rekonstruierbar", "quelle": "historischer Backtest",
                   "btc_trend": btc_trend},
        # AUSDRUECKLICH als fehlend markiert statt weggelassen - das Modell soll
        # wissen, dass hier nichts steht, und nicht raten. Die verbliebenen vier
        # brauchen macro_snapshot/open_interest_snapshot; beide liegen in der
        # DB, sind aber noch nicht im Export (siehe Commit vom 04.08.).
        "nicht_verfuegbar": ["funding_rate", "open_interest", "fear_greed",
                             "long_short_ratio", "historische_erfolgsquote"],
        "position_aktuell": None,
        # Kostenkontext (2026-08-05) - im Betrieb seit heute Teil des
        # Faktensatzes, deshalb auch hier. Ohne ihn wuerde der Backtest eine
        # andere Aufgabe messen als die Produktion loest.
        "kosten": kosten_kontext_fuer_prompt(5),
        "hebel_kontext": {"max_hebel_config": 5, "max_sicherer_hebel_geschaetzt": 3},
        "disclaimers": {"hinweis": "Historischer Backtest, keine Anlageberatung."},
    }


def bewerte(antwort: dict, reihe: list[Kerze], i: int) -> float | None:
    """R-Multiple der vom MODELL gesetzten Zonen gegen den echten Verlauf.

    Konventionen wie im Backward-Tracking: Stop schlaegt Ziel am selben Tag,
    gap-bewusster Fill, sonst Bewertung zum Schlusskurs am Fensterende."""
    if str(antwort.get("action", "")).upper() not in ("ERÖFFNEN", "EROEFFNEN"):
        return None                     # HALTEN wird nicht bewertet
    try:
        e = (antwort["entry"]["usd_von"] + antwort["entry"]["usd_bis"]) / 2.0
        ist_short = str(antwort.get("richtung", "LONG")).upper() == "SHORT"
        stop = antwort["stop_loss"]["usd_bis" if ist_short else "usd_von"]
        ziel = antwort["take_profit"]["usd_bis" if ist_short else "usd_von"]
    except (KeyError, TypeError):
        return None
    if not e or e <= 0:
        return None
    risiko = (stop - e) if ist_short else (e - stop)
    if risiko <= 0 or ((e - ziel) if ist_short else (ziel - e)) <= 0:
        return None
    for k in reihe[i + 1:i + 2 + HORIZONT]:
        if (k.high >= stop) if ist_short else (k.low <= stop):
            f = gap_bewusster_fill(stop, k.open, True, ist_short)
            return ((e - f) if ist_short else (f - e)) / risiko
        if (k.low <= ziel) if ist_short else (k.high >= ziel):
            f = gap_bewusster_fill(ziel, k.open, False, ist_short)
            return ((e - f) if ist_short else (f - e)) / risiko
    letzte = reihe[min(i + 1 + HORIZONT, len(reihe) - 1)]
    return ((e - letzte.close) if ist_short else (letzte.close - e)) / risiko


def frage(client, fakten: dict, system: str) -> dict | None:
    import time
    msg = [{"role": "system", "content": system},
           {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}]
    for v in range(VERSUCHE):
        try:
            time.sleep(WARTE_SEKUNDEN)
            return json.loads(client.chat(msg, temperature=0.2,
                                          response_format={"type": "json_object"}))
        except Exception as exc:
            if v == VERSUCHE - 1:
                print(f"    (aufgegeben: {type(exc).__name__})", flush=True)
                return None
            time.sleep(WARTE_SEKUNDEN * (2 ** v))
    return None


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        import re
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    n, w = _arg("--n", 12), _arg("--w", 3)
    reihen = lade_reihen()
    btc = reihen.get("BTC")

    # Ankerpunkte streuen: verschiedene Symbole UND verschiedene Zeitpunkte,
    # damit nicht eine Marktphase das Ergebnis traegt.
    anker = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + HORIZONT + 5:
            continue
        moeglich = range(VORLAUF_MIN, len(reihe) - HORIZONT - 2)
        if not moeglich:
            continue
        schritt = max(1, len(moeglich) // 3)
        for i in list(moeglich)[::schritt][:3]:
            anker.append((sym, i))
    anker.sort(key=lambda x: (x[1], x[0]))
    anker = anker[:: max(1, len(anker) // n)][:n]
    if not anker:
        print("keine Ankerpunkte mit genug Vorlauf")
        return 1

    client = MistralClient(api_key=key)
    print("=" * 76, flush=True)
    print(f"HISTORISCHER BACKTEST LLM1   {len(anker)} Ankerpunkte x "
          f"{len(VARIANTEN)} Varianten x {w} = {len(anker)*len(VARIANTEN)*w} Aufrufe",
          flush=True)
    print(f"Horizont {HORIZONT} T, Vorlauf {VORLAUF_MIN} T, Zonen vom Modell selbst",
          flush=True)
    print("=" * 76, flush=True)

    je_variante: dict[str, list[float]] = {v: [] for v in VARIANTEN}
    eroeffnet: dict[str, int] = {v: 0 for v in VARIANTEN}
    gefragt = 0

    for sym, i in anker:
        reihe = reihen[sym]
        fakten = baue_historische_fakten(sym, reihe, i, btc)
        if fakten is None:
            continue
        print(f"\n{sym} @ {reihe[i].date}:", flush=True)
        for name, system in VARIANTEN.items():
            rs = []
            for _ in range(w):
                a = frage(client, fakten, system)
                gefragt += 1
                if not a:
                    continue
                if str(a.get("action", "")).upper() in ("ERÖFFNEN", "EROEFFNEN"):
                    eroeffnet[name] += 1
                r = bewerte(a, reihe, i)
                if r is not None:
                    rs.append(r)
                    je_variante[name].append(r)
            m = f"{statistics.fmean(rs):+.3f} R" if rs else "kein Trade"
            print(f"  {name:20s} {len(rs)}/{w} Trades   {m}", flush=True)

    print("\n" + "=" * 76, flush=True)
    print(f"{'Variante':22s} {'Trades':>8s} {'EW (R)':>9s} {'Trefferq':>9s} "
          f"{'Summe R':>9s}", flush=True)
    for name in VARIANTEN:
        rs = je_variante[name]
        if not rs:
            print(f"{name:22s} {'0':>8s}   kein einziger Trade", flush=True)
            continue
        tq = sum(1 for x in rs if x > 0) / len(rs) * 100
        print(f"{name:22s} {len(rs):8d} {statistics.fmean(rs):+9.3f} "
              f"{tq:8.0f}% {sum(rs):+9.1f}", flush=True)
    print(flush=True)
    a, b = list(VARIANTEN)
    ra, rb = je_variante[a], je_variante[b]
    if ra and rb:
        d = statistics.fmean(rb) - statistics.fmean(ra)
        print(f"Unterschied B minus A: {d:+.3f} R je Trade", flush=True)
        print(f"Eroeffnungsrate: A {eroeffnet[a]}/{gefragt//2}, "
              f"B {eroeffnet[b]}/{gefragt//2}", flush=True)
        print(flush=True)
        print("VORBEHALT: keine Signifikanzaussage. Bei dieser Fallzahl und der", flush=True)
        print("bekannten Symbolklumpung braeuchte es einen symbolgeblockten", flush=True)
        print("Bootstrap - dieser Lauf zeigt eine Richtung, keinen Beweis.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
