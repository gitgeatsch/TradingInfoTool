# -*- coding: utf-8 -*-
"""Fuer WIEVIELE Werte gilt jeder Beitrag ueberhaupt? (31.08.2026)

⚠️ DIESES WERKZEUG HAETTE VOR R1 LAUFEN MUESSEN.

Nutzervorwurf 31.08., woertlich: *"Pruefe fuer die definierten Beitraege, ob
wir die erforderliche Abdeckung haben - das waere schon vorher dein JOB
gewesen - ich sagte bereits, wenn H FAELLT dann haben wir ein PROBLEM!"*

Er hat recht, und der Fehler ist benennbar:

    Vorfilter H      galt fuer JEDES Asset - er wurde je Anker aus den
                     Marken gerechnet. Abdeckung 100 %.
    Funding-Rang     gilt fuer Symbole in `funding_historie.db`.
    Turnover-Rang    gilt fuer Symbole mit Umlaufmenge in `onchain_historie`.

**Ich habe einen Beitrag mit voller Abdeckung durch zwei mit Luecken
ersetzt und nur die WIRKSAMKEIT geprueft, nicht die REICHWEITE.** Solange
Stufe 11 nur zaehlte, war das folgenlos. Seit G-6 (31.08.) entscheidet
genau diese Frage, ob ein Asset ueberhaupt je ein Signal bekommen kann:

    kein Beitrag  ->  Potential 0,000  ->  Stufe 11 verwirft  ->  NIE ein Signal

Die stehende Regel sagt es seit dem 30.08.: *"Die Haeufigkeit gehoert immer
dazu."* Ich habe sie auf H angewandt (2,2 % der Anker) und bei den
Nachfolgern vergessen.

## Was hier geprueft wird

    1  JE BEITRAG   fuer wieviele Werte der Watchlist liegt er vor?
    2  JE ASSET     wieviele Beitraege hat dieser Wert - und kann er
                    ueberhaupt je die Schwelle nehmen?
    3  DIE LUECKE   welche Werte haben GAR KEINEN Beitrag?
    4  DIE FOLGE    was heisst das mit scharfer Stufe 11?

    python pruefe_beitragsabdeckung.py [--klasse krypto]
"""
import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agent import assetklassen as AK                          # noqa: E402
from agent import marktrang as MR                             # noqa: E402
from agent import potential as PT                             # noqa: E402
from agent import wahrscheinlichkeit as WK                    # noqa: E402

CRV = 2.0
STOP_REL = 0.05


