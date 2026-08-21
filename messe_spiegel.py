"""Die Spiegelbedingung fuer SHORT - eine Vorhersage (20.08.2026, Umbauplan 110)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM DAS KEINE SUCHE IST. Kapitel 108 hat gemessen, dass H im Bullenmarkt
+5,1 Punkte ueber dem Breakeven liegt und im Baermarkt -8,5 darunter. Dafuer
gibt es einen GRUND: H ist eine LONG-Bedingung. "Kein Widerstand bis zum Ziel"
heisst im fallenden Markt "kein Halt nach unten", und die Unterstuetzungen,
auf die der Stop baut, sind gerade die, die reihenweise brechen.

    Wenn dieser Mechanismus stimmt, MUSS die gespiegelte Bedingung im
    Baermarkt tragen und im Bullenmarkt versagen.

Das ist eine VORHERSAGE, kein Fund. Sie kostet nach Methodik 2.49 die halbe
Huerde - und sie kann scheitern, was sie erst wertvoll macht.

DIE SPIEGELBEDINGUNG:

    A'  FREIER WEG NACH UNTEN   keine Marke mit >= 2 Beruehrungen zwischen
                                Kurs und Ziel (das UNTER dem Kurs liegt)
    B'  STOP GEDECKT            eine Marke mit >= 2 Beruehrungen zwischen
                                Kurs und Stop (der UEBER dem Kurs liegt)
    H'  = A' UND B'

⚠️ UND DAS IST AUSDRUECKLICH KEINE EINFACHE UMKEHRUNG. Der Nutzer hat darauf
hingewiesen, und die Pruefung gibt ihm recht - VIER Asymmetrien, alle vorab
benannt:

  1. DIE KOSTEN SIND ANDERE. Ein Short ist bei uns nur ueber Hebel moeglich,
     also faellt FINANZIERUNG_JE_TAG (0,03 %/Tag) an. Sie wird hier
     mitgerechnet; ein Vergleich mit den Long-Zahlen ohne sie waere falsch.

  2. DER MARKT DRIFTET NACH OBEN. Gemessen: 34,4 % gegen 33,3 % driftfrei.
     Ein Short laeuft dagegen an. Die Basisrate fuer Short ist deshalb
     mechanisch niedriger - verglichen wird darum H' gegen SHORT-Anker
     derselben Lage, nie gegen die Long-Zahlen.

  3. DER PREISRAUM IST NICHT SYMMETRISCH. Ein Ziel bei CRV x k x ATR UNTER
     dem Kurs kann unter null liegen; nach oben gibt es keine solche Grenze.
     Solche Anker werden verworfen und GEZAEHLT - ihre Zahl gehoert zum
     Ergebnis.

  4. DAS SYSTEM HANDELT NUR LONG (`nur_long`, seit 05.08.). Diese Messung ist
     deshalb eine MECHANISMUSPRUEFUNG, kein Handelsvorschlag. Beide Fragen
     werden getrennt ausgewiesen:

         traegt die Struktur?    H' gegen vergleichbare Anker
         traegt der Trade?       H' gegen seinen eigenen Breakeven MIT
                                 Finanzierung

⚠️ DER MARKT HAT SICH 2022 GEWANDELT (Nutzerhinweis, aus Sachkenntnis vorab
benannt - nicht aus einem Ergebnis). Deshalb wird zusaetzlich getrennt nach
vor und ab 2022 ausgewiesen. Das ist eine benannte Unterteilung, keine Suche.

DIE VORHERSAGE, DIE HIER GEPRUEFT WIRD:

    baer     H' besser als vergleichbare Anker
    bulle    H' schlechter
    Trifft das Muster NICHT zu, ist der Mechanismus aus 108 widerlegt -
    und dann war auch der Long-Befund eine Beschreibung, keine Erklaerung.

    python messe_spiegel.py [--blockplacebo 40]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                          # noqa: E402
from messe_marken import (MIN_BERUEHRUNGEN, _niveaus_schnell,   # noqa: E402
                          _SwingSpeicher)
from messe_struktur_bereinigt import MINDESTALTER, _reif        # noqa: E402
from simuliere_bremse import (FINANZIERUNG_JE_TAG, MAX_TAGE,    # noqa: E402
                              _marktphase, _reihen_roh,
                              gebuehr_je_seite, klassen_aus_db)

K = 2.0
CRV = 2.0
MIN_FAELLE = 300
BLOCKLAENGE = 250
LAGEN = ("bulle", "seitwaerts", "baer")
BRUCH = "2022-01-01"          # Nutzerhinweis, vorab benannt


def laufe_short(db: str, klasse: str, fortschritt: bool = False) -> tuple:
    """Je Anker die SHORT-Geometrie und die gespiegelten Bedingungen."""
    import time
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    phase = _marktphase(roh)
    aus, unmoeglich = [], 0
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        for i in range(off + 1, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            stop = einstieg + K * atr             # SHORT: der Stop liegt OBEN
            ziel = einstieg - CRV * (stop - einstieg)
            # ⚠️ ASYMMETRIE 3: nach unten ist bei null Schluss.
            if ziel <= 0:
                unmoeglich += 1
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            # A' - FREIER WEG NACH UNTEN.
            frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                           and m["preis"] > ziel for m in n["unten"])
            # B' - STOP GEDECKT: eine Marke zwischen Kurs und Stop.
            gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                          and m["preis"] < stop for m in n["oben"])
            ausgang, tage = "abgelaufen", MAX_TAGE
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                # Vorsichtige Lesart wie ueberall: faellt beides in eine
                # Kerze, gilt der STOP.
                if h[j] >= stop:
                    ausgang, tage = "stop", j - i
                    break
                if l[j] <= ziel:
                    ausgang, tage = "ziel", j - i
                    break
            aus.append({"sym": sym, "i": i, "datum": d[i],
                        "frei": frei, "gedeckt": gedeckt,
                        "phase": phase.get(d[i], "unbekannt"),
                        "ausgang": ausgang, "tage": tage,
                        "stop_relativ": float((stop - einstieg) / einstieg)})
        if fortschritt and time.time() - letzte >= 60:
            letzte = time.time()
            print(f"  [{(letzte - t0) / 60:4.1f} min] Reihe {nr}/{len(roh)}"
                  f" - {len(aus)} Anker", flush=True)
    return aus, unmoeglich


def bewerte_short(faelle, klasse: str) -> tuple[int, float, float]:
    """(Faelle, Quote, Abstand) - MIT Finanzierung, weil Short = Hebel."""
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if len(ent) < MIN_FAELLE:
        return len(ent), float("nan"), float("nan")
    quote = sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)
    stop_rel = float(np.median([f["stop_relativ"] for f in ent]))
    tage = float(np.median([f["tage"] for f in ent]))
    kosten_r = (2 * gebuehr_je_seite(klasse) / stop_rel
                + FINANZIERUNG_JE_TAG["hebel"] * tage / stop_rel)
    return len(ent), quote, quote - TB.breakeven(kosten_r, CRV)


def _zeile(name, faelle, klasse, breite=26):
    n, q, ab = bewerte_short(faelle, klasse)
    if math.isnan(ab):
        print(f"  {name:{breite}}{n:8} Faelle   zu wenige")
        return None
    print(f"  {name:{breite}}{n:8} Faelle   {100 * q:5.1f} %   "
          f"{100 * ab:+6.1f} Punkte")
    return ab


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=40)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_spiegel.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DIE SPIEGELBEDINGUNG FUER SHORT - eine Vorhersage")
    print("  Vorhergesagt: H' traegt im BAERMARKT und versagt im BULLEN.")
    print("  Trifft das nicht zu, ist der Mechanismus aus 108 widerlegt.")
    print("=" * 78)
    faelle, unmoeglich = laufe_short(a.db, a.klasse, fortschritt=True)
    faelle = _reif(faelle, MINDESTALTER)
    print(f"  {len(faelle)} reife Short-Anker")
    print(f"  ⚠️ {unmoeglich} Anker verworfen, weil ihr Ziel unter null laege")
    print(f"     (Asymmetrie 3 - nach unten ist bei null Schluss)")
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    print(f"  Median-Haltedauer {np.median([f['tage'] for f in ent]):.0f} "
          f"Handelstage, Finanzierung "
          f"{100 * FINANZIERUNG_JE_TAG['hebel']:.2f} %/Tag ist eingerechnet")

    print("\n" + "-" * 78)
    print("DIE VORHERSAGE - H' gegen vergleichbare Anker, JE LAGE")
    print("-" * 78)
    ergebnis = {}
    for lage in LAGEN:
        teil = [f for f in faelle if f["phase"] == lage]
        print(f"\n  {lage.upper()}")
        h = _zeile("H' (Spiegel)", [f for f in teil
                                    if f["frei"] and f["gedeckt"]], a.klasse)
        b = _zeile("alle Short-Anker", teil, a.klasse)
        if h is not None and b is not None:
            ergebnis[lage] = {"h": h, "basis": b, "vorsprung": h - b}
            print(f"  {'-> Vorsprung':26}{'':8}            "
                  f"{100 * (h - b):+6.1f} Punkte")

    # ⚠️ DER MARKT HAT SICH 2022 GEWANDELT - vorab benannt, keine Suche.
    print("\n" + "-" * 78)
    print(f"VOR UND AB {BRUCH} - der Nutzerhinweis, getrennt ausgewiesen")
    print("-" * 78)
    zeiten = {}
    for name, wo in (("vor " + BRUCH, lambda f: f["datum"] < BRUCH),
                     ("ab  " + BRUCH, lambda f: f["datum"] >= BRUCH)):
        teil = [f for f in faelle if wo(f)]
        print(f"\n  {name}  ({len(teil)} Anker)")
        h = _zeile("H' (Spiegel)", [f for f in teil
                                    if f["frei"] and f["gedeckt"]], a.klasse)
        b = _zeile("alle Short-Anker", teil, a.klasse)
        if h is not None and b is not None:
            zeiten[name] = {"h": h, "basis": b, "vorsprung": h - b}
            print(f"  {'-> Vorsprung':26}{'':8}            "
                  f"{100 * (h - b):+6.1f} Punkte")

    # ---- SCHWELLE FUER DIE VORHERGESAGTE LAGE ---------------------------
    # ⚠️ METHODIK 2.50: gewuerfelt wird NUR unter den Ankern derselben Lage.
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION im BAERMARKT - der vorhergesagten Lage")
    print("-" * 78)
    baer = [f for f in faelle
            if f["phase"] == "baer" and f["ausgang"] in ("ziel", "stop")]
    schwelle = float("nan")
    if len(baer) >= MIN_FAELLE:
        ziel = np.array([f["ausgang"] == "ziel" for f in baer])
        drin = np.array([f["frei"] and f["gedeckt"] for f in baer])
        if drin.sum() >= MIN_FAELLE:
            teil = [f for f, m in zip(baer, drin) if m]
            stop_rel = float(np.median([f["stop_relativ"] for f in teil]))
            tage = float(np.median([f["tage"] for f in teil]))
            be = TB.breakeven(2 * gebuehr_je_seite(a.klasse) / stop_rel
                              + FINANZIERUNG_JE_TAG["hebel"] * tage / stop_rel,
                              CRV)
            ordnung: dict = {}
            for pos, f in enumerate(baer):
                ordnung.setdefault(f["sym"], []).append((f["i"], pos))
            reihen = [np.array([p for _i, p in sorted(v)])
                      for v in ordnung.values()]
            lang = sum(1 for r in reihen if len(r) >= 2 * a.blocklaenge)
            rng = np.random.default_rng(20260828)
            werte = []
            for _lauf in range(a.blockplacebo):
                gew = ziel.copy()
                for reihe in reihen:
                    if len(reihe) < 2 * a.blocklaenge:
                        continue
                    v = int(rng.integers(0, a.blocklaenge))
                    tl = ([reihe[:v]] if v else []) + [
                        reihe[s:s + a.blocklaenge]
                        for s in range(v, len(reihe), a.blocklaenge)]
                    gew[reihe] = ziel[np.concatenate(
                        [tl[j] for j in rng.permutation(len(tl))])]
                werte.append(float(gew[drin].mean()) - be)
            schwelle = float(np.quantile(werte, 0.95))
            gemessen = ergebnis.get("baer", {}).get("h", float("nan"))
            streu = float(np.std(werte)) / math.sqrt(len(werte))
            print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
            print(f"  SCHWELLE (95 %)  {100 * schwelle:+.1f} Punkte")
            print(f"  gemessen (H')    {100 * gemessen:+.1f} Punkte")
            if abs(gemessen - schwelle) < 2 * streu:
                print("  ⚠️ ZU KNAPP (Methodik 2.48)")
            elif gemessen > schwelle:
                print("  -> DIE VORHERSAGE TRIFFT ZU.")
            else:
                print("  -> DIE VORHERSAGE TRIFFT NICHT ZU.")
        else:
            print(f"  nur {int(drin.sum())} H'-Faelle im Baermarkt - "
                  f"zu wenige fuer eine Schwelle")
    else:
        print(f"  nur {len(baer)} Short-Anker im Baermarkt")

    print("\n" + "=" * 78)
    print("LESEHILFE: das hier ist eine MECHANISMUSPRUEFUNG. Das System")
    print("handelt nur long; eine positive Zahl ist kein Handelsvorschlag,")
    print("sondern ein Beleg, dass die Struktur etwas ueber den Pfad sagt.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "lagen": ergebnis, "zeiten": zeiten, "schwelle_baer": schwelle,
            "verworfen_ziel_unter_null": unmoeglich},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
