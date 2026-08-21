"""Traegt die STRUKTUR? - eine vorab benannte Hypothese (20.08.2026, Umbauplan 104)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM DIESER KANAL. Kapitel 100-103 haben drei Hebel gemessen - Marktphase,
Driftband, Geometrie - und alle drei liefen ueber DENSELBEN Kanal: hoher ATR
-> weiter Stop in Prozent -> Kosten_R sinkt -> Breakeven sinkt. Sie sind
dieselbe Groesse unter drei Namen.

STRUKTUR IST ETWAS ANDERES. Marken beschreiben, WO im Kursverlauf der Einstieg
liegt, nicht WIE WEIT der Markt schwankt. Genau die verschiedene Information,
die das Nutzermodell voraussetzt ("ein Wert hat fast keine Auswirkung, aber
die richtige Kombination bildet den Trichter der Optimierung").

⚠️ UND ER IST NIE GEMESSEN WORDEN. Der eigene Docstring in
`entscheidungsrechnung` zitiert die strukturbasierte Schule - gebaut wurde sie
nie. Der offene Punkt "die Unterstuetzung traegt den Stop nicht" steht seit
dem 17.08.

DIE HYPOTHESE, AUS EINEM GRUND BENANNT - EINE, NICHT DREIHUNDERT:

    Ein Einstieg traegt sich eher, wenn zwischen Einstieg und Ziel KEINE
    mehrfach beruehrte Marke liegt UND der Stop UNTER einer mehrfach
    beruehrten Unterstuetzung steht.

    A  FREIER WEG    keine Marke mit >= 2 Beruehrungen zwischen Kurs und Ziel
    B  STOP GEDECKT  eine Marke mit >= 2 Beruehrungen zwischen Stop und Kurs
    H  = A UND B

Der Grund: die Marke ist der Ort, an dem die Bewegung erfahrungsgemaess dreht.
Liegt sie im Weg, muss der Kurs sie erst brechen; liegt sie unter dem Stop,
muss das Rauschen sie erst durchschlagen.

⚠️ WARUM DAS BILLIGER IST ALS KAPITEL 103. Die Huerde bei 300 abgesuchten
Zellen lag bei +20,5 Punkten, bei EINER vorab benannten Zelle bei +10,2
(Methodik 2.49). Die Haelfte der Huerde entsteht aus dem Suchen. Deshalb wird
hier NICHT gesucht: die Geometrie bleibt beim Betriebszustand k = 2,0 und
CRV = 2,0, es gibt kein Raster.

    A und B EINZELN werden ausgewiesen, aber sie sind KEINE Kandidaten fuer
    das Urteil - sonst waeren es wieder drei Versuche statt einem.

⚠️ WAS DIE PRODUKTIONSFUNKTION TUT UND WAS NICHT. `niveaus_werte` laesst
Marken naeher als 0,5 ATR weg (NIVEAU_MIN_ABSTAND_ATR) - eine Unterstuetzung
dicht unter dem Kurs zaehlt also NICHT als Deckung. Das ist eine Eigenschaft
des Betriebs, keine Annahme dieser Messung, und sie bleibt unangetastet.

DIE PFLICHTKONTROLLEN, alle vorab:

  1. BLOCK-PERMUTATION statt freiem Placebo (Methodik 2.47). Taegliche Anker
     mit 120 Tagen Vorwaertsfenster ueberlappen um mehr als 99 %; freies
     Wuerfeln macht die Schwelle um ein Vielfaches zu niedrig.
  2. LAEUFE ERHOEHEN, wenn der Messwert nahe der Schwelle liegt (2.48).
  3. POSITIVKONTROLLE - sonst heisst "nichts gefunden" nur "nicht hingesehen".
  4. PHASENPROBE - eine Struktur, die nur im Baermarkt traegt, ist die
     Marktphasenwette mit anderem Namen.

    python messe_marken.py [--klasse krypto] [--blockplacebo 40]
"""
from __future__ import annotations

