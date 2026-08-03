"""Welche Komponente der Positionsgroesse traegt was? (Task #605)

Aufruf:  python analyse_positionsgroessen_modell.py [export.json]

WARUM. Die Messung vom 03.08. benutzte fractional Kelly auf dem CRV - also nur
EINE der drei Komponenten, die der Literaturstand fuer die Positionsgroesse
nennt. Daraus wurden Schluesse gezogen (u.a. "Groessenabstufung schadet bei
Hebel"), die das unvollstaendige Modell gar nicht hergibt. Dieses Skript legt
die Komponenten einzeln frei.

DIE DREI KOMPONENTEN
  K  fractional Kelly auf CRV und Trefferquote. Der Mechanismus, der
     asymmetrische Auszahlungen ueberhaupt verarbeitet - reine
     Wahrscheinlichkeitsverfahren koennen das nicht. Viertel-Kelly, weil
     Voll-Kelly durchgehend als zu aggressiv gilt.
  V  Volatilitaets-Normierung (Volatility Targeting). Position ~ 1/Volatilitaet,
     damit jede Position denselben Risikobeitrag liefert. Institutioneller
     Standard, und ausdruecklich NICHT kanten-getrieben.
  C  Concurrency-Korrektur. Laufen zehn Signale gleichzeitig und bekommt jedes
     dieselbe Groesse, summiert sich das Exposure auf, ohne dass das je
     entschieden wurde. Betrifft dieses System unmittelbar - es feuert viele
     Signale parallel.

DER ENTSCHEIDENDE KONTROLLFALL ist "V allein": reines Volatility Targeting ohne
jede Kanteninformation. Liefert das denselben Gewinn wie K+V, dann steckt der
gemessene Nutzen in der Volatilitaet und nicht im CRV - und die ganze
CRV-Argumentation der letzten zwei Tage waere ein Umweg. Ohne diesen Vergleich
laesst sich das nicht auseinanderhalten.

KEIN BLICK IN DIE ZUKUNFT. Die Volatilitaet wird ausschliesslich aus Balken VOR
dem Signaldatum berechnet, die Trefferquote fuer Kelly laeuft walk-forward
(nur bereits aufgeloeste Faelle), und die Gleichzeitigkeit zaehlt nur frueher
entstandene Signale. Jede dieser Groessen waere sonst im Nachhinein bekannt und
wuerde das Ergebnis schoenrechnen.
"""
from __future__ import annotations

import io
import json
import math
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, r'D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool')
import config
import analyse_crv_gate_vs_positionsgroesse as basis
from analyse_crv_gate_survivorship import STANDARD_PFAD

VOL_FENSTER = 20        # Handelstage fuer die realisierte Volatilitaet
VOL_MIN_BALKEN = 10     # darunter keine belastbare Schaetzung -> Signal faellt raus
SPREIZUNG = 5.0         # praktisch umsetzbarer Deckel (entspricht 100-500 EUR)
MIN_N = 15


def realisierte_vol(reihe: list[dict], ab_datum: str) -> float | None:
    """Standardabweichung der taeglichen Log-Renditen VOR dem Signaldatum.

    Bewusst nicht ATR: der Export liefert die Kursreihe, nicht den
    Indikator-Snapshot zum Signalzeitpunkt. Log-Renditen sind aus denselben
    Daten rekonstruierbar und damit nachpruefbar - ATR waere hier eine
    Nachbildung, die von der Produktivberechnung abweichen koennte.
    """
    vorher = [p for p in reihe if p['date'] < ab_datum][-(VOL_FENSTER + 1):]
    if len(vorher) < VOL_MIN_BALKEN + 1:
        return None
    renditen = []
    for a, b in zip(vorher, vorher[1:]):
        if a['close'] and b['close'] and a['close'] > 0 and b['close'] > 0:
            renditen.append(math.log(b['close'] / a['close']))
    if len(renditen) < VOL_MIN_BALKEN:
        return None
    v = statistics.stdev(renditen)
    return v if v > 0 else None


def gleichzeitigkeit(signale: list[dict], horizont: int) -> list[int]:
    """Wie viele Signale waren beim Entstehen dieses Signals noch offen?

    Naeherung ueber das Entstehungsdatum: alles, was innerhalb des Horizonts
    davor entstand, laeuft noch. Nur FRUEHERE Signale zaehlen - spaetere waeren
    zum Entscheidungszeitpunkt unbekannt gewesen.
    """
    tage = [s['created_at'][:10] for s in signale]
    ergebnis = []
    for i, t in enumerate(tage):
        offen = 1
        for j in range(i):
            d1 = _tage_diff(tage[j], t)
            if d1 is not None and 0 <= d1 <= horizont:
                offen += 1
        ergebnis.append(offen)
    return ergebnis


