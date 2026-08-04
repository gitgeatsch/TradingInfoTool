"""Welche Score-Komponente traegt? (2026-08-04, Phase 0.1 Auswertung)

DIE FRAGE, die Ebene 1 blockiert. Der Screening-Score diskriminiert nicht
(Event-Study 04.08., nicht-monoton) und korreliert mit dem Ergebnis sogar
-0,200, also invers. Gilt das fuer den Gesamtscore oder nur fuer einzelne
seiner Bestandteile? Ohne `score_details_json` war das nicht entscheidbar -
seit dem Export vom 04.08. 17:23 liegt es vor.

DIE DATENLAGE ist deutlich besser als bisher:
  41.552 Trigger statt 6.412 Kandidaten - der beschnittene Wertebereich, der
  am 02.08. den CRV-Befund entwertet hat, ist weg. 35.140 Nicht-Kandidaten
  sind jetzt Teil der Auswertung.

ZWEI FALLEN, die dabei umgangen werden:

1. SCHEINGENAUIGKEIT DURCH UEBERLAPPUNG. 41.552 Zeilen stammen von 43
   Symbolen ueber 21 Tage - das Screening laeuft mehrmals taeglich, dieselbe
   Symbol-Tag-Kombination erscheint vielfach. Effektiv sind es rund 900
   unabhaengige Symbol-Tage, nicht 41.552 Faelle. Deshalb wird auf
   (Symbol, Tag, Richtung, Zweig) verdichtet, BEVOR gerechnet wird, und die
   Unsicherheit ueber Symbole geblockt.

2. ERGEBNIS OHNE SIGNALE. Nur rund 1.471 Trigger wurden ueberhaupt zu
   Signalen. Statt sich darauf zu beschraenken (und damit erneut selektiert
   zu messen), bekommt JEDER Trigger ein MECHANISCHES Ergebnis: Einstieg zum
   Schlusskurs des Screening-Tages in der vom Trigger genannten Richtung,
   Median-Parameter, dieselbe Fill-Logik wie das Backward-Tracking.

Lauf: python analyse_score_komponenten.py
"""
from __future__ import annotations

import ast
import io
import json
import math
import statistics
import sys
from collections import defaultdict

from agent.krypto.backward_tracking import gap_bewusster_fill

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
STOP_REL, CRV, HORIZONT = 0.0394, 2.6, 14      # Median der echten Signale

KOMPONENTEN = {
    "trendfolge": ["oi_change_pct", "kursaenderung_pct", "funding_rate_aktuell",
                   "konfluenz_bias"],
    "kontra": ["funding_rate_aktuell", "long_konten_anteil_prozent",
               "wende_anzeichen"],
}


def lade():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    reihen = {}
    for q in ("preishistorie_signal_symbole", "preishistorie_ueberholte_symbole"):
        for s, rr in ((d.get(q) or {}).get("preishistorie_je_symbol") or {}).items():
            g = [p for p in (rr or []) if p.get("currency") == "USD"]
            if len(g) > 20:
                kand = sorted(g, key=lambda p: str(p["date"])[:10])
                if len(kand) > len(reihen.get(s, [])):
                    reihen[s] = kand
    return d["rohdaten_fuer_backtest"]["hebel_triggers_alle"], reihen


def mechanisches_ergebnis(reihe, datum: str, ist_short: bool) -> float | None:
    """R-Multiple eines Einstiegs zum Schlusskurs von `datum`."""
    i = next((k for k, p in enumerate(reihe) if str(p["date"])[:10] == datum), None)
    if i is None or i + 2 >= len(reihe):
        return None
    e = reihe[i]["close"]
    if not e or e <= 0:
        return None
    risiko = e * STOP_REL
    stop = e + risiko if ist_short else e - risiko
    ziel = e - risiko * CRV if ist_short else e + risiko * CRV
    for p in reihe[i + 1:i + 2 + HORIZONT]:
        hoch, tief, auf = p["high"], p["low"], p["open"]
        if hoch is None or tief is None:
            continue
        if (hoch >= stop) if ist_short else (tief <= stop):
            fill = gap_bewusster_fill(stop, auf, True, ist_short)
            return ((e - fill) if ist_short else (fill - e)) / risiko
        if (tief <= ziel) if ist_short else (hoch >= ziel):
            fill = gap_bewusster_fill(ziel, auf, False, ist_short)
            return ((e - fill) if ist_short else (fill - e)) / risiko
    letzter = reihe[min(i + 1 + HORIZONT, len(reihe) - 1)]["close"]
    if not letzter:
        return None
    return ((e - letzter) if ist_short else (letzter - e)) / risiko


