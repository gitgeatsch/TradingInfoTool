# -*- coding: utf-8 -*-
"""TRAEGT DIE EIGENSCHAFT ZUSAETZLICH ZUR LAGE - IM NORMPFAD?

⚠️⚠️ WARUM DIESER ZWEITE ANLAUF NOETIG IST. Der Mitlaeufertest
(`phase4_c_mitlaeufer_asset_lage`) hat die eine Richtung beantwortet:
die LAGE traegt eigenstaendig, der Verlust durch Festhalten der
EIGENSCHAFT betraegt nur 2 bis 10 Prozent. Die andere Richtung blieb
ERGEBNISLOS: die Eigenschaft traegt dort auch in der ZUFALLSkontrolle
nicht - sie faellt also nicht durch die Schichtung, sie war auf jenem
Pfad nie nachweisbar.

Der Grund ist der Pfad, nicht die Sache:

    geschichtet + urteil_tage   feste Menge 20 %, Block 15,
                                Mediandifferenz, KEINE Trennschaerfe
    pruefe_auswahl (NORM)       Menge nach Datenlage, Nullpunkt aus 40
                                gemischten Welten, MIT Trennschaerfe

Nur der zweite kann „traegt nicht bis X" sagen. Der erste kann das
nicht, und ein Nullbefund dort ist deshalb nicht deutbar.

## Der Aufbau - RESIDUALISIEREN statt Schichten

Damit die Norm anwendbar bleibt, wird die Schicht nicht in die Messung
gezogen, sondern in die GROESSE: je Kalendertag wird nach der Schicht in
Fuenftel sortiert, und der Kandidat bekommt seinen RANG INNERHALB seines
Faches als neuen Wert. Ueber die Faecher hinweg tragen diese Raenge
keine Schichtinformation mehr - was danach noch traegt, kann die Schicht
nicht erklaeren.

⚠️ VIER ARME, SYMMETRISCH. Die erste Fassung des Mitlaeufertests gab nur
EINER Seite eine Zufallskontrolle; dadurch war nicht zu unterscheiden,
ob ein Arm DURCH die Residualisierung faellt oder ohnehin nicht traegt.
Jede Seite bekommt hier ihre eigene.

    A  LAGE        residualisiert nach EIGENSCHAFT
    B  EIGENSCHAFT residualisiert nach LAGE
    C  LAGE        residualisiert nach ZUFALL      (Kontrolle zu A)
    D  EIGENSCHAFT residualisiert nach ZUFALL      (Kontrolle zu B)

⚠️⚠️ DIE GLEICHSTANDSFALLE, ausgewiesen statt uebersehen
(`gleichstaende-brechen-nach-reihenfolge`): ein Rang INNERHALB eines
Faches liegt auf einem groben Raster, und ueber fuenf Faecher hinweg
tritt derselbe Wert mehrfach auf. `_rang` bricht Gleichstaende nach der
Reihenfolge. Deshalb laeuft eine REIHENFOLGEPROBE mit: dieselbe Messung
mit durchmischter Symbolreihenfolge je Tag. Verschiebt sie das Ergebnis,
haengt es an den Gleichstaenden und nicht an der Sache.

⚠️ R-R11: H2..H5, 365 Tage, freier Umlauf. Sagt nichts ueber die
registrierte Tabelle (H20, 2.636 Tage, Gesamtausgabe).

    python phase4_c_zusatzbeitrag_normpfad.py
    python phase4_c_zusatzbeitrag_normpfad.py --feste-menge 10% --reihenprobe
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messe_regel_wirksamkeit as W                        # noqa: E402
import messnorm as N                                       # noqa: E402
import messnorm_auswahl as MA                              # noqa: E402
import phase3_stufen as ST                                 # noqa: E402
import phase4_c_hypothese_turnover as HY                   # noqa: E402
import phase4_c_kalibrierung_freefloat as C                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250          # noqa: E402

SAAT = 20260921
FAECHER = 5
MIND_JE_FACH = 4


def _arg(args, f, v):
    return args[args.index(f) + 1] if f in args else v


def residualisieren(ziel: dict, schicht: dict) -> dict:
    """Rang des Ziels INNERHALB der Fuenftel der Schicht, je Tag.

    Gibt wieder `{symbol: {tag: wert}}` - dieselbe Form wie die Eingabe,
    damit `K.baue(..., 'turnover_markt', ...)` sie annimmt.

    ⚠️⚠️ `mische` GEHOERT HIER NICHT HIN - und das ist ein korrigierter
    Fehler. Die erste Fassung mischte die Symbolreihenfolge VOR der
    Residualisierung. Dort sind die Werte aber STETIG (log-Umschlag),
    also gleichstandsfrei: die Mischung aenderte nichts, und das
    Ergebnis war byteidentisch. Ein Schalter, der nichts anfasst,
    belegt keine Stabilitaet - dieselbe Klasse Fehler wie bei
    `--nullsaat`.
    Die Gleichstaende ENTSTEHEN durch die Residualisierung (Raenge auf
    grobem Raster) und wirken erst DANACH, im Querschnittsrang. Die
    Probe sitzt deshalb jetzt in `mische_tagesreihenfolge`.
    """
    tage = {}
    for sym, d in ziel.items():
        s = schicht.get(sym)
        if not s:
            continue
        for t, w in d.items():
            if t in s:
                tage.setdefault(t, []).append((sym, w, s[t]))
    aus: dict = {}
    for t, zeilen in tage.items():
        if len(zeilen) < FAECHER * MIND_JE_FACH:
            continue
        syms = [x[0] for x in zeilen]
        z = np.array([x[1] for x in zeilen], float)
        sw = np.array([x[2] for x in zeilen], float)
        fach = np.minimum((W.rang(sw) * FAECHER).astype(int), FAECHER - 1)
        for f in range(FAECHER):
            m = fach == f
            if m.sum() < MIND_JE_FACH:
                continue
            # ⚠️⚠️ STETIG STATT RANG - und das ist ein korrigierter
            # Fehler. Die erste Fassung nahm `W.rang(z[m])`: innerhalb
            # eines Faches liegen die Raenge dann auf einem Raster von
            # 1/73, und ueber fuenf Faecher hinweg wiederholen sich
            # dieselben Werte. Gemessen waren nur 38 Prozent der Werte
            # je Tag verschieden - 62 Prozent Gleichstaende. `W.rang`
            # bricht die nach REIHENFOLGE, und bei einer Auswahl der
            # obersten 20 Prozent entscheidet das am Rand ueber die
            # Zugehoerigkeit. Die Reihenfolgeprobe hat daraufhin ein
            # URTEIL GEKIPPT (Arm D bei H2, TRAEGT -> traegt nicht).
            #
            # Hier stattdessen die STANDARDISIERTE Abweichung vom
            # Fachmedian: Lage und Streuung des Faches sind heraus, die
            # Groesse bleibt STETIG und damit gleichstandsfrei. Der
            # Median statt des Mittels, weil die Verteilung schief ist.
            zz = z[m]
            mid = float(np.median(zz))
            q1, q3 = np.percentile(zz, [25, 75])
            spanne = float(q3 - q1)
            if spanne <= 0:
                continue
            for i, idx in enumerate(np.flatnonzero(m)):
                aus.setdefault(syms[idx], {})[t] = float(
                    (zz[i] - mid) / spanne)
    return aus


def mische_tagesreihenfolge(je_tag: dict, rng) -> dict:
    """Die REIHENFOLGE der Eintraege je Tag drehen - Werte unberuehrt.

    ⚠️ HIER wirkt sie: `W.rang` bricht Gleichstaende nach der
    Reihenfolge der Liste. Nach der Residualisierung liegen 62 Prozent
    der Werte auf Gleichstaenden (Raster 38 %), und bei einer Auswahl
    der obersten 20 Prozent entscheidet die Reihenfolge ueber die
    Zugehoerigkeit am Rand.
    """
    aus = {}
    for t, z in je_tag.items():
        z2 = list(z)
        rng.shuffle(z2)
        aus[t] = z2
    return aus


def raster(reihe: dict) -> tuple:
    """Wie grob ist das Raster? Gleichstaende sichtbar machen."""
    je_tag = {}
    for sym, d in reihe.items():
        for t, w in d.items():
            je_tag.setdefault(t, []).append(w)
    if not je_tag:
        return 0, 0.0
    n = [len(v) for v in je_tag.values()]
    u = [len(set(v)) for v in je_tag.values()]
    return int(np.median(n)), float(np.median(u)) / max(np.median(n), 1)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "2,3,5").split(","))
    fest = _arg(args, "--feste-menge", "10%")
    rueck = int(_arg(args, "--rueckblick", str(HY.RUECKBLICK)))
    saat = int(_arg(args, "--saat", str(SAAT)))
    reihenprobe = "--reihenprobe" in args

    print("=" * 112)
    print("ZUSATZBEITRAG IM NORMPFAD - traegt die EIGENSCHAFT noch, "
          "wenn die LAGE heraus ist?")
    print("=" * 112)
    print("  " + N.standardzeile())
    neu, _weg, _ges = C.menge_neu(C.MENGE_DB, True)
    datei, _sql = MR.MESSBASIS["schnitt"]
    log_u, ab = HY.reihen_umschlag(neu, datei)
    asset, lage = HY.zerlege(log_u, rueck)
    mr = np.random.default_rng(saat + 77) if reihenprobe else None
    # ⚠⚠ REPRODUZIERBARER ZUFALL. Die erste Fassung zog ihn aus
    # `hash((sym, tag))` - und `hash` ist in Python JE PROZESS anders
    # (PYTHONHASHSEED). Dieselbe Messung haette bei jedem Aufruf eine
    # andere Kontrolle gehabt, und eine Kontrolle, die sich selbst
    # aendert, ist keine.
    _rz = np.random.default_rng(saat + 991)
    zuf_a = {sy: {t: float(_rz.random()) for t in d}
             for sy, d in asset.items()}
    zuf_l = {sy: {t: float(_rz.random()) for t in d}
             for sy, d in lage.items()}

    arme = (("A LAGE ohne EIGENSCHAFT", lage, asset),
            ("B EIGENSCH ohne LAGE", asset, lage),
            ("C LAGE ohne ZUFALL", lage, zuf_l),
            ("D EIGENSCH ohne ZUFALL", asset, zuf_a))
    print("  Fenster ab %s · Rueckblick %d · feste Menge %s%s"
          % (ab, rueck, fest,
             " · REIHENFOLGEPROBE aktiv" if reihenprobe else ""))
    zellen = len(horizonte) * len(arme)
    print("  ⚠️ %d Zellen - familienweiter Fehlalarm rund %.0f %%. "
          "Geurteilt wird nach FORM ueber H2/H3/H5"
          % (zellen, 100 * ST.familienfehler(zellen)))
    print("  ⚠️ R-R11: sagt nichts ueber die registrierte Tabelle "
          "(H20, 2.636 Tage, Gesamtausgabe).")
    print()
    reihen = B.lade()
    mom = momentum250(reihen)
    lg = N.Lage(instrument="spot", strategie="einstieg")
    print("  %-24s %3s %6s %6s %9s %20s %9s %7s  %s"
          % ("Arm", "H", "Syms", "Raster", "Wirkung", "Band", "Bezug",
             "Blöcke", "Urteil"))
    erg: dict = {}
    for H in horizonte:
        for name, ziel, schicht in arme:
            res = residualisieren(ziel, schicht)
            n_tag, anteil = raster(res)
            je = C.beschneiden(
                K.baue(reihen, "turnover_markt", res, horizont=H), None, ab)
            if mr is not None:
                je = mische_tagesreihenfolge(je, mr)
            if not je:
                print("  %-24s %3d -> leere Welt" % (name, H))
                continue
            try:
                b = MA.pruefe_auswahl(
                    name.split()[1], je, mom, lage=lg, menge=fest,
                    rng=np.random.default_rng(saat), horizont=H,
                    hypothese="Zusatzbeitrag nach Residualisierung",
                    verwendung="Beitrag", zielgroesse="bewegung_r")
            except Exception as exc:                       # noqa: BLE001
                print("  %-24s %3d -> %s" % (name, H, str(exc)[:58]))
                continue
            erg.setdefault(name, {})[H] = b
            print("  %-24s %3d %6d %5.0f%% %+9.4f [%+.4f..%+.4f] %+9.4f "
                  "%7d  %s"
                  % (name, H, b.abdeckung_symbole, 100 * anteil,
                     b.wirkung, b.unten, b.oben, b.bezugswert,
                     b.n_bloecke, C.kurz(b.urteil)), flush=True)
        print()

    print("=" * 112)
    print("  AUSWERTUNG")
    print("=" * 112)
    print("  ⚠️ ,Raster` ist der Anteil VERSCHIEDENER Werte je Tag. "
          "Liegt er deutlich unter")
    print("     100 %, gibt es Gleichstaende, und `_rang` bricht sie "
          "nach Reihenfolge -")
    print("     dann gehoert die Reihenfolgeprobe (--reihenprobe) "
          "dazu, bevor man urteilt.")
    print()
    for name, _z, _s in arme:
        je_h = erg.get(name, {})
        if not je_h:
            print("  %-24s keine auswertbare Zelle" % name)
            continue
        ohne = [h for h, b in je_h.items()
                if b.urteil.startswith("KEIN BEFUND")]
        t = [h for h, b in je_h.items() if b.traegt and h not in ohne]
        print("  %-24s %s   traegt bei %s%s"
              % (name,
                 " ".join("H%d:%+.4f%s" % (h, je_h[h].wirkung,
                                           "*" if (je_h[h].traegt and
                                                   h not in ohne) else "")
                          for h in sorted(je_h)),
                 ("H" + ", H".join(str(x) for x in sorted(t))) if t
                 else "KEINEM",
                 (" ⚠️ kein Befund bei H%s" % ",H".join(str(x) for x in ohne))
                 if ohne else ""))
    print()
    print("  ➤ LESEART: Arm B gegen Arm D ist die eigentliche Frage. "
          "Traegt B nicht,")
    print("     D aber schon, hat die LAGE der EIGENSCHAFT ihren "
          "Beitrag genommen -")
    print("     sie waere ein Mitlaeufer. Tragen BEIDE nicht, war die "
          "Eigenschaft auf")
    print("     diesem Pfad nie nachweisbar, und der Test sagt ueber "
          "sie nichts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
