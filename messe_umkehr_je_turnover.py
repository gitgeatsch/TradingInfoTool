# -*- coding: utf-8 -*-
"""N-17d: kippt die Kurzfrist-Umkehr bei hohem Turnover? (04.09.2026)

Vorabfestlegung: `Anforderungen_Umbau_28_08.md` 9.6, Abschnitt **N-17d**,
geschrieben BEVOR gerechnet wurde (Commit 2fcd9f8).

## Die Hypothese - EINE, vorab benannt

    H-N17d  Die Kurzfrist-Umkehr (oberstes Fuenftel `momentum_kurz` ->
            schlechterer Ausgang) ist bei NIEDRIGEM Turnover stark und
            KIPPT bei hohem Turnover.

Quelle: Lee/Swaminathan (*Journal of Finance* 2000, „Momentum Life
Cycle") - bei hohem Turnover kippt Umkehr in Fortsetzung. Dazu die
Kurzfrist-Umkehr selbst: Lehmann (1990), Jegadeesh (1990); in Krypto
repliziert (CTREND, *JFQA* 2025, `sma_5d` -2,90 %/Woche, t = -3,35).

⚠️ **Wir erfinden hier nichts.** Beide Bausteine stehen in der Literatur;
gemessen wird, ob sie BEI UNS und auf UNSEREM Horizont tragen.

## Die Geometrie - horizontproportional, das war der Fehler in N-17c

    Handelsdauer   Median 2,0 Tage (F-202, 239 entschiedene Trades)
    Horizont       H2 - eben diese Dauer, nicht H20
    Achse A        momentum_kurz ueber 3 Tage (1,5x der Dauer)
    Achse B        turnover, in ZWEI Faecher (unter/ueber Median)

⚠️ ZWEI Faecher, nicht fuenf. Erstens ist das Lee/Swaminathans eigene
Form (hoch gegen niedrig). Zweitens ist die Datenlage duenn: `turnover`
deckt nur die Werte mit Umlaufmenge ab (~41 Symbole je Tag), fuenf
Faecher liessen je Fach zu wenige fuer ein oberstes Fuenftel uebrig.

## ⚠️⚠️ DER GEPAARTE TEST, nicht zwei Baender nebeneinander

Methodik **2.105**: zwei Vertrauensbaender nebeneinander sind KEIN
Vergleich. Gemessen wird deshalb je Kalendertag die DIFFERENZ

    d(Tag) = Wirkung im niedrigen Fach  -  Wirkung im hohen Fach

und darauf der Block-Bootstrap. Nur wenn dieses Band die Null ausschliesst,
ist die Umkehr in den Faechern verschieden stark.

## ⚠️ Die Wirkung je Fach kommt aus der ECHTEN Funktion

`messe_regel_wirksamkeit.wirkung()` - dieselbe, die alle registrierten
Befunde gerechnet hat. Diese Datei baut die Faecher und ruft sie auf; sie
rechnet die Wirkung NICHT selbst nach (Lehre aus G-b und F-206).

## Vorab festgelegt - was als Befund gilt

    TRAEGT       das Band der DIFFERENZ schliesst die Null aus
                 UND die Kontrollgroesse `zufall` tut das nicht
    TRAEGT NICHT sonst - dann ist Tempo x Richtung fuer uns erledigt

## ⚠️ Erwartung, ehrlich vorab

Literatur nennt 1-3 Prozentpunkte als realistisch. Die Schwelle 0,080 R
verlangt 2,67 Punkte. Auch ein positiver Befund ist daher wahrscheinlich
zu klein fuer eine AUSLOESUNG - sein Wert laege in der Schalterform, also
als SPERRE.

    python messe_umkehr_je_turnover.py [--selbsttest]
"""
from __future__ import annotations

import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                            # noqa: E402
import messe_bewertungskennzahl as MB                           # noqa: E402
import messe_eigenschaft_beitrag as B                           # noqa: E402
import messe_kandidaten_als_regel as K                          # noqa: E402
import messe_regel_wirksamkeit as W                             # noqa: E402

HORIZONT = 2                  # die gemessene Median-Haltedauer (F-202)
BLOCK = max(90, HORIZONT * 3)
FAECHER = 2                   # niedrig / hoch - Lee/Swaminathans Form
MIND_JE_FACH = 8              # sonst ist ein "oberstes Fuenftel" ein Wert


