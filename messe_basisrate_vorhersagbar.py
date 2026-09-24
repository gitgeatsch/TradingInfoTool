# -*- coding: utf-8 -*-
"""P-9 Schicht 3: schwankt die Basisrate ECHT - und ist sie VORHERSAGBAR?

Vorabfestlegung: `Basisinfos/Vorabfestlegung_P9_Schicht3_24_09.md`
Vorlaeufer: Befund 2.584 (die Quote schwankt je Jahr 26,4 bis 42,6 %).

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DIE FRAGE IST NICHT "SCHWANKT SIE" - DAS IST BEANTWORTET
═══════════════════════════════════════════════════════════════════════

Eine Groesse, die schwankt, aber nicht VORHER bekannt ist, kann man nicht
verwenden - man weiss erst hinterher, dass 2025 schlecht war.

    TEIL 1   ist die Schwankung ECHT oder ein Artefakt der Ueberlappung?
    TEIL 2   ist sie aus zum Zeitpunkt BEKANNTEN Groessen vorhersagbar?

Faellt Teil 1, entfaellt Teil 2 - man sagt nichts vorher, was nur Rauschen
ist.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️⚠️ DER NULLPUNKT IN TEIL 1 - hier steckt die ganze Schwierigkeit
═══════════════════════════════════════════════════════════════════════

Ein naiver Binomialtest wuerde die Schwankung SICHER als signifikant
ausweisen - und waere falsch. Zwei Abhaengigkeiten stehen dagegen:

    ÜBERLAPPUNG   ein Anker traegt ein 60-Tage-Fenster; zwei Anker im
                  Abstand von 5 Tagen teilen 55 Tage Kursverlauf
    TAGESKOPPLUNG an einem Tag bewegt sich der ganze Markt gemeinsam -
                  40 Symbole am selben Tag sind kein 40-faches n

➤ DER NULLPUNKT WIRD DESHALB GEZOGEN, NICHT GERECHNET: ganze KALENDERTAGE
mit Zuruecklegen (Tagesklammer), daraus Bloecke bilden, Streuung messen.
Das erhaelt beide Abhaengigkeiten. 200 Nullwelten.

⚠️ Die Bloecke selbst sind NICHT ueberlappend (60 Tage), damit ein Anker
und sein Vorwaertsfenster im selben Block liegen.

═══════════════════════════════════════════════════════════════════════
 ⚠️ DIE EINHEIT IST DER BLOCK, NICHT DER ANKER
═══════════════════════════════════════════════════════════════════════

Rund 48 Bloecke ueber 2018-2026. Wer ueber 644.336 Anker bootstrappt,
misst eine Sicherheit, die es nicht gibt - derselbe Fehler wie "32 Symbole
an 733 Tagen sind keine 23.000 Faelle" (messe_drift, 19.08.).

Bei 48 Punkten ist eine Korrelation ab rund r = 0,30 nachweisbar. Das
steht VORHER fest, nicht hinterher als Enttaeuschung.

    python messe_basisrate_vorhersagbar.py
    python messe_basisrate_vorhersagbar.py --symbole 60    # Probelauf
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402

CRV = 2.0
NAME = "ZIEL 2,0"
BLOCK_TAGE = 60            # = Horizont: Anker und Fenster im selben Block
NULLWELTEN = 200
SAAT = 20260924
KANDIDATEN = ("V1 Quote Vorblock", "V2 Marktvola", "V3 BTC-Trend",
              "V4 Streuung", "KON zufall")


def _blockquoten(zeilen: list) -> tuple:
    """Je nicht-ueberlappendem 60-Tage-Block: Quote, n, und die Tage."""
    je_tag = defaultdict(list)
    je_tag_sym = defaultdict(list)
    for z in zeilen:
        if z[NAME] in (-1.0, CRV):
            tag = str(z["anker_tag"])[:10]
            treffer = 1 if z[NAME] == CRV else 0
            je_tag[tag].append(treffer)
            je_tag_sym[tag].append((z["sym"], treffer))
    tage = sorted(je_tag)
    bloecke = []
    for i in range(0, len(tage) - BLOCK_TAGE + 1, BLOCK_TAGE):
        gruppe = tage[i:i + BLOCK_TAGE]
        werte = [w for t in gruppe for w in je_tag[t]]
        if len(werte) < 200:
            continue
        # ⚠️ V4: die Streuung UEBER DIE SYMBOLE - laufen die Werte im Block
        # auseinander? Nur Symbole mit genug Ankern, sonst misst man die
        # duenne Belegung statt der Streuung.
        js = defaultdict(list)
        for t in gruppe:
            for sym, tr in je_tag_sym[t]:
                js[sym].append(tr)
        quoten_sym = [float(np.mean(v)) for v in js.values() if len(v) >= 20]
        bloecke.append({"von": gruppe[0], "bis": gruppe[-1],
                        "quote": float(np.mean(werte)), "n": len(werte),
                        "tage": gruppe,
                        "streuung_sym": (float(np.std(quoten_sym))
                                         if len(quoten_sym) >= 5 else None)})
    return bloecke, je_tag


def _null_streuung(je_tag: dict, n_bloecke: int, rng) -> np.ndarray:
    """Die Streuung der Blockquoten in einer WELT OHNE Regimewechsel.

    ⚠️ Gezogen werden ganze KALENDERTAGE mit Zuruecklegen - damit bleiben
    Tageskopplung und Ueberlappung erhalten. Ein Binomialmodell haette
    beide weggelassen und jede Schwankung signifikant gemacht.
    """
    tage = list(je_tag)
    aus = []
    for _ in range(NULLWELTEN):
        gezogen = rng.choice(len(tage), len(tage), replace=True)
        quoten = []
        for i in range(0, len(gezogen) - BLOCK_TAGE + 1, BLOCK_TAGE):
            werte = [w for j in gezogen[i:i + BLOCK_TAGE]
                     for w in je_tag[tage[j]]]
            if len(werte) >= 200:
                quoten.append(float(np.mean(werte)))
        if len(quoten) >= max(5, n_bloecke // 2):
            aus.append(float(np.std(quoten)))
    return np.array(aus)


def _merkmale(bloecke: list, reihen: dict, rng) -> dict:
    """Je Block die Vorhersagegroessen - alle aus dem VORBLOCK."""
    btc = reihen.get("BTC") or []
    kurs = {str(z[0])[:10]: float(z[1]) for z in btc}
    aus = {k: [] for k in KANDIDATEN}
    ziel = []
    for i in range(1, len(bloecke)):
        vor, jetzt = bloecke[i - 1], bloecke[i]
        k0 = kurs.get(vor["tage"][0])
        k1 = kurs.get(vor["tage"][-1])
        tages = [kurs.get(t) for t in vor["tage"]]
        tages = [x for x in tages if x]
        if not (k0 and k1) or len(tages) < 20:
            continue
        r = np.diff(np.log(tages))
        aus["V1 Quote Vorblock"].append(vor["quote"])
        aus["V2 Marktvola"].append(float(np.std(r)))
        aus["V3 BTC-Trend"].append(float(k1 / k0 - 1.0))
        # ⚠️ V4 ist die Streuung UEBER DIE SYMBOLE des Vorblocks. Fehlt sie
        # (zu wenige Symbole mit genug Ankern), wird der Blockwert des
        # Vorgaengers NICHT geraten - der Kandidat faellt dann fuer diesen
        # Punkt aus, und das steht in der Zeile "nicht bildbar".
        aus["V4 Streuung"].append(vor.get("streuung_sym"))
        aus["KON zufall"].append(float(rng.random()))
        ziel.append(jetzt["quote"])
    if any(x is None for x in aus["V4 Streuung"]):
        aus["V4 Streuung"] = []
    return aus, np.array(ziel)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    rng = np.random.default_rng(SAAT)

    print("=" * 92)
    print("P-9 SCHICHT 3 - schwankt die Basisrate ECHT, und ist sie VORHERSAGBAR?")
    print("=" * 92)
    reihen = B.lade()
    if grenze:
        behalten = {"BTC"} | set(list(reihen)[:grenze])
        reihen = {k: v for k, v in reihen.items() if k in behalten}
    print("  %d Krypto-Reihen · Blocklaenge %d Tage · CRV %.1f"
          % (len(reihen), BLOCK_TAGE, CRV))
    print("  Barrieren rechnen...", flush=True)
    zeilen = ZR.ergebnisse(reihen, mit_gleichstand=True)
    bloecke, je_tag = _blockquoten(zeilen)
    q = np.array([b["quote"] for b in bloecke])

    print()
    print("─" * 92)
    print("TEIL 1 - IST DIE SCHWANKUNG ECHT?")
    print("─" * 92)
    print("  %d nicht-ueberlappende Bloecke · %d Kalendertage"
          % (len(bloecke), len(je_tag)))
    print("  Quote  Mittel %.4f   min %.4f   max %.4f   Spanne %.1f Pp"
          % (q.mean(), q.min(), q.max(), 100 * (q.max() - q.min())))
    print("  Streuung der Blockquoten: %.4f" % q.std())
    print("  Nullpunkt ziehen (%d Welten, Tagesklammer)..." % NULLWELTEN,
          flush=True)
    null = _null_streuung(je_tag, len(bloecke), rng)
    if len(null) < 20:
        print("  ⛔ zu wenige Nullwelten (%d) - kein Urteil" % len(null))
        return 1
    p90, p95 = np.percentile(null, 90), np.percentile(null, 95)
    print("  Nullwelten: Mittel %.4f   90. Perz %.4f   95. Perz %.4f"
          % (null.mean(), p90, p95))
    echt = q.std() > p95
    print()
    print("  ➤ ECHT" if echt else "  ⛔ NICHT VON DER NULLWELT ZU TRENNEN")
    print("    (%.4f gegen 95. Perzentil %.4f  -  Faktor %.2f)"
          % (q.std(), p95, q.std() / max(1e-9, null.mean())))
    if not echt:
        print()
        print("  ⚠️⚠️ TEIL 2 ENTFAELLT. Was nur Rauschen ist, sagt man nicht")
        print("     vorher - und 2.584 ist zu entschaerfen.")
        return 0

    # ───────────────────────────── TEIL 2 ─────────────────────────────
    print()
    print("─" * 92)
    print("TEIL 2 - IST SIE VORHERSAGBAR?")
    print("─" * 92)
    merk, ziel = _merkmale(bloecke, reihen, rng)
    n = len(ziel)
    print("  %d Blockpaare (Vorblock -> Block)" % n)
    if n < 12:
        print("  ⛔ zu wenige Paare - kein Urteil")
        return 1
    haelfte = n // 2
    print("  in-sample 1..%d · OUT-OF-SAMPLE %d..%d" % (haelfte, haelfte + 1, n))
    print()
    print("  %-22s %10s %12s %10s" % ("Kandidat", "r gesamt", "r out-of-s",
                                      "Urteil"))
    # ⚠️⚠️ DIE SCHWELLE GILT FUER DIE MENGE, AUF DER GEMESSEN WIRD.
    #
    # Meine erste Fassung rechnete sie aus ALLEN Paaren (n=48 -> 0,30) und
    # wandte sie auf die OUT-OF-SAMPLE-Haelfte an (n=24). Dort ist der
    # Standardfehler aber 1/sqrt(21) = 0,218 statt 0,149 - die Grenze liegt
    # bei 0,428, mit Bonferroni ueber vier Kandidaten bei 0,546.
    #
    # Der Fehler haette V4 (r_oos = 0,305) als TRAEGT ausgewiesen. Genau die
    # Sorte Befund, die dieses Projekt schon zweimal zuruecknehmen musste.
    n_oos = n - haelfte
    se_oos = 1.0 / np.sqrt(max(1, n_oos - 3))
    schwelle = 2.50 * se_oos          # 2,50 = Bonferroni ueber 4 Kandidaten
    for k in KANDIDATEN:
        w = merk.get(k) or []
        if len(w) != n:
            print("  %-22s %10s %12s   %s"
                  % (k, "-", "-", "nicht bildbar"))
            continue
        w = np.array(w)
        r_alle = float(np.corrcoef(w, ziel)[0, 1])
        r_oos = float(np.corrcoef(w[haelfte:], ziel[haelfte:])[0, 1])
        # ⚠️ ZWEITE BEDINGUNG: STABILITAET. Ist r_oos ein Vielfaches von
        # r_gesamt, muss die erste Haelfte gegenlaeufig sein - das ist
        # Instabilitaet, kein Effekt. Faktor 2 ist die Grenze.
        stabil = abs(r_alle) > 1e-9 and abs(r_oos / r_alle) <= 2.0
        gut = (abs(r_oos) >= schwelle
               and np.sign(r_oos) == np.sign(r_alle) and stabil)
        grund = ("TRAEGT" if gut else
                 "unter Grenze" if abs(r_oos) < schwelle else
                 "instabil" if not stabil else "traegt nicht")
        print("  %-22s %+10.3f %+12.3f   %s" % (k, r_alle, r_oos, grund))
    print()
    print("  ⚠️ Nachweisgrenze OUT-OF-SAMPLE (%d Paare): r = %.3f"
          % (n_oos, schwelle))
    print("     Standardfehler ±%.3f · Bonferroni ueber %d Kandidaten"
          % (se_oos, len(KANDIDATEN)))
    print("  ⚠️ Auf allen %d Paaren waere die Grenze %.3f - sie gilt hier NICHT,"
          % (n, 2.50 / np.sqrt(max(1, n - 3))))
    print("     weil out-of-sample nur die halbe Menge traegt.")
    print("  ⚠️ `KON zufall` muss ,traegt nicht' zeigen - sonst ist der Lauf")
    print("     ungueltig, egal was die uebrigen sagen.")
    print()
    print("─" * 92)
    print("  ⚠️⚠️ Traegt keiner, gilt Paragraf 6 der Vorabfestlegung:")
    print("     die Basisrate schwankt ECHT und ist NICHT vorhersagbar.")
    print("     Dann darf sie nicht als Konstante verwendet werden, die so")
    print("     tut, als waere sie bekannt - und ein `q` mit unbekanntem")
    print("     Fundament rechtfertigt einen KLEINEREN Hebel, nicht denselben.")
    print("     ⛔ Die Bauform ist eine ENTWURFSFRAGE fuer den Nutzer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
