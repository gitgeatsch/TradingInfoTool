"""Die Frage EINMAL richtig gestellt (20.08.2026, Umbauplan 118)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WAS 117 UEBRIG GELASSEN HAT. Die beste Zelle lag bei +4,5 Punkten, die
Schwelle fuer das Maximum aus 60 abgesuchten Zellen bei +4,7 - verfehlt um
0,2. Die Huerdenrechnung zeigte: bei EINER vorab benannten Zelle haette die
Schwelle bei +3,7 gelegen. Das Absuchen hat 1,0 Punkte gekostet.

⚠️ UND DIE VERSUCHUNG IST OFFENSICHTLICH. Die Zelle jetzt nachtraeglich zur
"vorab benannten" zu erklaeren, waere zirkulaer - genau der Fehler, gegen den
Methodik 2.49 gebaut ist. Diese Messung tut das ausdruecklich NICHT.

DER SAUBERE WEG STATTDESSEN: die Geometrie wird auf einem Teil der Daten
GEWAEHLT und auf einem anderen GEPRUEFT. Dort ist Suchen erlaubt, hier zaehlt
nur das Ergebnis - und die Schwelle ist die fuer EINE Zelle, weil auf der
Pruefseite nichts mehr gesucht wird.

ZWEI TEILUNGEN, weil sie verschiedene Fehler ausschliessen:

    ZEIT      Waehlen auf der ersten Haelfte, Pruefen auf der zweiten.
              ⚠️ Puffer von 250 Tagen dazwischen - ein Anker kurz vor der
              Trennlinie hat sein Vorwaertsfenster jenseits davon.
              Schliesst aus: dass die Regel nur in EINER Marktepoche gilt.
              Schwaeche: die Haelften sind verschiedene Regime (Kapitel 109
              mass 69,6 % Bulle gegen 12,4 %).

    SYMBOL    Waehlen auf der einen Haelfte der Reihen, Pruefen auf der
              anderen. Beide Haelften decken DENSELBEN Zeitraum ab.
              Schliesst aus: dass die Regel an einzelnen Werten haengt.
              Schwaeche: alle Coins laufen gleichzeitig durch dieselben
              Regime - der Test ist der schwaechere.

    ⚠️ BEIDE zusammen sind aussagekraeftig, weil ihre Schwaechen verschieden
    sind. Stimmen sie ueberein, ist das ein Beleg; widersprechen sie sich,
    sagt uns die Art des Widerspruchs, welcher Fehler wirkt.

DAS URTEIL, VORAB FESTGELEGT:

    Gemessen wird der Abstand von H zum eigenen Breakeven auf der
    PRUEFseite, in der VORSICHTIGEN Lesart (Ablauf = Fehlschlag, 2.54),
    gegen die Ein-Zellen-Schwelle aus der Block-Permutation.

    Es gibt KEINE zweite Runde. Was hier herauskommt, steht.

    python messe_dosis_sauber.py [--blockplacebo 200]
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
from messe_dosis import (CRV_WERTE, HORIZONTE, K_WERTE,          # noqa: E402
                         MIN_FAELLE, sammle)
from simuliere_bremse import gebuehr_je_seite                    # noqa: E402

PUFFER_TAGE = 250      # >= laengster Horizont, sonst sickert die Antwort


def _abstand(rz, maske, k, crv, hz, stops, klasse) -> tuple[int, float]:
    """Vorsichtige Lesart: ein Ablauf zaehlt als Fehlschlag (2.54)."""
    m = maske & rz["h"]
    n = int(m.sum())
    if n < MIN_FAELLE:
        return n, float("nan")
    treffer = int((m & (rz["aus"] == 1) & (rz["tg"] <= hz)).sum())
    sr = (float(np.median(stops["h"][(k, crv)]))
          if stops["h"].get((k, crv)) else stops["alle"][k])
    return n, treffer / n - TB.breakeven(
        2 * gebuehr_je_seite(klasse) / sr, crv)


def _waehle(roh_zellen, maske_je, stops, klasse):
    """Die Geometrie auf der WAEHLseite - hier IST Suchen erlaubt."""
    top = (None, -99.0, 0)
    for (k, crv), rz in roh_zellen.items():
        for hz in HORIZONTE:
            n, ab = _abstand(rz, maske_je[(k, crv)], k, crv, hz, stops,
                             klasse)
            if ab == ab and ab > top[1]:
                top = ((k, crv, hz), ab, n)
    return top


def _schwelle(rz, maske, k, crv, hz, stops, klasse, laeufe, rng) -> tuple:
    """Ein-Zellen-Schwelle: auf der Pruefseite wird NICHTS mehr gesucht."""
    idx = np.flatnonzero(maske)
    if len(idx) < MIN_FAELLE:
        return float("nan"), float("nan"), 0
    ordn: dict = {}
    for pos in idx:
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
    if not bloecke:
        return float("nan"), float("nan"), 0
    sr = (float(np.median(stops["h"][(k, crv)]))
          if stops["h"].get((k, crv)) else stops["alle"][k])
    be = TB.breakeven(2 * gebuehr_je_seite(klasse) / sr, crv)
    werte = []
    for _lauf in range(laeufe):
        aus, tg = rz["aus"].copy(), rz["tg"].copy()
        for gr in bloecke:
            alle = np.concatenate(gr)
            neu = np.concatenate([gr[j] for j in rng.permutation(len(gr))])
            aus[alle] = rz["aus"][neu]
            tg[alle] = rz["tg"][neu]
        m = maske & rz["h"]
        if m.sum() < MIN_FAELLE:
            continue
        treffer = int((m & (aus == 1) & (tg <= hz)).sum())
        werte.append(treffer / int(m.sum()) - be)
    if not werte:
        return float("nan"), float("nan"), len(bloecke)
    return (float(np.quantile(werte, 0.95)),
            float(np.std(werte)) / math.sqrt(len(werte)), len(bloecke))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--datei", default="messwerte_dosis_sauber.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DIE FRAGE EINMAL RICHTIG GESTELLT")
    print("  Geometrie WAEHLEN auf dem einen Teil, PRUEFEN auf dem anderen.")
    print("  Keine zweite Runde - was herauskommt, steht.")
    print("=" * 78)
    _z, stops, roh_zellen = sammle(a.db, a.klasse)
    bel = roh_zellen[(K_WERTE[0], CRV_WERTE[0])]
    print(f"  {len(bel['r'])} Anker je Geometrie, "
          f"{int(bel['h'].sum())} davon in H")

    rng = np.random.default_rng(20260905)
    ergebnis: dict = {}
    for art in ("ZEIT", "SYMBOL"):
        print("\n" + "=" * 78)
        print(f"TEILUNG NACH {art}")
        print("=" * 78)
        waehl_je, pruef_je = {}, {}
        for schl, rz in roh_zellen.items():
            if art == "ZEIT":
                tage = np.unique(rz["t"])
                trenn = tage[len(tage) // 2]
                # ⚠️ PUFFER: Anker, deren Vorwaertsfenster ueber die
                # Trennlinie reicht, gehoeren auf keine Seite.
                grenze = tage[max(0, len(tage) // 2 - PUFFER_TAGE)]
                waehl_je[schl] = rz["t"] < grenze
                pruef_je[schl] = rz["t"] >= trenn
            else:
                waehl_je[schl] = (rz["r"] % 2) == 0
                pruef_je[schl] = (rz["r"] % 2) == 1
        n_w = int(waehl_je[(K_WERTE[0], CRV_WERTE[0])].sum())
        n_p = int(pruef_je[(K_WERTE[0], CRV_WERTE[0])].sum())
        print(f"  waehlen {n_w} Anker   pruefen {n_p} Anker"
              + (f"   ({len(bel['r']) - n_w - n_p} im Puffer verworfen)"
                 if art == "ZEIT" else ""))

        gewaehlt = _waehle(roh_zellen, waehl_je, stops, a.klasse)
        k, crv, hz = gewaehlt[0]
        print(f"\n  GEWAEHLT auf der Waehlseite: k={k}, CRV={crv}, "
              f"{hz} Tage  ({100 * gewaehlt[1]:+.1f} Punkte dort)")

        rz = roh_zellen[(k, crv)]
        n_h, ab_h = _abstand(rz, pruef_je[(k, crv)], k, crv, hz, stops,
                             a.klasse)
        # Die Basis derselben Zelle auf derselben Seite - der faire Bezug.
        m_b = pruef_je[(k, crv)] & ~rz["h"]
        n_b = int(m_b.sum())
        sr = stops["alle"][k]
        be_b = TB.breakeven(2 * gebuehr_je_seite(a.klasse) / sr, crv)
        ab_b = (int((m_b & (rz["aus"] == 1) & (rz["tg"] <= hz)).sum()) / n_b
                - be_b) if n_b >= MIN_FAELLE else float("nan")
        print(f"\n  AUF DER PRUEFSEITE")
        print(f"    H       {n_h:8} Faelle   {100 * ab_h:+6.1f} Punkte")
        print(f"    Basis   {n_b:8} Faelle   {100 * ab_b:+6.1f} Punkte")
        if ab_h == ab_h and ab_b == ab_b:
            print(f"    -> H's Beitrag {100 * (ab_h - ab_b):+.1f} Punkte")

        s1, streu, nb = _schwelle(rz, pruef_je[(k, crv)], k, crv, hz, stops,
                                  a.klasse, a.blockplacebo, rng)
        print(f"\n  EIN-ZELLEN-SCHWELLE ({a.blockplacebo} Laeufe, {nb} Reihen"
              f" mit zwei Bloecken)")
        print(f"    Schwelle   {100 * s1:+6.1f} Punkte")
        print(f"    gemessen   {100 * ab_h:+6.1f} Punkte")
        if ab_h != ab_h or s1 != s1:
            urteil = "zu wenige Faelle"
        elif abs(ab_h - s1) < 2 * streu:
            urteil = "ZU KNAPP (2.48)"
        elif ab_h > s1:
            urteil = "TRAEGT"
        else:
            urteil = "traegt nicht"
        print(f"    -> {urteil}")
        ergebnis[art] = {"zelle": [k, crv, hz], "n_h": n_h, "abstand_h": ab_h,
                         "abstand_basis": ab_b, "schwelle": s1,
                         "urteil": urteil}

    print("\n" + "=" * 78)
    print("BEIDE TEILUNGEN")
    print("=" * 78)
    for art, e in ergebnis.items():
        print(f"  {art:8} k={e['zelle'][0]}, CRV={e['zelle'][1]}, "
              f"{e['zelle'][2]} Tage   {100 * e['abstand_h']:+6.1f} gegen "
              f"{100 * e['schwelle']:+6.1f}   {e['urteil']}")
    if all(e["urteil"] == "TRAEGT" for e in ergebnis.values()):
        print("\n  BEIDE TRAGEN. Das ist der erste Befund des Projekts, der")
        print("  ausserhalb seiner eigenen Daten steht.")
    elif any(e["urteil"] == "TRAEGT" for e in ergebnis.values()):
        print("\n  ⚠️ SIE WIDERSPRECHEN SICH. Die Art des Widerspruchs sagt,")
        print("     welcher Fehler wirkt - Regime oder Auswahl der Werte.")
    else:
        print("\n  KEINE TRAEGT. Damit ist die Frage in ihrer sauberen Form")
        print("  beantwortet, und zwar mit Nein.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            ergebnis, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
