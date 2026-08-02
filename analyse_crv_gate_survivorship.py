"""Filtert das CRV-Gate die richtigen Signale? Survivorship-bereinigt (Task #602).

Aufruf:  python analyse_crv_gate_survivorship.py [export.json]

WARUM NEU. Der Befund vom 02.08. ("das Gate sortiert aus, was funktioniert")
hielt der Gegenpruefung nicht stand: er verglich Gruppen mit sehr
unterschiedlicher Aufloesungsquote. Weite Stops werden zu 0,2% aufgeloest, enge
zu 31% - wer nur die aufgeloesten Faelle anschaut, vergleicht Selektionsgrade
statt Signalqualitaet. Der naheliegende Ausweg (MFE-Tracking) war selbst von
derselben Selektion betroffen und wurde am 02.08. repariert; die Daten dazu
entstehen aber erst mit dem naechsten Produktivlauf.

WAS DIESES SKRIPT ANDERS MACHT. Es liest den DB-Status gar nicht, sondern
simuliert JEDES Signal mit Zonen selbst gegen die Preishistorie - auch die, die
nie ein Ergebnis erreicht haben. Jedes Signal bekommt einen R-Wert:
  Take-Profit getroffen  -> +CRV
  Stop-Loss getroffen    -> -1,0
  keins von beidem       -> Mark-to-Market am Ende des Beobachtungsfensters
Damit gibt es keine ausgewertete Teilmenge mehr - die Selektion entfaellt
strukturell statt korrigiert zu werden.

EINSCHRAENKUNGEN, bewusst ausgewiesen (Zielgroessen_und_Erfolgsmasse.md, 4):
- Rechnung in EUR, weil der Export bis 02.08. nur EUR-Zonen enthielt. Der
  Produktivcode rechnet in USD. Ueber die Haltedauer bewegt sich EUR/USD, die
  Werte sind daher nicht bitgleich zur Produktivbewertung. Ab dem naechsten
  Export sind die USD-Zonen enthalten (Commit 789cc74) - dann diese Rechnung
  auf USD umstellen und gegenpruefen.
- Beobachtungsdauer je Signal ist begrenzt durch das Ende der Preisreihe.
  Deshalb wird sie je Gruppe MITAUSGEWIESEN: der Vergleich ist nur gueltig,
  wenn beide Gruppen aehnlich lang beobachtet wurden.
- Ausfuehrungspreis nach der Konvention vom 02.08. (Zonen-Grenze, bei Gap der
  Eroeffnungskurs, Regelwerksmanual Kapitel 21).
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
MIN_N = 15          # Test_und_Verifikationsmethodik: darunter keine Aussage
HORIZONT_TAGE = 14  # wie im Backward-Tracking


def zonen(r: dict) -> dict | None:
    """Entry-Mitte, Stop, Ziel und CRV nach der Z-2-Formel des Risk-Gates.

    Kantenwahl richtungsabhaengig - risk_gate.py nimmt bei bullischer These
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
        stop, ziel = s_bis, t_bis
    else:
        stop, ziel = s_von, t_von
    risiko = (stop - e) if ist_short else (e - stop)
    chance = (e - ziel) if ist_short else (ziel - e)
    if risiko <= 0 or e <= 0:
        return None
    return {'entry': e, 'stop': stop, 'ziel': ziel, 'ist_short': ist_short,
            'risiko': risiko, 'crv': chance / risiko, 'stop_rel': risiko / e}


def simuliere(z: dict, reihe: list[dict], ab_datum: str) -> dict | None:
    """Ein Signal gegen die Preisreihe laufen lassen - ohne DB-Status.

    Gibt R-Multiple, Ausgang und die tatsaechliche Beobachtungsdauer zurueck.
    Der Ausfuehrungspreis folgt der Konvention vom 02.08.: Zonen-Grenze, bei
    einem Gap der Eroeffnungskurs.
    """
    tage = [p for p in reihe if p['date'] >= ab_datum][:HORIZONT_TAGE + 1]
    if len(tage) < 2:
        return None
    e, stop, ziel, short = z['entry'], z['stop'], z['ziel'], z['ist_short']

    for p in tage:
        hoch, tief, auf = p['high'], p['low'], p.get('open')
        hit_stop = (hoch >= stop) if short else (tief <= stop)
        hit_ziel = (tief <= ziel) if short else (hoch >= ziel)
        # Konservativ wie im Backward-Tracking: Stop schlaegt Ziel am selben Tag.
        if hit_stop:
            fill = stop if auf is None else (max(stop, auf) if short else min(stop, auf))
            return {'r': ((e - fill) if short else (fill - e)) / z['risiko'],
                    'ausgang': 'stop', 'tage': len(tage)}
        if hit_ziel:
            fill = ziel if auf is None else (min(ziel, auf) if short else max(ziel, auf))
            return {'r': ((e - fill) if short else (fill - e)) / z['risiko'],
                    'ausgang': 'ziel', 'tage': len(tage)}
    schluss = tage[-1]['close']
    return {'r': ((e - schluss) if short else (schluss - e)) / z['risiko'],
            'ausgang': 'offen', 'tage': len(tage)}


