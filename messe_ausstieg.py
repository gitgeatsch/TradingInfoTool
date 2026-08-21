"""Der Ausstieg - der letzte unbearbeitete Hebel (20.08.2026, Umbauplan 123)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM. Die Kapitel 104-122 haben ausschliesslich den EINSTIEG geprueft. Der
Nutzer hat mehrfach auf die andere Haelfte hingewiesen, und im Projekt steht
seit dem 04.08. ein Befund, dem nie jemand nachgegangen ist:

    50 % der Trades standen bei +1R - angekommen sind 17,6 %.

Das war auf schmaler Basis gemessen. Wenn es stimmt, ist das ein
AUSSTIEGSproblem, kein Einstiegsproblem - und es verlangt KEINE Prognose,
sondern nur eine Regel fuer das Nachziehen.

⚠️ UND EIN HEBEL, DER AUF ALLE TRADES WIRKT. H feuert auf 2,1 % der Tage; eine
Ausstiegsregel wirkt auf jeden einzelnen Trade.

DIE ZWEI REGELN, VORAB FESTGELEGT - beide ohne jede Prognose:

    A1  TEILVERKAUF   Beruehrt der Kurs +1R, wird die HALBE Position
                      verkauft und der Stop der anderen Haelfte auf den
                      Einstand gezogen.
                      Ergebnis: +0,5 + 0,5 x CRV (Ziel erreicht)
                                +0,5 + 0     (Rest am Einstand raus)
                                -1           (+1R nie beruehrt)

    A2  EINSTANDSTOP  Kein Teilverkauf, aber bei +1R wandert der Stop auf
                      den Einstand.
                      Ergebnis: +CRV (Ziel) · 0 (Einstand) · -1 (davor aus)

⚠️ DIE KOSTEN SIND BEI ALLEN DREI VARIANTEN GLEICH. Ein Teilverkauf teilt die
Ausstiegsmenge, nicht die Summe - bei prozentualen Gebuehren zahlt man auf
dasselbe Volumen. Der Vergleich ist damit sauber; unterschiedliche Kosten
haetten ihn wertlos gemacht.

⚠️ DIE REIHENFOLGE IN DER KERZE IST UNBEKANNT. Faellt in einem Tag beides -
Stop und +1R, oder Einstandstop und Ziel - gilt die VORSICHTIGE Lesart: der
schlechtere Ausgang zaehlt. Das ist dieselbe Regel wie ueberall seit 2.54.

⚠️ UND EIN NICHT ENTSCHIEDENER TRADE zaehlt als Fehlschlag (-1R), nicht als
"kommt nicht vor". Sonst vergleicht man wieder verschiedene Auswahlen.

DIE VORHERSAGE:

    Beide Regeln heben den Erwartungswert gegenueber der Basis - weil viele
    Trades den halben Weg schaffen und dann drehen.

    ⚠️ Sie senken aber auch den Ertrag der Volltreffer. Ob NETTO etwas
    bleibt, ist offen - und genau das ist die Messung.

    python messe_ausstieg.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from messe_marken import (CRV, K, MIN_BERUEHRUNGEN,               # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import (MAX_TAGE, SAETZE_ZUM_BERICHTEN,     # noqa: E402
                              _reihen_roh, klassen_aus_db)

MINDESTALTER = 250
MIN_FAELLE = 300
BLOCKLAENGE = 250
VARIANTEN = ("Basis", "A1 Teilverkauf", "A2 Einstandstop")


def laufe_ausstieg(db: str, klasse: str) -> list[dict]:
    """Je Anker die Ergebnisse ALLER drei Varianten - eine Stichprobe."""
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v, d
        sp = _SwingSpeicher(h, l)
        for i in range(off + 1 + MINDESTALTER, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            stop = einstieg - K * atr
            if stop <= 0:
                continue
            risiko = einstieg - stop
            ziel = einstieg + CRV * risiko
            marke1 = einstieg + risiko          # +1R
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                           and m["preis"] < ziel for m in n["oben"])
            gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                          and m["preis"] > stop for m in n["unten"])
            # ⚠️ EIN Vorwaertsdurchlauf fuer alle drei Varianten - sonst
            # waeren es drei Stichproben statt einer.
            eins_beruehrt = False
            basis = a1 = a2 = None
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                # ⚠️ DIE KERZE, IN DER +1R ZUERST BERUEHRT WIRD, ZAEHLT
                # SCHON ALS AUSGELOEST. Beruehrt dieselbe Kerze auch den
                # Einstand, ist die Reihenfolge unbekannt - die vorsichtige
                # Lesart nimmt den schlechteren Fall an: der nachgezogene
                # Stop hat gegriffen. Die erste Fassung setzte die Marke
                # erst am Kerzenende und rechnete damit zu guenstig.
                ausgeloest = eins_beruehrt or h[j] >= marke1
                if not ausgeloest and l[j] <= stop:
                    basis = a1 = a2 = -1.0
                    break
                if ausgeloest and l[j] <= einstieg:
                    if a1 is None:
                        a1 = 0.5
                    if a2 is None:
                        a2 = 0.0
                if basis is None and l[j] <= stop:
                    basis = -1.0
                if h[j] >= ziel:
                    if basis is None:
                        basis = CRV
                    if a1 is None:
                        a1 = 0.5 + 0.5 * CRV
                    if a2 is None:
                        a2 = CRV
                eins_beruehrt = ausgeloest
                if basis is not None and a1 is not None and a2 is not None:
                    break
            # Nicht entschieden = Fehlschlag (2.54).
            basis = -1.0 if basis is None else basis
            a1 = (0.5 if eins_beruehrt else -1.0) if a1 is None else a1
            a2 = (0.0 if eins_beruehrt else -1.0) if a2 is None else a2
            aus.append({"sym": sym, "i": i, "frei": frei, "gedeckt": gedeckt,
                        "eins": eins_beruehrt,
                        "r": {"Basis": basis, "A1 Teilverkauf": a1,
                              "A2 Einstandstop": a2},
                        "stop_relativ": float(risiko / einstieg)})
        if time.time() - letzte >= 60:
            letzte = time.time()
            print(f"  [{(letzte - t0) / 60:4.1f} min] Reihe {nr}/{len(roh)}"
                  f" - {len(aus)} Anker", flush=True)
    return aus


def _netto(faelle, variante, satz) -> float:
    """Erwartungswert in R nach Kosten - die Kosten sind bei allen gleich."""
    if len(faelle) < MIN_FAELLE:
        return float("nan")
    brutto = float(np.mean([f["r"][variante] for f in faelle]))
    sr = float(np.median([f["stop_relativ"] for f in faelle]))
    return brutto - 2.0 * satz / sr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_ausstieg.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DER AUSSTIEG - Teilverkauf und Einstandstop gegen die Basis")
    print("  Beide Regeln brauchen KEINE Prognose, und sie wirken auf")
    print("  JEDEN Trade - nicht nur auf die 2,1 % mit H.")
    print("=" * 78)
    faelle = laufe_ausstieg(a.db, a.klasse)
    h = [f for f in faelle if f["frei"] and f["gedeckt"]]
    print(f"  {len(faelle)} Anker, davon {len(h)} in H")
    anteil1 = sum(1 for f in faelle if f["eins"]) / len(faelle)
    anteil2 = sum(1 for f in faelle if f["r"]["Basis"] == CRV) / len(faelle)
    print(f"\n  +1R beruehrt:  {100 * anteil1:5.1f} %")
    print(f"  Ziel erreicht: {100 * anteil2:5.1f} %")
    print(f"  -> von denen, die +1R sahen, kamen "
          f"{100 * anteil2 / anteil1:.1f} % an")
    print(f"     (Projektbefund 04.08. auf schmaler Basis: 50 % / 17,6 %)")

    for titel, menge in (("ALLE ANKER", faelle), ("NUR H", h)):
        print("\n" + "-" * 78)
        print(f"{titel} - Erwartungswert je Trade in R")
        print("-" * 78)
        print(f"  {'Variante':20}{'brutto':>10}"
              + "".join(f"{n:>20}" for n, _s in SAETZE_ZUM_BERICHTEN))
        for vv in VARIANTEN:
            brutto = float(np.mean([f["r"][vv] for f in menge]))
            zeile = f"  {vv:20}{brutto:+10.3f}"
            for _n, satz in SAETZE_ZUM_BERICHTEN:
                zeile += f"{_netto(menge, vv, satz):+19.3f}"
            print(zeile)

    # ---- SCHWELLE: IST DER UNTERSCHIED ZUFALL? --------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-BOOTSTRAP - {a.blockplacebo} Ziehungen auf den paarweisen")
    print("  Differenzen. Zeitbloecke werden MIT ZURUECKLEGEN gezogen;")
    print("  gefragt ist, wie genau der Unterschied geschaetzt ist.")
    print("-" * 78)
    ordn: dict = {}
    for pos, f in enumerate(faelle):
        ordn.setdefault(f["sym"], []).append((f["i"], pos))
    bl = []
    for vv2 in ordn.values():
        gr: list = []
        for ii, pos in sorted(vv2):
            if not gr or ii - gr[-1][0] >= a.blocklaenge:
                gr.append([ii, []])
            gr[-1][1].append(pos)
        if len(gr) >= 2:
            bl.append([np.array(g[1]) for g in gr])
    print(f"  {len(bl)} Reihen mit mindestens zwei Bloecken")
    # ⚠️ HIER STAND EINE PERMUTATION, UND SIE WAR DEGENERIERT. Eine
    # Permutation vertauscht Werte - sie aendert den MITTELWERT nicht. Die
    # "Schwelle" kam deshalb auf drei Stellen genau auf den Messwert heraus,
    # und "nicht besser" war keine Aussage, sondern eine Tautologie.
    #
    # Der Grund liegt tiefer als der Programmierfehler: HIER GIBT ES NICHTS
    # ZU PERMUTIEREN. A1 und A2 sind deterministische Umrechnungen DESSELBEN
    # Pfades - es existiert keine zufaellige Zuordnung, die man zerstoeren
    # koennte. Die Frage ist nicht "ist der Unterschied echt", sondern "wie
    # genau ist er geschaetzt".
    #
    # Richtig ist ein BLOCK-BOOTSTRAP auf den PAARWEISEN Differenzen: ganze
    # Zeitbloecke MIT ZURUECKLEGEN ziehen und den Mittelwert bilden.
    # Schliesst das Intervall die Null nicht ein, ist der Unterschied real.
    rng = np.random.default_rng(20260910)
    ergebnis: dict = {}
    bloecke = [np.concatenate(gr) for gr in bl]
    for vv in VARIANTEN[1:]:
        paar = np.array([f["r"][vv] - f["r"]["Basis"] for f in faelle])
        d = float(paar.mean())
        zieh = []
        for _lauf in range(a.blockplacebo):
            gezogen = np.concatenate(
                [bloecke[j] for j in
                 rng.integers(0, len(bloecke), len(bloecke))])
            zieh.append(float(paar[gezogen].mean()))
        u = float(np.quantile(zieh, 0.025))
        o = float(np.quantile(zieh, 0.975))
        ergebnis[vv] = {"diff": d, "unten": u, "oben": o}
        print(f"  {vv:20}{d:+10.3f} R   95-%-Intervall "
              f"[{u:+.3f}, {o:+.3f}]   "
              + ("BESSER" if u > 0 else "SCHLECHTER" if o < 0
                 else "nicht unterscheidbar"))
    print("\n  ⚠️ Block-Bootstrap statt Permutation: A1 und A2 sind")
    print("     deterministische Umrechnungen DESSELBEN Pfades - es gibt")
    print("     keine Zuordnung, die man zerstoeren koennte.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "anteil_1r": anteil1, "anteil_ziel": anteil2,
            "vergleich": ergebnis,
            "netto": {f"{t}|{vv}|{s}": _netto(m, vv, s)
                      for t, m in (("alle", faelle), ("H", h))
                      for vv in VARIANTEN
                      for _n, s in SAETZE_ZUM_BERICHTEN}},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
