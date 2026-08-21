"""Hilft der Strukturboden im Stop - oder schadet er? (20.08.2026, Umbauplan 124)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS - UND EINE KORREKTUR AM EIGENEN GEDAECHTNIS. Im Memory stand die
Asymmetrie ("die Unterstuetzung traegt den Stop nicht") als DRINGEND OFFEN.
An der Quelle nachgesehen ist sie seit dem 18.08.2026 gebaut UND verdrahtet:

    entscheidungsrechnung._boeden()     kennt drei Boeden, der weiteste gewinnt
    rollen_lauf._marke_am_stop()        liest die Unterstuetzung (LONG)
    rollen_lauf.py:1162                 reicht sie als `marke_preis` durch

Der Eintrag war veraltet. Damit stellt sich die naechste Frage, und sie ist
die wichtigere.

⚠️ DENN UNSERE EIGENEN MESSUNGEN SPRECHEN DAGEGEN. Der Strukturboden macht den
Stop WEITER - im Beispiel von 2,50 auf 5,25 ATR. Kapitel 119 hat zum
Referenzsatz gemessen:

    k = 1,5   -1,8        k = 3,0   -2,7
    k = 2,0   -1,5        k = 4,0   -5,2
    k = 2,5   -1,8

Weitere Stops sind bei realistischer Gebuehr SCHLECHTER. Ein Boden, der den
Stop ueber 2,5 ATR hinausschiebt, koennte also aktiv schaden.

⚠️ ABER DER VERGLEICH AUS 119 IST NICHT DIREKT UEBERTRAGBAR. Dort wurde k
EINHEITLICH ueber alle Anker variiert. Der Strukturboden variiert ihn JE ANKER
und abhaengig davon, wo die Marke liegt - das kann besser oder schlechter sein
als eine gleichmaessige Weitung. Genau deshalb wird hier gemessen statt
geschlossen.

DIE FRAGE, VORAB FESTGELEGT:

    Schlaegt der strukturgestuetzte Stop den rein mechanischen - je Anker
    gepaart, in R, nach Kosten?

    besser   -> der Boden bleibt, und Kapitel 119 gilt nur fuer gleichmaessige
                Weitung
    schlechter -> ein gebautes und verdrahtetes Produktionsmerkmal schadet,
                und das gehoert sofort gemeldet

⚠️ GERECHNET WIRD MIT DER PRODUKTIONSFUNKTION. `_stop_abstand` wird
aufgerufen, nicht nachgebaut - sonst misst man eine Kopie, die still veraltet.

⚠️ UND DIE KONTROLLE IST EIN BLOCK-BOOTSTRAP (2.55). Beide Varianten sind
deterministische Umrechnungen desselben Pfades; es gibt keine Zuordnung, die
eine Permutation zerstoeren koennte.

    python pruefe_strukturstop.py [--ziehungen 400]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from agent.entscheidungsrechnung import _stop_abstand            # noqa: E402
from messe_marken import (CRV, MIN_BERUEHRUNGEN,                 # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import (MAX_TAGE, SAETZE_ZUM_BERICHTEN,    # noqa: E402
                              _reihen_roh, klassen_aus_db)

MINDESTALTER = 250
BLOCKLAENGE = 250
VARIANTEN = ("mechanisch", "mit Strukturboden")


def _ausgang(c, h, l, i, stop, ziel) -> float:
    """Vorsichtige Lesart: Stop zuerst, Ablauf gilt als Fehlschlag (2.54)."""
    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
        if l[j] <= stop:
            return -1.0
        if h[j] >= ziel:
            return CRV
    return -1.0


def laufe(db: str, klasse: str) -> list[dict]:
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v, d
        sp = _SwingSpeicher(h, l)
        for i in range(off + 1 + MINDESTALTER, len(c) - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            # Die naechste Unterstuetzung - dieselbe Wahl wie
            # `rollen_lauf._marke_am_stop`: die naechste am Kurs.
            unten = [m["preis"] for m in n["unten"]
                     if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            marke = max(unten) if unten else None
            # ⚠️ DIE PRODUKTIONSFUNKTION, zweimal - einmal ohne Marke,
            # einmal mit. Der Unterschied IST der Strukturboden.
            ab_m, _r1 = _stop_abstand(kurs, atr, None, False, None, None)
            ab_s, regel = _stop_abstand(kurs, atr, None, False, None, marke)
            if ab_m <= 0 or ab_s <= 0 or kurs - ab_s <= 0:
                continue
            r_m = _ausgang(c, h, l, i, kurs - ab_m, kurs + CRV * ab_m)
            r_s = _ausgang(c, h, l, i, kurs - ab_s, kurs + CRV * ab_s)
            aus.append({"sym": sym, "i": i,
                        "r": {"mechanisch": r_m, "mit Strukturboden": r_s},
                        "stop_m": ab_m / kurs, "stop_s": ab_s / kurs,
                        "greift": regel == "jenseits der naechsten Marke"})
        if time.time() - letzte >= 60:
            letzte = time.time()
            print(f"  [{(letzte - t0) / 60:4.1f} min] Reihe {nr}/{len(roh)}"
                  f" - {len(aus)} Anker", flush=True)
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--ziehungen", type=int, default=400)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_strukturstop.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("HILFT DER STRUKTURBODEN IM STOP?")
    print("  Gebaut und verdrahtet seit 18.08. - hier zum ersten Mal")
    print("  gemessen. Gerechnet mit der PRODUKTIONSFUNKTION.")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse)
    greift = [f for f in faelle if f["greift"]]
    print(f"  {len(faelle)} Anker, bei {len(greift)} greift der Boden "
          f"({100 * len(greift) / len(faelle):.1f} %)")
    print(f"\n  Stopabstand im Median")
    print(f"    mechanisch          {100 * float(np.median([f['stop_m'] for f in faelle])):5.1f} %")
    print(f"    mit Strukturboden   {100 * float(np.median([f['stop_s'] for f in faelle])):5.1f} %")
    if greift:
        print(f"    ... wo er greift    "
              f"{100 * float(np.median([f['stop_m'] for f in greift])):5.1f} %"
              f" -> {100 * float(np.median([f['stop_s'] for f in greift])):5.1f} %")

    for titel, menge in (("ALLE ANKER", faelle),
                         ("NUR WO DER BODEN GREIFT", greift)):
        if len(menge) < 300:
            continue
        print("\n" + "-" * 78)
        print(f"{titel} - Erwartungswert je Trade in R")
        print("-" * 78)
        print(f"  {'Variante':22}{'brutto':>10}"
              + "".join(f"{n:>20}" for n, _s in SAETZE_ZUM_BERICHTEN))
        for vv in VARIANTEN:
            brutto = float(np.mean([f["r"][vv] for f in menge]))
            sr = float(np.median([f["stop_m" if vv == "mechanisch"
                                    else "stop_s"] for f in menge]))
            zeile = f"  {vv:22}{brutto:+10.3f}"
            for _n, satz in SAETZE_ZUM_BERICHTEN:
                zeile += f"{brutto - 2.0 * satz / sr:+19.3f}"
            print(zeile)

    # ---- BLOCK-BOOTSTRAP AUF DEN PAARWEISEN DIFFERENZEN (2.55) ----------
    print("\n" + "-" * 78)
    print(f"BLOCK-BOOTSTRAP - {a.ziehungen} Ziehungen, Zeitbloecke mit "
          f"Zuruecklegen")
    print("-" * 78)
    ordn: dict = {}
    for pos, f in enumerate(faelle):
        ordn.setdefault(f["sym"], []).append((f["i"], pos))
    bloecke = []
    for vv2 in ordn.values():
        gr: list = []
        for ii, pos in sorted(vv2):
            if not gr or ii - gr[-1][0] >= a.blocklaenge:
                gr.append([ii, []])
            gr[-1][1].append(pos)
        if len(gr) >= 2:
            bloecke.extend(np.array(g[1]) for g in gr)
    print(f"  {len(bloecke)} Zeitbloecke")
    paar = np.array([f["r"]["mit Strukturboden"] - f["r"]["mechanisch"]
                     for f in faelle])
    rng = np.random.default_rng(20260911)
    zieh = []
    for _lauf in range(a.ziehungen):
        gezogen = np.concatenate(
            [bloecke[j] for j in rng.integers(0, len(bloecke), len(bloecke))])
        zieh.append(float(paar[gezogen].mean()))
    d = float(paar.mean())
    u, o = float(np.quantile(zieh, 0.025)), float(np.quantile(zieh, 0.975))
    print(f"  Strukturboden gegen mechanisch: {d:+.3f} R")
    print(f"  95-%-Intervall [{u:+.3f}, {o:+.3f}]")
    # ⚠️ ZWEI HUERDEN, NICHT EINE (Methodik 2.53). Die erste Fassung urteilte
    # allein am Vertrauensintervall - und meldete bei -0,001 R ein
    # dramatisches "SCHLECHTER". Bei 631.755 Ankern ist fast jeder Effekt
    # statistisch von null verschieden; die Frage ist, ob er REICHT.
    #
    # RELEVANZ ist hier 0,01 R je Trade - ein Fuenfzehntel dessen, was H
    # bringt (+0,15 R). Darunter ist ein Unterschied messbar und bedeutungslos.
    RELEVANZ = 0.01
    if abs(d) < RELEVANZ:
        urteil = f"kein Unterschied von Belang (unter {RELEVANZ:.2f} R)"
    else:
        urteil = ("BESSER" if u > 0 else "SCHLECHTER" if o < 0
                  else "nicht unterscheidbar")
    print(f"  -> {urteil}")
    if abs(d) < RELEVANZ:
        print(f"     Statistisch von null verschieden ({u:+.3f} bis {o:+.3f}),"
              f" wirtschaftlich nicht.")
    elif urteil == "SCHLECHTER":
        print("\n  ⚠️ EIN GEBAUTES UND VERDRAHTETES PRODUKTIONSMERKMAL")
        print("     SCHADET. Das gehoert sofort gemeldet, nicht dokumentiert")
        print("     und liegengelassen.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "anteil_greift": len(greift) / len(faelle), "diff": d,
            "unten": u, "oben": o, "urteil": urteil},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