def _tage_diff(frueher: str, spaeter: str) -> int | None:
    from datetime import date
    try:
        a = date.fromisoformat(frueher)
        b = date.fromisoformat(spaeter)
    except ValueError:
        return None
    return (b - a).days


def drawdown_faktoren(signale: list[dict], horizont: int,
                      dd_max_r: float) -> tuple[list[float], list[float]]:
    """Wie stark war das System beim Entstehen dieses Signals im Rueckschlag?

    Vierte Komponente, aufgetaucht durch den Regler-Audit vom 04.08.: Ziel Z-3
    (`max_drawdown_prozent: 15`) steht seit Beginn in der Config, ist dort mit
    "[OFFEN] Vorschlag" markiert und wurde nie verdrahtet. Die Literatur kennt
    das als eigenstaendigen Ansatz neben Kelly und Volatility Targeting
    (Vince, "Risk averse fractional trading using the current drawdown").

    UMRECHNUNG in R: Z-3 nennt 15% Kapital, `risiko_pro_trade_prozent` sagt,
    wieviel Kapital ein R ist - 15/2 = 7,5 R fuer Spot, 15/1 = 15 R fuer Hebel.
    Kein frei gewaehlter Parameter, sondern aus zwei bestehenden Config-Werten
    abgeleitet.

    REFERENZ-EQUITY bewusst gleichgewichtet: der Rueckschlag soll ein Zustand
    des Systems sein, nicht des gerade getesteten Groessenmodells. Wuerde jede
    Variante ihren eigenen Rueckschlag benutzen, verglichen wir Modelle auf
    unterschiedlichen Zeitachsen. Dass echtes Drawdown-Sizing auf sich selbst
    zurueckwirkt, bleibt damit unmodelliert - eine bewusste Vereinfachung fuer
    die erste Messung.

    KEIN BLICK IN DIE ZUKUNFT: ein Signal zaehlt erst zur Equity, wenn sein
    Horizont zum Zeitpunkt des betrachteten Signals abgelaufen ist.
    """
    tage = [s['created_at'][:10] for s in signale]
    faktoren, rueckschlaege = [], []
    for i, t in enumerate(tage):
        equity = spitze = 0.0
        for j in range(i):
            diff = _tage_diff(tage[j], t)
            if diff is not None and diff > horizont:      # abgeschlossen
                equity += signale[j]['r']
                spitze = max(spitze, equity)
        dd = max(0.0, spitze - equity)
        rueckschlaege.append(dd)
        faktoren.append(max(0.0, 1.0 - dd / dd_max_r) if dd_max_r > 0 else 1.0)
    return faktoren, rueckschlaege


def stauche(rohwerte: list[float], s_max: float = SPREIZUNG) -> list[float]:
    """Rohgroessen ordnungserhaltend in [1/s_max .. 1] abbilden.

    Ohne Deckel entstehen Spreizungen bis 400-fach - rechnerisch optimal,
    praktisch unbrauchbar. Nullen bleiben Null (nicht gehandelt).
    """
    positiv = [x for x in rohwerte if x > 0]
    if not positiv:
        return list(rohwerte)
    gmax = max(positiv)
    boden = 1.0 / s_max
    return [0.0 if x <= 0 else boden + (1 - boden) * (x / gmax) for x in rohwerte]


