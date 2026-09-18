# -*- coding: utf-8 -*-
"""Phase 3, Schritt 2: DIE KETTE GEGEN NULLWELTEN (18.09.2026).

Die Einzelurteile (`phase3_normurteil.py`) sagen, was jeder Beitrag FUER SICH
leistet. Sie sagen nicht, was die KETTE leistet - dort wirken die Stufen
nacheinander, jede auf der Restmenge der vorigen.

    Stufe 5     Auswahl: oberste 20 % nach 250-Tage-Momentum
    Stufe 12a   `funding` und `turnover` sperren ihr oberstes Fuenftel
    Stufe 12b   `oi_aenderung` sperrt sein oberstes Fuenftel - auf dem REST

⚠️⚠️ WOGEGEN GEMESSEN WIRD: gegen NULLWELTEN, nicht gegen null. Dieselbe
Kette laeuft mit permutierten Raengen - die Stufen sperren dann zufaellig
gleich viele Anker. Der Unterschied ist das, was die Kette WIRKLICH leistet;
alles darunter ist die Mechanik des Sperrens selbst (Messstandard 09.09.).

⚠️ DIE ZAEHLUNG STEHT VOR DER DEUTUNG: wieviele Anker jede Stufe uebrig
laesst, wird ausgewiesen - eine Wirkung auf drei Ankern je Tag ist etwas
anderes als dieselbe Zahl auf dreissig.

⚠️ STELLVERTRETERMENGE (N3 b): gilt NICHT auf der Live-Menge (Blocker A8).
⚠️ Fenster ab 2023 (Vorgabe ZEITFENSTER-AB-2023). Nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messe_regel_wirksamkeit as RW
import messnorm
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250
from messnorm_auswahl import MENGEN
from n64_schnitt_stufen import PUNKT_JE_R, band
import messe_beitrag_auf_auswahl as A

AB = "2023-01-01"
MENGE = "20%"
ZIEHUNGEN = messnorm.NULL_ZIEHUNGEN          # 40 - der Messstandard
VORBEHALT = "gilt auf der Stellvertretermenge, NICHT auf der Live-Menge (N3 b)"


def tag_maske(w: dict, mom: dict, anteil: float, stufen: tuple, tag: str,
              zeilen: list, mische=None):
    """EIN Tag durch die Kette. Gibt (syms, y, gewaehlt, frei) oder None.

    ⚠️ HERAUSGEZOGEN AM 18.09.2026 fuer die Sperrmessung (`phase3_sperre.py`).
    Die Sperre ist eine WEITERE Stufe und braucht genau diese Masken - sie
    dort nachzubauen waere die Kopierfalle, die dieses Projekt schon mehrfach
    erwischt hat. `kette()` ruft dieselbe Funktion; wer sie aendert, aendert
    beide Messungen zugleich."""
    if tag < AB or len(zeilen) < 12:
        return None
    syms = [x["sym"] for x in zeilen]
    y = np.array([x["in_r"] for x in zeilen], float)
    m = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
    if m is None or m.sum() < 6:
        return None
    frei = m.copy()
    for a in stufen:
        zt = {x["sym"]: x["kennzahl"] for x in w[a].get(tag, [])}
        kz = np.array([zt.get(s, np.nan) for s in syms], float)
        ok = np.isfinite(kz)
        if ok.sum() < 12:
            continue                         # ⚠️ keine Datenlage -> keine Sperre
        r = np.full(len(syms), np.nan)
        rr = RW.rang(kz[ok])
        if mische is not None:
            rr = mische.permutation(rr)
        r[ok] = rr
        frei &= ~(np.nan_to_num(r, nan=0.0) >= RW.GRENZE)
    return syms, y, m, frei


def kette(w: dict, mom: dict, anteil: float, stufen: tuple,
          mische=None, pflanze: float = 0.0) -> tuple[dict, dict]:
    """Die Kette Stufe fuer Stufe. Gibt (Wirkung je Tag, Zaehlung) zurueck.

    `stufen` ist die Reihenfolge der sperrenden Beitraege. `mische` permutiert
    JEDEN Rang - das ist die Nullwelt: gleich viele Anker gesperrt, aber ohne
    Information."""
    aus: dict = {}
    z = {"gewaehlt": [], "uebrig": [], "gesperrt": []}
    for tag, zeilen in w[stufen[0]].items():
        gebaut = tag_maske(w, mom, anteil, stufen, tag, zeilen, mische)
        if gebaut is None:
            continue
        syms, y, m, frei = gebaut
        z["gewaehlt"].append(int(m.sum()))
        if frei.sum() < 3 or m.sum() == frei.sum():
            continue
        z["uebrig"].append(int(frei.sum()))
        z["gesperrt"].append(float(1.0 - frei.sum() / max(m.sum(), 1)))
        # ⚠️ DIE KETTE GEGEN IHRE EIGENE AUSWAHL: was die Stufen 12 bringen,
        # ist der Unterschied zwischen dem, was uebrig bleibt, und dem, was
        # die Auswahl allein geliefert haette.
        # ⚠️ DIE POSITIVKONTROLLE PFLANZT IN DIE GEMISCHTE WELT - genau wie
        # `messe_regel_wirksamkeit.wirkung()`: die GESPERRTEN werden um
        # `pflanze` schlechter gemacht. Auf die Freien zu pflanzen hiesse,
        # den eigenen Effekt zu messen (messnorm 06.09.: eine Kontrolle, die
        # ihren eigenen Effekt frisst, belegt nichts).
        y2 = y.copy()
        if pflanze:
            y2[m & ~frei] -= pflanze
        aus[tag] = float(np.median(y2[frei])) - float(np.median(y2[m]))
    return aus, z


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("PHASE 3 · SCHRITT 2 - DIE KETTE GEGEN NULLWELTEN")
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  Fenster ab %s · Menge %s · Horizont H%d · %d Nullziehungen"
          % (AB, MENGE, R.HORIZONT, ZIEHUNGEN))
    print("  ⚠️ %s" % VORBEHALT)
    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    print("  %d Reihen · %d Tage mit Auswahl" % (len(reihen), len(mom)))
    print("  Welten je Beitrag bauen ...")
    w = {a: R.K.baue(reihen, a, R._zusatz(a), horizont=R.HORIZONT)
         for a in ("funding", "turnover", "oi_aenderung")}
    print("  fertig (%.0f s)" % (time.time() - t0))

    anteil = MENGEN[MENGE]
    block = messnorm._block(R.HORIZONT)
    fragen = (("Kette gesamt", ("funding", "turnover", "oi_aenderung")),
              ("nur funding+turnover", ("funding", "turnover")),
              ("nur oi_aenderung", ("oi_aenderung",)))
    print("\n  %-22s %10s %26s %10s %11s %9s"
          % ("Stufen", "roh R", "Band", "Nullwelt", "entzerrt", "Anker/Tag"))
    erg = {}
    for name, stufen in fragen:
        echt, z = kette(w, mom, anteil, stufen)
        e = band(echt, block)
        if e is None:
            print("  %-22s zu wenige Tage (%d)" % (name, len(echt)))
            continue
        null = []
        for i in range(ZIEHUNGEN):
            n, _ = kette(w, mom, anteil, stufen,
                         mische=np.random.default_rng(messnorm.SAAT + i))
            nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
            if nb:
                null.append(nb[0])
        nw = float(np.mean(null)) if null else 0.0
        erg[name] = {"roh": e[0], "band": (e[1], e[2]), "null": nw,
                     "entzerrt": e[0] - nw, "tage": len(echt),
                     "uebrig": float(np.mean(z["uebrig"])) if z["uebrig"] else 0.0,
                     "gewaehlt": float(np.mean(z["gewaehlt"])) if z["gewaehlt"] else 0.0}
        print("  %-22s %+10.4f [%+.4f .. %+.4f] %+10.4f %+11.4f %9.1f"
              % (name, e[0], e[1], e[2], nw, e[0] - nw, erg[name]["uebrig"]),
              flush=True)

    # ---- DAS NORMURTEIL AUF DER KETTE ------------------------------------
    #
    # ⚠️ KEINE NACHBILDUNG DER NORM, SONDERN IHRE ANWENDUNG: `messnorm.pruefe`
    # urteilt ueber EINEN Kandidaten; eine Kette aus drei Stufen kennt sie
    # nicht. Die Groessen kommen deshalb aus `messnorm` selbst - STAERKEN,
    # NULL_PERZENTIL, ZIEHUNGEN, NULLBEZUG - gebaut ist hier nur die Mechanik.
    stufen_k = ("funding", "turnover", "oi_aenderung")
    print(chr(10) + "  DAS NORMURTEIL AUF DER KETTE")
    null = []
    for i in range(ZIEHUNGEN):
        n, _ = kette(w, mom, anteil, stufen_k,
                     mische=np.random.default_rng(messnorm.SAAT + i))
        nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
        if nb:
            null.append(nb[0])
    null_oben = float(np.percentile(null, messnorm.NULL_PERZENTIL))
    null_mittel = float(np.mean(null))
    echt_k, _ = kette(w, mom, anteil, stufen_k)
    e_k = band(echt_k, block)
    print("     Nullwelten    %d Ziehungen · Mittel %+.4f · %d. Perzentil %+.4f"
          % (len(null), null_mittel, messnorm.NULL_PERZENTIL, null_oben))
    print("     gemessen      %+.4f R [%+.4f .. %+.4f]" % tuple(e_k[:3]))
    print("     Bezug         %s (Messstandard 09.09.)" % messnorm.NULLBEZUG)
    print("     Positivkontrolle - gefunden = ueber dem %d. Perzentil der Nullwelten"
          % messnorm.NULL_PERZENTIL)
    trennschaerfe = None
    for staerke in messnorm.STAERKEN:
        treffer = 0
        for i in range(messnorm.ZIEHUNGEN):
            pw, _ = kette(w, mom, anteil, stufen_k, pflanze=staerke)
            pb = band(pw, block, zieh=300, saat=messnorm.SAAT + 1000 + i)
            if pb and pb[0] > null_oben:
                treffer += 1
        gefunden = treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5)
        print("       %.2f R: %d/%d %s"
              % (staerke, treffer, messnorm.ZIEHUNGEN,
                 "gefunden" if gefunden else ""))
        if gefunden and trennschaerfe is None:
            trennschaerfe = staerke
    print("     Trennschaerfe %s"
          % ("%.2f R" % trennschaerfe if trennschaerfe else "KEINE"))
    wirkung_k = e_k[0] - null_mittel
    if trennschaerfe is None:
        urteil = "KEIN URTEIL - die Positivkontrolle findet nichts"
    elif e_k[0] > null_oben and wirkung_k >= trennschaerfe:
        urteil = "TRAEGT"
    elif e_k[0] > null_oben:
        urteil = ("TRAEGT NICHT bis %.2f R - die Wirkung (%+.4f entzerrt) liegt "
                  "UNTER der Aufloesungsgrenze, aber ueber dem Nullpunkt"
                  % (trennschaerfe, wirkung_k))
    else:
        urteil = "TRAEGT NICHT - nicht ueber dem Nullpunkt"
    print("     ⚠️ URTEIL: %s" % urteil)
    print("     ⚠️ %s" % VORBEHALT)

    k = erg.get("Kette gesamt")
    if k:
        print("\n  DIE ZAEHLUNG VOR DER DEUTUNG")
        print("     nach der Auswahl (Stufe 5, 20 %%): %.1f Anker je Tag" % k["gewaehlt"])
        print("     nach den Beitragsstufen:          %.1f Anker je Tag" % k["uebrig"])
        print("     gemessene Tage:                   %d" % k["tage"])
        print("\n  ⚠️ EINORDNUNG: die Zahl in der Spalte `entzerrt` ist das, was die")
        print("     Stufen 12 GEGENUEBER DEM ZUFALL leisten. Ein Wert nahe null")
        print("     heisst: die Kette sperrt so gut wie eine Muenze - nicht, dass")
        print("     Sperren nichts braechte.")
        print("     Ein Normurteil (Trennschaerfe, Positivkontrolle) folgt getrennt;")
        print("     diese Messung beantwortet die ZAHL, nicht die Schranke.")
    print("\n  (%.0f s gesamt)" % (time.time() - t0))
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
