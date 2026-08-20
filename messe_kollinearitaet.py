"""Sind es drei Hebel oder einer mit drei Namen? (20.08.2026, Umbauplan 103)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DIE FRAGE DES NUTZERS: *"ich war der Meinung, dass der Trichter so
funktioniert, dass ein Wert fast keine positive Auswirkung hat, aber die
richtige Kombination der Trichterwerte dann den Trichter der Optimierung
bildet."*

Das Prinzip stimmt und ist etabliert: schwache Einzelteile, starke
Konjunktion. Es hat aber eine harte Vorbedingung - DIE BESTANDTEILE MUESSEN
VERSCHIEDENE INFORMATION TRAGEN. Zwei Werte, die dasselbe messen, ergeben
zusammen nicht mehr als einer, sondern denselben Effekt doppelt gezaehlt.

⚠️ UND GENAU DAS IST HIER ZU BEFUERCHTEN. Drei Hebel, drei Messungen, ein
Verdacht:

    Marktphase Baer      +8,0 Punkte   (Kapitel 100)
    Driftband extrem     +1,9 Punkte   (Kapitel 102)
    Geometrie k=4        +5,6 Punkte   (Kapitel 101)

Alle drei laufen ueber DENSELBEN Kanal: hoher ATR -> weiter Stop in Prozent
-> Kosten_R = 2 x Gebuehr / Stopabstand sinkt -> Breakeven sinkt. Die U-Form
der Driftbaender ist der Beleg - nicht die RICHTUNG entscheidet, sondern der
BETRAG, und ein starker Trend heisst hoher ATR.

Wer die drei addiert, rechnet mit 15,5 Punkten, die es nicht gibt.

DIE PRUEFUNG, VORAB FESTGELEGT: das Geometrieraster wird INNERHALB von Phase
und Driftband gerechnet. Verglichen werden drei Zahlen:

    Einzeln    der staerkste Hebel fuer sich
    Summe      was herauskaeme, wenn sich die Hebel addierten
    Gemessen   die beste Zelle der Kombination

    Gemessen nahe SUMME     -> die Hebel sind verschieden, Kombination lohnt
    Gemessen nahe EINZELN   -> es ist ein Hebel mit drei Namen

⚠️ EINE ZELLE MUSS GENUG FAELLE HABEN. 5 Geometrien x 4 CRV x 3 Phasen x 5
Baender sind 300 Zellen; ohne Mindestzahl misst man Rauschen. Hier gilt 300
entschiedene Faelle, wie in den Nachbarmessungen.

⚠️ UND DIE PHASENPROBE BLEIBT: eine Kombination, die nur im Baermarkt traegt,
ist die Marktphasenwette mit anderem Namen.

    python messe_kollinearitaet.py [--klasse krypto]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                        # noqa: E402
from messe_drift_absolut import BAENDER, DRIFT_FENSTER, _band  # noqa: E402
from messe_geometrie import CRV_WERTE, K_WERTE               # noqa: E402
from simuliere_bremse import (MAX_TAGE, _marktphase,         # noqa: E402
                              _reihen_roh)

MIN_FAELLE = 300
BASIS_K, BASIS_CRV = 2.0, 2.0


def laufe(db: str, klasse: str) -> list[dict]:
    """Je Anker alle Geometrien - MIT Phase und Driftband am selben Anker.

    ⚠️ EINE STICHPROBE, NICHT VIELE. Wer je Kombination neu anlaeuft, misst
    teils Auswahl statt Wirkung."""
    roh = _reihen_roh(db, klasse)
    phase = _marktphase(roh)
    aus = []
    for sym, (c, h, l, v, a, off, d) in roh.items():
        del v, sym
        start = max(off, DRIFT_FENSTER) + 1
        for i in range(start, len(c) - 1):
            atr, einstieg, frueher = a[i - off], c[i], c[i - DRIFT_FENSTER]
            if not (atr > 0 and einstieg > 0 and frueher > 0):
                continue
            ph = phase.get(d[i], "unbekannt")
            bd = _band(einstieg / frueher - 1.0)
            for k in K_WERTE:
                stop = einstieg - k * atr
                if stop <= 0:
                    continue
                risiko = einstieg - stop
                for crv in CRV_WERTE:
                    ziel = einstieg + crv * risiko
                    ausgang = "abgelaufen"
                    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                        if l[j] <= stop:
                            ausgang = "stop"
                            break
                        if h[j] >= ziel:
                            ausgang = "ziel"
                            break
                    aus.append({"phase": ph, "band": bd, "k": k, "crv": crv,
                                "ausgang": ausgang,
                                "stop_relativ": float(risiko / einstieg)})
    return aus


def abstand(faelle, klasse: str) -> tuple[int, float]:
    """(Faelle, Abstand zum eigenen Breakeven). Der Breakeven wandert mit."""
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if len(ent) < MIN_FAELLE:
        return len(ent), float("nan")
    quote = sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)
    stop_rel = float(np.median([f["stop_relativ"] for f in ent]))
    gebuehr = TB.KOSTEN_JE_SEITE.get(klasse, 0.015)
    return len(ent), quote - TB.breakeven(2 * gebuehr / stop_rel,
                                          ent[0]["crv"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--placebo", type=int, default=0,
                    help="N Laeufe mit INNERHALB der Geometrie gewuerfelten "
                         "Ausgaengen - prueft, ob das Maximum aus 300 Zellen "
                         "auch zufaellig entstuende")
    ap.add_argument("--datei", default="messwerte_kollinearitaet.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DREI HEBEL ODER EINER MIT DREI NAMEN?")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse)
    print(f"  {len(faelle)} Anker-Geometrie-Paare")

    def teil(**wo):
        return [f for f in faelle
                if all(f[k] == v for k, v in wo.items() if v is not None)]

    # --- Ausgangspunkt und die drei Hebel einzeln ------------------------
    n0, a0 = abstand(teil(k=BASIS_K, crv=BASIS_CRV), a.klasse)
    print(f"\n  AUSGANGSPUNKT k={BASIS_K}, CRV={BASIS_CRV}, alle Lagen: "
          f"{100 * a0:+.1f} Punkte ({n0} Faelle)")

    print("\n" + "-" * 78)
    print("DIE DREI HEBEL EINZELN - jeweils gegen den Ausgangspunkt")
    print("-" * 78)
    hebel = {}
    # 1. Geometrie allein.
    beste_geo, wert_geo = None, -9.9
    for k in K_WERTE:
        for crv in CRV_WERTE:
            n, w = abstand(teil(k=k, crv=crv), a.klasse)
            if not math.isnan(w) and w > wert_geo:
                beste_geo, wert_geo = (k, crv), w
    hebel["Geometrie"] = wert_geo - a0
    print(f"  Geometrie   beste {beste_geo}: {100 * wert_geo:+.1f}  ->  "
          f"Gewinn {100 * hebel['Geometrie']:+.1f} Punkte")
    # 2. Phase allein.
    beste_ph, wert_ph = None, -9.9
    for ph in ("bulle", "seitwaerts", "baer"):
        n, w = abstand(teil(k=BASIS_K, crv=BASIS_CRV, phase=ph), a.klasse)
        if not math.isnan(w) and w > wert_ph:
            beste_ph, wert_ph = ph, w
    hebel["Phase"] = wert_ph - a0
    print(f"  Phase       beste '{beste_ph}': {100 * wert_ph:+.1f}  ->  "
          f"Gewinn {100 * hebel['Phase']:+.1f} Punkte")
    # 3. Driftband allein.
    beste_bd, wert_bd = None, -9.9
    for _u, _o, bd in BAENDER:
        n, w = abstand(teil(k=BASIS_K, crv=BASIS_CRV, band=bd), a.klasse)
        if not math.isnan(w) and w > wert_bd:
            beste_bd, wert_bd = bd, w
    hebel["Driftband"] = wert_bd - a0
    print(f"  Driftband   bestes '{beste_bd}': {100 * wert_bd:+.1f}  ->  "
          f"Gewinn {100 * hebel['Driftband']:+.1f} Punkte")

    summe = a0 + sum(hebel.values())
    print(f"\n  WENN SIE SICH ADDIERTEN: {100 * a0:+.1f} "
          + "".join(f"{100 * v:+.1f} " for v in hebel.values())
          + f"= {100 * summe:+.1f} Punkte")

    # --- Die Kombination, gemessen ---------------------------------------
    print("\n" + "-" * 78)
    print("DIE KOMBINATION, GEMESSEN - Geometrie INNERHALB Phase und Band")
    print("-" * 78)
    bestes, wert_komb, n_komb = None, -9.9, 0
    for ph in ("bulle", "seitwaerts", "baer"):
        for _u, _o, bd in BAENDER:
            for k in K_WERTE:
                for crv in CRV_WERTE:
                    n, w = abstand(teil(k=k, crv=crv, phase=ph, band=bd),
                                   a.klasse)
                    if not math.isnan(w) and w > wert_komb:
                        bestes, wert_komb, n_komb = (ph, bd, k, crv), w, n
    if bestes:
        ph, bd, k, crv = bestes
        print(f"  BESTE ZELLE: Phase '{ph}', Band '{bd}', k={k}, CRV={crv}")
        print(f"    {100 * wert_komb:+.1f} Punkte auf {n_komb} Faellen")

    print("\n" + "=" * 78)
    print("DIE ANTWORT")
    print("=" * 78)
    staerkster = max(hebel.values())
    einzeln = a0 + staerkster
    print(f"  staerkster Hebel allein   {100 * einzeln:+6.1f} Punkte")
    print(f"  wenn sie sich addierten   {100 * summe:+6.1f} Punkte")
    print(f"  gemessen kombiniert       {100 * wert_komb:+6.1f} Punkte")
    if summe > einzeln:
        anteil = (wert_komb - einzeln) / (summe - einzeln)
        print(f"\n  Von dem, was eine Addition verspraeche, sind "
              f"{100 * anteil:.0f} % eingetreten.")
        if anteil < 0.35:
            print("  -> ES IST EIN HEBEL MIT DREI NAMEN. Die Kombination")
            print("     dieser drei lohnt nicht; sie messen dasselbe.")
        elif anteil > 0.7:
            print("  -> DIE HEBEL SIND WEITGEHEND VERSCHIEDEN. Eine")
            print("     Konjunktion lohnt, und Schritt 2 hat Substanz.")
        else:
            print("  -> TEILWEISE UEBERLAPPEND. Ein Teil ist derselbe")
            print("     Effekt, ein Teil nicht.")
    # ⚠️ DIE GEGENPROBE ZUM MAXIMUM AUS 300 ZELLEN.
    #
    # Gesucht wurde ueber 3 Phasen x 5 Baender x 5 k x 4 CRV. Das Maximum aus
    # 300 Ziehungen ist auch bei reinem Zufall gross - und genau hier hat
    # dieses Projekt sich schon einmal getaeuscht (93.17).
    #
    # GEWUERFELT WIRD INNERHALB JEDER GEOMETRIE. Damit bleiben die legitimen
    # Unterschiede zwischen k und CRV erhalten (ein Ziel bei CRV 1,0 wird
    # oefter erreicht - das ist Arithmetik), und zerstoert wird nur die
    # Zuordnung zu Phase und Band, also genau die Behauptung.
    if a.placebo:
        print("\n" + "-" * 78)
        print(f"PLACEBO - {a.placebo} Laeufe, Ausgaenge INNERHALB der")
        print("  Geometrie gewuerfelt. Was hier herauskommt, ist das Maximum")
        print("  aus 300 Zellen bei reinem Zufall.")
        print("-" * 78)
        rng = np.random.default_rng(20260820)
        gebuehr = TB.KOSTEN_JE_SEITE.get(a.klasse, 0.015)
        # ⚠️ EINMAL INDIZIEREN, NICHT DREIHUNDERTMAL FILTERN. Die erste
        # Fassung ging je Zelle durch alle 850.000 Saetze - zwoelf Laeufe
        # waeren 255 Millionen Vergleiche gewesen und liefen in kein
        # vernuenftiges Zeitfenster.
        geo: dict = {}
        for f in faelle:
            if f["ausgang"] not in ("ziel", "stop"):
                continue
            g = geo.setdefault((f["k"], f["crv"]),
                               {"zelle": [], "ausgang": [], "stop": []})
            g["zelle"].append((f["phase"], f["band"]))
            g["ausgang"].append(f["ausgang"] == "ziel")
            g["stop"].append(f["stop_relativ"])
        for g in geo.values():
            g["zelle"] = np.array([f"{p}|{b}" for p, b in g["zelle"]])
            g["ausgang"] = np.array(g["ausgang"])
            g["stop"] = np.array(g["stop"])
        hoechste = []
        for _lauf in range(a.placebo):
            beste = -9.9
            for (k, crv), g in geo.items():
                gew = rng.permutation(g["ausgang"])
                for zelle in np.unique(g["zelle"]):
                    m = g["zelle"] == zelle
                    if m.sum() < MIN_FAELLE:
                        continue
                    quote = float(gew[m].mean())
                    stop_rel = float(np.median(g["stop"][m]))
                    w = quote - TB.breakeven(2 * gebuehr / stop_rel, crv)
                    beste = max(beste, w)
            hoechste.append(beste)
        schwelle = float(np.quantile(hoechste, 0.95))
        print(f"  groesster Zufallswert  {100 * max(hoechste):+.1f} Punkte")
        print(f"  SCHWELLE (95 %)        {100 * schwelle:+.1f} Punkte")
        print(f"  gemessen               {100 * wert_komb:+.1f} Punkte")
        print("  -> " + ("TRAEGT - ueber dem, was der Zufall aus 300 Zellen "
                         "hergibt" if wert_komb > schwelle else
                         "NICHTS - das Maximum aus 300 Zellen entsteht auch "
                         "ohne jeden Zusammenhang"))

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "ausgangspunkt": a0, "hebel": hebel, "summe": summe,
            "kombiniert": wert_komb, "beste_zelle": str(bestes),
            "faelle_beste_zelle": n_komb}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
