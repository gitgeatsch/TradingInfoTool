# -*- coding: utf-8 -*-
"""SCHRITT 4a - DIE DURCHMESSUNG, GEGEN DIE REGISTRIERUNG GEHALTEN (06.09.)

## ⚠️ Der Grundsatz, der diese Datei traegt

**Nutzervorgabe 06.09.:** *"bevor ein zuvor tragender Wert umgestossen wird,
ist dies sauber zu begruenden - welche Hypothese liegt zugrunde, was wurde
warum gemessen, gilt das nur fuer den Einzelwert oder fehlt eine weitere
Bewertungsebene damit dieser traegt. Das Thema ist sehr schwierig, sonst
bleiben wir in der Umbauschleife."*

Daraus folgt die Regel:

    Ein registrierter Befund darf nur von einer Messung umgestossen werden,
    die ihn ZUERST REPRODUZIERT. Wer die Basis aendert und ein anderes
    Ergebnis bekommt, hat nichts widerlegt - er hat etwas anderes gemessen.

## Warum das hier noetig wurde

Schritt 3 hat alle Kandidaten bei H5 ab 2024 gemessen. Registriert wurden
sie aber anders:

    funding        2.369 Kalendertage · 290 Symbole · 6,3 Jahre · +0,0246 R
    turnover       2.636 Kalendertage · +0,0616 R [+0,0203 .. +0,1111]
    oi_aenderung   1.702 Kalendertage · H20 · +0,0145 R [+0,0097 .. +0,0193]

Schritt 3 mass 959 Tage ab 2024 bei H5. **Zwei Groessen wurden gleichzeitig
geaendert** - Horizont UND Abschnitt. Ein abweichendes Ergebnis sagt dann
nicht, WELCHE der beiden es verursacht hat.

## Der Aufbau: die zwei Aenderungen GETRENNT

    A  H20 · volle Historie     REPRODUKTION - kommt die Registrierung zurueck?
    B  H5  · volle Historie     nur der HORIZONT geaendert
    C  H5  · ab 2024            zusaetzlich der ABSCHNITT geaendert

    A -> B  isoliert die Wirkung des Horizonts
    B -> C  isoliert die Wirkung der Epoche

Beides auf BEIDEN Massstaeben (Mittel und Rand > +2 R, Schritt 3).

## Was ein Ergebnis bedeuten darf

    A reproduziert + B/C weichen ab   -> GELTUNGSBEREICH eingeschraenkt,
                                         kein Widerruf
    A reproduziert NICHT              -> ernster Fall: die Registrierung
                                         selbst ist zu pruefen, nicht der
                                         Kandidat
    A, B, C alle negativ              -> erst dann Widerruf - und auch dann
                                         erst nach der naechsten
                                         Bewertungsebene (Kombination,
                                         Schicht, Verwendungsform)

    python schritt4a_matched.py
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
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

STAERKEN = (0.02, 0.05, 0.10, 0.20)

# Was die Registrierung sagt - die Messlatte, nicht die Erwartung.
REGISTRIERT = {
    "funding": ("+0,0246 R", "2.369 Tage, 290 Symbole"),
    "turnover": ("+0,0616 R [+0,0203 .. +0,1111]", "2.636 Tage"),
    "oi_aenderung": ("+0,0145 R [+0,0097 .. +0,0193]", "1.702 Tage, H20"),
    # ⚠️ KORREKTUR 06.09.: die erste Fassung schrieb hier "ZURUECKGENOMMEN
    # 31.08." - das gilt fuer `schnitt` (200-Tage-Abstand), NICHT fuer
    # `schnitt50` (50-Tage). Der Horizontlauf vom 31.08. mass BEIDE; die
    # Zahlen H5 -0,0069 / H20 -0,0221 gehoeren zum 200er. Der 50er wurde
    # bei H2 (+0,0029, traegt nicht) und H20 (kein Urteil, Positivkontrolle
    # versagte) gemessen - H5 NIE.
    "schnitt50": ("H2 +0,0029 traegt nicht · H20 kein Urteil",
                  "31.08., H5 nie gemessen"),
    "schnitt": ("ZURUECKGENOMMEN 31.08. (200-Tage)",
                "H5 -0,0069 · H20 -0,0221"),
    "vola": ("nicht registriert", "-"),
    "amihud": ("nicht registriert", "-"),
}

# A / B / C  -  (Bezeichnung, Horizont, ab-Datum oder None)
LAEUFE = (("A H20 voll", 20, None),
          ("B H5  voll", 5, None),
          ("C H5  2024", 5, "2024-01-01"))


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")

    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    print("  %d Kryptoreihen" % len(reihen), flush=True)
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    try:
        tm = K.lade_terminmarkt()
    except Exception:                                        # noqa: BLE001
        tm = {}
    arten = [("schnitt50", None), ("vola", None), ("amihud", None),
             ("funding", fu), ("turnover", tu)]
    if "oi_aenderung" in tm:
        arten.append(("oi_aenderung", tm["oi_aenderung"]))

    print()
    print("=" * 112)
    print("SCHRITT 4a  -  DIE ZWEI AENDERUNGEN GETRENNT")
    print("=" * 112)
    print("  A -> B  isoliert den HORIZONT      B -> C  isoliert die EPOCHE")
    print()

    ergebnis: dict = {}
    for art, quelle in arten:
        reg, basis = REGISTRIERT.get(art, ("-", "-"))
        print("  %s   registriert: %s   (%s)" % (art.upper(), reg, basis),
              flush=True)
        print("    %-12s %6s %5s  %-42s  %s"
              % ("Lauf", "Tage", "Blk", "MITTEL", "RAND > +2 R"))
        ergebnis[art] = {}
        for lab, hor, ab in LAEUFE:
            g = K.baue(reihen, art, quelle, horizont=hor)
            if ab:
                g = {t: z for t, z in g.items() if t >= ab}
            if len(g) < 100:
                print("    %-12s   zu wenige Tage (%d)" % (lab, len(g)))
                continue
            zeile, tage, blk = {}, 0, 0
            for mass in ("mittel", "rand2"):
                rng = np.random.default_rng(N.SAAT)
                try:
                    if mass == "mittel":
                        f = N.pruefe(art, g, lage=L, zielgroesse="bewegung_r",
                                     menge="frei", rng=rng, horizont=hor,
                                     staerken=STAERKEN)
                    else:
                        f = R.pruefe_rand(art, g, lage=L, menge="frei",
                                          rng=rng, marke=2.0, horizont=hor,
                                          staerken=STAERKEN)
                except Exception as e:                       # noqa: BLE001
                    zeile[mass] = None
                    print("      %s/%s: %s" % (art, mass, e))
                    continue
                zeile[mass] = f
                tage, blk = f.n_tage, f.n_bloecke
            ergebnis[art][lab] = zeile

            def kurz(f):
                if f is None:
                    return "-"
                k = ("TRAEGT" if f.traegt else
                     "kein Befund" if f.trennschaerfe_in_r is None else
                     "nicht trennbar" if abs(f.wirkung) >= f.trennschaerfe
                     else "traegt nicht")
                return "%+.5f [%+.5f..%+.5f] %s" % (f.wirkung, f.unten,
                                                    f.oben, k)

            print("    %-12s %6d %5d  %-42s  %s"
                  % (lab, tage, blk, kurz(zeile.get("mittel")),
                     kurz(zeile.get("rand2"))), flush=True)
        print()

    # ---------------------------------------------------------------- Urteil
    print("=" * 112)
    print("WAS SICH GEAENDERT HAT - und wodurch")
    print("=" * 112)
    print("  %-14s %-10s %-16s %-16s  %s"
          % ("Kandidat", "Massstab", "A->B (Horizont)", "B->C (Epoche)",
             "Deutung"))
    for art, laeufe in ergebnis.items():
        for mass, mname in (("mittel", "Mittel"), ("rand2", "Rand>+2R")):
            hol = lambda l: (laeufe.get(l, {}) or {}).get(mass)   # noqa: E731
            a, b, c = hol("A H20 voll"), hol("B H5  voll"), hol("C H5  2024")
            if a is None:
                continue
            tr = lambda f: (f is not None and f.traegt)           # noqa: E731
            ab_ = "%s -> %s" % ("TRAEGT" if tr(a) else "nein",
                                "TRAEGT" if tr(b) else "nein")
            bc = "%s -> %s" % ("TRAEGT" if tr(b) else "nein",
                               "TRAEGT" if tr(c) else "nein")
            # ⚠️ FEHLER IN DER ERSTEN FASSUNG (06.09., beim Lesen des
            # eigenen Ergebnisses gefunden): sie schrieb "REPRODUKTION
            # MISSLUNGEN" auch fuer Kandidaten, die NIE registriert wurden
            # (vola, amihud), und fuer den RAND-Massstab, auf dem ueberhaupt
            # nie etwas registriert worden ist. Von einer Reproduktion kann
            # nur sprechen, wo es etwas zu reproduzieren GIBT.
            hat_registrierung = (
                mass == "mittel"
                and art in ("funding", "turnover", "oi_aenderung"))
            if tr(a) and not tr(b):
                deut = "faellt am HORIZONT"
            elif tr(a) and tr(b) and not tr(c):
                deut = "faellt an der EPOCHE"
            elif tr(a) and tr(c):
                deut = "haelt durchgehend"
            elif not tr(a) and hat_registrierung:
                deut = "⚠️ REPRODUKTION MISSLUNGEN - Registrierung pruefen"
            elif not tr(a):
                deut = "traegt auf keinem Lauf (nie registriert)"
            else:
                deut = "-"
            print("  %-14s %-10s %-16s %-16s  %s"
                  % (art, mname, ab_, bc, deut))
    print()
    print("  ⚠️ 'faellt am Horizont' oder 'an der Epoche' ist eine")
    print("     GELTUNGSBEREICHS-Aussage, KEIN Widerruf. Ein Widerruf")
    print("     verlangt zusaetzlich die naechste Bewertungsebene:")
    print("     Kombination, Schichtentest, Verwendungsform.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