import argparse
import io
import time
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import lagebeschreibung as LB                      # noqa: E402
from agent import trefferbilanz as TB                         # noqa: E402
from simuliere_bremse import gebuehr_je_seite as _GEB  # noqa: E402
from simuliere_bremse import klassen_aus_db as _KLASSEN  # noqa: E402
from simuliere_bremse import (MAX_TAGE, _marktphase,          # noqa: E402
                              _reihen_roh)

K = 2.0
CRV = 2.0
MIN_BERUEHRUNGEN = 2      # "mehrfach beruehrt" - ein Wendepunkt ist keine Marke
MIN_FAELLE = 300
BLOCKLAENGE = 250         # > MAX_TAGE, sonst zerschneidet der Block die
#                           Abhaengigkeit, die er erhalten soll


class _SwingSpeicher:
    """Ruft `LB._swings` EINMAL je Reihe statt einmal je Anker.

    ⚠️ DAS IST KEIN NACHBAU, SONDERN DIESELBE FUNKTION. `_swings(h, l, bis)`
    laeuft ueber `range(FENSTER, min(len(h) - FENSTER, bis - FENSTER + 1))` -
    das Ergebnis fuer ein kleineres `bis` ist damit ein PRAEFIX des Ergebnisses
    fuer ein groesseres. Hier wird die volle Liste einmal geholt und je Anker
    zugeschnitten.

    Ohne das laeuft die Messung quadratisch: 1.300 Anker x 1.300 Kerzen x 40
    Reihen sind 67 Millionen Fensteroperationen.

    Die Gleichheit wird nicht behauptet, sondern in `pruefe_gleichheit()` an
    echten Ankern gegen das Original geprueft."""

    def __init__(self, h, l):
        self._h, self._l = h, l
        self._hi, self._lo = LB._swings(h, l, len(h) - 1)

    def bis(self, i: int) -> tuple[list, list]:
        grenze = i - LB.FENSTER_SWING
        return ([j for j in self._hi if j <= grenze],
                [j for j in self._lo if j <= grenze])

    def pruefe_gleichheit(self, anker: list[int]) -> bool:
        for i in anker:
            if self.bis(i) != LB._swings(self._h, self._l, i):
                return False
        return True


def _niveaus_schnell(sp: _SwingSpeicher, c, h, l, i, atr) -> dict:
    """`LB.niveaus_werte` mit vorberechneten Swings - Rest unveraendert.

    Der Code darunter ist Zeile fuer Zeile der der Produktion; nur die
    Swing-Ermittlung kommt aus dem Speicher."""
    hi, lo = sp.bis(i)
    if (not hi and not lo) or atr <= 0:
        return {"oben": [], "unten": []}
    kurs = float(c[i])
    grenze = LB.NIVEAU_MIN_ABSTAND_ATR * atr
    niveaus = LB._cluster_mit_art(
        [(float(h[j]), "hoch", j) for j in hi]
        + [(float(l[j]), "tief", j) for j in lo], atr)
    oben, unten = [], []
    for e in niveaus:
        satz = {"preis": e["preis"], "beruehrungen": e["hoch"] + e["tief"]}
        if e["preis"] - kurs >= grenze:
            oben.append(satz)
        elif kurs - e["preis"] >= grenze:
            unten.append(satz)
    return {"oben": oben, "unten": unten}