def abdeckung(klasse: str) -> dict:
    """Je Symbol: welche Merkmale liegen vor?"""
    symbole = AK.gruppiere().get(klasse) or []
    if not symbole:
        return {}
    aus = {s: {} for s in symbole}
    if klasse == "krypto":
        try:
            r = MR.raenge(symbole)
        except Exception as exc:                             # noqa: BLE001
            print("⚠️ Marktrang nicht abrufbar: %s" % exc)
            r = {}
        for s in symbole:
            e = r.get(s) or {}
            # ⚠️ JEDES registrierte Merkmal, nicht eine feste Liste. Die
            # erste Fassung nannte nur Funding und Turnover - der am
            # 31.08. dazugekommene Schnittabstand erschien deshalb mit
            # 0 % Abdeckung, obwohl er lieferte. Eine Abdeckungspruefung,
            # die neue Beitraege nicht kennt, prueft die falsche Menge.
            for b in WK.BEITRAEGE:
                if b.merkmal and b.merkmal != "h":
                    aus[s][b.merkmal] = e.get(b.merkmal)
    # ⚠️ H WIRD JE ANKER GERECHNET, nicht abgerufen - er galt fuer JEDES
    # Asset. Genau das ist der Punkt dieser Pruefung.
    return aus


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--klasse", default=None, help="nur diese Klasse")
    a = p.parse_args()

    gruppen = AK.gruppiere()
    klassen = [a.klasse] if a.klasse else sorted(gruppen)

    print("=" * 100)
    print("ABDECKUNG DER BEITRAEGE — fuer wieviele Werte gilt jeder ueberhaupt?")
    print("=" * 100)
    print("Schwelle %.3f R, CRV %.1f" % (PT.schwelle(), CRV))
    print()
    print("⚠️ SEIT G-6 ENTSCHEIDET DAS UEBER LEBEN UND TOD JEDES ASSETS:")
    print("   kein Beitrag -> Potential 0,000 -> Stufe 11 verwirft -> nie ein Signal")

    tragend = [b for b in WK.BEITRAEGE if b.zustand == "traegt"]
    print()
    print("Registriert als `traegt`: %s"
          % (", ".join(b.name for b in tragend) or "KEINER"))

    schlimm = []
    for klasse in klassen:
        symbole = gruppen.get(klasse) or []
        if not symbole:
            continue
        deck = abdeckung(klasse)
        print()
        print("-" * 100)
        print("  %s — %d Werte" % (klasse.upper(), len(symbole)))
        print("-" * 100)

        # ---- 1 JE BEITRAG -------------------------------------------
        gilt_hier = [b for b in tragend
                     if not b.klassen or klasse in b.klassen]
        if not gilt_hier:
            print("  ⚠️⚠️ KEIN EINZIGER BEITRAG IST FUER %s REGISTRIERT."
                  % klasse.upper())
            print("     Jedes Potential liegt bei 0,000 - mit scharfer")
            print("     Stufe 11 bekommt hier NIE ein Wert ein Signal.")
            schlimm.append((klasse, len(symbole), len(symbole)))
            continue
        print("  %-26s %10s %10s" % ("Beitrag", "vorhanden", "Abdeckung"))
        for b in gilt_hier:
            n = sum(1 for s in symbole
                    if deck.get(s, {}).get(b.merkmal) is not None)
            marke = "" if n >= 0.8 * len(symbole) else "  ⚠️"
            print("  %-26s %8d/%-3d %8.0f %%%s"
                  % (b.name[:26], n, len(symbole), 100 * n / len(symbole),
                     marke))

        # ---- 2/3 JE ASSET -------------------------------------------
        ohne, gesperrt = [], []
        for s in symbole:
            m = {k: v for k, v in deck.get(s, {}).items() if v is not None}
            if not m:
                ohne.append(s)
            try:
                pot = PT.rechne(crv=CRV, stop_relativ=STOP_REL, klasse=klasse,
                                instrument="spot", strategie="einstieg",
                                h=None, merkmale=m or None).wert_r
            except Exception:                                # noqa: BLE001
                continue
            if not PT.traegt(pot):
                gesperrt.append(s)
        print()
        print("  ⚠️ OHNE JEDEN BEITRAG: %d von %d (%.0f %%)"
              % (len(ohne), len(symbole), 100 * len(ohne) / len(symbole)))
        if ohne:
            print("     %s" % ", ".join(sorted(ohne)))
            print("     -> diese Werte koennen NIE ein Signal bekommen,")
            print("        unabhaengig von Kurs, Lage und Modellurteil.")
        print("  bei heutigem Stand unter der Schwelle: %d von %d (%.0f %%)"
              % (len(gesperrt), len(symbole), 100 * len(gesperrt) / len(symbole)))
        if len(ohne):
            schlimm.append((klasse, len(symbole), len(ohne)))

    # ---- 4 DIE FOLGE -----------------------------------------------
    print()
    print("=" * 100)
    print("URTEIL")
    print("=" * 100)
    if not schlimm:
        print("  ✔ Jeder Wert jeder gepruesten Klasse hat mindestens einen")
        print("    Beitrag. Die Abdeckung traegt die scharfe Stufe 11.")
        return 0
    print("  ⚠️⚠️ DIE ABDECKUNG TRAEGT DIE SCHARFE STUFE 11 NICHT:")
    for klasse, n, o in schlimm:
        print("     %-12s %d von %d Werten ohne jeden Beitrag (%.0f %%)"
              % (klasse, o, n, 100 * o / n))
    print()
    print("  Solange das gilt, ist eine scharfe Stufe 11 kein Filter,")
    print("  sondern ein Ausschluss - und zwar nach Datenlage, nicht nach")
    print("  Qualitaet. Das ist genau der Fehler, den H nicht hatte:")
    print("  er galt fuer JEDEN Wert.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
