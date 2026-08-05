"""Erst Population trennen, dann datieren - ohne den Trennpunkt vorher zu kennen.

WARUM DIESES SKRIPT NOETIG IST: meine bisherige Datierung hatte zwei Fehler,
die sich gegenseitig verdecken.

FEHLER 1 - DER TRENNPUNKT WAR DATENGETRIEBEN GEWAEHLT. Ich habe die Tagesreihe
angesehen, den 29.07. als Kipppunkt ERKANNT und dann GENAU DORT getestet. Ein
p-Wert aus einem so gewaehlten Schnitt ist wertlos: bei 20 moeglichen
Trennpunkten findet man auch in reinem Rauschen fast immer einen, der
"signifikant" aussieht. Richtig ist die Max-Statistik - die Teststatistik ist
der GROESSTE ueber alle Trennpunkte gefundene Unterschied, und die
Nullverteilung wird fuer genau diese Groesse simuliert. Dasselbe Verfahren
steckt schon in ausschuss_suche.py.

FEHLER 2 - ICH HABE ZWEI MESSPFADE VERMISCHT. Ein Signal kann sein Ergebnis
aus drei verschiedenen Quellen haben: dem regulaeren Outcome (nur ausgefuehrte
Signale), dem Veto-Schatten (vom Gate gedrehte) und dem Selbst-HALTEN-Schatten
(seit 31.07.). Im selben Zeitraum liefern diese Gruppen voellig verschiedene
Trefferquoten - bis 28.07. lagen die ausgefuehrten Signale bei rund 17 %, die
Schattengruppe bei 55 %. Meine Basislinie "45,1 % vor dem 29.07." stammte
ueberwiegend aus dem Schattenpfad. Die tatsaechlich ausgefuehrten Signale lagen
NIE bei 45 %.

Beide Fehler zusammen koennen einen Einbruch vortaeuschen, der in Wahrheit eine
Verschiebung der Zusammensetzung ist. Deshalb hier: jede Population EINZELN,
und der Trennpunkt wird gesucht statt gesetzt.

WAS SCHON AUSGESCHLOSSEN IST (messe_short_und_einbruch.py + Codelektuere):
Markt (direkt ueber 41 Symbole gemessen, Einbruchsperiode minimal BESSER),
Stop-Breite (alle Baender gleich), Richtung, Rechtszensierung (Landmark
H=3/4/5), Symbol-Clusterung, die drei Gate-Commits vom 29.07. (Positions-
groesse bzw. reine Darstellung), der Cooldown-Regler (24h->8h am 28.07. war
nie bindend - Median-Abstand 3,6 h vorher wie nachher) sowie zwei
Messaenderungen, die zu SPAET kamen: Ausfuehrungspreis auf Zonen-Grenze
(d16242e, 02.08. 23:46) und CoinGecko-OHLC-Rueckfall (875f0f5, 04.08. 06:21).

Lauf: python -u datiere_einbruch.py
"""
from __future__ import annotations

import io
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
TP, SL = "take_profit_erreicht", "stop_loss_erreicht"
H = 4                    # Beobachtungsfenster je Signal, in Tagen
MIN_JE_SEITE = 25        # weniger Faelle je Seite -> Trennpunkt nicht bewertbar
ZIEHUNGEN = 5000


def _tag(x):
    try:
        return datetime.strptime(str(x or "")[:10], "%Y-%m-%d")
    except ValueError:
        return None


def sammle(sig, pfad):
    """Ein Ergebnis je Signal, NUR aus dem angegebenen Messpfad.

    Der entscheidende Unterschied zu meinen frueheren Auswertungen: die nahmen
    das erste Ergebnis, das irgendeine der drei Familien lieferte, und mischten
    damit unvergleichbare Populationen."""
    raus = []
    for s in sig:
        a = _tag(s.get("created_at"))
        st = str(s.get(pfad + "outcome_status") or "")
        if not a or st not in (TP, SL):
            continue
        b = _tag(s.get(pfad + "outcome_entschieden_am"))
        if b and (b - a).days <= H:
            raus.append((a, s.get("symbol") or "?", 1 if st == TP else 0,
                         str(s.get("richtung") or "").upper()))
    return raus