def laufe(db: str, klasse: str, roh_pruefen: bool = True,
          fortschritt: bool = False) -> list[dict]:
    """Je Anker: A, B, Ausgang, Phase - und Symbol/Zeit fuer die Bloecke.

    `fortschritt` meldet einmal je Minute den Stand - bei 347 Reihen laeuft
    das eine halbe Stunde, und ein Lauf ohne Lebenszeichen ist von einem
    haengenden nicht zu unterscheiden."""
    roh = _reihen_roh(db, klasse, _KLASSEN(db))
    phase = _marktphase(roh)
    aus, geprueft = [], 0
    _t0 = _letzte = time.time()
    for _nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        if roh_pruefen:
            # ⚠️ AN ECHTEN ANKERN, nicht an gedachten. Fuenf ueber die Reihe
            # verteilt; stimmt einer nicht, ist die ganze Messung hinfaellig.
            probe = [int(x) for x in
                     np.linspace(LB.FENSTER_SWING + 1, len(c) - 1, 5)]
            if not sp.pruefe_gleichheit(probe):
                raise SystemExit(f"Swing-Speicher weicht ab bei {sym}")
            geprueft += len(probe)
        for i in range(off + 1, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            stop = einstieg - K * atr
            if stop <= 0:
                continue
            ziel = einstieg + CRV * (einstieg - stop)
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            # A - FREIER WEG: keine mehrfach beruehrte Marke bis zum Ziel.
            frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                           and m["preis"] < ziel for m in n["oben"])
            # B - STOP GEDECKT: eine mehrfach beruehrte Marke ueber dem Stop.
            gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                          and m["preis"] > stop for m in n["unten"])
            ausgang = "abgelaufen"
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                # Faellt beides in eine Kerze, gilt der STOP - die vorsichtige
                # Lesart. Gemessen (Kapitel 102.3): 0,1 Punkte Unterschied.
                if l[j] <= stop:
                    ausgang = "stop"
                    break
                if h[j] >= ziel:
                    ausgang = "ziel"
                    break
            aus.append({"sym": sym, "i": i, "frei": frei, "gedeckt": gedeckt,
                        # Das Datum, damit sich die Phase NACHTRAEGLICH mit
                        # einem anderen Index nachrechnen laesst (107.4).
                        "datum": d[i],
                        "phase": phase.get(d[i], "unbekannt"),
                        "ausgang": ausgang,
                        "stop_relativ": float((einstieg - stop) / einstieg)})
        if fortschritt and time.time() - _letzte >= 60:
            _letzte = time.time()
            _h = sum(1 for f in aus if f["frei"] and f["gedeckt"])
            _rest = (_letzte - _t0) * (len(roh) - _nr) / max(_nr, 1)
            print(f"  [{(_letzte - _t0) / 60:4.1f} min] Reihe {_nr}/{len(roh)}"
                  f" - {len(aus)} Anker, {_h} in H"
                  f" - noch ca. {_rest / 60:.0f} min", flush=True)
    if roh_pruefen:
        print(f"  Swing-Speicher an {geprueft} echten Ankern gegen die "
              f"Produktionsfunktion geprueft - gleich")
    return aus