def spearman(x, y):
    def rg(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        for platz, i in enumerate(s):
            out[i] = platz + 1.0
        return out
    rx, ry = rg(x), rg(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    z = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    n = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return z / n if n else 0.0


def block_intervall(werte_je_symbol: dict, ziehungen: int = 2000):
    """95 %-Intervall des Mittelwerts, ueber Symbole geblockt."""
    import random
    rng = random.Random(20260804)
    syms = list(werte_je_symbol)
    if len(syms) < 4:
        return None, None
    mittel = []
    for _ in range(ziehungen):
        zieh = [werte_je_symbol[rng.choice(syms)] for _ in syms]
        flach = [v for w in zieh for v in w]
        if flach:
            mittel.append(statistics.fmean(flach))
    if not mittel:
        return None, None
    mittel.sort()
    return mittel[int(0.025 * len(mittel))], mittel[int(0.975 * len(mittel))]


def main() -> int:
    alle, reihen = lade()
    print("=" * 78)
    print("WELCHE SCORE-KOMPONENTE TRAEGT?")
    print("=" * 78)
    print(f"{len(alle)} Trigger, {len(reihen)} Symbole mit Kursreihe")

    # --- Verdichten auf (Symbol, Tag, Richtung, Zweig) ---------------------
    eimer: dict[tuple, list[dict]] = defaultdict(list)
    for x in alle:
        try:
            det = ast.literal_eval(x["score_details_json"])
        except Exception:
            continue
        eimer[(x["symbol"], str(x["screened_at"])[:10], x["richtung"],
               x["trigger_zweig"])].append({**det, "score_gesamt": x["score_gesamt"]})
    print(f"nach Verdichtung auf (Symbol, Tag, Richtung, Zweig): {len(eimer)} Faelle")
    print("  (die 41.552 Zeilen ueberlappen stark - das Screening laeuft")
    print("   mehrmals taeglich auf denselben Symbolen)")

    faelle = []
    for (sym, tag, richtung, zweig), liste in eimer.items():
        if sym not in reihen:
            continue
        r = mechanisches_ergebnis(reihen[sym], tag, richtung == "SHORT")
        if r is None:
            continue
        eintrag = {"sym": sym, "tag": tag, "zweig": zweig, "r": r}
        for k in set().union(*(set(x) for x in liste)):
            werte = [x[k] for x in liste if isinstance(x.get(k), (int, float))
                     and not isinstance(x.get(k), bool)]
            if werte:
                eintrag[k] = statistics.median(werte)
            else:
                texte = [str(x.get(k)) for x in liste if x.get(k) is not None]
                if texte:
                    eintrag[k] = max(set(texte), key=texte.count)
        faelle.append(eintrag)

    print(f"mit mechanischem Ergebnis: {len(faelle)}")
    if len(faelle) < 100:
        print("zu wenig - Abbruch")
        return 1
    print(f"Gesamt-EW: {statistics.fmean([f['r'] for f in faelle]):+.4f} R")

    for zweig, komps in KOMPONENTEN.items():
        teil = [f for f in faelle if f["zweig"] == zweig]
        if len(teil) < 50:
            print(f"\n--- {zweig}: nur {len(teil)} Faelle, uebersprungen")
            continue
        print()
        print("=" * 78)
        print(f"ZWEIG {zweig.upper()}   {len(teil)} Faelle, "
              f"{len(set(f['sym'] for f in teil))} Symbole")
        print("=" * 78)
        print(f"{'Komponente':28s} {'n':>6s} {'rho':>7s} {'Q1 EW':>8s} {'Q4 EW':>8s} "
              f"{'Q4-Q1':>8s} {'95%-Intervall':>20s}")
        for k in komps + ["score_gesamt"]:
            g = [f for f in teil if isinstance(f.get(k), (int, float))
                 and not isinstance(f.get(k), bool)]
            if len(g) < 50:
                # kategorisch
                kat = defaultdict(list)
                for f in teil:
                    if f.get(k) is not None:
                        kat[str(f[k])].append(f["r"])
                if kat:
                    teile = "  ".join(f"{a}:{statistics.fmean(b):+.3f}({len(b)})"
                                      for a, b in sorted(kat.items()))
                    print(f"{k:28s} {'kategorisch':>6s}   {teile}")
                continue
            g.sort(key=lambda f: f[k])
            q = len(g) // 4
            q1 = statistics.fmean([f["r"] for f in g[:q]])
            q4 = statistics.fmean([f["r"] for f in g[-q:]])
            rho = spearman([f[k] for f in g], [f["r"] for f in g])
            # Blockintervall auf die Differenz Q4-Q1
            je_sym = defaultdict(list)
            for f in g[-q:]:
                je_sym[f["sym"]].append(f["r"])
            for f in g[:q]:
                je_sym[f["sym"]].append(-f["r"])
            u, o = block_intervall(je_sym)
            iv = (f"[{u:+.3f}, {o:+.3f}]" if u is not None else "—")
            marke = "  <--" if u is not None and (u > 0 or o < 0) else ""
            print(f"{k:28s} {len(g):6d} {rho:+7.3f} {q1:+8.3f} {q4:+8.3f} "
                  f"{q4-q1:+8.3f} {iv:>20s}{marke}")

    print()
    print("Lesart: <-- markiert Komponenten, deren symbolgeblocktes")
    print("95%-Intervall die Null ausschliesst. Nur die tragen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