def max_statistik(daten, ziehungen=ZIEHUNGEN, rnd=None):
    """Groesster Trefferquoten-Unterschied ueber ALLE Trennpunkte, und wie oft
    reines Rauschen so etwas hergibt.

    Die Nullverteilung wird per BLOCK-Permutation ueber Symbole erzeugt: die
    Datumszuordnung wird symbolweise gemischt, damit die Clusterung innerhalb
    eines Symbols erhalten bleibt. Wuerde man einzelne Signale mischen, waere
    die Nullverteilung zu eng und fast jeder Trennpunkt saehe signifikant aus."""
    rnd = rnd or random.Random(20260805)
    daten = sorted(daten, key=lambda x: x[0])
    kandidaten = sorted({d[0] for d in daten})[1:]

    def bester(werte):
        best = (0.0, None, 0, 0)
        for k in kandidaten:
            a = [y for t, _, y, _ in werte if t < k]
            b = [y for t, _, y, _ in werte if t >= k]
            if len(a) < MIN_JE_SEITE or len(b) < MIN_JE_SEITE:
                continue
            diff = sum(a) / len(a) - sum(b) / len(b)
            if abs(diff) > abs(best[0]):
                best = (diff, k, len(a), len(b))
        return best

    echt = bester(daten)
    if echt[1] is None:
        return echt, None
    # Block-Permutation: Datumsspalte symbolweise durchmischen
    proSym = defaultdict(list)
    for i, (t, sym, y, r) in enumerate(daten):
        proSym[sym].append(i)
    treffer = 0
    for _ in range(ziehungen):
        kopie = list(daten)
        for idx in proSym.values():
            daten_idx = [kopie[i][0] for i in idx]
            rnd.shuffle(daten_idx)
            for j, i in enumerate(idx):
                t, sym, y, r = kopie[i]
                kopie[i] = (daten_idx[j], sym, y, r)
        if abs(bester(kopie)[0]) >= abs(echt[0]):
            treffer += 1
    return echt, (treffer + 1) / (ziehungen + 1)


def main():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    sig = d["hebel_signals"]

    print("=" * 78)
    print("A. Die drei Messpfade GETRENNT - Reichweite und Niveau")
    print("=" * 78)
    pfade = {"regulaer (ausgefuehrt)": "", "Veto-Schatten": "veto_",
             "Selbst-HALTEN-Schatten": "selbst_halten_"}
    gesammelt = {}
    for name, pfad in pfade.items():
        g = sammle(sig, pfad)
        gesammelt[name] = g
        if not g:
            print(f"  {name:26s} keine Faelle")
            continue
        tage = sorted({t for t, _, _, _ in g})
        print(f"  {name:26s} n={len(g):4d}  Trefferquote {sum(x[2] for x in g) / len(g) * 100:5.1f}%"
              f"  {tage[0]:%m-%d} .. {tage[-1]:%m-%d}  Symbole {len({x[1] for x in g})}")

    print("\n  Merke: unterschiedliche NIVEAUS im selben Zeitraum sind ein")
    print("  Populationsunterschied, kein Zeiteffekt. Genau diese Vermischung")
    print("  hat meine Basislinie von 45 % erzeugt.")

    print("\n" + "=" * 78)
    print("B. Trennpunkt SUCHEN statt setzen - Max-Statistik je Population")
    print("=" * 78)
    rnd = random.Random(20260805)
    for name, g in gesammelt.items():
        for label, teil in (("alle", g), ("nur LONG", [x for x in g if x[3] == "LONG"])):
            if len(teil) < 2 * MIN_JE_SEITE:
                print(f"  {name} / {label:9s}: n={len(teil)} zu klein "
                      f"(mindestens {2 * MIN_JE_SEITE} noetig)")
                continue
            (diff, k, na, nb), p = max_statistik(teil, rnd=rnd)
            if k is None:
                print(f"  {name} / {label:9s}: kein bewertbarer Trennpunkt")
                continue
            urteil = "SIGNIFIKANT" if p is not None and p < 0.05 else "nicht signifikant"
            print(f"  {name:26s} / {label:9s} bester Schnitt {k:%m-%d}  "
                  f"{diff * 100:+6.1f} pp  (n {na}/{nb})  p={p:.4f}  {urteil}")

    print("\n" + "=" * 78)
    print("C. Gegenprobe: was passiert an den beiden Verdachtstagen?")
    print("=" * 78)
    for name, g in gesammelt.items():
        if len(g) < 2 * MIN_JE_SEITE:
            continue
        for k in (datetime(2026, 7, 29), datetime(2026, 8, 2)):
            a = [y for t, _, y, _ in g if t < k]
            b = [y for t, _, y, _ in g if t >= k]
            if len(a) < MIN_JE_SEITE or len(b) < MIN_JE_SEITE:
                continue
            print(f"  {name:26s} Schnitt {k:%d.%m.}: "
                  f"{sum(a) / len(a) * 100:5.1f}% (n={len(a):3d}) -> "
                  f"{sum(b) / len(b) * 100:5.1f}% (n={len(b):3d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
