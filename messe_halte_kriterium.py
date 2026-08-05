"""Taugt das `halte_kriterium` etwas? 1.747 Zielpreise, nie ausgewertet (05.08.)

DIE LUECKE steht in der Zielgroessen-Doku, Messkette Stufe 6: "halte_kriterium
wird GESETZT, aber nie gegen den Verlauf ausgewertet". Das Modell benennt bei
fast jedem HALTEN, unter welcher Bedingung es seine Meinung aendern wuerde -
ein Zielpreis, teils mit Datum. Ob diese Bedingungen jemals eintraten und ob
sie etwas taugen, wurde nie gemessen.

WAS GEPRUEFT WIRD, in dieser Reihenfolge:

  1. IST DIE BEDINGUNG UEBERHAUPT ERREICHBAR? Ein Zielpreis 40 % entfernt ist
     bei zwei Wochen Frist eine Formalie, keine Bedingung. Gemessen wird der
     Abstand zum Kurs am Signaltag - eine Verteilung nahe null wuerde
     bedeuten, dass das Kriterium trivial erfuellt wird, eine weit entfernte,
     dass es nie greift. Beides waere gleich wertlos.

  2. WURDE SIE ERREICHT, und wie schnell im Verhaeltnis zur Frist? Die Frist
     steckt im `halte_kriterium_bucket` (kurz/mittel/lang = 14/45/120 Tage);
     nur ein Fuenftel der Signale traegt zusaetzlich ein explizites Datum.

  3. TRENNT SIE? Das ist die eigentliche Frage. Wenn das Erreichen des
     Kriteriums nichts ueber den weiteren Verlauf sagt, ist es Dekoration -
     dann waere es der SECHSTE Selektionsmechanismus in Folge ohne Nachweis
     (nach Screening-Score, Konfidenz, Richtungswahl, Prompt-Aenderungen und
     den CRV-Baendern).

EINSCHRAENKUNG, die vorweg gehoert: die Daten reichen bis 10.07. zurueck, das
sind knapp vier Wochen. Nur der "kurz"-Bucket (14 Tage) ist damit vollstaendig
bewertbar. "mittel" (45 Tage) ist strukturell unvollstaendig, "lang" (120
Tage) gar nicht bewertbar - deren Zahlen sind Zwischenstaende, keine
Ergebnisse, und werden entsprechend gekennzeichnet.

KEIN VORAUSSCHAUEN: bewertet wird ausschliesslich der Verlauf NACH dem
Signaltag.

ERGEBNIS (05.08.), drei Befunde - zwei davon strukturell:

1. DIE FRIST MACHT DAS KRITERIUM UNPRUEFBAR. Das Modell waehlt fast immer
   "mittel" (45 Tage): 713 von 830 bei Hebel, 554 von 616 bei Spot. Die
   Datentiefe betraegt aber rund 26 Tage - vollstaendig beobachtet sind damit
   19 Hebel- und 3 Spot-Faelle. Das Kriterium setzt sich selbst eine Frist,
   die unsere gesamte Historie ueberschreitet.

2. DAS KRITERIUM IST EINSEITIG. Bei Spot liegt der Zielpreis in 96 % der
   Faelle UEBER dem aktuellen Kurs, bei Hebel in 89 %. Es beschreibt also fast
   immer, wann man Gewinne mitnimmt - praktisch nie, wann eine These
   gescheitert ist. Als "Bedingung, unter der ich meine Meinung aendere" ist
   das die halbe Antwort.

3. ES TRENNT NICHT NACHWEISBAR. Statt auf die 45-Tage-Frist zu warten (der
   stehenden Vorgabe folgend, nicht mit "zu wenig n" abzuschliessen), wurden
   ALLE Faelle einheitlich auf 14 Tage ausgewertet:
       Hebel  erreicht n= 54  Verlauf +0,12 %   nicht erreicht n=216  -5,22 %
              Differenz +5,34 pp, Bootstrap [-2,48 ; +10,04]
       Spot   erreicht n= 45  Verlauf -2,80 %   nicht erreicht n=254  -5,12 %
              Differenz +2,32 pp, Bootstrap [-1,77 ; +6,44]
   Beide Intervalle schliessen null ein. Die Richtung stimmt zwar (erreichte
   Kriterien gehen mit besserem Verlauf einher), aber der Nachweis fehlt.

   Damit ist es der SECHSTE gepruefte Mechanismus in Folge ohne Nachweis -
   nach Screening-Score, Konfidenz, Richtungswahl, Prompt-Aenderungen und den
   CRV-Baendern.

ERREICHT WIRD DAS ZIEL binnen 14 Tagen in 20 % (Hebel) bzw. 15 % (Spot) der
Faelle, im Median nach 4-5 Tagen. Der Median-Abstand betraegt 12,8 % bzw.
17,3 % - die Bedingung ist also weder trivial noch unerreichbar.

WIEDERVORLAGE: der 45-Tage-Bucket wird ab etwa Mitte September vollstaendig
bewertbar. Bis dahin bleibt die 14-Tage-Auswertung der belastbarere Zugang.

Lauf: python -u messe_halte_kriterium.py
"""
from __future__ import annotations

