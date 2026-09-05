# -*- coding: utf-8 -*-
"""N-49: Die FORM je Groesse — gegen eine Nullpunkt-KURVE (05.09.2026)

## Der Anlass — eine Regel richtig gelesen

Nutzerklarstellung 05.09.: Die Fassung in `CLAUDE.md` (*„Wir bewerten
Zeitpunkte, nicht Assets"*, Beispiel *„SUPRA ist Schrott"*) steht so in
KEINEM Quelldokument. Der Wortlaut vom 27.08. lautet:

    "Wir bewerten nicht Assets, sondern suchen unabhaengig davon, WANN ein
     Handeln begruendet ist. Auch ein Shitcoin/Altcoin hat Potential."

Und praezisiert am 05.09.:

    - der TAKT bzw. Messzeitpunkt darf nicht entscheiden
    - beim HEBEL darf kein Asset-RANG entscheiden
    - in der MAIL ist "wie gut steht das Asset" ausdruecklich erwuenscht

⚠️ Damit ist die Frage nicht *"amihud registrieren oder nicht"*, sondern
**welcher ANTEIL seiner Wirkung ueber den MOMENT spricht** statt ueber das
Asset. Das ist eine fachliche Frage - also eine Messung.

## ⚠️ Warum eine KURVE und nicht ein Nullpunkt

N-48 hat gezeigt: eine Kunstgroesse ohne jede Information erzeugt allein
durch **Persistenz plus ueberlappende Ausgaenge** rund einen Punkt Spanne.
Der ehrliche Nullpunkt haengt also von der Persistenz ab - und die
unterscheidet sich je Form dramatisch:

    amihud NIVEAU quer     95,4 %
    amihud LAENGS          niedriger
    amihud VERAENDERUNG    niedriger

**Ein einziger Nullpunkt taugt deshalb nicht.** Hier wird eine KURVE
gemessen: Kunstgroessen mit Blocklaengen von 1 bis unendlich, je mit ihrer
Persistenz und ihrer Spanne. Jede echte Form wird dann gegen den Nullpunkt
**bei ihrer eigenen Persistenz** gelesen.

## Die Formen

    NIVEAU quer        Rang gegen die anderen Werte desselben Tages
    NIVEAU laengs      Rang gegen die EIGENE Vergangenheit (250 Tage)
    VERAENDERUNG quer  Rang der Veraenderung ueber 20 Tage
                       -> "dieser Wert ist gerade illiquider als er war"

⚠️ Alle nachlaufend: `kennzahl` benutzt nur Vergangenheit, die Differenz
ebenso.

    python messe_form_und_nullpunktkurve.py
"""
from __future__ import annotations

import sys
from binascii import crc32
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ ALLES IMPORTIERT, NICHTS NACHGEBAUT.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)
from pruefe_vola_zeitpunkt_oder_asset import (              # noqa: E402
    laengs_fuenftel, _als_reihen)
from pruefe_persistenz_und_nullpunkt import (               # noqa: E402
    persistenz, kunst_fuenftel)

ARTEN = ("amihud", "vola", "schnitt50")
ZIEHUNGEN = 5
DIFFERENZ_TAGE = 20


def veraenderung_quer(gebaut: dict, tage_je_sym: dict, n: int) -> dict:
    """Fuenftel der VERAENDERUNG der Kennzahl ueber n Tage, quer je Tag.

    ⚠️ Nachlaufend: kennzahl(t) - kennzahl(t-n), beide aus der
    Vergangenheit. Die Fuenftel entstehen ueber `_fuenftel_je_tag`, also
    ueber dieselbe Rangfunktion wie bei allen anderen Formen.
    """
    reihen = _als_reihen(gebaut, tage_je_sym)
    neu: dict = defaultdict(list)
    for sym, folge in reihen.items():
        tage = tage_je_sym.get(sym)
        if not tage:
            continue
        for i in range(n, min(len(folge), len(tage))):
            a, b = folge[i], folge[i - n]
            if a is None or b is None:
                continue
            neu[tage[i]].append({"sym": sym, "kennzahl": float(a - b)})
    return _fuenftel_je_tag({t: v for t, v in neu.items() if len(v) >= 10})


