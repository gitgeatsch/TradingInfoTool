# -*- coding: utf-8 -*-
"""PHASE 3 SCHRITT 2c - IST DIE KETTE AUF DER NEUEN QUELLE BELEGT BESSER?

## Warum diese Datei noetig ist

Zwei Laeufe von `phase3_kette.py` haben am 22.09. geliefert:

    --quelle gesamt   +0,0401 R [+0,0134 .. +0,0662]   entzerrt +0,0440
    --quelle frei     +0,0880 R [+0,0316 .. +0,1509]   entzerrt +0,0851

⚠️⚠️ DIE BAENDER UEBERLAPPEN zwischen +0,0316 und +0,0662. Aus zwei
ueberlappenden Baendern folgt KEINE Aussage ueber ihren Unterschied -
weder dass er da ist, noch dass er fehlt. Wer hier "doppelt so stark"
schreibt, hat zwei Punktschaetzer dividiert und nichts gemessen.

Methodik 2.105 verlangt den GEPAARTEN Test auf die DIFFERENZ, und genau
den rechnet diese Datei.

## Der Aufbau

Beide Ketten laufen auf DENSELBEN Tagen, derselben Auswahl, demselben
Momentum - der einzige Unterschied ist die turnover-Quelle. Damit ist die
Differenz je Tag sauber zuschreibbar:

    diff[tag] = wirkung_frei[tag] - wirkung_gesamt[tag]

    BAND          Blockbootstrap auf die Differenzreihe (Blocklaenge aus
                  dem Horizont, `messnorm._block`)
    NULLWELT      VORZEICHEN-PERMUTATION je Block. Waere die wahre
                  Differenz null, waere die Reihe verteilungsgleich zu
                  ihrer vorzeichengedrehten Fassung. Das ist der
                  Standardtest fuer gepaarte Daten - und er braucht keine
                  Annahme ueber die Form der Verteilung.
    POSITIVKONTR. gepflanzte Differenz bekannter Groesse: ab welcher
                  Hoehe findet die Anlage sie? Ohne diese Zahl ist ein
                  Nullbefund nicht von "zu klein zum Sehen" zu trennen.

## ⚠️ Die eingebaute Zuschreibungskontrolle

`oi_aenderung` haengt NICHT an der turnover-Quelle. Seine Zahl muss in
beiden Laeufen identisch sein - sie war es (+0,0440 / 12,7 Anker). Waere
sie es nicht, laege der Unterschied am Pruefstand und nicht an der
Quelle. Diese Datei prueft das als ZEILE VOR dem Ergebnis, nicht als
Fussnote danach: bewegt sich der unbeteiligte Arm, bricht sie ab.

## Zwei Gegenstaende, dieselbe Frage

    python phase3_kette_quellenvergleich.py
        die KETTE aus funding + turnover + oi_aenderung (Phase 3
        Schritt 2), Fenster ab 2023

    python phase3_kette_quellenvergleich.py --n67
        `schnitt` NACH funding + turnover (N-67, M1-Kriterium 3),
        volles Fenster - n67 filtert nicht ab 2023

⚠️⚠️ DIE ZAHLEN DER BEIDEN LAEUFE SIND NICHT VERGLEICHBAR: anderer
Gegenstand, anderes Fenster, andere Kettenstellung. Jeder Lauf
beantwortet nur seine eigene Frage.

⚠️ NUR LESEND, am Desktop, gegen die Messbasis - kein LLM, kein
Kontingent, keine Beruehrung der Produktion.
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messmenge                                             # noqa: E402
import messnorm                                              # noqa: E402
import phase3_kette as PK                                    # noqa: E402
import phase3_reproduktion as R                              # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import MENGEN                          # noqa: E402

ZIEHUNGEN = 40
STAERKEN = (0.005, 0.01, 0.02, 0.05, 0.10)
STUFEN = ("funding", "turnover", "oi_aenderung")


def differenz(a: dict, b: dict) -> dict:
    """a - b auf den GEMEINSAMEN Tagen.

    ⚠️ Alles andere waere ein Vergleich zweier verschiedener Mengen -
    genau der Fehler, vor dem CLAUDE.md unter "Die Grundgesamtheit ist
    keine Stellschraube" warnt.
    """
    return {t: a[t] - b[t] for t in set(a) & set(b)}


def blockdreh(reihe: dict, block: int, rng) -> dict:
    """Vorzeichen JE BLOCK drehen - nicht je Tag.

    ⚠️ Je Tag zu drehen wuerde die Autokorrelation zerstoeren und das
    Band viel zu eng machen; derselbe Fehlertyp steckte in 2.238, wo
    durch Wurzel-Bloecke statt Wurzel-Tage geteilt wurde.
    """
    tage = sorted(reihe)
    aus = {}
    for i in range(0, len(tage), block):
        v = -1.0 if rng.random() < 0.5 else 1.0
        for t in tage[i:i + block]:
            aus[t] = reihe[t] * v
    return aus


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("PHASE 3 · SCHRITT 2c - QUELLENVERGLEICH DER KETTE, GEPAART")
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  Fenster ab %s · Menge %s · H%d · %d Ziehungen"
          % (PK.AB, PK.MENGE, R.HORIZONT, ZIEHUNGEN))
    print("  ⚠️ %s" % PK.VORBEHALT)

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    anteil = MENGEN[PK.MENGE]
    block = messnorm._block(R.HORIZONT)

    # ⚠️⚠️ `--n67` wechselt den GEGENSTAND, nicht nur eine Einstellung:
    # gemessen wird dann `schnitt` NACH funding+turnover (M1-Kriterium 3)
    # statt der Dreierkette. n67 braucht dafuer eine eigene Welt
    # (`schnitt` und `zufall` zusaetzlich) und seine eigene
    # `kette`-Funktion - die Reihenfolge ist eine andere.
    n67 = "--n67" in sys.argv
    if n67:
        import n67_schnitt_ueber_die_kette as N67
        laeufer, stufen_arg = N67.kette, "schnitt"
        kontrollarm = "zufall"
        arten = ("schnitt", "funding", "turnover", "zufall")
        print("  ⚠️ GEGENSTAND: N-67 (`schnitt` nach der Kette), volles "
              "Fenster")
    else:
        laeufer, stufen_arg = PK.kette, STUFEN
        kontrollarm = None
        arten = STUFEN
        print("  ⚠️ GEGENSTAND: die Dreierkette, Fenster ab %s" % PK.AB)

    welt = {}
    for q in ("gesamt", "frei"):
        print("  Welten bauen, Quelle %s ..." % q)
        welt[q] = {a: R.K.baue(reihen, a, R._zusatz(a, q),
                               horizont=R.HORIZONT) for a in arten}
    print("  fertig (%.0f s)" % (time.time() - t0))

    # ---- 1) DIE ZUSCHREIBUNGSKONTROLLE ZUERST ---------------------------
    #
    # ⚠️ VOR dem Ergebnis, nicht danach. Bewegt sich der unbeteiligte Arm,
    # ist alles Weitere hinfaellig - dann misst der Pruefstand sich selbst.
    print("\n  KONTROLLE - der unbeteiligte Arm darf sich NICHT bewegen")
    print("  " + "-" * 84)
    # ⚠️ DER UNBETEILIGTE ARM ist je Gegenstand ein anderer: bei der Kette
    # `oi_aenderung` (haengt nicht an der turnover-Quelle), bei n67
    # `zufall` (traegt per Bau keine Information). Beide muessen zwischen
    # den Quellen gleich bleiben.
    oi = {}
    _name = kontrollarm or "oi_aenderung"
    for q in ("gesamt", "frei"):
        if n67:
            e, z = laeufer(welt[q], mom, anteil, kontrollarm)
            uebrig = float(np.mean(z["nach_beitraegen"]))
        else:
            e, z = PK.kette(welt[q], mom, anteil, ("oi_aenderung",))
            uebrig = float(np.mean(z["uebrig"]))
        b = PK.band(e, block)
        oi[q] = (b[0], uebrig, len(e))
        print("     nur %-12s Quelle %-7s %+.4f R · %.1f Anker · %d Tage"
              % (_name, q, b[0], oi[q][1], oi[q][2]))
    gleich = abs(oi["gesamt"][0] - oi["frei"][0]) < 1e-9
    print("     %s  %s"
          % ("✔ IDENTISCH" if gleich else "⛔ ABWEICHUNG",
             "der Unterschied ist der Quelle zuschreibbar" if gleich
             else "der Pruefstand ist nicht neutral - ABBRUCH"))
    if not gleich:
        if n67:
            # ⚠️⚠️⚠️ BEI N-67 IST DAS KEIN DEFEKT, SONDERN DIE ANTWORT
            # (23.09.2026, gemessen). `zufall` laeuft dort auf der
            # RESTMENGE nach funding+turnover - und genau die aendert die
            # Quelle (43,4 -> 37,3 Anker je Tag). Er MUSS sich bewegen.
            #
            # Damit gibt es bei n67 keinen unbeteiligten Arm, und die
            # Folge ist groesser als eine fehlende Kontrollzeile: die
            # beiden Laeufe messen `schnitt` auf VERSCHIEDENEN
            # Restmengen. Das ist kein gepaarter Vergleich derselben
            # Sache, sondern zwei verschiedene Fragen - ein Band um ihre
            # Differenz waere eine Zahl ohne Gegenstand.
            #
            # ⚠️ Bei der KETTE liegt es anders: dort ist `oi_aenderung`
            # eine eigene Stufe, die nicht an der turnover-Quelle haengt,
            # und beide Laeufe laufen auf derselben Auswahl.
            print()
            print("     ⚠️⚠️ BEI N-67 IST DAS KEIN "
                  "DEFEKT, SONDERN DIE ANTWORT:")
            print("        `zufall` laeuft auf der RESTMENGE nach "
                  "funding+turnover, und die")
            print("        aendert die Quelle (%.1f -> %.1f Anker/Tag). "
                  "Er MUSS sich bewegen."
                  % (oi["gesamt"][1], oi["frei"][1]))
            print("        ➤ Es gibt hier keinen unbeteiligten Arm - "
                  "und damit messen die")
            print("          beiden Laeufe `schnitt` auf VERSCHIEDENEN "
                  "Restmengen. Ein Band")
            print("          um ihre Differenz waere eine Zahl ohne "
                  "Gegenstand.")
            print("        ⚠️ Jeder Lauf gilt fuer sich "
                  "(n67 --quelle gesamt|frei, je eigenes")
            print("          Normurteil). Was NICHT geht, ist die "
                  "Verrechnung der beiden.")
        return 1

    # ---- 2) DIE GEPAARTE DIFFERENZ --------------------------------------
    print("\n  DIE KETTE, BEIDE QUELLEN")
    print("  " + "-" * 84)
    echt, anker = {}, {}
    for q in ("gesamt", "frei"):
        e, z = laeufer(welt[q], mom, anteil, stufen_arg)
        echt[q] = e
        _n = z["nach_beitraegen"] if n67 else z["uebrig"]
        anker[q] = float(np.mean(_n)) if _n else 0.0
        b = PK.band(e, block)
        print("     %-7s %+.4f R [%+.4f .. %+.4f] · %.1f Anker/Tag "
              "· %d Tage" % (q, b[0], b[1], b[2], anker[q], len(e)))

    d = differenz(echt["frei"], echt["gesamt"])
    bd = PK.band(d, block)
    print("\n  DIE DIFFERENZ (frei minus gesamt), GEPAART auf %d gemeinsamen "
          "Tagen" % len(d))
    print("  " + "-" * 84)
    # ⚠️ `band` liefert VIER Werte - der vierte ist die Zahl der Tage, die
    # in den Bootstrap eingingen. Sie wird mit ausgewiesen: ein Band ueber
    # 60 Tagen ist etwas anderes als dasselbe Band ueber 1.300.
    print("     gemessen      %+.4f R [%+.4f .. %+.4f]  (%d Tage im Band)"
          % bd)

    null = []
    for i in range(ZIEHUNGEN):
        rng = np.random.default_rng(messnorm.SAAT + i)
        nb = PK.band(blockdreh(d, block, rng), block, zieh=300,
                     saat=messnorm.SAAT + i)
        if nb:
            null.append(nb[0])
    n_mittel = float(np.mean(null))
    n_oben = float(np.percentile(null, messnorm.NULL_PERZENTIL))
    print("     Nullwelten    %d Ziehungen · Mittel %+.4f · %d. "
          "Perzentil %+.4f"
          % (len(null), n_mittel, messnorm.NULL_PERZENTIL, n_oben))
    print("     Bezug         nullpunkt (Messstandard 09.09.)")

    # ⚠️ POSITIVKONTROLLE AUF DIE DIFFERENZ (Methodik 2.105). Gepflanzt
    # wird in die VORZEICHENGEDREHTE Reihe - also in eine Welt, in der die
    # wahre Differenz null ist. Wer in die echte Reihe pflanzt, misst den
    # vorhandenen Effekt mit.
    print("     Positivkontrolle - auf die DIFFERENZ gepflanzt")
    schaerfe = None
    for s in STAERKEN:
        tr = 0
        for i in range(5):
            rng = np.random.default_rng(messnorm.SAAT + 1000 + i)
            gepflanzt = {t: v + s
                         for t, v in blockdreh(d, block, rng).items()}
            pb = PK.band(gepflanzt, block, zieh=300,
                         saat=messnorm.SAAT + 1000 + i)
            if pb and pb[0] > n_oben:
                tr += 1
        print("       %.3f R: %d/5 gefunden" % (s, tr))
        if tr == 5 and schaerfe is None:
            schaerfe = s
    print("     Trennschaerfe %s"
          % ("%.3f R" % schaerfe if schaerfe else "> %.3f R" % STAERKEN[-1]))

    traegt = (bd[0] > n_oben and schaerfe is not None and bd[0] >= schaerfe)
    print("\n     ⚠️ URTEIL: DIE DIFFERENZ IST %s"
          % ("BELEGT" if traegt else "NICHT BELEGT"))
    if not traegt:
        print("        ⚠️ 'NICHT BELEGT' heisst NICHT 'kein "
              "Unterschied'. Belegt ist:")
        print("           beide Quellen tragen (je eigenes Normurteil). Ob "
              "die neue")
        print("           BESSER ist, loest diese Datenlage nicht auf.")
    print("     ⚠️ %s" % PK.VORBEHALT)

    # ---- 3) WARUM IST DIE DIFFERENZ SO GROB AUFGELOEST? -----------------
    #
    # ⚠️⚠️ Ein gepaarter Test ist normalerweise SCHAERFER als die
    # Einzelmessungen - das gemeinsame Rauschen faellt heraus. Hier ist es
    # umgekehrt (0,02 R je Lauf, 0,100 R auf der Differenz). Das ist kein
    # Widerspruch, sondern eine Aussage ueber die Sache: die Paarung hilft
    # nur, soweit die beiden Reihen MITEINANDER laufen. Die Zahl dazu
    # gehoert ausgewiesen, sonst steht die grobe Trennschaerfe unerklaert
    # da und sieht nach einem Fehler des Pruefstands aus.
    tage = sorted(set(echt["gesamt"]) & set(echt["frei"]))
    va = np.array([echt["gesamt"][t] for t in tage])
    vb = np.array([echt["frei"][t] for t in tage])
    r = float(np.corrcoef(va, vb)[0, 1])
    print("\n  WARUM DIE DIFFERENZ GROB AUFGELOEST IST")
    print("  " + "-" * 84)
    print("     Korrelation der beiden Tagesreihen   %+.3f" % r)
    print("     Streuung  gesamt %.4f · frei %.4f · Differenz %.4f"
          % (va.std(), vb.std(), (vb - va).std()))
    print("     ⚠️ Bei hoher Korrelation streut die Differenz "
          "WENIGER als jede")
    print("        Reihe einzeln - dann ist der gepaarte Test schaerfer. "
          "Streut sie")
    print("        MEHR, sperren die beiden Ketten weitgehend "
          "VERSCHIEDENE Anker,")
    print("        und die Paarung bringt nichts. Was hier zutrifft, sagen "
          "die Zahlen")
    print("        oben - nicht diese Zeile.")

    print("\n  DER DURCHLASS - ein FAKT, keine Bewertung")
    print("  " + "-" * 84)
    print("     gesamt %.1f Anker/Tag → frei %.1f  (%+.1f)"
          % (anker["gesamt"], anker["frei"], anker["frei"] - anker["gesamt"]))
    print("     ⚠️ Was der engere Durchlass im BETRIEB kostet, "
          "steht hier nicht -")
    print("        das haengt am Cooldown, nicht an dieser Stufe.")
    print("\n  (%.0f s gesamt)" % (time.time() - t0))
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
