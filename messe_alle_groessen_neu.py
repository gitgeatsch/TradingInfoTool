# -*- coding: utf-8 -*-
"""N-51: ALLE Groessen neu — mit allen Kontrollen dieses Tages (05.09.2026)

## Warum eine vollstaendige Neupruefung

Nutzerauftrag: *„auch bisher gefallene Messungen [pruefen], wenn wir keine
tragende Groesse mehr haben."*

**Vier systematische Fehler sind heute aufgeflogen, und jeder hat Kandidaten
zu Unrecht durchfallen ODER zu Unrecht bestehen lassen:**

    gepoolt statt Tagesklammer   erfindet bis 12 Punkte auf einem
                                 Nulleffekt (F-223)
    zu freundlicher Nullpunkt    Faktor 4 zu klein bei persistenten
                                 Groessen (F-226)
    falsche Einheit              `in_r` als Quotenpunkte gelesen,
                                 Faktor 2-3 (F-218/F-219)
    N-19-Kontamination           Nicht-Krypto in jeder Krypto-Messung,
                                 44 Skripte betroffen

⚠️ **Ein Beleg liegt schon vor:** `schnitt50` galt als *„traegt nicht"* und
traegt in der heutigen Messung mit 9,1x am staerksten von allen.

## Was hier gemessen wird — je Groesse, in BEIDEN Formen

    Abdeckung     fuer wie viele Symbole liegt sie vor
    Persistenz    behaelt ein Symbol sein Fuenftel
    Spanne        Abweichung je Fuenftel unter der TAGESKLAMMER
    Nullpunkt     bei der EIGENEN Persistenz, aus der Kurve (5 Ziehungen)
    Verhaeltnis   Spanne / Nullpunkt - die einzige vergleichbare Zahl
    Monotonie     ordnet sie, oder ist sie zweiseitig

⚠️ **Die Veraenderungsform bekommt zusaetzlich die Pruefung, an der
`amihud VER` gefallen ist:** traegt sie noch, wenn ihr EIGENES Niveau
festgehalten wird? Ohne die ist jede Veraenderung nur eine Faerbung des
Niveaus - und die 0,177 Korrelation hat das bei amihud nicht verraten.
Diese Pruefung laeuft nur fuer Formen, die unbedingt ueber 2,5x liegen -
alles darunter ist es nicht wert.

    python messe_alle_groessen_neu.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ ALLES IMPORTIERT, NICHTS NACHGEBAUT.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)
from messe_form_und_nullpunktkurve import (                 # noqa: E402
    veraenderung_quer, DIFFERENZ_TAGE)
from pruefe_persistenz_und_nullpunkt import (               # noqa: E402
    persistenz, kunst_fuenftel)
from pruefe_veraenderungsformen_unabhaengig import bedingt  # noqa: E402

ZIEHUNGEN = 5
BEDINGT_AB = 2.5          # nur was unbedingt so weit traegt, wird bedingt geprueft

AUS_KURSDATEN = ("amihud", "vola", "schnitt", "schnitt50", "rsi",
                 "momentum", "momentum_kurz", "zufall")
AUS_FUNDING = ("funding", "funding_extrem")
AUS_TURNOVER = ("turnover",)
AUS_TERMIN = ("oi_aenderung", "long_bias", "top_bias", "taker_bias",
              "oi_je_umsatz")


def _monoton(w) -> bool:
    g = [x for x in w if x == x]
    if len(g) < 5:
        return False
    return (all(g[i] >= g[i + 1] for i in range(4))
            or all(g[i] <= g[i + 1] for i in range(4)))


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen · Horizont %d"
          % (len(zeilen), len(reihen), ZR.HORIZONT))

    quelle = {}
    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    for a in AUS_FUNDING:
        quelle[a] = fu
    print("  lade turnover ...", flush=True)
    quelle["turnover"] = MB.reihe("data/onchain_historie.db", "splycur")
    print("  lade terminmarkt ...", flush=True)
    try:
        tm = K.lade_terminmarkt()
        for a in AUS_TERMIN:
            if a in tm:
                quelle[a] = tm[a]
        fehlend = [a for a in AUS_TERMIN if a not in quelle]
        if fehlend:
            print("    ⚠️ ohne Quelle, werden uebersprungen: %s" % ", ".join(fehlend))
    except Exception as e:                                   # noqa: BLE001
        print("    ⚠️ Terminmarkt nicht ladbar (%s) - diese Arten entfallen" % e)

    arten = [a for a in (AUS_KURSDATEN + AUS_FUNDING + AUS_TURNOVER
                         + AUS_TERMIN)
             if a in AUS_KURSDATEN or a in quelle]

    # ---- die Nullpunkt-Kurve ----------------------------------------
    print()
    print("=" * 104)
    print("NULLPUNKT-KURVE — Kunstgroessen ohne Information (%d Ziehungen je Block)"
          % ZIEHUNGEN)
    print("=" * 104)
    basis = K.baue(reihen, "amihud", None, horizont=20)
    kurve, bloecke = [], []
    for block in (1, 5, 20, 60, 250, None):
        sp, pe = [], []
        for z in range(ZIEHUNGEN):
            kf = kunst_fuenftel(basis, block, salz=z)
            pe.append(persistenz(kf, tage_je_sym))
            tg, _n, _f = abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, kf))
            sp.append(_spanne(tg))
        kurve.append((float(np.mean(pe)), float(np.max(sp))))
        bloecke.append((float(np.mean(pe)), block))
        print("  Block %-6s Persistenz %5.1f %% · Nullpunkt (max) %5.2f"
              % (str(block), 100 * kurve[-1][0], kurve[-1][1]))
    kurve.sort()

    # ⚠️ DIE GETEILTE KURVE TAUGT NUR ALS BLOCK-ZUORDNUNG (06.09.,
    # vor dem Lauf gefunden).
    #
    # Sie ist auf der Struktur von `amihud` gebaut - 516 Symbole je Tag.
    # `funding` hat 287, `turnover` nur 65. Bei weniger Symbolen je Tag
    # sind die Fuenftel duenner besetzt und verrauschter, der wahre
    # Nullpunkt also GROESSER. Die geteilte Kurve haette Groessen mit
    # duenner Abdeckung besser aussehen lassen, als sie sind - genau der
    # Fehler, der bei turnover schon einmal getaeuscht hat.
    #
    # Deshalb: die Kurve liefert nur noch, WELCHE Blocklaenge zu einer
    # gemessenen Persistenz gehoert. Der Nullpunkt selbst wird je Groesse
    # auf IHRER EIGENEN Struktur gezogen.
    def block_zu_persistenz(p: float):
        return min(bloecke, key=lambda b: abs(b[0] - p))[1]

    def _syms(g: dict) -> int:
        return len({e["sym"] for liste in g.values() for e in liste})

    syms_basis = _syms(basis)

    def nullpunkt_eigen(gebaut_art: dict, p: float) -> float:
        # ⚠️ NUR ZIEHEN, WO DIE ABDECKUNG ABWEICHT (06.09., vor dem Lauf).
        #
        # Die Kurve ist auf `amihud` gebaut. Fuer die acht kursbasierten
        # Arten mit denselben 516 Symbolen IST sie richtig - dort nochmal
        # zu ziehen kostet nur Zeit. Gezogen wird, wenn die Symbolzahl um
        # mehr als 10 % abweicht.
        n = _syms(gebaut_art)
        if abs(n - syms_basis) <= 0.10 * syms_basis:
            w = [sp for pp, sp in kurve if pp <= p + 0.02]
            return max(w) if w else max(sp for _p, sp in kurve)
        block = block_zu_persistenz(p)
        w = []
        for z in range(ZIEHUNGEN):
            kf = kunst_fuenftel(gebaut_art, block, salz=z)
            tg, _n, _f = abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, kf))
            sp = _spanne(tg)
            if sp == sp:
                w.append(sp)
        return float(np.max(w)) if w else float("nan")

    # ---- alle Groessen, beide Formen --------------------------------
    print()
    print("=" * 104)
    print("ALLE GROESSEN — Tagesklammer, Nullpunkt bei der eigenen Persistenz")
    print("=" * 104)
    # ⚠️ DIE TAGESZAHL GEHOERT IN DIE AUSGABE (05.09.).
    # Die Terminmarkt-Quellen umfassen nur 122 Tage gegen 2.884 der
    # Barrierenbasis. Eine Spanne aus 60 Tagen ist etwas voellig anderes
    # als eine aus 2.800 - und `oi_aenderung` ist als Live-Sperre
    # registriert, geprueft auf eben diesen 122 Tagen.
    print("  %-15s %-8s %6s %6s %6s %7s %6s %7s %6s %s"
          % ("Groesse", "Form", "Syms", "Tage", "Spanne", "Pers.", "Null",
             "Verh.", "monot", ""))
    kandidaten = []
    for art in arten:
        try:
            gebaut = K.baue(reihen, art, quelle.get(art), horizont=20)
        except Exception as e:                               # noqa: BLE001
            print("  %-15s -> nicht baubar (%s)" % (art, str(e)[:40]))
            continue
        for form, f5 in (("NIVEAU", _fuenftel_je_tag(gebaut)),
                         ("VERAEND", veraenderung_quer(gebaut, tage_je_sym,
                                                       DIFFERENZ_TAGE))):
            if not f5:
                continue
            syms = len({s for d in f5.values() for s in d})
            p = persistenz(f5, tage_je_sym)
            tg, n_tage, _f = abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
            sp = _spanne(tg)
            if sp != sp:
                continue
            null = nullpunkt_eigen(gebaut, p)
            v = sp / null if null > 0 else float("nan")
            warn = ""
            if n_tage < 400:
                warn = "<- nur %d Tage, nicht belastbar" % n_tage
            elif v <= 2.5:
                warn = "<- traegt nicht"
            print("  %-15s %-8s %6d %6d %6.2f %6.1f%% %6.2f %6.1fx %6s %s"
                  % (art, form, syms, n_tage, sp, 100 * p, null, v,
                     "ja" if _monoton(tg) else "nein", warn))
            if v > BEDINGT_AB and n_tage >= 400:
                kandidaten.append((art, form, f5, sp, v))

    # ---- die Pruefung, an der amihud VER gefallen ist ---------------
    print()
    print("=" * 104)
    print("BEDINGT — traegt die VERAENDERUNG noch, wenn ihr EIGENES Niveau"
          " festgehalten wird?")
    print("=" * 104)
    for art, form, f5, sp, v in kandidaten:
        if form != "VERAEND":
            continue
        # ⚠️ EINMAL BAUEN, NICHT IN DER SCHLEIFE (06.09., vor dem Lauf).
        # Die erste Fassung rief `K.baue` INNERHALB der Ziehungsschleife -
        # fuenfmal je Fuenftel je Art, also 25 unnoetige Aufbauten je
        # Kandidat.
        gebaut_art = K.baue(reihen, art, quelle.get(art), horizont=20)
        niv = _fuenftel_je_tag(gebaut_art)
        echte, nulls = [], []
        for g in range(5):
            fz = bedingt(f5, niv, g)
            if len(fz) < 200:
                continue
            echte.append(_spanne_von := _spanne(abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, fz))[0]))
            kk = []
            for z in range(ZIEHUNGEN):
                kb = bedingt(kunst_fuenftel(
                    gebaut_art, block_zu_persistenz(0.82), salz=z), niv, g)
                if len(kb) >= 200:
                    kk.append(_spanne(abweichung_je_fuenftel(
                        je_tag_und_fuenftel(zeilen, tage_je_sym, kb))[0]))
            if kk:
                nulls.append(float(np.max(kk)))
        if echte and nulls:
            m, n0 = float(np.mean(echte)), float(np.mean(nulls))
            print("  %-15s unbedingt %5.2f (%.1fx) · bedingt %5.2f gegen %5.2f"
                  "  ->  %.1fx  %s"
                  % (art, sp, v, m, n0, m / n0 if n0 > 0 else float("nan"),
                     "✔ eigenstaendig" if n0 > 0 and m / n0 > 2.0
                     else "⚠️ nur eine Faerbung des Niveaus"))
        else:
            print("  %-15s bedingt nicht messbar" % art)

    print()
    print("  ⚠️ NIVEAU-Formen mit hoher Persistenz sind ASSET-Aussagen und")
    print("     gehoeren in die Mail. Nur eigenstaendige VERAENDERUNGEN")
    print("     duerfen den Hebel treiben (Regel 3 in der Fassung vom 05.09.).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
