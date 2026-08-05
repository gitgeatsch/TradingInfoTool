"""Sagt Konfidenz etwas vorher - und muessen die Schwellen nach dem Drift neu? (05.08.)

ANLASS. Mistral hat am 31.07. anbieterseitig sein Verhalten geaendert
(nachgewiesen per Replay mit bitgleichem Juli-Prompt: 55,4 % -> 68,0 %
Konfidenz). Die Regime-Mindestschwellen R-5.10 stehen seither auf einer
Verteilung, die es nicht mehr gibt:

    Hebel-Konfidenz   Median   >=70 %   >=75 %
    bis 30.07.          60,0      9 %      5 %
    ab  31.07.          70,0     61 %      5 %

Schwellen: krise_extrem 85, baer 75, seitwaerts 65, bulle 60. Im Baerenregime
filtert 75 unveraendert. Bei einem Wechsel nach seitwaerts (65) liesse das Gate
schlagartig 61 % statt 9 % durch.

METHODE AUS DER DOKU, nicht selbst gewaehlt. Zwei Vorgaben greifen:

  Testmethodik 2.8 (Schwellen-Herleitung): Referenzgroesse -> Verteilung ->
  Herleitung -> NUTZER-FREIGABE vor Operationalisierung. Eine hergeleitete
  Zahl ersetzt die fachliche Freigabe nicht, sie macht sie informierter.

  Dead-Loop-Synthese: die Bucket-Methode braucht reale Power n~340 und ist
  damit "strukturell nicht praktikabel" (~4,5 Monate). Ausdruecklicher
  Alternativvorschlag: "auf den kontinuierlichen Korrelationstest umschwenken
  statt auf Bucket-n zu warten - nutzt alle Datenpunkte gleichzeitig statt
  eines 3-Buckets-Splits."

Deshalb hier KEINE Buckets, sondern die durchgehende Beziehung zwischen
Konfidenz und Ergebnis.

DIE REIHENFOLGE IST NICHT VERHANDELBAR. Zuerst die Frage, ob Konfidenz
ueberhaupt etwas vorhersagt. Faellt das negativ aus, ist jede
Schwellen-Kalibrierung Theater - man verschoebe eine Zahl, die nichts
selektiert. Erst wenn ein Zusammenhang belegt ist, lohnt die Frage, WO die
Schwelle liegen soll.

BRUCHSTELLE 31.07. (Testmethodik 2.1b): jede Auswertung laeuft getrennt fuer
vorher und nachher. Ein gepoolter Wert wuerde zwei Modellzustaende mischen.

BLOCK-BOOTSTRAP UEBER SYMBOLE, wie bei allen Auswertungen dieses Projekts -
zwei Signale desselben Symbols sind keine zwei unabhaengigen Beobachtungen.

Lauf: python -u messe_konfidenz_kalibrierung_neu.py
"""
from __future__ import annotations

import io
import json
import random
import statistics
from collections import defaultdict

from datiere_einbruch import ORDNER

GRENZE = "2026-07-31"
TP, SL = "take_profit_erreicht", "stop_loss_erreicht"
PRAEFIXE = ("", "veto_", "selbst_halten_")


def _ergebnis(s):
    """Ein Ergebnis je Signal, aus der ersten Familie die eines liefert.

    Getrennte Auswertung je Familie waere sauberer (siehe Bruchstellen-
    Tabelle), scheitert hier aber an der Menge: die regulaere Familie hat bei
    Spot nur eine Handvoll aufgeloester Faelle. Der Mischtopf ist hier
    vertretbar, weil die FRAGE (sagt Konfidenz etwas vorher) innerhalb jeder
    Familie dieselbe ist - anders als bei Niveau-Vergleichen."""
    for pre in PRAEFIXE:
        st = str(s.get(pre + "outcome_status") or "")
        if st in (TP, SL):
            crv = s.get(pre + "outcome_realisiertes_crv")
            return (1 if st == TP else 0,
                    float(crv) if isinstance(crv, (int, float)) else None)
    return None, None