import io
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime

from backtest_llm1_historisch import lade_reihen
from datiere_einbruch import ORDNER

# Fristen je Bucket, aus dem Regelwerk (halte_kriterium_bucket).
FRIST_TAGE = {"kurz": 14, "mittel": 45, "lang": 120}
# Was ist mit den vorhandenen Daten ueberhaupt vollstaendig bewertbar?
DATENTIEFE_TAGE = 26


def sammle(signale, reihen, index):
    raus = []
    verworfen = Counter()
    for s in signale:
        ziel = s.get("halte_kriterium_ziel_preis_usd")
        if not isinstance(ziel, (int, float)) or ziel <= 0:
            verworfen["kein Zielpreis"] += 1
            continue
        sym = s.get("symbol")
        reihe = reihen.get(sym)
        if not reihe:
            verworfen["keine Kursreihe"] += 1
            continue
        tag = str(s.get("created_at") or "")[:10]
        i = index[sym].get(tag)
        if i is None:
            verworfen["Signaltag nicht in der Reihe"] += 1
            continue
        start = reihe[i].close
        if not start or start <= 0:
            verworfen["kein Startkurs"] += 1
            continue
        bucket = str(s.get("halte_kriterium_bucket") or "?")
        frist = FRIST_TAGE.get(bucket)
        if frist is None:
            verworfen["Bucket unbekannt"] += 1
            continue
        verfuegbar = len(reihe) - i - 1
        # Erreichen: der Zielpreis liegt entweder ueber oder unter dem
        # Startkurs - die Richtung ergibt sich aus dem Ziel selbst, das
        # Kriterium sagt nicht "steigt" oder "faellt", sondern nennt einen Kurs.
        nach_oben = ziel > start
        fenster = reihe[i + 1:i + 1 + frist]
        erreicht_am = None
        for versatz, k in enumerate(fenster, start=1):
            if (k.high >= ziel) if nach_oben else (k.low <= ziel):
                erreicht_am = versatz
                break
        # Weiterer Verlauf ab dem Signaltag, fuer die Trennschaerfe-Frage
        h = min(14, verfuegbar)
        weiter = ((reihe[i + h].close - start) / start * 100) if h > 0 else None
        raus.append({
            "symbol": sym, "tag": tag, "bucket": bucket, "frist": frist,
            "abstand_pct": (ziel - start) / start * 100,
            "nach_oben": nach_oben,
            "erreicht": erreicht_am is not None,
            "erreicht_nach_tagen": erreicht_am,
            "beobachtet_tage": min(verfuegbar, frist),
            "vollstaendig": verfuegbar >= frist,
            "verlauf_14t_pct": weiter,
            "action": str(s.get("action") or "?"),
        })
    return raus, verworfen


def block_bootstrap_anteil(daten, ziehungen=8000, seed=13):
    blk = defaultdict(list)
    for z in daten:
        blk[z["symbol"]].append(1 if z["erreicht"] else 0)
    b = list(blk.values())
    rnd = random.Random(seed)
    werte = []
    for _ in range(ziehungen):
        x = [w for _ in b for w in rnd.choice(b)]
        if x:
            werte.append(sum(x) / len(x))
    werte.sort()
    return werte[int(.025 * len(werte))], werte[int(.975 * len(werte))], len(b)


