"""Aus dem Kettennaht-Lauf eine ENTSCHEIDUNG machen, nicht eine Tabelle.

Der Lauf selbst berichtet Verhalten - Konfidenz, Hebel, Richtung,
Selbstzustimmung. Das beantwortet nur die halbe Frage. Die andere Haelfte
(Nutzer, 09.08.): *"Reicht uns die Messung um Loesungen umzusetzen?"* Dafuer
muss dazukommen, ob das geaenderte Verhalten auch BESSER ist - sonst waere ein
Eingriff, der mehr Signale erzeugt, Lockerung statt Qualitaet.

DIE ZWEI FRAGEN UND IHRE JEWEILS RICHTIGE MESSGROESSE - sie sind bewusst
verschieden:

  1. SCHLAEGT DER EINSTIEG DEN ZUFALL?
     Gemessen an der Zielquote gegen `1/(1+CRV)`, und zwar auf den STATISCHEN
     Barrieren. Grund: die Breakeven-Formel folgt aus der Barrieren-Geometrie
     (das Ziel liegt CRV-mal weiter als der Stop). Wer sie gegen ein Ergebnis
     unter Trailing-Stop haelt, vergleicht zwei verschiedene Spiele.
     Zensierung ueber die kumulative Inzidenz (Aalen-Johansen), NICHT ueber
     "Ziel durch aufgeloeste" - das war der Fehler vom 02.08.

  2. WAS BRINGT ES WIRTSCHAFTLICH?
     Gemessen am R-Multiple unter der LIVE gefahrenen Ausstiegsregel
     (`dyn_r`, Trailing ab +1R), zusaetzlich in der auf 3 Tage gekappten
     Variante (`dyn3_r`) als konservative Untergrenze.

DER WAECHTER MIT VORRANG. Eine Verbesserung, die aus NICHTHANDELN stammt,
zaehlt nicht. Bei 35 Verlierern gegen 3 Gewinner ist Nichthandeln immer die
punktbeste Strategie und trotzdem keine Loesung - genau daran haette am 09.08.
schon einmal ein Anbieter faelschlich gewonnen. Faellt die EROEFFNEN-Quote
eines Arms um mehr als 10 Prozentpunkte gegen die Grundlinie, wird sein
R-Gewinn ausdruecklich als moeglicherweise erschlichen markiert.

GEPAART JE ANKER, geclustert je SYMBOL: alle Arme sehen denselben Anker, also
kuerzen sich Symbol und Zeitpunkt heraus. Die verbleibende Streuung sitzt
zwischen den Symbolen - deshalb Cluster-Bootstrap und Wild-Cluster-Test
(Cameron/Gelbach/Miller: cluster-robuste Verfahren ueber-verwerfen bei 5 bis
30 Clustern, und wir liegen mittendrin).

    python werte_kettennaht_aus.py --datei kettennaht.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict

from agent.krypto.backward_tracking import kumulative_inzidenz
from bewerte_dynamisch import breakeven_trefferquote
from bewerte_fakt_wirkung import _cluster_bootstrap, _wild_cluster_p_wert

GRUNDLINIE = "A1"
RAUSCHARM = "A2"
EROEFFNEN_EINBRUCH_PP = 10.0

# --- WAECHTER, nachgezogen am 09.08. nach drei Fehlurteilen -------------
#
# Der Auswerter hat an diesem Tag "WIRKSAM" gemeldet, wo nichts nachweisbar
# war. Drei Ursachen, drei Waechter:
#
#   1. ZELLENGROESSE. Ein Richtungsvergleich mit n=3 bekam dasselbe Urteil wie
#      einer mit n=36. Unter MIN_ZELLE wird gar nicht mehr geurteilt.
#   2. GLEICHE FALLMENGE. Der Richtungsfilter lief JE ARM - Q_alt hatte 3
#      LONG-Faelle, Q_neu 4, teils andere. Die "gepaarte Differenz" verglich
#      damit zwei Mittelwerte ueber verschiedene Mengen. Jetzt wird auf der
#      SCHNITTMENGE gerechnet.
#   3. RAUSCHBODEN. Fehlt der A2-Arm, meldete der Auswerter "0,00" und liess
#      damit jeden noch so kleinen Effekt als Befund durch. Jetzt ist er ein
#      Pflichtparameter, wenn A2 fehlt.
#
# Dazu zwei Ausweise, die vorher fehlten und die den Befund vom 09.08. gekippt
# haben: Beitrags-Konzentration (BTC trug 30 % eines Effekts - ohne BTC hielt
# er nicht) und die Zahl der Vergleiche (vier Arme gegen A1 heisst rund 19 %
# Wahrscheinlichkeit, dass einer zufaellig die 5-%-Schwelle trifft).
MIN_ZELLE = 8
MIN_SYMBOLE = 5


def _gepaart(a: list[dict], b: list[dict], feld: str):
    idx = {(z["symbol"], z["datum"]): z for z in a}
    diffs, symbole = [], []
    for z in b:
        v = idx.get((z["symbol"], z["datum"]))
        if not v:
            continue
        x, y = v.get(feld), z.get(feld)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            diffs.append(float(y) - float(x))
            symbole.append(z["symbol"])
    return diffs, symbole


def _konzentration(diffs: list[float], symbole: list[str]) -> dict:
    """Traegt ein einzelnes Symbol den Effekt - und haelt er ohne dieses?

    WARUM PFLICHT: am 09.08. trug BTC 30,2 % eines R-Effekts, dessen Intervall
    die Null ausschloss. Ohne BTC lag das Intervall wieder auf der Null
    (wild p 0,105). Ein Effekt, der an einem Symbol haengt, ist keiner - das
    steht so in der Methodik und fehlte hier trotzdem im Code.
    """
    je: dict[str, float] = defaultdict(float)
    for s, x in zip(symbole, diffs):
        je[s] += x
    summe = sum(je.values())
    if not je or summe == 0:
        return {}
    # Das Symbol, das am meisten IN DIE RICHTUNG DES EFFEKTS zieht.
    groesstes = (min(je, key=je.get) if summe < 0 else max(je, key=je.get))
    anteil = je[groesstes] / summe
    ohne = [(s, x) for s, x in zip(symbole, diffs) if s != groesstes]
    aus = {"groesstes_symbol": groesstes, "anteil": anteil,
           "n_ohne": len(ohne)}
    if len(ohne) >= 3:
        w = [x for _, x in ohne]
        sym = [s for s, _ in ohne]
        u, o = _cluster_bootstrap(w, sym)
        aus.update({"wirkung_ohne": statistics.fmean(w), "ci_unten_ohne": u,
                    "ci_oben_ohne": o,
                    "wild_p_ohne": _wild_cluster_p_wert(w, sym),
                    "haelt_ohne": bool(u is not None and (u > 0 or o < 0))})
    return aus


def _wirkung(a: list[dict], b: list[dict], feld: str,
             gleiche_menge: bool = False) -> dict | None:
    """`gleiche_menge` erzwingt die SCHNITTMENGE beider Arme.

    Noetig bei Richtungsvergleichen: dort filtert man je Arm nach der vom
    Modell GEWAEHLTEN Richtung, und die kann sich zwischen den Armen
    unterscheiden. Ohne den Schnitt vergleicht man zwei Mittelwerte ueber
    verschiedene Faelle und nennt es gepaart."""
    if gleiche_menge:
        schluessel = ({(z["symbol"], z["datum"]) for z in a}
                      & {(z["symbol"], z["datum"]) for z in b})
        a = [z for z in a if (z["symbol"], z["datum"]) in schluessel]
        b = [z for z in b if (z["symbol"], z["datum"]) in schluessel]
    diffs, symbole = _gepaart(a, b, feld)
    if len(diffs) < 3:
        return None
    unten, oben = _cluster_bootstrap(diffs, symbole)
    aus = {"n": len(diffs), "symbole": len(set(symbole)),
           "wirkung": statistics.fmean(diffs), "ci_unten": unten,
           "ci_oben": oben, "wild_p": _wild_cluster_p_wert(diffs, symbole)}
    aus["belastbar"] = (len(diffs) >= MIN_ZELLE
                        and len(set(symbole)) >= MIN_SYMBOLE)
    aus["konzentration"] = _konzentration(diffs, symbole)
    return aus


def _zufallsvergleich(zeilen: list[dict], horizont: int = 14) -> dict | None:
    """Zielquote gegen 1/(1+CRV) - auf den STATISCHEN Barrieren, je CRV-Band.

    Die Latte haengt am CRV: bei 2,0 liegt sie bei 33,3 %, bei 3,0 bei 25,0 %.
    Ein Gesamtmittel ueber Baender vermischt Latten verschiedener Hoehe und ist
    deshalb bedeutungslos.
    """
    baender = [(1.0, 2.0), (2.0, 3.0), (3.0, 5.0), (5.0, 99.0)]
    aus = []
    for lo, hi in baender:
        teil = [z for z in zeilen
                if isinstance(z.get("crv"), (int, float)) and lo <= z["crv"] < hi
                and isinstance(z.get("nachrangig_statisch"), dict)]
        if len(teil) < 8:
            continue
        ereignisse = [(z["nachrangig_statisch"]["tag"],
                       z["nachrangig_statisch"]["ausgang"], z["symbol"])
                      for z in teil]
        # `simuliere`-Ausgaenge heissen ziel/stop/zensiert - genau die drei
        # Arten, die kumulative_inzidenz() erwartet.
        ki = kumulative_inzidenz(ereignisse, horizont)
        crv_med = statistics.median(z["crv"] for z in teil)
        latte = breakeven_trefferquote(crv_med)
        aus.append({
            "band": f"{lo:.0f}-{hi:.0f}", "n": len(teil),
            "crv_median": crv_med,
            "ziel_anteil": ki.get("ziel_anteil"),
            "breakeven": latte,
            "vorsprung_pp": ((ki.get("ziel_anteil") or 0) - latte) * 100,
            "aufloesungsquote": ki.get("aufloesungsquote"),
        })
    return {"baender": aus} if aus else None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datei", required=True)
    p.add_argument("--horizont", type=int, default=14)
    p.add_argument("--rauschboden", type=float, default=None,
                   help="Pflicht, wenn die Datei keinen A2-Arm hat. Gemessen 09.08.: gemini 0.83, openrouter 2.20.")
    args = p.parse_args()

    daten = json.loads(open(args.datei, encoding="utf-8").read())
    zeilen = daten["zeilen"]
    arme = list(zeilen)
    basis = zeilen.get(GRUNDLINIE, [])
    if not basis:
        print(f"Kein {GRUNDLINIE}-Arm in der Datei.")
        return 1

    print("=" * 94)
    print("1  VERHALTEN - aendert der Eingriff etwas?")
    boden = _wirkung(basis, zeilen.get(RAUSCHARM, []), "konfidenz")
    if boden:
        schwelle = abs(boden["wirkung"])
        print(f"   Rauschboden (A1 gegen A2, identische Eingabe): "
              f"{schwelle:.2f} Konfidenzpunkte, n={boden['n']}")
    elif args.rauschboden is not None:
        schwelle = args.rauschboden
        print(f"   Rauschboden UEBERNOMMEN: {schwelle:.2f} Punkte "
              f"(kein A2-Arm in dieser Datei)")
    else:
        # Frueher stand hier stillschweigend 0,00 - und damit galt jeder noch
        # so kleine Effekt als ueber dem Rauschen. Genau so entstand am
        # 09.08. ein "WIRKSAM" ohne Grundlage.
        print("   ABBRUCH: kein A2-Arm und kein --rauschboden angegeben.")
        print("   Ohne Rauschboden ist keine Aussage moeglich - ein Effekt ist")
        print("   nur gegen die Streuung bei IDENTISCHER Eingabe lesbar.")
        return 2
    print()
    print(f"{'Arm':22} {'n':>4} {'EROEFF':>7} {'LONG':>7} {'Konf':>8} "
          f"{'Hebel':>8} {'selbst-ja':>10}")
    eroeffnen = {}
    for arm in arme:
        z = zeilen[arm]
        if not z:
            continue
        eo = [x for x in z if x.get("action") == "ERÖFFNEN"]
        eroeffnen[arm] = len(eo) / len(z)
        mf = [x for x in z if x.get("fazit_folgen")]
        ja = sum(1 for x in mf if x["fazit_folgen"] == "ja")
        lo = [x for x in z if x.get("richtung")]
        lq = (sum(1 for x in lo if x["richtung"] == "LONG") / len(lo)) if lo else None
        wk = _wirkung(basis, z, "konfidenz")
        wh = _wirkung(basis, z, "hebel")
        print(f"{arm:22} {len(z):4} {eroeffnen[arm]:6.1%} "
              f"{(lq if lq is not None else 0):6.1%} "
              f"{(wk['wirkung'] if wk else 0):+8.2f} "
              f"{(wh['wirkung'] if wh else 0):+8.2f} "
              f"{(ja / len(mf) if mf else 0):9.1%}")
    print("   Konf/Hebel sind DIFFERENZEN gegen A1, gepaart je Anker.")
    print(f"   Alles unter {max(schwelle, 1.0):.2f} Punkten ist Rauschen.")

    print()
    print("=" * 94)
    print("2  ERGEBNIS - ist das geaenderte Verhalten BESSER?")
    print(f"{'Arm':22} {'dyn R':>9} {'gg. A1':>9} {'Intervall':>20} "
          f"{'wild p':>7} {'gekappt R':>10} {'Waechter':>12}")
    for arm in arme:
        z = zeilen[arm]
        rs = [x["dyn_r"] for x in z if isinstance(x.get("dyn_r"), (int, float))]
        r3 = [x["dyn3_r"] for x in z if isinstance(x.get("dyn3_r"), (int, float))]
        w = _wirkung(basis, z, "dyn_r") if arm != GRUNDLINIE else None
        ci = (f"[{w['ci_unten']:+.3f}; {w['ci_oben']:+.3f}]"
              if w and w["ci_unten"] is not None else "")
        # DER WAECHTER: ist der R-Gewinn womoeglich nur Nichthandeln?
        einbruch = (eroeffnen.get(GRUNDLINIE, 0) - eroeffnen.get(arm, 0)) * 100
        wache = ""
        if arm != GRUNDLINIE and einbruch > EROEFFNEN_EINBRUCH_PP:
            wache = f"EROEFF -{einbruch:.0f}pp"
        print(f"{arm:22} {(statistics.fmean(rs) if rs else 0):+9.3f} "
              f"{(w['wirkung'] if w else 0):+9.3f} {ci:>20} "
              f"{(w['wild_p'] if w and w['wild_p'] is not None else float('nan')):7.3f} "
              f"{(statistics.fmean(r3) if r3 else 0):+10.3f} {wache:>12}")
    print("   'Waechter' markiert Arme, deren R-Gewinn aus NICHTHANDELN stammen")
    print("   koennte. Ein solcher Gewinn zaehlt nicht als Loesung.")
    n_vergleiche = len([a for a in arme if a not in (GRUNDLINIE, RAUSCHARM)])
    if n_vergleiche > 1:
        zufall = 1 - (0.95 ** n_vergleiche)
        print(f"   MEHRFACHVERGLEICH: {n_vergleiche} Arme gegen {GRUNDLINIE}. "
              f"Unter reinem Zufall trifft in rund {zufall:.0%} der Faelle")
        print("   mindestens einer die 5-%-Schwelle. Ein einzelner Grenzwert")
        print("   (p um 0,05) ist damit KEIN Nachweis.")
    print()
    print("   BEITRAGS-KONZENTRATION - traegt ein Symbol den Effekt?")
    for arm in arme:
        if arm in (GRUNDLINIE, RAUSCHARM):
            continue
        w = _wirkung(basis, zeilen[arm], "dyn_r")
        k = (w or {}).get("konzentration") or {}
        if not k:
            continue
        marke = ""
        if "haelt_ohne" in k and not k["haelt_ohne"]:
            marke = "   <-- HAELT OHNE DIESES SYMBOL NICHT"
        print(f"     {arm:22} groesstes Symbol {k['groesstes_symbol']:8} "
              f"{k['anteil']:5.1%} des Effekts"
              + (f", ohne es p={k['wild_p_ohne']:.3f}" if "wild_p_ohne" in k else "")
              + marke)

    print()
    print("=" * 94)
    print("3  SCHLAEGT DER EINSTIEG DEN ZUFALL? (statische Barrieren, je CRV-Band)")
    for arm in arme:
        zv = _zufallsvergleich(zeilen[arm], args.horizont)
        if not zv:
            print(f"   {arm:22} zu wenige Faelle je Band")
            continue
        for b in zv["baender"]:
            marke = "  <-- ueber dem Zufall" if b["vorsprung_pp"] > 0 else ""
            print(f"   {arm:22} CRV {b['band']:>5} n={b['n']:3}  "
                  f"Zielquote {(b['ziel_anteil'] or 0):5.1%}  "
                  f"Breakeven {b['breakeven']:5.1%}  "
                  f"Vorsprung {b['vorsprung_pp']:+5.1f} pp  "
                  f"(aufgeloest {(b['aufloesungsquote'] or 0):4.0%}){marke}")
    print("   Die Latte ist 1/(1+CRV), NICHT 50 %. Zielquote ueber kumulative")
    print("   Inzidenz, damit Zensierte nicht als Verlierer zaehlen.")

    print()
    print("=" * 94)
    print("4  WAS DAS FUER EINE MASSNAHME BEDEUTET")
    print("   Ein Eingriff ist umsetzungsreif, wenn ALLE DREI gelten:")
    print("     a) er aendert das Verhalten ueber dem Rauschboden,")
    print("     b) sein R-Effekt schliesst die Null aus,")
    print("     c) der EROEFFNEN-Waechter meldet nichts.")
    print("   Faellt eines weg, ist es ein Befund - aber keine Massnahme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
