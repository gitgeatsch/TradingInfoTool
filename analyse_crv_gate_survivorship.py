"""Filtert das CRV-Gate die richtigen Signale? Survivorship-bereinigt (Task #602).

Aufruf:  python analyse_crv_gate_survivorship.py [export.json]

WARUM. Der Befund vom 02.08. ("das Gate sortiert aus, was funktioniert") hielt
der Gegenpruefung nicht stand: er verglich Gruppen mit sehr unterschiedlicher
Aufloesungsquote. Weite Stops werden kaum aufgeloest, enge oft - wer nur die
aufgeloesten Faelle anschaut, vergleicht Selektionsgrade statt Signalqualitaet.

ANSATZ. Der DB-Status wird nicht gelesen. Stattdessen wird JEDES Signal mit
Zonen selbst gegen die Preishistorie simuliert - auch die nie ausgewerteten.
Jedes bekommt einen R-Wert: Ziel getroffen -> +CRV, Stop -> -1,0, sonst
Mark-to-Market am Ende des Fensters. Die Selektion entfaellt damit strukturell.

DREI KONTROLLEN, die dieses Skript mitfuehrt, weil ohne sie am 02.08. zwei
Befunde nacheinander gekippt sind:
 1. GLEICHE BEOBACHTUNGSDAUER. Nur Signale, deren Preisreihe den vollen
    Horizont abdeckt. Laenger beobachtete Signale haben mehr Gelegenheit, ihren
    Stop zu treffen - ohne diese Bedingung misst man Beobachtungszeit.
 2. MECHANISCHE BASISLINIE (Test_und_Verifikationsmethodik 2.5.7). Dieselben
    Stop-/Ziel-Abstaende an zufaelligen Einstiegspunkten derselben Symbole.
    Ohne sie misst man die Marktphase, nicht die Signalqualitaet.
 3. SYMBOL-KONZENTRATION. Wenn ein Symbol eine Gruppe dominiert, ist der
    Gruppenwert dessen Kursverlauf, kein Gate-Effekt.

Rechnung in USD wie der Produktivcode (die USD-Zonen sind seit Commit 789cc74
im Export). Ausfuehrungspreise nach der Konvention vom 02.08.: Zonen-Grenze,
bei einem Gap der Eroeffnungskurs (Regelwerksmanual Kapitel 21).
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, r'D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool')
from agent.krypto.statistik import wilson_intervall
from agent.krypto.backward_tracking import _zonen_absolut, simuliere_signal

STANDARD_PFAD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
                 r'\notebook_diagnose.json')
MIN_N = 15            # Test_und_Verifikationsmethodik: darunter keine Aussage
HORIZONTE = (7, 14)   # 14 wie im Backward-Tracking, 7 als groessere Stichprobe


def zonen(r: dict) -> dict | None:
    """Entry-Mitte, Stop, Ziel und CRV nach der Z-2-Formel des Risk-Gates.

    Seit 03.08. nur noch ein Wrapper auf backward_tracking._zonen_absolut() -
    die Formel stand vorher zweimal im Projekt (hier und dort) und waere beim
    naechsten Eingriff auseinandergelaufen. Der Export liefert dicts, der
    Produktivcode sqlite3.Row; _zonen_absolut() kommt mit beidem zurecht, weil
    es Feldzugriffe ueber try/except kapselt.
    """
    return _zonen_absolut(r)


def _lauf(e: float, stop: float, ziel: float, short: bool, risiko: float,
          tage: list[dict]) -> dict:
    """Kern der Simulation - auch von der Basislinie genutzt, damit beide
    exakt dieselbe Abbruch- und Fill-Logik verwenden."""
    for p in tage:
        hoch, tief, auf = p['high'], p['low'], p.get('open')
        hit_stop = (hoch >= stop) if short else (tief <= stop)
        hit_ziel = (tief <= ziel) if short else (hoch >= ziel)
        # Konservativ wie im Backward-Tracking: Stop schlaegt Ziel am selben Tag.
        if hit_stop:
            fill = stop if auf is None else (max(stop, auf) if short else min(stop, auf))
            return {'r': ((e - fill) if short else (fill - e)) / risiko, 'ausgang': 'stop'}
        if hit_ziel:
            fill = ziel if auf is None else (min(ziel, auf) if short else max(ziel, auf))
            return {'r': ((e - fill) if short else (fill - e)) / risiko, 'ausgang': 'ziel'}
    schluss = tage[-1]['close']
    return {'r': ((e - schluss) if short else (schluss - e)) / risiko, 'ausgang': 'offen'}


def simuliere(z: dict, reihe: list[dict], ab_datum: str, horizont: int) -> dict | None:
    """Nur auswerten, wenn die Reihe den vollen Horizont abdeckt (Kontrolle 1).

    Seit 03.08. Wrapper auf backward_tracking.simuliere_signal() - dieselbe
    Begruendung wie bei zonen(): eine Implementierung, nicht zwei.
    """
    return simuliere_signal(z, reihe, ab_datum, horizont)


def basislinie(reihen: dict, stop_rel: float, crv: float, short: bool,
               horizont: int) -> list[float]:
    """Zufallseinstieg an jedem Tagesbalken mit exakt diesen Parametern
    (Kontrolle 2). Gibt die R-Multiples zurueck."""
    werte = []
    for rows in reihen.values():
        for i in range(len(rows) - horizont - 1):
            e = rows[i]['close']
            if not e or e <= 0:
                continue
            risiko = e * stop_rel
            stop = e + risiko if short else e - risiko
            ziel = e - risiko * crv if short else e + risiko * crv
            werte.append(_lauf(e, stop, ziel, short, risiko,
                               rows[i + 1:i + 2 + horizont])['r'])
    return werte


def kennzahlen(werte: list[float]) -> tuple[float, str]:
    n = len(werte)
    mittel = statistics.fmean(werte)
    streuung = statistics.stdev(werte) if n >= 2 else None
    sqn = (mittel / streuung * (n ** 0.5)) if streuung else None
    gewinner = sum(1 for r in werte if r > 0)
    lo, hi = wilson_intervall(gewinner, n)
    txt = (f"n={n:4d}  EW {mittel:+.3f} R  positiv {gewinner / n * 100:4.1f}% "
           f"[{lo * 100:.0f}-{hi * 100:.0f}%]")
    if sqn is not None:
        txt += f"  SQN {sqn:+.2f}"
    return mittel, txt


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding='utf-8'))
    je = d.get('preishistorie_signal_symbole', {}).get('preishistorie_je_symbol', {})
    reihen = {}
    for sym, rows in je.items():
        r = sorted([x for x in rows if x.get('currency') == 'USD'
                    and None not in (x.get('high'), x.get('low'), x.get('close'))],
                   key=lambda x: x['date'])
        if r:
            reihen[sym] = r
    print(f"Export: {pfad}")
    print(f"{len(reihen)} Symbole mit USD-Preisreihe, Rechnung in USD wie im Produktivcode\n")

    for horizont in HORIZONTE:
        gruppen: dict[tuple[str, str], list[dict]] = defaultdict(list)
        verworfen = 0
        for quelle, tier in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
            for r in d.get(quelle, []):
                z = zonen(r)
                if not z or r['symbol'] not in reihen:
                    continue
                sim = simuliere(z, reihen[r['symbol']], r['created_at'][:10], horizont)
                if sim is None:
                    verworfen += 1
                    continue
                grund = (r.get('risk_veto_reason') or '').lower()
                vetot = bool(r.get('risk_veto'))
                art = ('crv-vetot' if vetot and 'crv' in grund
                       else 'anders vetot' if vetot else 'ausgefuehrt')
                gruppen[(tier, art)].append({**sim, **z, 'symbol': r['symbol']})

        print("=" * 78)
        print(f"HORIZONT {horizont} TAGE - nur Signale mit vollstaendiger Preisreihe")
        print(f"({verworfen} Signale verworfen, weil die Reihe nicht so weit reicht)")
        print("=" * 78)

        for tier in ('hebel', 'spot'):
            arten = sorted((a, g) for (t, a), g in gruppen.items() if t == tier)
            if not arten:
                continue
            print(f"\n  --- {tier} ---")
            for art, g in arten:
                werte = [x['r'] for x in g]
                if not werte:
                    continue
                ew, txt = kennzahlen(werte)
                warn = "" if len(g) >= MIN_N else f"   <-- n<{MIN_N}, KEINE Aussage"
                print(f"\n    {art:14s} {txt}{warn}")

                med_crv = statistics.median(x['crv'] for x in g)
                med_stop = statistics.median(x['stop_rel'] for x in g)
                ausg = defaultdict(int)
                for x in g:
                    ausg[x['ausgang']] += 1
                print(f"    {'':14s} Median-CRV {med_crv:4.2f}, Stop {med_stop*100:5.2f}%"
                      f" | Ziel {ausg['ziel']}, Stop {ausg['stop']}, offen {ausg['offen']}")

                sym = defaultdict(int)
                for x in g:
                    sym[x['symbol']] += 1
                top, anz = max(sym.items(), key=lambda kv: kv[1])
                print(f"    {'':14s} groesstes Symbol: {top} {anz}/{len(g)} "
                      f"({anz/len(g)*100:.0f}%), {len(sym)} Symbole gesamt")

                anteil_short = sum(1 for x in g if x['ist_short']) / len(g)
                bl = basislinie(reihen, med_stop, med_crv, anteil_short > 0.5, horizont)
                if bl:
                    b_ew, b_txt = kennzahlen(bl)
                    print(f"    {'':14s} Basislinie (Zufallseinstieg, gleiche Parameter): {b_txt}")
                    print(f"    {'':14s} -> SIGNALBEITRAG {ew - b_ew:+.3f} R")
        print()


if __name__ == '__main__':
    main()