def auswerten(name, daten):
    print("\n" + "=" * 78)
    print(name)
    print("=" * 78)
    if not daten:
        print("  keine Faelle")
        return

    print("1. IST DIE BEDINGUNG ERREICHBAR? Abstand des Zielpreises zum Kurs am Signaltag")
    ab = sorted(abs(z["abstand_pct"]) for z in daten)
    print(f"   n={len(ab)}  Median {statistics.median(ab):5.1f} %  "
          f"p25 {ab[len(ab) // 4]:5.1f} %  p75 {ab[3 * len(ab) // 4]:5.1f} %  "
          f"Max {ab[-1]:6.1f} %")
    oben = sum(1 for z in daten if z["nach_oben"])
    print(f"   Ziel liegt ueber dem Kurs: {oben * 100 // len(daten)} %,  darunter: "
          f"{(len(daten) - oben) * 100 // len(daten)} %")

    print("\n2. WURDE SIE ERREICHT? (nur vollstaendig beobachtete Faelle zaehlen)")
    print(f"   {'Bucket':10s}{'Frist':>7s}{'n gesamt':>10s}{'davon vollst.':>15s}"
          f"{'erreicht':>10s}{'Median Tage':>13s}")
    for bucket in ("kurz", "mittel", "lang"):
        teil = [z for z in daten if z["bucket"] == bucket]
        if not teil:
            continue
        voll = [z for z in teil if z["vollstaendig"]]
        err = [z for z in voll if z["erreicht"]]
        tage = [z["erreicht_nach_tagen"] for z in err]
        anteil = f"{len(err) / len(voll) * 100:8.0f}%" if voll else "       -"
        md = f"{statistics.median(tage):11.1f}" if tage else "          -"
        print(f"   {bucket:10s}{FRIST_TAGE[bucket]:7d}{len(teil):10d}{len(voll):15d}"
              f"{anteil}{md}")
    unvoll = [z for z in daten if not z["vollstaendig"]]
    if unvoll:
        print(f"   HINWEIS: {len(unvoll)} von {len(daten)} Faellen sind noch nicht")
        print(f"   vollstaendig beobachtet - die Datentiefe betraegt nur rund "
              f"{DATENTIEFE_TAGE} Tage.")

    voll = [z for z in daten if z["vollstaendig"]]
    if len(voll) >= 30:
        u, o, nsym = block_bootstrap_anteil(voll)
        q = sum(1 for z in voll if z["erreicht"]) / len(voll)
        print(f"\n   Erreichungsquote gesamt {q * 100:.0f} %  "
              f"95%-Intervall [{u * 100:.0f} , {o * 100:.0f}]  {nsym} Symbole")

    print("\n3. TRENNT DAS KRITERIUM? Verlauf 14 Tage nach dem Signal")
    a = [z for z in voll if z["erreicht"] and z["verlauf_14t_pct"] is not None]
    b = [z for z in voll if not z["erreicht"] and z["verlauf_14t_pct"] is not None]
    if len(a) < 15 or len(b) < 15:
        print(f"   zu wenige Faelle je Gruppe (erreicht {len(a)}, nicht erreicht {len(b)})")
        return
    ma, mb = (statistics.fmean([z["verlauf_14t_pct"] for z in a]),
              statistics.fmean([z["verlauf_14t_pct"] for z in b]))
    blk_a, blk_b = defaultdict(list), defaultdict(list)
    for z in a:
        blk_a[z["symbol"]].append(z["verlauf_14t_pct"])
    for z in b:
        blk_b[z["symbol"]].append(z["verlauf_14t_pct"])
    rnd = random.Random(17)
    ba, bb = list(blk_a.values()), list(blk_b.values())
    diffs = []
    for _ in range(8000):
        x = [w for _ in ba for w in rnd.choice(ba)]
        y = [w for _ in bb for w in rnd.choice(bb)]
        if x and y:
            diffs.append(statistics.fmean(x) - statistics.fmean(y))
    diffs.sort()
    u, o = diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))]
    urteil = ("TRENNT" if u > 0 or o < 0 else "trennt NICHT nachweisbar")
    print(f"   Kriterium erreicht     n={len(a):4d}  Verlauf {ma:+6.2f} %")
    print(f"   Kriterium NICHT erreicht n={len(b):4d}  Verlauf {mb:+6.2f} %")
    print(f"   Differenz {ma - mb:+.2f} pp   95%-Intervall [{u:+.2f} , {o:+.2f}]   {urteil}")


def main():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    reihen = lade_reihen()
    index = {s: {k.date: i for i, k in enumerate(r)} for s, r in reihen.items()}
    print("=" * 78)
    print("halte_kriterium: 1.747 gesetzte Zielpreise, erstmals gegen den Verlauf geprueft")
    print("=" * 78)
    for name, key in (("HEBEL", "hebel_signals"), ("SPOT", "spot_signals")):
        daten, verworfen = sammle(d[key], reihen, index)
        auswerten(f"{name} - {len(daten)} auswertbare Faelle "
                  f"(verworfen: {dict(verworfen)})", daten)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