def faecher_je_tag(je_tag: dict, schicht: dict) -> list[dict]:
    """Zerlegt die Anker je Kalendertag in Turnover-Faecher.

    Rueckgabe: eine Liste von je_tag-Strukturen, eine je Fach - in genau
    der Form, die `messe_regel_wirksamkeit.wirkung()` erwartet. Die
    Wirkung selbst wird hier NICHT gerechnet.
    """
    aus: list[dict] = [{} for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        s = schicht.get(tag)
        if not s:
            continue
        gut = [x for x in z if np.isfinite(s.get(x["sym"], np.nan))]
        if len(gut) < MIND_JE_FACH * FAECHER:
            continue
        sw = np.array([s[x["sym"]] for x in gut], float)
        # ⚠️ DER RANG JE TAG - die Tagesklammer. Ein absoluter
        # Turnover-Schnitt ueber die ganze Historie waere eine Aussage
        # ueber die Marktphase, nicht ueber das Asset von heute.
        fach = np.minimum((W.rang(sw) * FAECHER).astype(int), FAECHER - 1)
        for f in range(FAECHER):
            teil = [x for x, ff in zip(gut, fach) if ff == f]
            if len(teil) >= MIND_JE_FACH:
                aus[f][tag] = teil
    return aus


def differenz_je_tag(teile: list[dict], mische=None) -> dict:
    """d(Tag) = Wirkung im NIEDRIGEN Fach minus Wirkung im HOHEN Fach.

    ⚠️ Beide Seiten kommen aus `W.wirkung()` - der echten Funktion. Nur
    Tage, an denen BEIDE Faecher eine Wirkung liefern, gehen ein; sonst
    waere es ein Vergleich verschiedener Tage.
    """
    w_niedrig, *_ = W.wirkung(teile[0], True, mische=mische)
    w_hoch, *_ = W.wirkung(teile[-1], True, mische=mische)
    gemeinsam = set(w_niedrig) & set(w_hoch)
    return {t: float(w_niedrig[t] - w_hoch[t]) for t in gemeinsam}


def bericht(name: str, je_tag: dict, schicht: dict, rng) -> dict | None:
    teile = faecher_je_tag(je_tag, schicht)
    print()
    print("=" * 92)
    print("%s  —  REGEL je Fach: kein Einstieg im obersten 20 %% von "
          "momentum_kurz" % name)
    print("=" * 92)
    for f, teil in enumerate(teile):
        etikett = "NIEDRIGER Turnover" if f == 0 else "HOHER Turnover"
        n = sum(len(z) for z in teil.values())
        print("  Fach %d (%s): %d Anker · %d Tage" % (f, etikett, n, len(teil)))
        d, anteil, gesperrt, uebrig = W.wirkung(teil, True)
        if not d:
            print("    keine verwertbaren Tage")
            continue
        print("    gesperrt %.1f %%   Ertrag gesperrt %+.4f R   uebrig %+.4f R"
              % (100 * st.mean(anteil), st.mean(gesperrt), st.mean(uebrig)))
        M.urteil_tage("    Wirkung", d, rng, BLOCK)
    print()
    print("  ⚠️ DIE ZAHL, AN DER DIE HYPOTHESE HAENGT - der GEPAARTE")
    print("     Vergleich (2.105), nicht die zwei Baender oben:")
    d = differenz_je_tag(teile)
    if len(d) < 60:
        print("     zu wenige gemeinsame Tage (%d)" % len(d))
        return None
    echt = M.urteil_tage("     NIEDRIG minus HOCH", d, rng, BLOCK)
    M.urteil_tage("     Negativkontrolle",
                  differenz_je_tag(teile, mische=rng), rng, BLOCK)
    tage = sorted(d)
    mitte = tage[len(tage) // 2]
    h1 = M.urteil_tage("       erste Haelfte",
                       {t: v for t, v in d.items() if t < mitte}, rng, BLOCK)
    h2 = M.urteil_tage("       zweite Haelfte",
                       {t: v for t, v in d.items() if t >= mitte}, rng, BLOCK)
    einig = bool(h1 and h2 and (h1["mittel"] > 0) == (h2["mittel"] > 0))
    print("     Haelften: %s" % ("einig" if einig else "UNEINS"))
    return {"echt": echt, "einig": einig}


def selbsttest() -> bool:
    """Zwei Welten mit BEKANNTER Antwort - vor dem teuren Lauf.

    Welt A: die Umkehr wirkt NUR im niedrigen Fach -> Differenz muss
            gefunden werden.
    Welt B: die Umkehr wirkt in BEIDEN Faechern gleich -> Differenz muss
            NICHT gefunden werden (sonst erfindet das Verfahren einen
            Unterschied).
    """
    ok = True
    for welt, nur_niedrig in (("A (Effekt NUR niedrig)", True),
                              ("B (Effekt in BEIDEN gleich)", False)):
        rng = np.random.default_rng(11)
        je_tag, schicht = {}, {}
        for t in range(400):
            n = 40
            mom = rng.uniform(size=n)
            tur = rng.uniform(size=n)
            tag = "t%03d" % t
            zeilen, s = [], {}
            for i in range(n):
                niedrig = tur[i] < 0.5
                # Umkehr: hohes momentum -> schlechterer Ausgang
                straf = -0.30 if mom[i] > 0.8 else 0.0
                if nur_niedrig and not niedrig:
                    straf = 0.0
                zeilen.append({"sym": "S%02d" % i, "kennzahl": float(mom[i]),
                               "in_r": float(rng.normal(straf, 0.5))})
                s["S%02d" % i] = float(tur[i])
            je_tag[tag] = zeilen
            schicht[tag] = s
        teile = faecher_je_tag(je_tag, schicht)
        d = differenz_je_tag(teile)
        rng2 = np.random.default_rng(3)
        e = M.urteil_tage("  SELBSTTEST %s" % welt, d, rng2, BLOCK)
        gefunden = bool(e and e["traegt"])
        erwartet = nur_niedrig
        if gefunden != erwartet:
            print("  ✖ FEHLER: erwartet %s, gefunden %s"
                  % ("Befund" if erwartet else "kein Befund",
                     "Befund" if gefunden else "kein Befund"))
            ok = False
    print("  ✔ Selbsttest bestanden" if ok else "  ✖ SELBSTTEST FEHLGESCHLAGEN")
    return ok


def main() -> int:
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    print("%d Krypto-Reihen (F-204-gefiltert)" % len(reihen))

    # Die Schicht: turnover je Tag/Symbol, ueber die ECHTE Bauroutine
    tur_je_tag = K.baue(reihen, "turnover", menge, horizont=HORIZONT)
    schicht = {t: {x["sym"]: x["kennzahl"] for x in z}
               for t, z in tur_je_tag.items()}

    rng = np.random.default_rng(20260904)
    mom = K.baue(reihen, "momentum_kurz", None, horizont=HORIZONT)
    zuf = K.baue(reihen, "zufall", None, horizont=HORIZONT)

    print()
    print("#" * 92)
    print("# H-N17d  —  kippt die Kurzfrist-Umkehr bei hohem Turnover?")
    print("#          Horizont H%d (gemessene Median-Haltedauer, F-202)" % HORIZONT)
    print("#" * 92)
    e = bericht("momentum_kurz, geschichtet nach turnover", mom, schicht, rng)
    k = bericht("⚠️ KONTROLLE: `zufall` statt momentum_kurz", zuf, schicht, rng)

    print()
    print("=" * 92)
    print("BEFUND")
    print("=" * 92)
    kontrolle_traegt = bool(k and k["echt"] and k["echt"]["traegt"])
    if kontrolle_traegt:
        print("  ⚠️⚠️ DIE KONTROLLGROESSE TRAEGT - dann traegt das VERFAHREN.")
        print("     Kein Befund dieses Laufs gilt.")
        return 0
    print("  ✔ Die Kontrollgroesse traegt nicht.")
    if e and e["echt"] and e["echt"]["traegt"] and e["einig"]:
        print("  ✔ H-N17d TRAEGT: die Umkehr ist in den Turnover-Faechern")
        print("    verschieden stark.")
        print("  ⚠️ Vor jeder Verwendung: Groesse gegen die Schwelle pruefen")
        print("     (2,67 Punkte noetig) - und die Schalterform als SPERRE")
        print("     erwaegen, nicht als Beitrag.")
    else:
        print("  ✖ H-N17d traegt NICHT. Tempo x Richtung ist damit fuer uns")
        print("    erledigt, und der Gabelpunkt H-2 ist ohne diese Option")
        print("    zu entscheiden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
