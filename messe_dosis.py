"""Die Dosis: welche Geometrie und welche Dauer braucht H? (Umbauplan 117)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER NUTZERVERGLEICH, der diese Messung ausgeloest hat: *"Nur weil ich nicht
weiss, warum ein Heilmittel hilft, ist das zwar nicht gut - aber wenn ich
weiss, WANN ich es einnehmen soll und WIE LANGE, damit es wirkt, sollte das
reichen."*

⚠️ UND ER TRIFFT EINE LUECKE. Kapitel 115 hat den ZEITPUNKT geprueft und
verworfen. DOSIS und DAUER wurden nie geprueft:

    H wurde in JEDEM Kapitel (104-116) bei genau EINER Geometrie gemessen -
    k = 2,0 und CRV = 2,0. Das ist unser Betriebszustand und laut Kapitel 101
    die SCHLECHTESTE ECKE des ganzen Rasters:

        Basis bei k=2,0 / CRV=2,0     -6,0 Punkte
        Basis bei k=4,0 / CRV=3,0     +0,1 Punkte
        H    bei k=2,0 / CRV=2,0      -0,3 Punkte

    Und die Haltedauer steht ueberall auf MAX_TAGE = 120, nie variiert.

⚠️ WICHTIG: H HAENGT SELBST AN DER GEOMETRIE. A fragt nach Marken zwischen
Kurs und ZIEL, B nach einer Marke ueber dem STOP - beide wandern mit k und
CRV. Die Bedingung wird also je Zelle NEU gebildet, nicht einmal fixiert und
dann durchgereicht. Genau das ist mit "Dosis" gemeint.

DIE FRAGE, VORAB FESTGELEGT - und sie ist NICHT "welche Zelle ist die beste":

    D1  LIEGT H's OPTIMUM WOANDERS als das der Basis?
        gleiche Ecke  -> es ist wieder nur Kostenarithmetik (Kapitel 101),
                         H aendert daran nichts.
        andere Ecke   -> DAS ist die Dosis: H braucht eine andere Geometrie
                         als der Durchschnitt.

    D2  LIEGT H AN SEINEM OPTIMUM UEBER NULL?
        Erst dann waere aus "traegt Information" ein Trade geworden.

⚠️ 5 k x 4 CRV x 3 Horizonte sind 60 ZELLEN. Das ist ein echter Suchpreis
(2.49). Ausgewiesen werden BEIDE Schwellen - fuer eine einzelne vorab
benannte Zelle und fuer das Maximum aus sechzig. Wer nur die erste liest,
unterschlaegt das Absuchen.

⚠️ UND DER ABSTAND ZUM BREAKEVEN WANDERT MIT (2.53). Ein weiterer Stop senkt
die Huerde - jede Zelle wird deshalb gegen IHREN EIGENEN Breakeven gemessen,
und der Vergleich H gegen Basis laeuft INNERHALB derselben Zelle (2.50).

    python messe_dosis.py [--blockplacebo 60]
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
from agent import trefferbilanz as TB                           # noqa: E402
from messe_geometrie import CRV_WERTE, K_WERTE                   # noqa: E402
from messe_marken import (MIN_BERUEHRUNGEN, _niveaus_schnell,    # noqa: E402
                          _SwingSpeicher)
from simuliere_bremse import (_reihen_roh, gebuehr_je_seite,     # noqa: E402
                              klassen_aus_db)

HORIZONTE = (60, 120, 250)
MINDESTALTER = 250
MIN_FAELLE = 300


def sammle(db: str, klasse: str,
           totzone: float | None = None,
           mindestalter: int | None = None) -> tuple[dict, dict, dict]:
    """Je Zelle (k, crv, horizont, gruppe): Treffer, Entschiedene, Stopweiten.

    ⚠️ KEINE ANKERLISTE IM SPEICHER. 533.000 Anker x 60 Zellen waeren
    32 Millionen Saetze; hier wird direkt gezaehlt."""
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    zaehler: dict = {}
    stop_h: dict = {}
    stop_alle: dict = {k: [] for k in K_WERTE}
    # Je Zelle die Rohdaten, damit die Block-Permutation moeglich wird:
    # (Reihennummer, Ankerindex, Ausgang, Tage, istH). Als Listen gesammelt
    # und am Ende zu numpy verdichtet - 8,9 Mio. Saetze als dicts waeren
    # nicht tragbar.
    roh_zellen: dict = {(k, crv): {"r": [], "i": [], "t": [], "aus": [],
                                   "tg": [], "h": []}
                        for k in K_WERTE for crv in CRV_WERTE}
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v, sym
        sp = _SwingSpeicher(h, l)
        # S4 (25.08.2026): der Reifeschnitt ist pruefbar gemacht. `None`
        # heisst unveraendert 250 (Kapitel 104.3) - jeder bestehende
        # Aufrufer rechnet bitgleich weiter.
        start = off + 1 + (MINDESTALTER if mindestalter is None
                           else mindestalter)
        for i in range(start, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr, totzone)
            oben = [m["preis"] for m in n["oben"]
                    if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            unten = [m["preis"] for m in n["unten"]
                     if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            for k in K_WERTE:
                stop = einstieg - k * atr
                if stop <= 0:
                    continue
                risiko = einstieg - stop
                stop_rel = float(risiko / einstieg)
                stop_alle[k].append(stop_rel)
                # B haengt nur an k.
                gedeckt = any(p > stop for p in unten)
                for crv in CRV_WERTE:
                    ziel = einstieg + crv * risiko
                    # A haengt an k UND crv - die Bedingung wandert mit.
                    frei = not any(p < ziel for p in oben)
                    ausgang, tage = "abgelaufen", HORIZONTE[-1]
                    for j in range(i + 1, min(i + 1 + HORIZONTE[-1], len(c))):
                        if l[j] <= stop:
                            ausgang, tage = "stop", j - i
                            break
                        if h[j] >= ziel:
                            ausgang, tage = "ziel", j - i
                            break
                    grp = "H" if (frei and gedeckt) else "basis"
                    if grp == "H":
                        stop_h.setdefault((k, crv), []).append(stop_rel)
                    rz = roh_zellen[(k, crv)]
                    rz["r"].append(nr)
                    rz["i"].append(i)
                    # Das Datum als Zahl - fuer die Zeitteilung in 118.
                    rz["t"].append(int(str(d[i])[:10].replace("-", "")))
                    rz["aus"].append(0 if ausgang == "stop"
                                     else 1 if ausgang == "ziel" else 2)
                    rz["tg"].append(tage)
                    rz["h"].append(grp == "H")
                    for hz in HORIZONTE:
                        erledigt = ausgang != "abgelaufen" and tage <= hz
                        # MILD: nur Entschiedene zaehlen (bisherige Lesart).
                        if erledigt:
                            z = zaehler.setdefault((k, crv, hz, grp), [0, 0])
                            z[0] += 1 if ausgang == "ziel" else 0
                            z[1] += 1
                        # ⚠️ VORSICHTIG: ein Fall, der im Horizont NICHT
                        # entscheidet, zaehlt als Fehlschlag. Er ist in
                        # Wahrheit ein Ausstieg zum Marktpreis, also
                        # irgendwo dazwischen - aber nur so sind die
                        # Horizonte VERGLEICHBAR. Bei 60 Tagen entscheiden
                        # in H's bester Zelle nur 53,9 %, bei 250 Tagen
                        # 87,5 %; wer nur die Entschiedenen vergleicht,
                        # vergleicht drei verschiedene Auswahlen.
                        zv = zaehler.setdefault((k, crv, hz, grp, "v"),
                                                [0, 0])
                        zv[0] += 1 if (erledigt and ausgang == "ziel") else 0
                        zv[1] += 1
        if time.time() - letzte >= 60:
            letzte = time.time()
            print(f"  [{(letzte - t0) / 60:4.1f} min] Reihe {nr}/{len(roh)}"
                  f" - noch ca. {(letzte - t0) * (len(roh) - nr) / nr / 60:.0f}"
                  f" min", flush=True)
    for schl, rz in roh_zellen.items():
        roh_zellen[schl] = {
            "r": np.array(rz["r"], dtype=np.int16),
            "i": np.array(rz["i"], dtype=np.int32),
            "t": np.array(rz["t"], dtype=np.int32),
            "aus": np.array(rz["aus"], dtype=np.int8),
            "tg": np.array(rz["tg"], dtype=np.int16),
            "h": np.array(rz["h"], dtype=bool)}
    return zaehler, {"h": stop_h,
                     "alle": {k: float(np.median(vv)) if vv else float("nan")
                              for k, vv in stop_alle.items()}}, roh_zellen


def abstand(zaehler, stops, k, crv, hz, grp, klasse,
            lesart: str = "mild") -> tuple[int, float]:
    """`mild` zaehlt nur Entschiedene, `vorsichtig` wertet Ablaeufe als
    Fehlschlag. Nur die vorsichtige Lesart macht die Horizonte
    vergleichbar - die milde vergleicht drei verschiedene Auswahlen."""
    z = zaehler.get((k, crv, hz, grp) if lesart == "mild"
                    else (k, crv, hz, grp, "v"))
    if not z or z[1] < MIN_FAELLE:
        return (z[1] if z else 0), float("nan")
    quote = z[0] / z[1]
    sr = (float(np.median(stops["h"][(k, crv)]))
          if grp == "H" and stops["h"].get((k, crv)) else stops["alle"][k])
    return z[1], quote - TB.breakeven(2 * gebuehr_je_seite(klasse) / sr, crv)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=0)
    ap.add_argument("--datei", default="messwerte_dosis.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DIE DOSIS - welche Geometrie und welche Dauer braucht H?")
    print("  H wurde in zwoelf Kapiteln bei EINER Geometrie gemessen:")
    print("  k=2,0 / CRV=2,0 - der schlechtesten Ecke des Rasters (101).")
    print("=" * 78)
    zaehler, stops, roh_zellen = sammle(a.db, a.klasse)

    # ⚠️ DIE VORSICHTIGE LESART ENTSCHEIDET. Sie wertet einen Fall, der im
    # Horizont nicht entscheidet, als Fehlschlag - nur so sind 60, 120 und
    # 250 Tage ueberhaupt vergleichbar. Die milde Lesart steht daneben, weil
    # die Wahrheit dazwischen liegt (ein Ablauf ist ein Ausstieg zum
    # Marktpreis), aber das URTEIL haengt an der vorsichtigen.
    bestes: dict = {}
    for grp in ("basis", "H"):
        print("\n" + "-" * 78)
        print(f"{grp.upper()} - Abstand zum EIGENEN Breakeven je Zelle")
        print("  vorsichtig (Ablauf = Fehlschlag)  |  mild (nur Entschiedene)")
        print("-" * 78)
        top = (None, -99.0, 0)
        for hz in HORIZONTE:
            print(f"\n  Haltedauer {hz} Tage")
            print(f"  {'k \\ CRV':10}"
                  + "".join(f"{str(c) + ' v/m':>15}" for c in CRV_WERTE))
            for k in K_WERTE:
                zeile = f"  {k:<10}"
                for crv in CRV_WERTE:
                    n, av = abstand(zaehler, stops, k, crv, hz, grp,
                                    a.klasse, "vorsichtig")
                    _m, am = abstand(zaehler, stops, k, crv, hz, grp,
                                     a.klasse, "mild")
                    zeile += (f"{100 * av:+7.1f}/{100 * am:+6.1f}"
                              if av == av else f"{'-':>15}")
                    if av == av and av > top[1]:
                        top = ((k, crv, hz), av, n)
                print(zeile)
        bestes[grp] = top
        print(f"\n  BESTE ZELLE {grp}: k={top[0][0]}, CRV={top[0][1]}, "
              f"{top[0][2]} Tage  ->  {100 * top[1]:+.1f} Punkte "
              f"({top[2]} Faelle)")

    print("\n" + "=" * 78)
    print("D1 - LIEGT H's OPTIMUM WOANDERS?")
    print("=" * 78)
    print(f"  Basis:  k={bestes['basis'][0][0]}, CRV={bestes['basis'][0][1]}, "
          f"{bestes['basis'][0][2]} Tage   {100 * bestes['basis'][1]:+.1f}")
    print(f"  H:      k={bestes['H'][0][0]}, CRV={bestes['H'][0][1]}, "
          f"{bestes['H'][0][2]} Tage   {100 * bestes['H'][1]:+.1f}")
    if bestes["basis"][0] == bestes["H"][0]:
        print("  -> DIESELBE ECKE. H aendert an der Geometriewahl nichts;")
        print("     es bleibt die Kostenarithmetik aus Kapitel 101.")
    else:
        print("  -> ANDERE ECKE. Das waere die Dosis: H braucht eine andere")
        print("     Geometrie als der Durchschnitt.")

    print("\nD2 - LIEGT H AN SEINEM OPTIMUM UEBER NULL?")
    print(f"  {100 * bestes['H'][1]:+.1f} Punkte -> "
          + ("JA - erstmals ein positiver Erwartungswert"
             if bestes["H"][1] > 0 else "nein"))
    n_b, ab_b = abstand(zaehler, stops, bestes["H"][0][0], bestes["H"][0][1],
                        bestes["H"][0][2], "basis", a.klasse, "vorsichtig")
    print(f"  Die Basis in DERSELBEN Zelle: {100 * ab_b:+.1f} Punkte "
          f"({n_b} Faelle)")
    print(f"  -> H's eigener Beitrag dort: {100 * (bestes['H'][1] - ab_b):+.1f}"
          f" Punkte")
    # ---- WIE VIELE ENTSCHEIDEN SICH UEBERHAUPT? -------------------------
    # ⚠️ DER HORIZONTVERGLEICH IST NICHT UNSCHULDIG. Ein kuerzerer Horizont
    # laesst mehr Faelle "abgelaufen" und wertet sie NICHT - wer die Quote
    # unter den ENTSCHIEDENEN vergleicht, vergleicht bei 60 Tagen eine
    # andere Auswahl als bei 250. Dass ausgerechnet 60 Tage am besten
    # aussehen, koennte genau daher kommen. Also steht der Anteil daneben.
    print("\n" + "-" * 78)
    print("ENTSCHEIDUNGSQUOTE - welcher Anteil laeuft nicht ab?")
    print("-" * 78)
    kz, cz, _hz0 = bestes["H"][0]
    print(f"  in H's bester Zelle (k={kz}, CRV={cz}):")
    rz0 = roh_zellen[(kz, cz)]
    n_h_ges = int(rz0["h"].sum())
    for hz in HORIZONTE:
        m = rz0["h"] & (rz0["aus"] != 2) & (rz0["tg"] <= hz)
        print(f"    {hz:4} Tage   {int(m.sum()):7} von {n_h_ges:7}"
              f"   {100 * m.sum() / max(n_h_ges, 1):5.1f} %")

    # ---- DIE SCHWELLE FUER DAS MAXIMUM AUS 60 ZELLEN --------------------
    if a.blockplacebo:
        print("\n" + "-" * 78)
        print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Kalenderzeit")
        print("  Gewuerfelt werden die AUSGAENGE je Zelle in Zeitbloecken;")
        print("  die Zugehoerigkeit zu H bleibt, wo sie ist.")
        print("-" * 78)
        rng = np.random.default_rng(20260904)
        bloecke_je: dict = {}
        for schl, rz in roh_zellen.items():
            ordn: dict = {}
            for pos in range(len(rz["r"])):
                ordn.setdefault(int(rz["r"][pos]), []).append(
                    (int(rz["i"][pos]), pos))
            bl = []
            for v in ordn.values():
                gr: list = []
                for idx, pos in sorted(v):
                    if not gr or idx - gr[-1][0] >= 250:
                        gr.append([idx, []])
                    gr[-1][1].append(pos)
                if len(gr) >= 2:
                    bl.append([np.array(g[1]) for g in gr])
            bloecke_je[schl] = bl
        print(f"  {len(bloecke_je[(kz, cz)])} Reihen mit mindestens zwei "
              f"Bloecken (in H's bester Zelle)")
        # ⚠️ DIE HUERDENRECHNUNG (2.49). Neben dem Maximum aus 60 Zellen wird
        # dieselbe Ziehung fuer GENAU EINE Zelle ausgewertet - die, die H am
        # Ende waehlt. Nicht als Urteil (sie nachtraeglich zu benennen waere
        # zirkulaer), sondern um zu beziffern, was das Absuchen kostet und
        # was eine VORAB benannte Geometrie wert waere.
        hoechste, eine_zelle = [], []
        for _lauf in range(a.blockplacebo):
            beste = -99.0
            for (k, crv), rz in roh_zellen.items():
                aus, tg = rz["aus"].copy(), rz["tg"].copy()
                for gr in bloecke_je[(k, crv)]:
                    alle = np.concatenate(gr)
                    neu_ord = np.concatenate(
                        [gr[j] for j in rng.permutation(len(gr))])
                    aus[alle] = rz["aus"][neu_ord]
                    tg[alle] = rz["tg"][neu_ord]
                sr = (float(np.median(stops["h"][(k, crv)]))
                      if stops["h"].get((k, crv)) else stops["alle"][k])
                be = TB.breakeven(2 * gebuehr_je_seite(a.klasse) / sr, crv)
                for hz in HORIZONTE:
                    # ⚠️ DIESELBE LESART WIE DAS URTEIL: Ablauf = Fehlschlag.
                    # Ein Placebo, der milder rechnet als die Messung, waere
                    # ein zu niedriger Massstab (2.50).
                    m = rz["h"]
                    if m.sum() < MIN_FAELLE:
                        continue
                    treffer = m & (aus == 1) & (tg <= hz)
                    w = float(treffer.sum()) / float(m.sum()) - be
                    beste = max(beste, w)
                    if (k, crv, hz) == bestes["H"][0]:
                        eine_zelle.append(w)
            hoechste.append(beste)
        s60 = float(np.quantile(hoechste, 0.95))
        streu = float(np.std(hoechste)) / math.sqrt(len(hoechste))
        print(f"  groesster Zufallswert  {100 * max(hoechste):+.1f} Punkte")
        print(f"  SCHWELLE, Maximum aus 60 Zellen  {100 * s60:+.1f} Punkte")
        print(f"  gemessen (H's beste Zelle)       "
              f"{100 * bestes['H'][1]:+.1f} Punkte")
        if eine_zelle:
            s1 = float(np.quantile(eine_zelle, 0.95))
            print(f"\n  HUERDENRECHNUNG (2.49) - dieselben Ziehungen, aber")
            print(f"  nur EINE Zelle statt sechzig. Kein Urteil, sondern die")
            print(f"  Frage: was waere eine VORAB benannte Geometrie wert?")
            print(f"    Schwelle bei 60 Zellen    {100 * s60:+.1f} Punkte")
            print(f"    Schwelle bei EINER Zelle  {100 * s1:+.1f} Punkte")
            print(f"    Preis des Absuchens:      {100 * (s60 - s1):.1f} "
                  f"Punkte")
        if abs(bestes["H"][1] - s60) < 2 * streu:
            print("  -> ⚠️ ZU KNAPP (Methodik 2.48)")
        elif bestes["H"][1] > s60:
            print("  -> TRAEGT - ueber dem, was 60 abgesuchte Zellen bei")
            print("     reinem Zufall hergeben.")
        else:
            print("  -> NICHTS - das Maximum aus 60 Zellen entsteht auch")
            print("     ohne jeden Zusammenhang.")
    else:
        print("\n  ⚠️ 60 Zellen abgesucht. Ohne --blockplacebo ist keine")
        print("     dieser Zahlen ein Befund (2.49).")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "bestes": {g: {"zelle": list(v[0]), "abstand": v[1], "n": v[2]}
                       for g, v in bestes.items()},
            "zellen": {"|".join(str(x) for x in schl): v
                       for schl, v in zaehler.items()}},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
