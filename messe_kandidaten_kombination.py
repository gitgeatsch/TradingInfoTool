# -*- coding: utf-8 -*-
"""N-17b: tragen die zwei vorab bestätigten Kombinationen ZUSAMMEN mehr
als jede Größe einzeln? (04.09.2026)

## Warum

Nutzervorgabe 04.09.: *„auch wenn eine bestimmte Kombination keine
Aussage hat... sollten diese Indikatoren mit anderen in Kombination
gemessen werden."* Redundanzprüfung (F-205,
`messe_kandidaten_redundanz.py`) hat zwei vorab vorgeschlagene Paare als
unabhängig bestätigt — dieselben zwei bleiben hier stehen, keine neue
Suche:

    oi_aenderung  UND  funding_extrem   (ρ=+0,010 — Terminmarkt: der
                                          klassische "Squeeze"-Aufbau)
    turnover      UND  vola             (ρ=+0,046 — Umschlag mit echter
                                          Bewegung, nicht Umschlag allein)

## Vorabfestlegung

    Frage      Trennt die GEMEINSAME Extremlage beider Größen (an
               DEMSELBEN Tag, für DASSELBE Symbol) staerker als jede
               Groesse fuer sich (F-205)?
    Konstruktion  Ein Anker zaehlt zur Kombination nur, wenn BEIDE
               Groessen an diesem Tag JEWEILS im eigenen obersten
               Fuenftel stehen - zwei getrennte Schwellen (je 80.
               Perzentil), keine kombinierte Kennzahl.
    Massstab   DIESELBE Wirkungsformel wie jede Einzelmessung
               (`messe_form_kurz_gegen_lang.wahl_je_tag`):
               (Mittel der Gewaehlten - Mittel aller) x Anteil der
               Gewaehlten, macht die Auswahlgroesse Teil der Zahl (2.93,
               "Wirksamkeit statt Merkmalsmessung"). Tagesklammer,
               quotengleicher Zufall, Placebo-Band, Positivkontrolle,
               beide Historienhaelften - dieselbe Statistik
               (`messe_bewertungskennzahl.urteil_tage`), nur eine andere
               Auswahlregel als bei einer einzelnen Groesse.

## ⚠️⚠️ ERSTER ANLAUF WAR FALSCH - vom eigenen Selbsttest gefangen

Die erste Fassung waehlte das oberste Fuenftel des RANG-MINIMUMS beider
Groessen. Das klingt nach einem UND, ist aber keins: bei zwei
unabhaengigen Groessen liegt die Schwelle des Minimums, die genau 20 %
uebrig laesst, beim ~55. statt beim 80. Perzentil JE Groesse
(`(1-t)^2 = 0,20 -> t ~= 0,553`). Die Kombination waehlte damit ein
LOCKERERES Kriterium je Einzelgroesse als die Einzelmessung selbst -
der Selbsttest zeigte prompt, dass die Einzelgroesse "a allein"
STAERKER wirkte als die vermeintliche Kombination. Jetzt: zwei getrennte
80.-Perzentil-Schwellen, echtes UND, kleinere aber ehrlichere Auswahl.

    python messe_kandidaten_kombination.py [--selbsttest]
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                            # noqa: E402
import messe_eigenschaft_beitrag as B                           # noqa: E402
import messe_form_kurz_gegen_lang as FL                         # noqa: E402

FL.ZIEL = "frontloading"
ANTEIL = FL.ANTEIL  # 0.20 - dieselbe Fuenftel-Konvention wie ueberall

# ⚠️ VORAB BENANNT (siehe Modulkopf) - beide Groessen "oben" gewaehlt,
# dieselbe Richtung, in der sie in F-205 einzeln trugen.
KOMBINATIONEN = (
    ("oi_aenderung", "funding_extrem", "oben"),
    ("turnover", "vola", "oben"),
)


def _rang01(werte: list[float]) -> np.ndarray:
    r = np.argsort(np.argsort(np.asarray(werte, float)))
    return r / max(len(r) - 1, 1)


def wahl_je_tag_kombi(je_tag: dict, a: str, b: str, richtung: str = "oben",
                       mische=None, pflanze=None) -> dict:
    """Dieselbe Wirkungsformel wie `FL.wahl_je_tag`, aber mit einer
    ECHTEN Und-Auswahl: nur Anker, die in a UND in b je fuer sich im
    obersten (oder untersten) Fuenftel DIESES Tages stehen."""
    aus = {}
    for tag, zeilen in je_tag.items():
        gewaehlt, d = _auswahl_je_tag(zeilen, a, b, richtung, mische)
        if gewaehlt is None:
            continue
        n = int(gewaehlt.sum())
        if n < 1:
            continue
        vorteil = d[gewaehlt]
        if pflanze:
            vorteil = vorteil + float(pflanze)
        aus[tag] = float((vorteil.mean() - d.mean()) * (n / len(d)))
    return aus


def _auswahl_je_tag(zeilen: list, a: str, b: str, richtung: str,
                     mische=None):
    """DIE EINE Stelle, an der die UND-Auswahl entsteht - `wahl_je_tag_kombi`
    (die echte Messung) UND `_reinheit` (der Selbsttest-Gegencheck) rufen
    beide diese Funktion, nie eine eigene Kopie (Lehre vom selben Tag wie
    G-b: ein Test, der die Auswahl nachbaut statt aufzurufen, prueft sich
    selbst). Gibt `(gewaehlt_maske, ziel_array)` zurueck, oder `(None,
    None)` wenn zu wenige Anker."""
    z2 = [x for x in zeilen if a in x and b in x and FL._ziel(x) is not None]
    if len(z2) < FL.MIN_JE_TAG:
        return None, None
    wa = _rang01([x[a] for x in z2])
    wb = _rang01([x[b] for x in z2])
    if mische is not None:
        # BEIDE mit DERSELBEN Permutation - entkoppelt die Auswahl vom
        # Ziel, laesst aber die Paarbeziehung a-zu-b unberuehrt (sonst
        # wuerde die Negativkontrolle etwas anderes zerstoeren als die
        # Kandidat-Ziel-Kopplung).
        perm = mische.permutation(len(z2))
        wa, wb = wa[perm], wb[perm]
    schwelle = 1.0 - ANTEIL
    if richtung == "oben":
        gewaehlt = (wa >= schwelle) & (wb >= schwelle)
    else:
        gewaehlt = (wa <= ANTEIL) & (wb <= ANTEIL)
    d = np.array([FL._ziel(x) for x in z2])
    return gewaehlt, d


def bericht_kombi(name: str, je_tag: dict, a: str, b: str, rng,
                   richtung: str = "oben",
                   mit_positivkontrolle: bool = True) -> dict | None:
    """Dieselbe Berichtsform wie `FL.bericht_wahl` - EIN Statistikkern
    (`M.urteil_tage`), nur die Auswahl kommt aus `wahl_je_tag_kombi`."""
    print()
    print("=" * 92)
    print("%s  —  REGEL: BEIDE im %s Fuenftel  [Ziel %s]"
          % (name, "obersten" if richtung == "oben" else "untersten",
             FL.ZIEL))
    print("=" * 92)
    d = wahl_je_tag_kombi(je_tag, a, b, richtung)
    if len(d) < 60:
        print("  zu wenige Tage (%d) - uebersprungen" % len(d))
        return None
    zeilen = [x for z in je_tag.values() for x in z if a in x and b in x]
    syms = len({x["sym"] for x in zeilen})
    print("  %d Anker · %d Symbole · %d Kalendertage" % (len(zeilen), syms, len(d)))
    block = max(90, FL.LANG * 3)
    echt = M.urteil_tage("  NETTO (die Wirkung)", d, rng, block)
    M.urteil_tage("  Negativkontrolle",
                  wahl_je_tag_kombi(je_tag, a, b, richtung, mische=rng),
                  rng, block)
    tage = sorted(d)
    mitte = tage[len(tage) // 2]
    h1 = M.urteil_tage("    erste Haelfte",
                       {t: v for t, v in d.items() if t < mitte}, rng, block)
    h2 = M.urteil_tage("    zweite Haelfte",
                       {t: v for t, v in d.items() if t >= mitte}, rng, block)
    if mit_positivkontrolle:
        for s in (0.02, 0.05):
            M.urteil_tage("  Positivkontrolle %+.2f R" % s,
                          wahl_je_tag_kombi(je_tag, a, b, richtung,
                                            pflanze=s), rng, block)
    haelften_einig = (h1 and h2
                      and (h1["mittel"] > 0) == (h2["mittel"] > 0))
    return {"echt": echt, "haelften_einig": bool(haelften_einig)}


def _reinheit(je_tag: dict, a: str, b: str | None, art: str) -> float:
    """Ueberschuss PRO AUSGEWAEHLTEM Anker, gepoolt ueber alle Tage - OHNE
    Anteils-Gewichtung. `art='und'` ruft DIESELBE Auswahlfunktion wie die
    echte Messung (`_auswahl_je_tag`) - keine zweite, eigene Kopie der
    UND-Logik. `art='einzeln'` waehlt nur `a` >= 80. Perzentil, ueber
    `FL.wahl_je_tag`s eigene Rang-Logik nachgebildet (dort gibt es keinen
    Roh-Rueckgabemodus - deshalb hier minimal nachgebaut, nur fuer den
    Vergleichswert, NICHT fuer das Pruefergebnis selbst)."""
    gewaehlt_werte, alle_werte = [], []
    for zeilen in je_tag.values():
        if art == "und":
            gewaehlt, d = _auswahl_je_tag(zeilen, a, b, "oben")
            if gewaehlt is None:
                continue
        else:
            z2 = [x for x in zeilen if a in x and FL._ziel(x) is not None]
            if len(z2) < FL.MIN_JE_TAG:
                continue
            wa = _rang01([x[a] for x in z2])
            gewaehlt = wa >= 0.8
            d = np.array([FL._ziel(x) for x in z2])
        gewaehlt_werte.extend(d[gewaehlt].tolist())
        alle_werte.extend(d.tolist())
    if not gewaehlt_werte:
        return 0.0
    return float(np.mean(gewaehlt_werte) - np.mean(alle_werte))


def selbsttest() -> bool:
    """Zwei getrennte Pruefungen - eine mechanisch, eine statistisch.

    ⚠️⚠️ ERSTER ANLAUF fiel durch (siehe Modulkopf) - die Auswahl war zu
    lasch konstruiert. Jetzt:

    1. MECHANISCH: waehlt `wahl_je_tag_kombi` wirklich nur Anker, die in
       BEIDEN Groessen ueber dem 80. Perzentil stehen? Reine
       Konstruktionspruefung, kein Signal noetig.
    2. STATISTISCH: ist die Kombinationswirkung STAERKER als jede
       Einzelwirkung, wenn der wahre Effekt NUR in der Konjunktion
       sitzt?"""
    rng = np.random.default_rng(5)
    ok = True

    # ---- 1: mechanische Pruefung -----------------------------------
    je_tag = {}
    for tag in range(50):
        n = 40
        a = rng.uniform(size=n)
        b = rng.uniform(size=n)
        je_tag[f"tag{tag}"] = [
            {"sym": f"S{i}", "a": float(a[i]), "b": float(b[i]),
             "frontloading": 0.0, "r_kurz": 0.0, "r_rest": 0.0}
            for i in range(n)]
    treffer_a, treffer_b, groessen = [], [], []
    for tag, zeilen in je_tag.items():
        wa = _rang01([z["a"] for z in zeilen])
        wb = _rang01([z["b"] for z in zeilen])
        gewaehlt = (wa >= 0.8) & (wb >= 0.8)
        groessen.append(int(gewaehlt.sum()))
        if gewaehlt.any():
            treffer_a.append(float(np.mean([z["a"] for z, g in
                                            zip(zeilen, gewaehlt) if g])))
            treffer_b.append(float(np.mean([z["b"] for z, g in
                                            zip(zeilen, gewaehlt) if g])))
    ra = sum(treffer_a) / len(treffer_a) if treffer_a else 0.0
    rb = sum(treffer_b) / len(treffer_b) if treffer_b else 0.0
    print(f"  Mechanik: mittlere Anzahl Gewaehlte/Tag "
          f"{sum(groessen)/len(groessen):.1f} von 40 "
          f"(erwartet ~{40*ANTEIL*ANTEIL:.1f}); Mittel a={ra:.2f} b={rb:.2f}")
    if not (ra > 0.85 and rb > 0.85):
        print("  ✖ FEHLER: die Kombinationsauswahl haette in BEIDEN "
              "Groessen deutlich ueber 0,80 liegen muessen")
        ok = False

    # ---- 2: statistische Pruefung -----------------------------------
    je_tag2 = {}
    for tag in range(400):
        n = 40
        a = rng.uniform(size=n)
        b = rng.uniform(size=n)
        zeilen = []
        for i in range(n):
            beide_hoch = (a[i] > 0.8) and (b[i] > 0.8)
            r_kurz = rng.normal(0.08 if beide_hoch else 0.0, 0.05)
            r_rest = rng.normal(0.0, 0.05)
            weg = abs(r_kurz) + abs(r_rest)
            zeilen.append({
                "sym": f"S{i}",
                "a": float(a[i]), "b": float(b[i]),
                "r_kurz": r_kurz, "r_rest": r_rest,
                "frontloading": (abs(r_kurz) / weg) if weg > 1e-9 else None})
        je_tag2[f"tag{tag}"] = zeilen

    rng2 = np.random.default_rng(1)
    erg_kombi = bericht_kombi("SELBSTTEST kombi", je_tag2, "a", "b", rng2,
                              mit_positivkontrolle=False)
    erg_a = FL.bericht_wahl("SELBSTTEST a allein", je_tag2, "a", rng2,
                            mit_positivkontrolle=False)
    erg_b = FL.bericht_wahl("SELBSTTEST b allein", je_tag2, "b", rng2,
                            mit_positivkontrolle=False)
    w_k = erg_kombi["echt"]["mittel"] if erg_kombi and erg_kombi["echt"] else None
    w_a = erg_a["echt"]["mittel"] if erg_a and erg_a["echt"] else None
    w_b = erg_b["echt"]["mittel"] if erg_b and erg_b["echt"] else None
    print(f"  Wirkung (anteilgewichtet) Kombi={w_k:+.4f}  a allein={w_a:+.4f}  "
          f"b allein={w_b:+.4f}")
    # ⚠️⚠️ NICHT "Wirkung Kombi > Wirkung Einzelgroesse" verlangen - das
    # war der zweite Denkfehler (04.09.2026, selbst gefunden). Die
    # anteilgewichtete Wirkung misst "wieviel Vorteil bringt der ganze
    # Filter", nicht "wie sauber ist die Auswahl" - eine breite Auswahl,
    # die JEDEN wahren Treffer mitnimmt (a>0,8 ist hier notwendig fuer den
    # Effekt), kann bei dieser Gewichtung mit einer schmaleren, reineren
    # Auswahl gleichziehen, obwohl die Kombination die sauberere ist.
    # Die richtige Pruefgroesse ist die REINHEIT: der Ueberschuss PRO
    # AUSGEWAEHLTEM Anker, ohne die Anteils-Gewichtung - dort MUSS die
    # Kombination klar vorn liegen, weil ihre Auswahl (a>0,8 UND b>0,8)
    # ausschliesslich wahre Treffer enthaelt, "a allein" aber zu 80 % aus
    # Rauschen (a>0,8, b<=0,8) besteht.
    reinheit_k = _reinheit(je_tag2, "a", "b", "und")
    reinheit_a = _reinheit(je_tag2, "a", None, "einzeln")
    reinheit_b = _reinheit(je_tag2, "b", None, "einzeln")
    print(f"  Reinheit (Ueberschuss je Ausgewaehltem) Kombi={reinheit_k:+.4f}  "
          f"a allein={reinheit_a:+.4f}  b allein={reinheit_b:+.4f} "
          "(Kombi muss beide klar uebertreffen)")
    if not (reinheit_k > reinheit_a * 1.5 and reinheit_k > reinheit_b * 1.5):
        print("  ✖ FEHLER: die Kombinationsauswahl haette deutlich "
              "reiner sein muessen als jede Einzelauswahl")
        ok = False

    print("  ✔ Selbsttest bestanden" if ok else "  ✖ SELBSTTEST FEHLGESCHLAGEN")
    return ok


def main():
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1

    print("Lade Reihen und baue Anker...", flush=True)
    reihen = B.lade()
    zusatz = FL.lade_zusatz()
    je_tag = FL.baue(reihen, zusatz)
    print(f"{len(je_tag)} Kalendertage")

    rng = np.random.default_rng(FL.SAAT)
    for a, b, richtung in KOMBINATIONEN:
        bericht_kombi(f"KOMBINATION {a} UND {b}", je_tag, a, b, rng,
                      richtung=richtung)


if __name__ == "__main__":
    sys.exit(main())
