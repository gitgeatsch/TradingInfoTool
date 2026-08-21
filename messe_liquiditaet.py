"""Braucht H Liquiditaet? (20.08.2026, Umbauplan 116)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DIE LUECKE. `_reihen_roh` liefert seit jeher das Volumen - und JEDES
Messwerkzeug seit Kapitel 99 beginnt mit `del v`. Wir haben es zwoelf Kapitel
lang weggeworfen.

DREI UNABHAENGIGE GRUENDE, DIESE BEDINGUNG ZU PRUEFEN:

  1. DER MECHANISMUS. Unterstuetzung und Widerstand sind ein
     KOORDINATIONSphaenomen - sie wirken, weil viele Teilnehmer dieselbe
     Marke beobachten und dort handeln. In einem duennen Markt gibt es diese
     Vielen nicht. Liquiditaet ist damit keine Zusatzbedingung, sondern die
     VORBEDINGUNG dafuer, dass H ueberhaupt Sinn ergeben kann.

  2. DIE LITERATUR. Osler (2000, Fed New York) findet, dass Unterstuetzungs-
     und Widerstandsniveaus Trendunterbrechungen vorhersagen - "the levels'
     predictive power is found to vary across the exchange rates and firms
     examined". Der Effekt ist also INSTRUMENTABHAENGIG.
     https://ideas.repec.org/a/fip/fednep/y2000ijulp53-68nv.6no.2.html

  3. DIE PRAXISLITERATUR sagt dasselbe: Marken brechen eher in Maerkten mit
     wenig Liquiditaet. ⚠️ Sie ist KEIN Beleg - dieselben Quellen behaupten
     auch, mehrfach getestete Marken hielten besser, und das haben wir in
     Kapitel 112 gemessen: es traegt nicht.

⚠️ UND SCHON VOR DER MESSUNG EIN VERDACHT. H liegt bei einem Median-
Tagesumsatz von 20,7 Mio. USD gegen 5,1 Mio. im Schnitt - viermal liquider.
Damit ist Liquiditaet zugleich HYPOTHESE und KONFUNDIERUNG: ein Teil von H's
Vorsprung koennte schlicht daher kommen, dass H in groesseren Werten
vorkommt.

ZWEI FRAGEN, wie in Kapitel 111 als ZERLEGUNG statt als Fallbeil (2.51):

    L1  BEDINGUNG   Traegt H in liquiden Werten mehr als in illiquiden?
                    Vorhergesagt: ja. Eine Zahl - die beiden obersten
                    Umsatzfuenftel gegen die beiden untersten.

    L2  ZERLEGUNG   Wie viel von H's Vorsprung erklaert die Liquiditaet?
                    Restvorsprung INNERHALB gleicher Umsatzbaender.
                    Und die Liquiditaet SELBST als eigener Kandidat - faellt
                    der Rest auf null, ist das ein TAUSCH, kein Ende.

⚠️ UMSATZ, NICHT STUECKZAHL. Stueckzahlen sind zwischen Symbolen bedeutungslos
(BTC handelt in Coins, FLOKI in Milliarden). Gerechnet wird Kurs x Volumen,
Median der letzten 60 Kerzen, NUR rueckwaerts.

⚠️ UND DIE KOSTENBEREINIGUNG GEHOERT DAZU. Umsatz haengt an der Groesse, Groesse
an der Volatilitaet - der ATR-Kanal ist in diesem Projekt viermal unter neuem
Namen aufgetreten. Ausgewiesen wird deshalb auch der Vorsprung INNERHALB
gleicher Stopbaender.

    python messe_liquiditaet.py [--blockplacebo 120]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_marken import bewerte, laufe                        # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif        # noqa: E402

BAENDER = 5
MIN_FAELLE = 300
BLOCKLAENGE = 250


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def _band(x, grenzen) -> int:
    return int(min(np.searchsorted(grenzen, x, side="right") - 1, BAENDER - 1))


def _je_band(faelle, grenzen, feld: str) -> list[dict]:
    zeilen = []
    for b in range(BAENDER):
        drin = [f for f in faelle if _band(f[feld], grenzen) == b]
        h = [f for f in drin if f["frei"] and f["gedeckt"]]
        r = [f for f in drin if not (f["frei"] and f["gedeckt"])]
        nh, qh = _quote(h)
        nr, qr = _quote(r)
        _x, _y, ab_h = bewerte(h, "krypto")
        _u, _v, ab_a = bewerte(drin, "krypto")
        zeilen.append({"band": b, "u": grenzen[b], "o": grenzen[b + 1],
                       "n_h": nh, "n_rest": nr, "quote_h": qh,
                       "quote_rest": qr, "abstand_h": ab_h,
                       "abstand_alle": ab_a})
    return zeilen


def _rest(zeilen) -> float:
    """Gewichtete Summe der Binnendifferenzen - direkte Standardisierung."""
    summe = gew = 0.0
    for z in zeilen:
        if z["n_h"] >= MIN_FAELLE and z["n_rest"] >= MIN_FAELLE:
            summe += z["n_h"] * (z["quote_h"] - z["quote_rest"])
            gew += z["n_h"]
    return summe / gew if gew else float("nan")


def _l1(zeilen) -> float:
    """L1 als EINE Zahl: obere zwei Baender gegen untere zwei."""
    oben = [z for z in zeilen[-2:]
            if z["n_h"] >= MIN_FAELLE and z["n_rest"] >= MIN_FAELLE]
    unten = [z for z in zeilen[:2]
             if z["n_h"] >= MIN_FAELLE and z["n_rest"] >= MIN_FAELLE]
    if not oben or not unten:
        return float("nan")
    do = sum(z["n_h"] * (z["quote_h"] - z["quote_rest"]) for z in oben) \
        / sum(z["n_h"] for z in oben)
    du = sum(z["n_h"] * (z["quote_h"] - z["quote_rest"]) for z in unten) \
        / sum(z["n_h"] for z in unten)
    return do - du


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=120)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_liquiditaet.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("BRAUCHT H LIQUIDITAET?")
    print("  Der Mechanismus verlangt es: Marken wirken, weil VIELE sie")
    print("  beobachten. Zwoelf Kapitel lang haben wir das Volumen mit")
    print("  `del v` weggeworfen.")
    print("=" * 78)
    faelle = [f for f in _reif(laufe(a.db, a.klasse, fortschritt=True),
                               MINDESTALTER) if f["umsatz"]]
    h = [f for f in faelle if f["frei"] and f["gedeckt"]]
    print(f"  {len(faelle)} reife Anker mit Umsatz, davon {len(h)} in H")
    print(f"  Median-Tagesumsatz  H {np.median([f['umsatz'] for f in h]):,.0f}"
          f"  gegen alle {np.median([f['umsatz'] for f in faelle]):,.0f} USD")

    grenzen = np.quantile([f["umsatz"] for f in faelle],
                          np.linspace(0, 1, BAENDER + 1))
    zeilen = _je_band(faelle, grenzen, "umsatz")

    print("\n" + "-" * 78)
    print("L1 - JE UMSATZBAND: H gegen den Rest DESSELBEN Bandes")
    print("-" * 78)
    print(f"  {'Umsatz USD/Tag':26}{'H':>8}{'Quote H':>10}{'Rest':>9}"
          f"{'Quote Rest':>12}{'Diff':>8}{'Abst. H':>10}")
    for z in zeilen:
        name = f"{z['u']:,.0f} - {z['o']:,.0f}"
        if z["n_h"] < MIN_FAELLE or z["n_rest"] < MIN_FAELLE:
            print(f"  {name:26}{z['n_h']:8}   zu wenige")
            continue
        print(f"  {name:26}{z['n_h']:8}{100 * z['quote_h']:9.1f} %"
              f"{z['n_rest']:9}{100 * z['quote_rest']:11.1f} %"
              f"{100 * (z['quote_h'] - z['quote_rest']):+7.1f}"
              f"{100 * z['abstand_h']:+9.1f}")
    l1 = _l1(zeilen)
    print(f"\n  L1 - obere zwei Baender gegen untere zwei: "
          f"{100 * l1:+.1f} Punkte")

    print("\n" + "-" * 78)
    print("L2 - ZERLEGUNG (2.51): wie viel erklaert die Liquiditaet?")
    print("-" * 78)
    _n, qh = _quote(h)
    _m, qr = _quote([f for f in faelle if not (f["frei"] and f["gedeckt"])])
    roh_v = qh - qr
    rest_v = _rest(zeilen)
    print(f"  roher Vorsprung   {100 * roh_v:+.1f} Punkte")
    print(f"  Restvorsprung     {100 * rest_v:+.1f} Punkte "
          f"(bei gleichem Umsatz)")
    if roh_v:
        print(f"  -> Die Liquiditaet erklaert "
              f"{100 * (1 - rest_v / roh_v):.0f} % des Vorsprungs.")

    print("\n  DIE LIQUIDITAET ALS EIGENER KANDIDAT")
    print(f"  {'Umsatz USD/Tag':26}{'Faelle':>10}{'Abstand':>11}")
    for z in zeilen:
        n = z["n_h"] + z["n_rest"]
        if z["abstand_alle"] == z["abstand_alle"]:
            print(f"  {z['u']:,.0f} - {z['o']:,.0f}".ljust(28)
                  + f"{n:10}{100 * z['abstand_alle']:+10.1f}")

    # ---- KONTROLLE ------------------------------------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Kalenderzeit (2.52)")
    print("-" * 78)
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    ziel = np.array([f["ausgang"] == "ziel" for f in ent])
    ordnung: dict = {}
    for pos, f in enumerate(ent):
        ordnung.setdefault(f["sym"], []).append((f["i"], pos))
    reihen = []
    for v in ordnung.values():
        bl: list = []
        for idx, pos in sorted(v):
            if not bl or idx - bl[-1][0] >= a.blocklaenge:
                bl.append([idx, []])
            bl[-1][1].append(pos)
        if len(bl) >= 2:
            reihen.append([np.array(b[1]) for b in bl])
    print(f"  {len(reihen)} Reihen lang genug fuer mindestens zwei Bloecke")
    rng = np.random.default_rng(20260903)
    z1, z2, zmax = [], [], []
    for _lauf in range(a.blockplacebo):
        gew = ziel.copy()
        for bl in reihen:
            alle = np.concatenate(bl)
            gew[alle] = ziel[np.concatenate(
                [bl[j] for j in rng.permutation(len(bl))])]
        getauscht = [{**f, "ausgang": ("ziel" if g else "stop")}
                     for f, g in zip(ent, gew)]
        zz = _je_band(getauscht, grenzen, "umsatz")
        x1, x2 = _l1(zz), _rest(zz)
        if x1 == x1:
            z1.append(x1)
        if x2 == x2:
            z2.append(x2)
        gute = [x for x in (x1, x2) if x == x]
        if gute:
            zmax.append(max(gute))
    print(f"\n  {'Frage':28}{'gemessen':>12}{'Schwelle':>12}{'Urteil':>16}")
    ergebnis = {}
    for name, wert, zieh in (("L1 liquide vs illiquide", l1, z1),
                             ("L2 Restvorsprung", rest_v, z2)):
        if wert != wert or not zieh:
            print(f"  {name:28}{'zu wenige':>12}")
            continue
        s = float(np.quantile(zieh, 0.95))
        streu = float(np.std(zieh)) / math.sqrt(len(zieh))
        urteil = ("ZU KNAPP (2.48)" if abs(wert - s) < 2 * streu
                  else "traegt" if wert > s else "traegt nicht")
        ergebnis[name] = {"wert": wert, "schwelle": s, "urteil": urteil}
        print(f"  {name:28}{100 * wert:+11.1f}{100 * s:+11.1f}{urteil:>16}")
    if zmax:
        print(f"\n  ⚠️ Schwelle fuer das Maximum aus beiden Fragen: "
              f"{100 * float(np.quantile(zmax, 0.95)):+.1f} (2.49)")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "baender": zeilen, "l1": l1, "roh_vorsprung": roh_v,
            "rest_vorsprung": rest_v, "urteile": ergebnis},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
