"""Gate oder Positionsgroesse? Die uebliche Anwendung von CRV im Vergleich (Task #602).

Aufruf:  python analyse_crv_gate_vs_positionsgroesse.py [export.json]

WARUM. Task #602 hat gezeigt, DASS das CRV-Gate in die richtige Richtung
filtert. Es hat nicht gezeigt, dass ein Gate die richtige FORM ist. In der
Literatur (Van Tharp, Kelly/Vince) wird das Chance-Risiko-Verhaeltnis
ueblicherweise nicht als Ja/Nein-Schwelle benutzt, sondern zur Bemessung der
POSITIONSGROESSE: schwache Kante klein, starke Kante gross. Ein Gate ist der
Sonderfall "Groesse 0 oder 1". Diese Frage stellte der Nutzer, und sie war
offen - hier wird sie gemessen.

DREI VARIANTEN auf derselben Signalmenge, identische Simulation, nur die
Gewichtung unterscheidet sich:
  A  Gate wie heute - CRV unter der Schwelle faellt weg, Rest gleich gross.
  B  Kein Gate - jedes Signal wird gehandelt, Groesse nach Viertel-Kelly.
  C  Mischform - harter Boden bei sehr schlechtem CRV, darueber Kelly.

ZIRKULARITAETSFALLE. Die Kelly-Formel braucht eine Trefferwahrscheinlichkeit.
Schaetzt man sie aus denselben Faellen, die man anschliessend bewertet, misst
man sich selbst - der Fehler, der in dieser Untersuchungsreihe schon zweimal
einen Befund gekippt hat. Deshalb WALK-FORWARD: fuer jedes Signal fliesst nur
ein, was zu seinem Zeitpunkt bereits aufgeloest war. Vor Erreichen einer
Mindestzahl gibt es keine Schaetzung und damit keine Position.

Die Simulation selbst (Zonen, Fill-Regel, Abbruch) wird aus
analyse_crv_gate_survivorship.py importiert statt nachgebaut - zwei
Implementierungen wuerden auseinanderlaufen und den Vergleich entwerten.
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, r'D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool')
from analyse_crv_gate_survivorship import STANDARD_PFAD, simuliere, zonen

MIN_N = 15                  # Test_und_Verifikationsmethodik: darunter keine Aussage
HORIZONT = 7                # groessere Stichprobe als 14, siehe #602
KELLY_ANTEIL = 0.25         # Viertel-Kelly - Standard gegen Schaetzfehler
MIN_N_FUER_SCHAETZUNG = 30  # vorher keine Trefferquote, also keine Position
CRV_GATE_SCHWELLE = 2.0     # wie im Produktivcode (risk_gate.py)
CRV_BODEN_VARIANTE_C = 1.0  # unterhalb ist Kelly ohnehin negativ bei p<0.5
# Werte aus Basisinfos/config.yaml, fuer die Nachbildung des heutigen Verhaltens
SOCKEL_ANTEIL = 0.5             # risiko.konfidenz_positionsgroesse_sockel_anteil
CRV_KNAPP_SCHWELLE_RELATIV = 0.2  # risiko.crv_knapp_schwelle_relativ
CRV_KNAPP_DECKEL_ANTEIL = 0.6   # risiko.crv_knapp_positionsgroesse_deckel_anteil
# regime.profile.*.min_konfidenz_prozent liegt je Regime zwischen 60 und 85; das
# Regime je Signal steht nicht im Export, deshalb ein mittlerer Wert. Die
# Empfindlichkeit dagegen wird unten mitgeprueft.
MIN_KONFIDENZ_ANNAHME = 65.0
GROESSE_DECKEL = 1.0        # keine Variante darf mehr riskieren als das Gate
BOOTSTRAP_ZIEHUNGEN = 1000
BOOTSTRAP_SEED = 20260803


def kelly_groesse(crv: float, p: float) -> float:
    """Viertel-Kelly, gedeckelt.

    f* = (p*b - q) / b mit b = CRV. Negatives f* heisst "keine Kante" - das
    ergibt Groesse 0 und wirkt damit als Gate, das sich aus der Formel ERGIBT
    statt gesetzt zu sein. Der Deckel sorgt dafuer, dass keine Variante mehr
    riskieren darf als das heutige Gate, sonst vergliche man Hebelwirkung
    statt Auswahlqualitaet.
    """
    if crv <= 0:
        return 0.0
    f_stern = (p * crv - (1.0 - p)) / crv
    return max(0.0, min(GROESSE_DECKEL, KELLY_ANTEIL * f_stern))


def kennzahlen(gewichtete: list[tuple[float, float]]) -> dict:
    """gewichtete = [(groesse, r_multiple), ...] - Groesse 0 heisst nicht gehandelt.

    NORMIERUNG (03.08., eigener Fund beim ersten Lauf): Kelly liefert mittlere
    Groessen um 0,06, das Gate setzt 1,00 - ein Vergleich der Summen wuerde
    dann Einsatzhoehe messen statt Auswahlqualitaet, und die Kelly-Varianten
    saehen faelschlich schwach aus. Da der Nutzer den Invest ohnehin selbst
    festlegt (siehe Memory "Positionsgroessen: Praxis vs. System entkoppelt"),
    ist nur die RELATIVE Gewichtung die Aussage. Jede Variante wird deshalb auf
    mittlere Groesse 1,0 skaliert; das Verhaeltnis der Groessen zueinander
    bleibt dabei unveraendert. SQN ist skaleninvariant und aendert sich nicht -
    genau deshalb ist es hier der ehrlichste Vergleichswert.
    """
    gehandelt = [(g, r) for g, r in gewichtete if g > 0]
    if not gehandelt:
        return {'trades': 0}
    roh_mittel = statistics.fmean(g for g, _ in gehandelt)
    faktor = (1.0 / roh_mittel) if roh_mittel > 0 else 1.0
    beitraege = [g * faktor * r for g, r in gehandelt]
    n = len(beitraege)
    mittel = statistics.fmean(beitraege)
    streuung = statistics.stdev(beitraege) if n >= 2 else None
    # Equity-Kurve fuer den Rueckschlag - die Reihenfolge ist die zeitliche,
    # deshalb wird die Eingangsliste nicht sortiert.
    kumuliert, spitze, max_rueckschlag = 0.0, 0.0, 0.0
    for b in beitraege:
        kumuliert += b
        spitze = max(spitze, kumuliert)
        max_rueckschlag = max(max_rueckschlag, spitze - kumuliert)
    return {
        'trades': n,
        'summe_r': sum(beitraege),
        'mittel_r': mittel,
        'sqn': (mittel / streuung * (n ** 0.5)) if streuung else None,
        'max_rueckschlag_r': max_rueckschlag,
        'roh_groesse': roh_mittel,       # vor der Normierung, nur zur Information
        'spreizung': (max(g for g, _ in gehandelt) / min(g for g, _ in gehandelt)
                      if min(g for g, _ in gehandelt) > 0 else float('inf')),
        'beitraege': beitraege,
    }


def bootstrap_ci(werte: list[float]) -> tuple[float, float]:
    """Perzentil-Intervall auf den Mittelwert. Fester Startwert, damit zwei
    Laeufe dasselbe zeigen - sonst wirkt Rauschen wie ein Unterschied."""
    if len(werte) < 2:
        return (float('nan'), float('nan'))
    rnd = random.Random(BOOTSTRAP_SEED)
    n = len(werte)
    mittel = sorted(statistics.fmean(rnd.choices(werte, k=n))
                    for _ in range(BOOTSTRAP_ZIEHUNGEN))
    return (mittel[int(0.025 * BOOTSTRAP_ZIEHUNGEN)],
            mittel[int(0.975 * BOOTSTRAP_ZIEHUNGEN)])


def lade_signale(d: dict, reihen: dict) -> list[dict]:
    """Alle Signale mit Zonen und vollstaendiger Preisreihe, zeitlich sortiert.

    Zeitliche Sortierung ist Voraussetzung fuer den Walk-Forward: die
    Trefferquote fuer Signal i darf nur aus Signalen vor i stammen.
    """
    ergebnis = []
    for quelle, tier in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
        for r in d.get(quelle, []):
            z = zonen(r)
            if not z or r['symbol'] not in reihen:
                continue
            sim = simuliere(z, reihen[r['symbol']], r['created_at'][:10], HORIZONT)
            if sim is None:
                continue
            grund = (r.get('risk_veto_reason') or '').lower()
            ergebnis.append({
                'tier': tier, 'symbol': r['symbol'], 'created_at': r['created_at'],
                'crv': z['crv'], 'r': sim['r'], 'ausgang': sim['ausgang'],
                'crv_vetot': bool(r.get('risk_veto')) and 'crv' in grund,
                'confidence_pct': r.get('confidence_pct'),
            })
    ergebnis.sort(key=lambda x: x['created_at'])
    return ergebnis


def walk_forward_trefferquoten(signale: list[dict]) -> list[float | None]:
    """Fuer jedes Signal die Trefferquote der VORHER aufgeloesten Faelle.

    Bewusst ueber alle Signale hinweg statt je CRV-Klasse: die Stichprobe
    reicht nicht fuer klassenweise Schaetzungen (das war der Grund, warum die
    ADX-Auswertung am 01.08. abgebrochen wurde). Die CRV-Abhaengigkeit steckt
    ohnehin schon im b der Kelly-Formel.
    """
    quoten: list[float | None] = []
    treffer = gesamt = 0
    for s in signale:
        quoten.append(treffer / gesamt if gesamt >= MIN_N_FUER_SCHAETZUNG else None)
        if s['ausgang'] in ('ziel', 'stop'):
            gesamt += 1
            treffer += 1 if s['ausgang'] == 'ziel' else 0
    return quoten


def heutige_groesse(s: dict, min_konfidenz: float) -> float:
    """Was der Produktivcode heute WIRKLICH macht (risk_gate.py::post_check).

    Nachgebildet werden die beiden Deckel-Kandidaten, die von CRV und Konfidenz
    abhaengen: die Konfidenz-Skalierung (Sockel 50% an der Regime-Mindest-
    schwelle, linear bis 100%) und der CRV-knapp-Deckel (60% unterhalb
    CRV_MINIMUM * 1,2 = 2,4). Verknuepfung per min() ueber die ausgeloesten
    Kandidaten, wie seit 2026-07-24 im Code.

    NICHT nachgebildet: Gegenszenario-Deckel und technischer-Konflikt-Deckel -
    die dafuer noetigen Felder (forecast.bear, Konfluenz-Bias) stehen nicht im
    Export. Diese Variante ist damit eine UNTERGRENZE dessen, was das heutige
    System an Differenzierung leistet; sie ueberschaetzt den Abstand zu Kelly
    nicht, sondern unterschaetzt ihn eher.
    """
    if s['crv_vetot']:
        return 0.0
    kandidaten = [GROESSE_DECKEL]
    konf = s.get('confidence_pct')
    if konf is not None and min_konfidenz < 100:
        spanne = max(0.0, min(1.0, (konf - min_konfidenz) / (100 - min_konfidenz)))
        kandidaten.append(SOCKEL_ANTEIL + (1 - SOCKEL_ANTEIL) * spanne)
    if s['crv'] < CRV_GATE_SCHWELLE * (1 + CRV_KNAPP_SCHWELLE_RELATIV):
        kandidaten.append(CRV_KNAPP_DECKEL_ANTEIL)
    return min(kandidaten)


def varianten(signale: list[dict], quoten: list[float | None],
              min_konfidenz: float = MIN_KONFIDENZ_ANNAHME) -> dict:
    a, aplus, b, c = [], [], [], []
    for s, p in zip(signale, quoten):
        r, crv = s['r'], s['crv']
        # A: nur das Gate - durchgelassene Signale alle gleich gross.
        a.append((0.0 if s['crv_vetot'] else GROESSE_DECKEL, r))
        # A+: Gate PLUS die heute schon vorhandenen Deckel. Ohne diese Variante
        # verglichen wir gegen einen Strohmann.
        aplus.append((heutige_groesse(s, min_konfidenz), r))
        # B/C: Kelly. Ohne belastbare Schaetzung wird nicht gehandelt.
        groesse = 0.0 if p is None else kelly_groesse(crv, p)
        b.append((groesse, r))
        c.append((0.0 if crv < CRV_BODEN_VARIANTE_C else groesse, r))
    return {'A nur Gate': a, 'A+ Gate + heutige Deckel': aplus,
            'B nur Positionsgroesse': b, 'C Boden + Groesse': c}


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

    signale = lade_signale(d, reihen)
    quoten = walk_forward_trefferquoten(signale)
    ohne_schaetzung = sum(1 for p in quoten if p is None)

    print(f"Export: {pfad}")
    print(f"{len(signale)} Signale mit Zonen und vollstaendiger {HORIZONT}-Tage-Reihe")
    print(f"davon {ohne_schaetzung} ohne Trefferquoten-Schaetzung "
          f"(erste {MIN_N_FUER_SCHAETZUNG} aufgeloeste Faelle, walk-forward)")
    letzte = [p for p in quoten if p is not None]
    if letzte:
        print(f"Trefferquote am Ende des Zeitraums: {letzte[-1]*100:.1f}%")
    print()

    for tier_filter in (None, 'hebel', 'spot'):
        teil = [s for s in signale if tier_filter is None or s['tier'] == tier_filter]
        teil_q = [p for s, p in zip(signale, quoten)
                  if tier_filter is None or s['tier'] == tier_filter]
        if len(teil) < MIN_N:
            continue
        titel = tier_filter or 'ALLE'
        print("=" * 78)
        print(f"{titel.upper()}  (n={len(teil)} auswertbare Signale)")
        print("=" * 78)
        print("  auf gleiche mittlere Positionsgroesse normiert - vergleichbar")
        print(f"  {'Variante':24s} {'Trades':>7s} {'Summe R':>9s} {'je Trade':>9s} "
              f"{'SQN':>7s} {'Rueckschl':>10s} {'Spreizg':>8s}")
        for name, gew in varianten(teil, teil_q).items():
            k = kennzahlen(gew)
            if not k['trades']:
                print(f"  {name:24s} {'-':>7s}   keine Position")
                continue
            sqn = f"{k['sqn']:+.2f}" if k['sqn'] is not None else "  -  "
            spr = "1.0x" if k['spreizung'] <= 1.0001 else f"{k['spreizung']:.0f}x"
            print(f"  {name:24s} {k['trades']:7d} {k['summe_r']:+9.1f} "
                  f"{k['mittel_r']:+9.3f} {sqn:>7s} {k['max_rueckschlag_r']:10.1f} "
                  f"{spr:>8s}")
            lo, hi = bootstrap_ci(k['beitraege'])
            print(f"  {'':24s} {'':7s} je Trade 95%-Intervall [{lo:+.3f} .. {hi:+.3f}] R")
        print()


if __name__ == '__main__':
    main()
