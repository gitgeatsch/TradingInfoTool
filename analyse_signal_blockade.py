"""Wo bleiben die Signale haengen? - wiederverwendbares Analyse-Skript.

Aufruf:  python analyse_signal_blockade.py [pfad_zum_export.json]

Beantwortet vier Fragen gegen einen Notebook-Export:
1. Wie aktuell sind die Daten (sonst misst man Vergangenheit)?
2. Wo genau versickern die Signale - LLM, Richtungsfilter oder Risiko-Gate?
3. Wie stark drueckt die konservative CRV-Formel (Z-2) das Ergebnis?
4. Wie entscheidungsfreudig ist das LLM im Zeitverlauf?

Reine Leseanalyse, kein Schreibzugriff. Ergaenzt den Kennzahlen-Katalog aus
Basisinfos/Test_und_Verifikationsmethodik.md 2.1 um die Blockade-Perspektive.
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, r'D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool')
try:
    from agent.krypto.statistik import wilson_intervall
except Exception:                                    # Skript soll auch ohne Repo laufen
    def wilson_intervall(t, n):                      # grobe Naeherung als Rueckfall
        if not n:
            return (0.0, 0.0)
        p = t / n
        rand = 1.96 * (p * (1 - p) / n) ** 0.5
        return (max(0.0, p - rand), min(1.0, p + rand))

STANDARD_PFAD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
                 r'\notebook_diagnose.json')
AUFGELOEST = {'take_profit_erreicht', 'stop_loss_erreicht', 'liquidation_wahrscheinlich'}
CRV_MINIMUM = 2.0


def lade(pfad: str) -> dict:
    return json.load(io.open(pfad, encoding='utf-8'))


def kopf(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def frage1_aktualitaet(d: dict) -> None:
    kopf("1) AKTUALITAET - misst diese Analyse ueberhaupt die Gegenwart?")
    jetzt = datetime.now(timezone.utc)
    for quelle in ('spot_signals', 'hebel_signals'):
        rows = d.get(quelle, [])
        if not rows:
            print(f"  {quelle:15s} leer")
            continue
        juengst = max(r['created_at'] for r in rows)
        try:
            alter = (jetzt - datetime.fromisoformat(juengst)).total_seconds() / 3600
            hinweis = "" if alter < 3 else "  <-- ALT, Aussagen gelten nicht fuer heute"
            print(f"  {quelle:15s} n={len(rows):5d}  juengstes {juengst[:16]} UTC "
                  f"({alter:.1f}h alt){hinweis}")
        except Exception:
            print(f"  {quelle:15s} n={len(rows):5d}  juengstes {juengst[:16]}")


def frage2_blockade(d: dict, seit: str) -> None:
    kopf(f"2) BLOCKADE-KETTE - wo versickern die Signale? (seit {seit})")
    for quelle, lbl in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
        rows = [r for r in d.get(quelle, []) if r['created_at'][:10] >= seit]
        if not rows:
            print(f"\n  --- {lbl}: keine Signale im Zeitraum ---")
            continue
        gesendet = [r for r in rows if r.get('action') not in (None, 'HALTEN')]
        vetot = [r for r in rows if r.get('risk_veto')]
        llm_halten = [r for r in rows if r.get('action') == 'HALTEN' and not r.get('risk_veto')]
        print(f"\n  --- {lbl}: {len(rows)} LLM-Bewertungen ---")
        print(f"    {len(gesendet):4d}  ergaben ein Signal")
        print(f"    {len(vetot):4d}  von einem Gate gestoppt")
        print(f"    {len(llm_halten):4d}  LLM waehlte selbst HALTEN (kein Gate beteiligt)")
        if vetot:
            print("    Gate-Aufschluesselung:")
            c = Counter()
            for r in vetot:
                g = r.get('risk_veto_reason') or ''
                if 'Nur Long' in g:
                    c['Nur-Long-Richtungsfilter'] += 1
                elif 'RM-1b' in g or 'RM-1c' in g:
                    c['Stop-Untergrenze (RM-1b/1c)'] += 1
                elif 'CRV' in g:
                    c['CRV unter Minimum'] += 1
                elif 'Konfidenz' in g:
                    c['Konfidenz zu niedrig'] += 1
                elif 'Cash' in g or 'cash' in g:
                    c['Cash-Veto'] += 1
                else:
                    c[g[:45] or '(ohne Text)'] += 1
            for k, v in c.most_common():
                print(f"      {v:4d}  {k}")


def _zonen(r: dict) -> dict | None:
    """Konservative (Z-2) und mittige CRV-Variante aus den Zonengrenzen.

    WICHTIG - die Kantenwahl haengt an der Richtung, sonst misst man Unsinn:
    risk_gate.py nutzt bei bullischer These `stop_von`/`take_von`, bei
    bearischer die gespiegelten `stop_bis`/`take_bis` (Zeile 1082 vs. 1145).
    Beides waehlt jeweils den UNGUENSTIGSTEN Zonenrand. Nimmt man stur `_von`,
    dreht sich das Vorzeichen des Abschlags bei SHORT um und die konservative
    Formel sieht faelschlich aus, als wuerde sie Signale beguenstigen."""
    e_von, e_bis = r.get('entry_eur_von'), r.get('entry_eur_bis')
    s_von, s_bis = r.get('stop_loss_eur_von'), r.get('stop_loss_eur_bis')
    t_von, t_bis = r.get('take_profit_eur_von'), r.get('take_profit_eur_bis')
    if None in (e_von, s_von, t_von):
        return None
    e_mid = (e_von + (e_bis or e_von)) / 2
    ist_short = t_von < e_mid
    if ist_short:
        if s_bis is None or t_bis is None:
            return None
        risiko_k, chance_k = s_bis - e_mid, e_mid - t_bis
    else:
        risiko_k, chance_k = e_mid - s_von, t_von - e_mid
    # Mittig: beide Zonen auf ihre Mitte - richtungsneutral, da nur Betraege
    s_mid = (s_von + (s_bis or s_von)) / 2
    t_mid = (t_von + (t_bis or t_von)) / 2
    risiko_m, chance_m = abs(e_mid - s_mid), abs(t_mid - e_mid)
    if risiko_k <= 0 or risiko_m <= 0:
        return None
    return {'crv_konservativ': chance_k / risiko_k, 'crv_mittig': chance_m / risiko_m,
            'ist_short': ist_short}


def frage3_crv_abschlag(d: dict, seit: str) -> None:
    kopf(f"3) CRV-ABSCHLAG (Z-2 konservativ) - wie stark drueckt er? (seit {seit})")
    print("    Z-2 rechnet: Entry-Mitte, unguenstigster Stop, unguenstigstes Ziel.")
    print("    Beide Zonenenden liegen also GEGEN das Signal.\n")
    for quelle, lbl in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
        rows = [r for r in d.get(quelle, []) if r['created_at'][:10] >= seit]
        z = [x for x in (_zonen(r) for r in rows) if x]
        if not z:
            print(f"  {lbl}: keine auswertbaren Zonen")
            continue
        med_k = statistics.median(x['crv_konservativ'] for x in z)
        med_m = statistics.median(x['crv_mittig'] for x in z)
        # Signale, die NUR wegen des Abschlags scheitern
        opfer = [x for x in z if x['crv_konservativ'] < CRV_MINIMUM <= x['crv_mittig']]
        print(f"  --- {lbl}: {len(z)} Signale mit vollstaendigen Zonen ---")
        print(f"    CRV konservativ (Z-2), Median: {med_k:5.2f}")
        print(f"    CRV mittig gerechnet,   Median: {med_m:5.2f}")
        if med_m:
            print(f"    -> Abschlag: {(1 - med_k/med_m)*100:4.1f}% des CRV")
        print(f"    NUR wegen des Abschlags unter {CRV_MINIMUM}: {len(opfer)} Signale "
              f"({len(opfer)/len(z)*100:.1f}%)")
        if opfer:
            print(f"       (mittig waeren sie Median {statistics.median(x['crv_mittig'] for x in opfer):.2f},"
                  f" konservativ {statistics.median(x['crv_konservativ'] for x in opfer):.2f})")


def frage4_entscheidungsfreude(d: dict, seit: str) -> None:
    kopf(f"4) ENTSCHEIDUNGSFREUDE des LLM im Zeitverlauf (seit {seit})")
    print("    echte Aktion = action != HALTEN ODER risk_veto (ein vetotes HALTEN")
    print("    war urspruenglich eine Handlungsempfehlung)\n")
    for quelle, lbl in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
        je_tag = defaultdict(lambda: [0, 0])
        for r in d.get(quelle, []):
            tag = r['created_at'][:10]
            if tag < seit:
                continue
            je_tag[tag][0] += 1
            if r.get('action') != 'HALTEN' or r.get('risk_veto'):
                je_tag[tag][1] += 1
        if not je_tag:
            continue
        print(f"  --- {lbl} ---")
        for tag in sorted(je_tag):
            ges, echt = je_tag[tag]
            lo, hi = wilson_intervall(echt, ges)
            print(f"    {tag}  n={ges:3d}  {echt/ges*100:5.1f}% "
                  f"[{lo*100:.0f}-{hi*100:.0f}%]  {'#' * int(echt/ges*35)}")
        print()


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    seit = sys.argv[2] if len(sys.argv) > 2 else '2026-07-29'
    print(f"Export: {pfad}")
    d = lade(pfad)
    frage1_aktualitaet(d)
    frage2_blockade(d, seit)
    frage3_crv_abschlag(d, seit)
    frage4_entscheidungsfreude(d, seit)
    print()


if __name__ == '__main__':
    main()
