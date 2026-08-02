"""Welche Zonen-Charakteristik hatte tatsaechlich positive Erwartungswerte?

Aufruf:  python analyse_zonen_erwartungswert.py [export.json]

Hintergrund (02.08.): Im voll gematchten Vergleich haben BEIDE Gruppen einen
negativen Erwartungswert - die CRV-vetoten -0,049 R, die ausgefuehrten
-0,426 R. Das CRV-Gate ist damit nachweislich falsch justiert, aber es ist
nicht die Ursache der Verluste. Bevor Gate ODER Prompt justiert werden, muss
die Frage beantwortet sein: WELCHE Kombination aus Stop-Abstand und CRV hat
ueberhaupt funktioniert?

Methodisch zwingend (Test_und_Verifikationsmethodik.md 2.5.7): jeder Bucket
braucht seine EIGENE mechanische Basislinie mit DENSELBEN Parametern. Ohne
sie misst man Marktphasen und haelt sie fuer Signalqualitaet - genau der
Fehler, an dem der ADX-Regelkandidat am selben Tag gescheitert ist.

Der Erwartungswert in R (Vielfaches des riskierten Betrags):
    EW = Trefferquote * CRV - (1 - Trefferquote)
Break-even liegt bei 1/(1+CRV).
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, r'D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool')
from agent.krypto.statistik import wilson_intervall

STANDARD_PFAD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
                 r'\notebook_diagnose.json')
AUFGELOEST = {'take_profit_erreicht', 'stop_loss_erreicht', 'liquidation_wahrscheinlich'}
TP = 'take_profit_erreicht'
MIN_N = 15          # Test_und_Verifikationsmethodik: darunter keine Aussage
HORIZONT_TAGE = 14  # wie im Backward-Tracking


def zonen_kennzahlen(r: dict) -> dict | None:
    """Stop-Abstand (relativ) und CRV nach der Z-2-Formel des Risk-Gates.

    Kantenwahl richtungsabhaengig - risk_gate.py nutzt bei bullischer These
    stop_von/take_von, bei bearischer die gespiegelten _bis (Zeile 1082/1145).
    """
    e_von, e_bis = r.get('entry_eur_von'), r.get('entry_eur_bis')
    s_von, s_bis = r.get('stop_loss_eur_von'), r.get('stop_loss_eur_bis')
    t_von, t_bis = r.get('take_profit_eur_von'), r.get('take_profit_eur_bis')
    if None in (e_von, s_von, t_von):
        return None
    e = (e_von + (e_bis or e_von)) / 2
    ist_short = t_von < e
    if ist_short:
        if s_bis is None or t_bis is None:
            return None
        risiko, chance = s_bis - e, e - t_bis
    else:
        risiko, chance = e - s_von, t_von - e
    if risiko <= 0 or e <= 0:
        return None
    return {'stop_rel': risiko / e, 'crv': chance / risiko, 'ist_short': ist_short}


def erwartungswert(treffer: int, n: int, crv: float) -> float:
    q = treffer / n
    return q * crv - (1 - q)


def lade_serien(d: dict) -> dict:
    je = d.get('preishistorie_signal_symbole', {}).get('preishistorie_je_symbol', {})
    serien = {}
    for sym, rows in je.items():
        usd = sorted([r for r in rows if r.get('currency') == 'USD'
                      and None not in (r.get('high'), r.get('low'), r.get('close'))],
                     key=lambda r: r['date'])
        if len(usd) > HORIZONT_TAGE * 3:
            serien[sym] = usd
    return serien


def basislinie(serien: dict, stop_rel: float, crv: float, ist_short: bool) -> tuple:
    """Zufallseinstieg an JEDEM Tagesbalken mit exakt diesen Parametern."""
    tp = sl = 0
    for rows in serien.values():
        for i in range(len(rows) - HORIZONT_TAGE):
            e = rows[i]['close']
            if not e or e <= 0:
                continue
            if ist_short:
                s_, t_ = e * (1 + stop_rel), e * (1 - stop_rel * crv)
            else:
                s_, t_ = e * (1 - stop_rel), e * (1 + stop_rel * crv)
            for j in range(i + 1, i + 1 + HORIZONT_TAGE):
                if (rows[j]['high'] >= s_) if ist_short else (rows[j]['low'] <= s_):
                    sl += 1
                    break
                if (rows[j]['low'] <= t_) if ist_short else (rows[j]['high'] >= t_):
                    tp += 1
                    break
    n = tp + sl
    return (tp, n) if n else (0, 0)


def bucket_stop(x: float) -> str:
    if x < 0.03:
        return "A <3%"
    if x < 0.06:
        return "B 3-6%"
    if x < 0.10:
        return "C 6-10%"
    return "D >10%"


def bucket_crv(x: float) -> str:
    if x < 1.5:
        return "1 <1,5"
    if x < 2.0:
        return "2 1,5-2,0"
    if x < 3.0:
        return "3 2,0-3,0"
    return "4 >3,0"


def sammle(d: dict) -> list:
    """Alle aufgeloesten Signale - ausgefuehrte UND Veto-Schatten.

    Beide Zweige werden von identischer Logik bewertet (verifiziert 02.08.:
    check_hebel_signal_outcome vs. check_hebel_signal_veto_shadow_outcome
    nutzen dieselben hit_stop/hit_take/hit_liquidation-Kriterien), der
    Zusammenwurf ist also zulaessig und verdoppelt die Stichprobe.
    """
    faelle = []
    for quelle in ('hebel_signals', 'spot_signals'):
        for r in d.get(quelle, []):
            for feld in ('outcome_status', 'veto_outcome_status'):
                st = r.get(feld)
                if st not in AUFGELOEST:
                    continue
                z = zonen_kennzahlen(r)
                if not z:
                    continue
                faelle.append({**z, 'treffer': st == TP, 'quelle': quelle,
                               'symbol': r['symbol'], 'geschattet': feld.startswith('veto')})
                break
    return faelle


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding='utf-8'))
    faelle = sammle(d)
    serien = lade_serien(d)
    print(f"Export: {pfad}")
    print(f"{len(faelle)} aufgeloeste Signale mit Zonen, "
          f"{sum(1 for f in faelle if f['geschattet'])} davon Veto-Schatten")
    print(f"{len(serien)} Preisreihen fuer die Basislinien\n")

    for dim, name, fn in (('stop_rel', 'STOP-ABSTAND', bucket_stop),
                          ('crv', 'CRV', bucket_crv)):
        print("=" * 72)
        print(f"{name}: Erwartungswert je Bucket, gegen mechanische Basislinie")
        print("=" * 72)
        gr = defaultdict(list)
        for f in faelle:
            gr[fn(f[dim])].append(f)
        for b in sorted(gr):
            g = gr[b]
            n = len(g)
            t = sum(1 for f in g if f['treffer'])
            med_stop = statistics.median(f['stop_rel'] for f in g)
            med_crv = statistics.median(f['crv'] for f in g)
            ew = erwartungswert(t, n, med_crv)
            lo, hi = wilson_intervall(t, n)
            warn = "" if n >= MIN_N else f"  <-- n<{MIN_N}, KEINE Aussage"
            print(f"\n  {b:10s} n={n:4d}  Stop {med_stop*100:5.2f}%  CRV {med_crv:4.2f}"
                  f"  Treffer {t/n*100:5.1f}% [{lo*100:.0f}-{hi*100:.0f}%]{warn}")
            print(f"  {'':10s} Break-even {1/(1+med_crv)*100:4.1f}%   "
                  f"ERWARTUNGSWERT {ew:+.3f} R")
            anteil_short = sum(1 for f in g if f['ist_short']) / n
            bt, bn = basislinie(serien, med_stop, med_crv, ist_short=anteil_short > 0.5)
            if bn:
                bew = erwartungswert(bt, bn, med_crv)
                blo, bhi = wilson_intervall(bt, bn)
                ueber = lo <= bhi and blo <= hi
                print(f"  {'':10s} Basislinie (Zufall, gleiche Parameter, n={bn}): "
                      f"{bt/bn*100:5.1f}% [{blo*100:.0f}-{bhi*100:.0f}%]  EW {bew:+.3f} R")
                print(f"  {'':10s} -> Signalbeitrag {ew-bew:+.3f} R  "
                      f"({'im Rauschen' if ueber else 'Intervalle getrennt'})")
        print()


if __name__ == '__main__':
    main()
