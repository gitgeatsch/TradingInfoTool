# -*- coding: utf-8 -*-
"""SCHRITT 3 - DIE GEGENPRUEFUNG (06.09.2026)

Der Hauptlauf hat vier Behauptungen erzeugt. Keine davon wird ausgesprochen,
bevor sie eine ANDERE SAAT ueberlebt hat - und bevor die Nullbaender selbst
sichtbar sind.

  G1  SAATSTABILITAET
      Die Trefferzahlen der Positivkontrolle sind teils knapp (vola/Rand2:
      0,02 -> 3 von 5). Eine Trennschaerfe, die mit der Saat wandert, ist
      keine. Geprueft mit drei Saaten.

  G2  DAS NULLBAND SICHTBAR MACHEN
      turnover zeigt am Mittel +0,0172 mit Band [+0,0094 .. +0,0251] - das
      Band schliesst die Null aus, das Urteil lautet trotzdem "traegt
      nicht". Grund muss sein, dass das NULLBAND ebenso hoch reicht. Das
      ist nachzuweisen, nicht zu vermuten.

  G3  DER EINE ECHTE FUND
      vola traegt am Rand (+0,0038) und nicht am Mittel (-0,0013). Das ist
      genau der Fall, den 2.112 vorhergesagt hat. Haelt er?

  G4  DIE EINSEITIGKEIT DER NORM
      `Befund.traegt` prueft nur `unten > null_oben` - also nur die
      POSITIVE Richtung. oi_aenderung zeigt am Rand -0,0015 mit Band
      [-0,0022 .. -0,0008], das die Null klar ausschliesst, und wird als
      "traegt nicht" gemeldet. Das ist zu zeigen und zu bewerten.

    python schritt3_gegenpruefung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

HORIZONT, AB = 5, "2024-01-01"
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)
SAATEN = (20260906, 12345, 987654321)
PRUEFE = ("vola", "funding", "turnover", "oi_aenderung")


def _band(d, rng, block, titel="x"):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return MB.urteil_tage(titel, d, rng, block)


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    block = N._block(HORIZONT)

    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    try:
        tm = K.lade_terminmarkt()
    except Exception:                                        # noqa: BLE001
        tm = {}
    quellen = {"vola": None, "funding": fu, "turnover": tu,
               "oi_aenderung": tm.get("oi_aenderung")}
    welten = {}
    for art in PRUEFE:
        if art != "vola" and quellen[art] is None:
            continue
        g = K.baue(reihen, art, quellen[art], horizont=HORIZONT)
        welten[art] = {t: z for t, z in g.items() if t >= AB}
    print("  %d Kandidaten gebaut" % len(welten), flush=True)

    # ---------------- G2 + G4  die BAENDER offenlegen ---------------------
    print()
    print("=" * 100)
    print("G2/G4  DIE BAENDER OFFENGELEGT  -  Wirkung, Nullband, und was das")
    print("       einseitige `traegt` daraus macht")
    print("=" * 100)
    print("  %-13s %-6s %10s %22s %22s  %s"
          % ("Kandidat", "Mass", "Wirkung", "Band der Wirkung",
             "NULLBAND (5 Ziehungen)", "einseitig?"))
    for art, je_tag in welten.items():
        for lab, fn in (("Mittel", None), ("Rand2", 2.0), ("Rand3", 3.0)):
            rng = np.random.default_rng(N.SAAT)
            if fn is None:
                d, _a, _g, _u = W.wirkung(je_tag, True)
            else:
                d, _a, _g, _u = R.wirkung_rand(je_tag, True, marke=fn)
            h = _band(d, rng, block)
            nu, no = [], []
            for z in range(N.ZIEHUNGEN):
                m = np.random.default_rng(N.SAAT + z)
                if fn is None:
                    n0, _b, _c, _e = W.wirkung(je_tag, True, mische=m)
                else:
                    n0, _b, _c, _e = R.wirkung_rand(je_tag, True, mische=m,
                                                    marke=fn)
                nb = _band(n0, rng, block)
                if nb:
                    nu.append(nb["unten"]); no.append(nb["oben"])
            nun, non = min(nu), max(no)
            pos = h["unten"] > max(0.0, non)
            neg = h["oben"] < min(0.0, nun)
            merk = ("-" if pos else
                    "JA - negativ und klar" if neg else
                    "nein")
            print("  %-13s %-6s %10.5f  [%+.5f .. %+.5f]  [%+.5f .. %+.5f]  %s"
                  % (art, lab, h["mittel"], h["unten"], h["oben"], nun, non,
                     merk))
        print()

    # ---------------- G1 + G3  SAATSTABILITAET ----------------------------
    print("=" * 100)
    print("G1/G3  SAATSTABILITAET  -  dieselbe Messung mit drei Saaten")
    print("=" * 100)
    print("  %-13s %-6s %-10s %-10s %-10s  %s"
          % ("Kandidat", "Mass", "Saat 1", "Saat 2", "Saat 3", "stabil?"))
    for art, je_tag in welten.items():
        for lab, mk in (("Mittel", None), ("Rand2", 2.0), ("Rand3", 3.0)):
            ts, urteile = [], []
            for saat in SAATEN:
                rng = np.random.default_rng(saat)
                alt = N.SAAT
                N.SAAT = saat
                R.SAAT = saat
                try:
                    if mk is None:
                        f = N.pruefe(art, je_tag, lage=L, frageart="markt",
                                     zielgroesse="bewegung_r", menge="frei",
                                     rng=rng, horizont=HORIZONT,
                                     staerken=STAERKEN)
                    else:
                        f = R.pruefe_rand(art, je_tag, lage=L, frageart="markt", menge="frei",
                                          rng=rng, marke=mk,
                                          horizont=HORIZONT,
                                          staerken=STAERKEN)
                finally:
                    N.SAAT = alt
                    R.SAAT = alt
                ts.append(f.trennschaerfe_in_r)
                urteile.append("TRAEGT" if f.traegt else "nein")
            gleich = len(set(urteile)) == 1
            print("  %-13s %-6s %-10s %-10s %-10s  %s"
                  % (art, lab,
                     *["%s/%s" % (("%.2f" % t) if t else "-", u)
                       for t, u in zip(ts, urteile)],
                     "JA" if gleich else "⚠️ WANDERT"))
        print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