def bewerte(faelle, klasse: str) -> tuple[int, float, float]:
    """(Faelle, Quote, Abstand zum eigenen Breakeven)."""
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if len(ent) < MIN_FAELLE:
        return len(ent), float("nan"), float("nan")
    quote = sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)
    stop_rel = float(np.median([f["stop_relativ"] for f in ent]))
    gebuehr = _GEB(klasse)
    return len(ent), quote, quote - TB.breakeven(2 * gebuehr / stop_rel, CRV)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=40,
                    help="Laeufe der Block-Permutation (Methodik 2.47)")
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--mindestalter", type=int, default=0,
                    help="ARTEFAKTPROBE: verwirft die ersten N Handelstage "
                         "jeder Reihe. Am Anfang einer Reihe gibt es kaum "
                         "bestaetigte Swings - 'kein Widerstand im Weg' ist "
                         "dort fast geschenkt. Gemessen: H tritt in den "
                         "ersten 250 Tagen mit 12,6 %% auf, danach mit 2-4 %%.")
    ap.add_argument("--positiv", type=float, default=0.0,
                    help="POSITIVKONTROLLE: hebt die Quote in der Gruppe H "
                         "kuenstlich an. Findet die Probe das nicht, ist sie "
                         "stumpf - und ein Nullbefund waere wertlos.")
    ap.add_argument("--datei", default="messwerte_marken.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("TRAEGT DIE STRUKTUR? - eine vorab benannte Hypothese")
    print("  H = kein Widerstand im Weg UND eine Unterstuetzung ueber dem Stop")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse)
    print(f"  {len(faelle)} Anker")

    # ⚠️ DIE ARTEFAKTPROBE, DIE UEBER DEN BEFUND ENTSCHEIDET.
    # 48 % aller H-Faelle liegen in den ersten 250 Handelstagen ihrer Reihe.
    # Dort ist "kein Widerstand im Weg" kein Marktzustand, sondern ein
    # Datenzustand: es gibt noch kaum bestaetigte Swings. Ueberlebt der
    # Befund den Schnitt nicht, war er die Datenlage.
    if a.mindestalter:
        erst: dict = {}
        for f in faelle:
            erst[f["sym"]] = min(erst.get(f["sym"], f["i"]), f["i"])
        vor = len(faelle)
        faelle = [f for f in faelle
                  if f["i"] - erst[f["sym"]] >= a.mindestalter]
        print(f"  ⚠️ ARTEFAKTPROBE: die ersten {a.mindestalter} Handelstage "
              f"je Reihe verworfen")
        print(f"     {vor} -> {len(faelle)} Anker")

    if a.positiv:
        rngp = np.random.default_rng(20260823)
        traf = 0
        for f in faelle:
            if f["frei"] and f["gedeckt"] and f["ausgang"] == "stop" \
                    and rngp.random() < a.positiv:
                f["ausgang"] = "ziel"
                traf += 1
        print(f"  ⚠️ POSITIVKONTROLLE AKTIV: {traf} Stops in H zu Zielen "
              f"gemacht - die Probe MUSS das finden.")

    print("\n" + "-" * 78)
    print("DIE GRUPPEN")
    print("-" * 78)
    print(f"  {'Gruppe':34}{'Faelle':>9}{'Quote':>10}{'Abstand':>11}")
    gruppen = {
        "alle Anker": lambda f: True,
        "A  freier Weg (einzeln, kein Urteil)": lambda f: f["frei"],
        "B  Stop gedeckt (einzeln, kein Urteil)": lambda f: f["gedeckt"],
        "H  A UND B  <- die Hypothese": lambda f: f["frei"] and f["gedeckt"],
    }
    ergebnis, basis, h_abstand, h_n = {}, None, float("nan"), 0
    for name, wo in gruppen.items():
        n, q, ab = bewerte([f for f in faelle if wo(f)], a.klasse)
        if math.isnan(q):
            print(f"  {name:34}{n:9}   zu wenige Faelle")
            continue
        ergebnis[name] = {"n": n, "quote": q, "abstand": ab}
        print(f"  {name:34}{n:9}{100 * q:9.1f} %{100 * ab:+10.1f}")
        if name.startswith("alle"):
            basis = ab
        if name.startswith("H "):
            h_abstand, h_n = ab, n
    if basis is not None and not math.isnan(h_abstand):
        print(f"\n  H gegen alle Anker: {100 * (h_abstand - basis):+.1f} "
              f"Punkte")

    # ---- PHASENPROBE ----------------------------------------------------
    print("\n" + "-" * 78)
    print("PHASENPROBE - traegt H in allen Lagen oder nur im Baermarkt?")
    print("-" * 78)
    phasen = {}
    for ph in ("bulle", "seitwaerts", "baer"):
        n, q, ab = bewerte([f for f in faelle if f["frei"] and f["gedeckt"]
                            and f["phase"] == ph], a.klasse)
        nb, _qb, ab_b = bewerte([f for f in faelle if f["phase"] == ph],
                                a.klasse)
        if math.isnan(ab) or math.isnan(ab_b):
            print(f"  {ph:12}{n:8} Faelle   zu wenige")
            continue
        phasen[ph] = {"n": n, "abstand": ab, "gegen_basis": ab - ab_b}
        print(f"  {ph:12}{n:8} Faelle   H {100 * ab:+6.1f}   "
              f"alle {100 * ab_b:+6.1f}   Vorsprung "
              f"{100 * (ab - ab_b):+6.1f}")

    # ---- BLOCK-PERMUTATION ----------------------------------------------
    # ⚠️ EINE GRUPPE, VORAB BENANNT - also die Ein-Zellen-Huerde, nicht das
    # Maximum aus vielen. Genau darin liegt der Rabatt aus Methodik 2.49.
    schwelle_b = float("nan")
    if a.blockplacebo and not math.isnan(h_abstand):
        print("\n" + "-" * 78)
        print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Zeitbloecke von "
              f"{a.blocklaenge} Tagen")
        print("  Ein freier Placebo waere hier kein Massstab: die Anker "
              "ueberlappen")
        print("  einander um mehr als 99 % (Methodik 2.47).")
        print("-" * 78)
        rngb = np.random.default_rng(20260824)
        ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
        ziel_arr = np.array([f["ausgang"] == "ziel" for f in ent])
        ist_h = np.array([f["frei"] and f["gedeckt"] for f in ent])
        stop_arr = np.array([f["stop_relativ"] for f in ent])
        ordnung: dict = {}
        for pos, f in enumerate(ent):
            ordnung.setdefault(f["sym"], []).append((f["i"], pos))
        reihen = [np.array([p for _i, p in sorted(v)])
                  for v in ordnung.values()]
        lang = sum(1 for r in reihen if len(r) >= 2 * a.blocklaenge)
        gebuehr = _GEB(a.klasse)
        stop_h = float(np.median(stop_arr[ist_h]))
        schwelle_be = TB.breakeven(2 * gebuehr / stop_h, CRV)
        werte = []
        for _lauf in range(a.blockplacebo):
            gew = ziel_arr.copy()
            for reihe in reihen:
                if len(reihe) < 2 * a.blocklaenge:
                    continue
                # Wandernde Blockgrenzen (2.47) - feste liessen immer
                # dieselben Anker gemeinsam reisen.
                v = int(rngb.integers(0, a.blocklaenge))
                teile = ([reihe[:v]] if v else []) + [
                    reihe[s:s + a.blocklaenge]
                    for s in range(v, len(reihe), a.blocklaenge)]
                neu = np.concatenate([teile[j] for j in
                                      rngb.permutation(len(teile))])
                gew[reihe] = ziel_arr[neu]
            werte.append(float(gew[ist_h].mean()) - schwelle_be)
        schwelle_b = float(np.quantile(werte, 0.95))
        print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
        print(f"  groesster Zufallswert  {100 * max(werte):+.1f} Punkte")
        print(f"  SCHWELLE (95 %)        {100 * schwelle_b:+.1f} Punkte")
        print(f"  gemessen (H)           {100 * h_abstand:+.1f} Punkte "
              f"auf {h_n} Faellen")
        # ⚠️ 2.48 - liegt der Messwert nahe an der Schwelle, entscheidet der
        # Schaetzfehler der Schwelle das Urteil. Dann gilt gar nichts.
        streu = float(np.std(werte)) / math.sqrt(len(werte))
        if abs(h_abstand - schwelle_b) < 2 * streu:
            print(f"  ⚠️ ZU KNAPP - der Abstand ({100 * abs(h_abstand - schwelle_b):.1f} "
                  f"Punkte) liegt im Schaetzfehler der Schwelle")
            print("     (Methodik 2.48). Hier gilt nichts, bevor die Zahl der")
            print("     Laeufe erhoeht ist.")
        else:
            print("  -> " + ("TRAEGT" if h_abstand > schwelle_b else
                             "TRAEGT NICHT - die Struktur erklaert nichts, "
                             "was die Zeitstruktur nicht auch hergibt"))

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "gruppen": ergebnis, "phasen": phasen,
            "schwelle_block": schwelle_b, "h_abstand": h_abstand},
            ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