def _messe(zeilen, tage_je_sym, f5) -> tuple[list, float]:
    tg, _n, _f = abweichung_je_fuenftel(
        je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
    return tg, _spanne(tg)


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen · Horizont %d"
          % (len(zeilen), len(reihen), ZR.HORIZONT))

    gebaut = {}
    for art in ARTEN:
        print("  baue %s ..." % art, flush=True)
        gebaut[art] = K.baue(reihen, art, None, horizont=20)

    # ---- 1. Die Nullpunkt-KURVE -------------------------------------
    print()
    print("=" * 96)
    print("1. NULLPUNKT-KURVE — Kunstgroessen ohne Information, je Blocklaenge")
    print("=" * 96)
    print("  %-22s %10s %8s" % ("Kunstgroesse", "Persistenz", "Spanne"))
    # ⚠️ MEHRERE ZIEHUNGEN JE BLOCKLAENGE (05.09., eigener Fehler).
    #
    # Die erste Fassung zog EINMAL je Blocklaenge - und die Kurve fiel und
    # stieg wieder (95,9 % -> 0,49 · 98,5 % -> 0,41 · 99,6 % -> 1,14),
    # obwohl sie monoton wachsen muss. Das war Streuung einer Einzelziehung,
    # kein Verlauf. EINE ZIEHUNG IST KEIN NULLPUNKT - derselbe Fehler wie
    # heute frueh in F-215, dort mit einer Mischung statt zehn.
    #
    # Berichtet wird der MITTELWERT und das MAXIMUM; als Grenze gilt das
    # Maximum, damit der Nullpunkt nie zu freundlich ausfaellt.
    print("  %-22s %10s %8s %8s %8s"
          % ("", "Persistenz", "Mittel", "max", "Ziehungen"))
    kurve = []
    for name, block in (("neu je Tag", 1), ("neu alle 5 Tage", 5),
                        ("neu alle 20 Tage", 20), ("neu alle 60 Tage", 60),
                        ("neu alle 250 Tage", 250), ("fest je Symbol", None)):
        spannen, pers = [], []
        for z in range(ZIEHUNGEN):
            kf = kunst_fuenftel(gebaut["amihud"], block, salz=z)
            pers.append(persistenz(kf, tage_je_sym))
            _tg, sp = _messe(zeilen, tage_je_sym, kf)
            spannen.append(sp)
        pm = float(np.mean(pers))
        kurve.append((pm, float(np.max(spannen))))
        print("  %-22s %9.1f %% %7.2f %8.2f %8d"
              % (name, 100 * pm, float(np.mean(spannen)),
                 float(np.max(spannen)), ZIEHUNGEN))
    kurve.sort()

    def nullpunkt(p: float) -> float:
        """Interpolierter Nullpunkt bei Persistenz p - der HOECHSTE
        Kurvenwert bis p, damit die Grenze nie zu freundlich ausfaellt."""
        werte = [sp for pp, sp in kurve if pp <= p + 0.02]
        return max(werte) if werte else max(sp for _p, sp in kurve)

    # ---- 2. Die echten Formen ---------------------------------------
    print()
    print("=" * 96)
    print("2. DIE FORMEN — jede gegen den Nullpunkt BEI IHRER Persistenz")
    print("=" * 96)
    print("  %-11s %-14s %-34s %7s %6s %7s %s"
          % ("Groesse", "Form", "Abweichung je Fuenftel", "Spanne",
             "Pers.", "Null", "Verhaeltnis"))
    for art in ARTEN:
        formen = (
            ("NIVEAU quer", _fuenftel_je_tag(gebaut[art])),
            ("NIVEAU laengs", laengs_fuenftel(
                _als_reihen(gebaut[art], tage_je_sym), tage_je_sym)),
            ("VERAENDERUNG", veraenderung_quer(
                gebaut[art], tage_je_sym, DIFFERENZ_TAGE)),
        )
        for name, f5 in formen:
            if not f5:
                print("  %-11s %-14s keine Fuenftel" % (art, name))
                continue
            p = persistenz(f5, tage_je_sym)
            tg, sp = _messe(zeilen, tage_je_sym, f5)
            null = nullpunkt(p)
            v = sp / null if null > 0 else float("nan")
            print("  %-11s %-14s %-34s %7.2f %5.1f%% %7.2f %6.1fx%s"
                  % (art, name, " ".join("%+5.2f" % x for x in tg), sp,
                     100 * p, null, v, "" if v > 2.0 else "   <- traegt nicht"))
        print()

    print("=" * 96)
    print("⚠️ LESEART")
    print("=" * 96)
    print("  NIVEAU quer   sagt ueberwiegend 'welches ASSET' - gehoert in die")
    print("                Mail als Einordnung, nicht in die Hebelerzeugung")
    print("  LAENGS/VERAENDERUNG  sagen 'wie steht dieser Wert GERADE' -")
    print("                nur diese duerfen den Hebel treiben")
    print()
    print("  Das Verhaeltnis ist die einzige vergleichbare Zahl: die Spanne")
    print("  allein waechst mit der Persistenz, auch ganz ohne Information.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