def sammle(signale):
    raus = []
    for s in signale:
        k = s.get("confidence_pct")
        if not isinstance(k, (int, float)):
            continue
        treffer, crv = _ergebnis(s)
        if treffer is None:
            continue
        raus.append({
            "symbol": s.get("symbol") or "?",
            "tag": str(s.get("created_at") or "")[:10],
            "konfidenz": float(k), "treffer": treffer, "crv": crv,
        })
    return raus


def korrelation(xs, ys):
    """Spearman-Rangkorrelation - robust gegen die Klumpung der Konfidenz auf
    runden Werten (60/65/70), an der Pearson scheitern wuerde."""
    def raenge(v):
        paare = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(paare):
            j = i
            while j + 1 < len(paare) and v[paare[j + 1]] == v[paare[i]]:
                j += 1
            mittel = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[paare[k]] = mittel
            i = j + 1
        return r
    rx, ry = raenge(xs), raenge(ys)
    n = len(xs)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    zaehler = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    nenner = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return zaehler / nenner if nenner else 0.0


def bootstrap_korrelation(daten, feld, ziehungen=10000, seed=7):
    blk = defaultdict(list)
    for z in daten:
        blk[z["symbol"]].append(z)
    b = list(blk.values())
    rnd = random.Random(seed)
    werte = []
    for _ in range(ziehungen):
        zieh = [x for _ in b for x in rnd.choice(b)]
        xs = [z["konfidenz"] for z in zieh if z[feld] is not None]
        ys = [z[feld] for z in zieh if z[feld] is not None]
        if len(set(xs)) > 1 and len(set(ys)) > 1:
            werte.append(korrelation(xs, ys))
    werte.sort()
    return (werte[int(.025 * len(werte))], werte[int(.975 * len(werte))],
            len(b)) if werte else (float("nan"), float("nan"), len(b))


def auswerten(name, signale):
    daten = sammle(signale)
    print("\n" + "=" * 78)
    print(f"{name}")
    print("=" * 78)
    if not daten:
        print("  keine auswertbaren Faelle")
        return
    for lab, teil in (("bis 30.07.", [z for z in daten if z["tag"] < GRENZE]),
                      ("ab 31.07.", [z for z in daten if z["tag"] >= GRENZE])):
        if len(teil) < 10:
            print(f"  {lab:12s} n={len(teil)} - zu klein")
            continue
        k = [z["konfidenz"] for z in teil]
        print(f"  {lab:12s} n={len(teil):4d}  Symbole={len({z['symbol'] for z in teil}):3d}  "
              f"Konfidenz-Median {statistics.median(k):5.1f}  "
              f"Trefferquote {sum(z['treffer'] for z in teil) / len(teil) * 100:5.1f}%")
        for feld, txt in (("treffer", "Konfidenz -> Treffer"), ("crv", "Konfidenz -> R")):
            xs = [z["konfidenz"] for z in teil if z[feld] is not None]
            ys = [z[feld] for z in teil if z[feld] is not None]
            if len(xs) < 10 or len(set(xs)) < 2:
                continue
            rho = korrelation(xs, ys)
            u, o, nsym = bootstrap_korrelation(teil, feld)
            urteil = ("POSITIV - Konfidenz sagt etwas vorher" if u > 0 else
                      "NEGATIV - hoehere Konfidenz, schlechteres Ergebnis" if o < 0 else
                      "kein Zusammenhang nachweisbar")
            print(f"      {txt:22s} rho={rho:+.3f}  95%-Intervall [{u:+.3f} , {o:+.3f}]"
                  f"  {nsym} Symbole   {urteil}")


def main():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    print("=" * 78)
    print("Sagt die Konfidenz etwas ueber das Ergebnis? (kontinuierlich, keine Buckets)")
    print("=" * 78)
    print("Reihenfolge: erst diese Frage, dann erst die Schwellen. Ohne belegten")
    print("Zusammenhang waere jede Schwellen-Kalibrierung Theater.")
    auswerten("SPOT - hier greift R-5.10 (min_konfidenz_prozent)", d["spot_signals"])
    auswerten("HEBEL - hier greifen nur die Konfidenz-Konstanten", d["hebel_signals"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