def kennzahlen(werte: list[float]) -> str:
    if not werte:
        return "keine Faelle"
    n = len(werte)
    mittel = statistics.fmean(werte)
    streuung = statistics.stdev(werte) if n >= 2 else None
    sqn = (mittel / streuung * (n ** 0.5)) if streuung else None
    gewinner = sum(1 for r in werte if r > 0)
    lo, hi = wilson_intervall(gewinner, n)
    txt = (f"n={n:4d}  EW {mittel:+.3f} R  "
           f"positiv {gewinner / n * 100:4.1f}% [{lo * 100:.0f}-{hi * 100:.0f}%]")
    if sqn is not None:
        txt += f"  SQN {sqn:+.2f}"
    return txt


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding='utf-8'))
    je_symbol = d.get('preishistorie_signal_symbole', {}).get('preishistorie_je_symbol', {})
    reihen = {}
    for sym, rows in je_symbol.items():
        eur = sorted([r for r in rows if r.get('currency') == 'EUR'
                      and None not in (r.get('high'), r.get('low'), r.get('close'))],
                     key=lambda r: r['date'])
        if eur:
            reihen[sym] = eur

    print(f"Export: {pfad}")
    print(f"{len(reihen)} Symbole mit EUR-Preisreihe\n")

    gruppen: dict[tuple[str, str], list[dict]] = defaultdict(list)
    ohne_reihe = zu_kurz = 0
    for quelle, tier in (('hebel_signals', 'hebel'), ('spot_signals', 'spot')):
        for r in d.get(quelle, []):
            z = zonen(r)
            if not z:
                continue
            if r['symbol'] not in reihen:
                ohne_reihe += 1
                continue
            sim = simuliere(z, reihen[r['symbol']], r['created_at'][:10])
            if sim is None:
                zu_kurz += 1
                continue
            # Gruppe: hat das Gate wegen CRV zurueckgestuft, oder ging es raus?
            grund = (r.get('risk_veto_reason') or '').lower()
            vetot = bool(r.get('risk_veto'))
            art = ('crv-vetot' if vetot and 'crv' in grund
                   else 'anders vetot' if vetot else 'ausgefuehrt')
            gruppen[(tier, art)].append({**sim, 'crv': z['crv'],
                                         'stop_rel': z['stop_rel'], 'symbol': r['symbol']})

    print(f"uebersprungen: {ohne_reihe} ohne Preisreihe, {zu_kurz} mit zu kurzer Reihe\n")

    for tier in ('hebel', 'spot'):
        arten = [(a, g) for (t, a), g in gruppen.items() if t == tier]
        if not arten:
            continue
        print("=" * 78)
        print(f"{tier.upper()} - jedes Signal simuliert, keine Auswahl nach DB-Status")
        print("=" * 78)
        for art, g in sorted(arten):
            werte = [x['r'] for x in g]
            dauer = statistics.median(x['tage'] for x in g)
            med_crv = statistics.median(x['crv'] for x in g)
            ausgang = defaultdict(int)
            for x in g:
                ausgang[x['ausgang']] += 1
            warn = "" if len(g) >= MIN_N else f"   <-- n<{MIN_N}, KEINE Aussage"
            print(f"\n  {art:14s} {kennzahlen(werte)}{warn}")
            print(f"  {'':14s} Median-CRV {med_crv:4.2f}, "
                  f"Beobachtung {dauer:.0f} Tage (Median)")
            print(f"  {'':14s} Ausgang: {ausgang['ziel']} Ziel, {ausgang['stop']} Stop, "
                  f"{ausgang['offen']} am Fensterende bewertet")
            symbole = defaultdict(int)
            for x in g:
                symbole[x['symbol']] += 1
            top = max(symbole.items(), key=lambda kv: kv[1])
            print(f"  {'':14s} groesstes Symbol: {top[0]} mit {top[1]}/{len(g)} "
                  f"({top[1] / len(g) * 100:.0f}%)")
        print()

    for schwelle in (10, HORIZONT_TAGE):
        stratifiziert(gruppen, schwelle)


def stratifiziert(gruppen: dict, mindest_tage: int) -> None:
    """Gegenpruefung: nur Signale mit MINDESTENS derselben Beobachtungsdauer.

    Ohne das vergleicht man wieder Aepfel mit Birnen - laenger beobachtete
    Signale haben mehr Gelegenheit, ihren Stop zu treffen. Genau diese Art
    Ungleichheit hat den ersten CRV-Befund am 02.08. zu Fall gebracht.
    """
    print("=" * 78)
    print(f"GEGENPRUEFUNG: nur Signale mit mindestens {mindest_tage} Tagen "
          f"Beobachtung (gleiche Dauer)")
    print("=" * 78)
    for tier in ('hebel', 'spot'):
        zeilen = []
        for (t, art), g in sorted(gruppen.items()):
            if t != tier:
                continue
            eng = [x for x in g if x['tage'] >= mindest_tage]
            if eng:
                zeilen.append((art, eng))
        if not zeilen:
            continue
        print(f"\n  --- {tier} ---")
        for art, eng in zeilen:
            werte = [x['r'] for x in eng]
            warn = "" if len(eng) >= MIN_N else f"   <-- n<{MIN_N}, KEINE Aussage"
            print(f"    {art:14s} {kennzahlen(werte)}{warn}")
    print()


if __name__ == '__main__':
    main()