def modelle(signale: list[dict], quoten: list[float | None],
            gleich: list[int]) -> dict[str, list[tuple[float, float]]]:
    """Alle Varianten auf derselben Signalmenge, nur die Gewichtung wechselt."""
    n = len(signale)
    roh: dict[str, list[float]] = {k: [0.0] * n for k in
                                   ('K', 'V', 'KV', 'KC', 'KVC', 'C')}
    for i, (s, p) in enumerate(zip(signale, quoten)):
        if s['crv_vetot']:
            continue                       # Gate bleibt in allen Varianten aktiv
        k = 0.0 if p is None else basis.kelly_groesse(s['crv'], p)
        v = (1.0 / s['vol']) if s.get('vol') else 0.0
        c = 1.0 / math.sqrt(gleich[i]) if gleich[i] > 0 else 0.0
        roh['K'][i] = k
        roh['V'][i] = v
        roh['C'][i] = c
        roh['KV'][i] = k * v
        roh['KC'][i] = k * c
        roh['KVC'][i] = k * v * c
    r = [s['r'] for s in signale]
    aus = {}
    # Ist-Zustand als Bezugspunkt: Gate plus die heute vorhandenen Deckel.
    aus['0  heute (Gate + Deckel)'] = basis.varianten(
        signale, quoten)['A+ Gate + heutige Deckel']
    aus['K  nur Kelly (CRV)'] = list(zip(stauche(roh['K']), r))
    aus['V  nur Volatilitaet'] = list(zip(stauche(roh['V']), r))
    aus['C  nur Gleichzeitigkeit'] = list(zip(stauche(roh['C']), r))
    aus['KV Kelly x Volatilitaet'] = list(zip(stauche(roh['KV']), r))
    aus['KC Kelly x Gleichzeitigk.'] = list(zip(stauche(roh['KC']), r))
    aus['KVC alle drei'] = list(zip(stauche(roh['KVC']), r))
    return aus


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding='utf-8'))
    je = d.get('preishistorie_signal_symbole', {}).get('preishistorie_je_symbol', {})
    reihen = {}
    for sym, rows in je.items():
        rs = sorted([x for x in rows if x.get('currency') == 'USD'
                     and None not in (x.get('high'), x.get('low'), x.get('close'))],
                    key=lambda x: x['date'])
        if rs:
            reihen[sym] = rs

    alle = basis.lade_signale(d, reihen)
    quoten = basis.walk_forward_trefferquoten(alle)
    for s, p in zip(alle, quoten):
        s['quote'] = p
        s['vol'] = realisierte_vol(reihen[s['symbol']], s['created_at'][:10])
    ohne_vol = sum(1 for s in alle if s['vol'] is None)

    klassen = {a.symbol: (a.assetklasse or '?') for a in config.get_watchlist()}
    print(f"Export: {pfad}")
    print(f"{len(alle)} Signale, davon {ohne_vol} ohne belastbare Volatilitaet "
          f"(<{VOL_MIN_BALKEN} Balken vor dem Signal)")
    print(f"Volatilitaet: Streuung der Log-Renditen ueber {VOL_FENSTER} Tage VOR "
          f"dem Signal | Spreizung gedeckelt auf {SPREIZUNG:.0f}x\n")

    gruppen = (
        ('KRYPTO-SPOT', lambda s: s['tier'] == 'spot'
         and klassen.get(s['symbol']) == 'krypto'),
        ('HEBEL', lambda s: s['tier'] == 'hebel'),
    )
    for titel, filt in gruppen:
        teil = [s for s in alle if filt(s) and s['vol'] is not None]
        if len(teil) < MIN_N:
            print(f"{titel}: n={len(teil)} - unter MIN_N, keine Aussage\n")
            continue
        tq = [s['quote'] for s in teil]
        gl = gleichzeitigkeit(teil, basis.HORIZONT)
        print("=" * 76)
        print(f"{titel}  (n={len(teil)} mit Volatilitaet, "
              f"Gleichzeitigkeit im Median {statistics.median(gl):.0f} offene Signale)")
        print("=" * 76)
        print(f"  {'Modell':26s} {'Trades':>7s} {'SQN':>7s} {'Summe R':>9s} "
              f"{'Rueckschl':>10s}")
        basis_sqn = None
        for name, gew in modelle(teil, tq, gl).items():
            k = basis.kennzahlen(gew)
            if not k['trades']:
                print(f"  {name:26s} {'-':>7s}  keine Position")
                continue
            sqn = k['sqn']
            if basis_sqn is None:
                basis_sqn = sqn
            delta = "" if sqn is None or basis_sqn is None else f"  ({sqn - basis_sqn:+.2f})"
            lo, hi = basis.bootstrap_ci(k['beitraege'])
            # Ein Intervall, das die Null enthaelt, heisst: der Ertrag je Trade
            # ist von "nichts" nicht zu unterscheiden - unabhaengig davon, wie
            # gut der SQN aussieht.
            marke = "" if lo > 0 else "   <-- Intervall enthaelt 0"
            print(f"  {name:26s} {k['trades']:7d} {sqn:+7.2f} {k['summe_r']:+9.1f} "
                  f"{k['max_rueckschlag_r']:10.1f}{delta}")
            print(f"  {'':26s} {'':7s} je Trade [{lo:+.3f} .. {hi:+.3f}] R{marke}")
        print()


if __name__ == '__main__':
    main()
