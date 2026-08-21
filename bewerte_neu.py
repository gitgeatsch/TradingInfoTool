"""Alles noch einmal - zu zwei Gebuehrensaetzen (20.08.2026, Umbauplan 119)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER FEHLER, DER ACHTZEHN KAPITEL DURCHZOGEN HAT. Jedes Urteil der Kapitel
99-118 lief ueber den "Abstand zum Breakeven" - und der Breakeven enthaelt die
Gebuehr. Gerechnet wurde durchgehend mit 1,5 % je Seite, also mit Bitpandas
BROKERSPREAD.

    Nutzer, 20.08.: *"Die Kalkulation SOLL und MUSS boersenunabhaengig
    passieren. Ich rede die ganze Zeit von einem GUTEN TRADE = Kurs &
    Wahrscheinlichkeit - das Gebuehrenthema ist NICHT das Thema eines
    NEUTRALEN Trades."*

⚠️ UND DIE FOLGE IST GROESSER ALS EIN VORZEICHEN. Die Huerde haengt ueber
`Kosten_R = 2 x Gebuehr / Stopabstand` am Stopabstand - und zwar umso
staerker, je hoeher die Gebuehr:

    Gebuehr je Seite     Huerdenunterschied Stop 10 % gegen 29 %
    1,50 %                6,6 Punkte
    0,30 %                1,3 Punkte
    0,10 %                0,4 Punkte

Der "ATR-Kanal", der in den Kapiteln 100, 101, 102, 111, 113 und 116 FUENFMAL
unter neuem Namen auftauchte und jeden Befund verschluckt hat, ist damit zu
grossen Teilen KEIN Marktphaenomen, sondern ein Gebuehrenphaenomen. Er wandert
mit dem Satz, nicht mit dem Markt.

WAS HIER GERECHNET WIRD - EIN DURCHLAUF, ZWEI SPALTEN:

    Referenz 0,30 %   "Ist das ein guter Trade?" - boersenunabhaengig,
                      hergeleitet aus veroeffentlichten Taker-Gebuehren
                      (Bitpanda Pro 0,15 · Bitvavo 0,25 · Kraken 0,40 ->
                      Mittel 0,27, plus rund 0,03 Slippage).
    Betrieb 1,50 %    "Rechnet sich das fuer mich?" - Bitpandas Spread.

⚠️ BEIDE IMMER NEBENEINANDER. Ein Ergebnis ohne sein reales Gegenstueck laedt
zur Fehldeutung ein; laufen die Spalten auseinander, IST das die Aussage.

⚠️ UND DIE ZAEHLUNG IST GEBUEHRENFREI. `sammle` zaehlt Ausgaenge; die Gebuehr
geht erst in `abstand` ein. Ein Durchlauf reicht deshalb fuer beide Saetze -
und die Zahlen sind garantiert dieselben Faelle, nicht zwei Stichproben.

DIE FRAGEN, VORAB FESTGELEGT:

    N1  Wie gross ist der ATR-Kanal je Satz - also wie viel der
        Geometriewirkung aus Kapitel 101 war die Gebuehr?
    N2  Wo steht die BASIS im Betriebszustand (k=2,0/CRV=2,0/120 Tage) je
        Satz? Das ist die Ausgangslage ohne jeden Filter.
    N3  Wo steht H dort - und wie gross ist sein Vorsprung GEBUEHRENFREI
        (reine Quotendifferenz)?
    N4  Haelt dieser Vorsprung ausserhalb der eigenen Daten (Symbolteilung
        wie 118)?

    python bewerte_neu.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                           # noqa: E402
from messe_dosis import (CRV_WERTE, K_WERTE,                     # noqa: E402
                         MIN_FAELLE, sammle)
from simuliere_bremse import SAETZE_ZUM_BERICHTEN                # noqa: E402

BETRIEB = (2.0, 2.0, 120)     # k, CRV, Horizont - der Zustand des Systems


def _quote(rz, maske, hz) -> tuple[int, float]:
    """Vorsichtige Lesart (2.54): ein Ablauf zaehlt als Fehlschlag."""
    n = int(maske.sum())
    if n < MIN_FAELLE:
        return n, float("nan")
    return n, int((maske & (rz["aus"] == 1) & (rz["tg"] <= hz)).sum()) / n


def _abstand(quote, stop_rel, crv, satz) -> float:
    return quote - TB.breakeven(2 * satz / stop_rel, crv)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--datei", default="messwerte_neubewertung.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("ALLES NOCH EINMAL - zu zwei Gebuehrensaetzen")
    print("  Ein Durchlauf, zwei Spalten. Die Zaehlung ist gebuehrenfrei;")
    print("  die Gebuehr geht erst in die Bewertung ein.")
    print("=" * 78)
    _z, stops, roh = sammle(a.db, a.klasse)
    bel = roh[(K_WERTE[0], CRV_WERTE[0])]
    print(f"  {len(bel['r'])} Anker je Geometrie, "
          f"{int(bel['h'].sum())} davon in H")

    # ---- N1: WIE GROSS IST DER ATR-KANAL JE SATZ? -----------------------
    print("\n" + "-" * 78)
    print("N1 - DER ATR-KANAL: wie viel Geometriewirkung ist die Gebuehr?")
    print("-" * 78)
    print(f"  {'Satz':18}" + "".join(f"{f'k={k}':>10}" for k in K_WERTE)
          + f"{'Spanne':>10}")
    n1 = {}
    for name, satz in SAETZE_ZUM_BERICHTEN:
        werte = []
        for k in K_WERTE:
            rz = roh[(k, 2.0)]
            n, q = _quote(rz, np.ones(len(rz["r"]), bool), 120)
            werte.append(_abstand(q, stops["alle"][k], 2.0, satz))
        n1[name] = {"je_k": werte, "spanne": max(werte) - min(werte)}
        print(f"  {name:18}" + "".join(f"{100 * w:+9.1f}" for w in werte)
              + f"{100 * (max(werte) - min(werte)):9.1f}")
    print("\n  ⚠️ Die Spanne IST der Kanal. Er schrumpft mit dem Satz -")
    print("     also war er zum grossen Teil nie ein Marktphaenomen.")

    # ---- N2 + N3: DER BETRIEBSZUSTAND -----------------------------------
    k, crv, hz = BETRIEB
    rz = roh[(k, crv)]
    alle = np.ones(len(rz["r"]), bool)
    n_a, q_a = _quote(rz, alle, hz)
    n_h, q_h = _quote(rz, rz["h"], hz)
    n_r, q_r = _quote(rz, ~rz["h"], hz)
    sr_a, sr_h = stops["alle"][k], float(np.median(stops["h"][(k, crv)]))
    print("\n" + "-" * 78)
    print(f"N2/N3 - BETRIEBSZUSTAND k={k}, CRV={crv}, {hz} Tage")
    print("-" * 78)
    print(f"  {'':22}{'Faelle':>10}{'Quote':>10}"
          + "".join(f"{n:>18}" for n, _s in SAETZE_ZUM_BERICHTEN))
    for etikett, n, q, sr in (("alle Anker", n_a, q_a, sr_a),
                              ("H", n_h, q_h, sr_h),
                              ("Nicht-H", n_r, q_r, sr_a)):
        zeile = f"  {etikett:22}{n:10}{100 * q:9.1f} %"
        for _nm, satz in SAETZE_ZUM_BERICHTEN:
            zeile += f"{100 * _abstand(q, sr, crv, satz):+17.1f}"
        print(zeile)
    print(f"\n  ⚠️ H's Vorsprung GEBUEHRENFREI (reine Quotendifferenz):"
          f" {100 * (q_h - q_r):+.1f} Punkte")
    print("     Diese Zahl haengt an KEINEM Gebuehrensatz - sie ist die")
    print("     Antwort auf 'Kurs und Wahrscheinlichkeit'.")

    # ---- N4: HAELT DER VORSPRUNG AUSSERHALB DER EIGENEN DATEN? ----------
    print("\n" + "-" * 78)
    print("N4 - SYMBOLTEILUNG: gilt der Vorsprung auf FREMDEN Reihen?")
    print("  Gewaehlt wird nichts - die Geometrie ist der Betriebszustand,")
    print("  seit jeher gesetzt. Es gibt also nur eine Pruefseite.")
    print("-" * 78)
    # ⚠️ EIN DENKFEHLER IM AUFBAU, BEIM LESEN DER ERGEBNISSE BEMERKT.
    # Die Symbolteilung haelt eine Haelfte zurueck - aber es gibt hier
    # nichts zurueckzuhalten: die Geometrie ist der BETRIEBSZUSTAND, seit
    # jeher gesetzt und unabhaengig von jedem Ergebnis, und die Bedingung H
    # stammt aus Kapitel 104. Auf der "Waehlseite" wird NICHTS gewaehlt.
    # Damit ist die volle Stichprobe bereits ein gueltiger Test, und die
    # Teilung halbiert nur die Aussagekraft.
    #
    # Berichtet wird deshalb BEIDES: die halbe Stichprobe (konservativ, und
    # sie schliesst zusaetzlich eine Coinwette aus) und die volle, die die
    # eigentliche Frage beantwortet.
    ergebnisse = {}
    for name, pruef in (("halbe Stichprobe (jede zweite Reihe)",
                         (rz["r"] % 2) == 1),
                        ("VOLLE Stichprobe (nichts wurde gewaehlt)",
                         np.ones(len(rz["r"]), bool))):
        print(f"\n  {name}")
        ergebnisse[name] = _pruefe(rz, pruef, hz, a.blockplacebo)
    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "atr_kanal": n1,
            "betrieb": {"quote_alle": q_a, "quote_h": q_h,
                        "quote_rest": q_r, "vorsprung": q_h - q_r},
            "symbolteilung": ergebnisse},
            ensure_ascii=False, indent=1, default=float))
    return 0


def _pruefe(rz, pruef, hz, laeufe) -> dict:
    """Quotendifferenz H gegen Nicht-H auf der Pruefmenge, mit Schwelle."""
    n_hp, q_hp = _quote(rz, pruef & rz["h"], hz)
    n_rp, q_rp = _quote(rz, pruef & ~rz["h"], hz)
    print(f"  H        {n_hp:8} Faelle   Quote {100 * q_hp:5.1f} %")
    print(f"  Nicht-H  {n_rp:8} Faelle   Quote {100 * q_rp:5.1f} %")
    vorsprung = q_hp - q_rp
    print(f"  -> Vorsprung {100 * vorsprung:+.1f} Punkte, gebuehrenfrei")

    # ⚠️ Die Schwelle gilt der QUOTENDIFFERENZ, nicht dem Abstand - sonst
    # steckt die Gebuehr wieder im Urteil (der Fehler dieses Kapitels).
    ordn: dict = {}
    for pos in np.flatnonzero(pruef):
        ordn.setdefault(int(rz["r"][pos]), []).append((int(rz["i"][pos]),
                                                       int(pos)))
    bloecke = []
    for vv in ordn.values():
        gr: list = []
        for ii, pos in sorted(vv):
            if not gr or ii - gr[-1][0] >= 250:
                gr.append([ii, []])
            gr[-1][1].append(pos)
        if len(gr) >= 2:
            bloecke.append([np.array(g[1]) for g in gr])
    rng = np.random.default_rng(20260906)
    zieh = []
    for _lauf in range(laeufe):
        aus, tg = rz["aus"].copy(), rz["tg"].copy()
        for gr in bloecke:
            al = np.concatenate(gr)
            neu = np.concatenate([gr[j] for j in rng.permutation(len(gr))])
            aus[al] = rz["aus"][neu]
            tg[al] = rz["tg"][neu]
        mh, mr = pruef & rz["h"], pruef & ~rz["h"]
        zieh.append(int((mh & (aus == 1) & (tg <= hz)).sum()) / int(mh.sum())
                    - int((mr & (aus == 1) & (tg <= hz)).sum())
                    / int(mr.sum()))
    s = float(np.quantile(zieh, 0.95))
    streu = float(np.std(zieh)) / math.sqrt(len(zieh))
    print(f"  {len(bloecke)} Reihen mit zwei Bloecken, {laeufe} Laeufe")
    print(f"  SCHWELLE (95 %)  {100 * s:+.1f} Punkte")
    print(f"  gemessen         {100 * vorsprung:+.1f} Punkte")
    urteil = ("ZU KNAPP (2.48)" if abs(vorsprung - s) < 2 * streu
              else "TRAEGT" if vorsprung > s else "traegt nicht")
    print(f"  -> {urteil}")
    if urteil == "TRAEGT":
        print("     Es GIBT den besseren Trade, in Kurs und "
              "Wahrscheinlichkeit.")
        print("     Ob er sich RECHNET, entscheidet die Gebuehr (N2/N3).")
    return {"vorsprung": vorsprung, "schwelle": s, "urteil": urteil,
            "n_h": n_hp, "n_rest": n_rp, "bloecke": len(bloecke)}


if __name__ == "__main__":
    raise SystemExit(main())
