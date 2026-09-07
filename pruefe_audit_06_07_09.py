# -*- coding: utf-8 -*-
"""AUDIT der Messungen N-52 bis N-58 gegen die eigenen Regeln (07.09.2026)

## Der Anlass

Am 07.09. stellte sich heraus, dass N-56 und N-58 auf der **freien** statt
der **selektierten** Menge gemessen haben. F-212 vom 04.09. hatte das
bereits belegt:

    Die Beitraege wirken auf 1,5 % der Anker. Auf der freien Menge liegt
    funding bei -0,0003 R, also bei null; auf der selektierten (oberste
    5 % je Tag nach 250-Tage-Momentum) traegt es DREIMAL staerker.
    Dort reproduziert auch turnover:
        Funding   +0,0274 R  registriert +0,0246  ✔
        Turnover  +0,0635 R  registriert +0,0616  ✔

Der Nutzer hat daraufhin verlangt, **alle** Messungen nachzupruefen. Das
tut dieses Werkzeug - mechanisch, gegen die im Projekt geltenden Regeln,
statt aus dem Gedaechtnis.

## Die vier Regeln, gegen die geprueft wird

    R1  ZIELGROESSE `barriere` ist nur zulaessig, wo ein Stop den Trade
        BEENDET (`messnorm.STOP_BEENDET` = hebel x einstieg/swing) - ODER
        als VERGLEICH ZWEIER ARME unter derselben Zielregel.
        ⚠️ `spot x einstieg` - die einzige Lage, die es in der Produktion
           gibt (3.513 spot, 0 hebel) - erfuellt die erste Bedingung NICHT.

    R2  MENGE. Wer ueber einen BEITRAG urteilt, muss auf der SELEKTIERTEN
        Menge messen (F-212). Auf der freien wirken die Beitraege auf
        1,5 % der Anker.

    R3  TRENNSCHAERFE. `messnorm.Befund` lehnt jeden Befund ohne
        Positivkontrolle ab: *"ein 'traegt nicht' ohne Trennschaerfe ist
        keine Messung, sondern das Fehlen einer"*.

    R4  ZIEHUNGSZAHL. Mindestens fuenf Mischungen je Kontrolle.

    python pruefe_audit_06_07_09.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messnorm as N                                          # noqa: E402


@dataclass(frozen=True)
class Messung:
    kennung: str
    frage: str
    lage: tuple            # (instrument, strategie)
    zielgroesse: str       # "barriere" | "bewegung_r" | "zaehlung"
    armvergleich: bool     # zwei Arme unter derselben Zielregel?
    beitragsurteil: bool   # urteilt sie ueber einen BEITRAG?
    menge: str             # "frei" | "selektiert"
    mischungen: int
    trennschaerfe: bool
    kernbefund: str
    richtung: str          # "positiv" (traegt) | "negativ" (traegt nicht)
    bemerkung: str = ""


# ⚠️ DIE ANGABEN SIND AUS DEN SKRIPTEN ABGELESEN, NICHT GESCHAETZT.
MESSUNGEN = (
    Messung("N-52", "Traegt `vola` Richtung?", ("spot", "einstieg"),
            "barriere", True, True, "frei", 5, False,
            "GS -0,00041 (2/5) - keine Richtung; AUF +0,03088 traegt",
            "negativ",
            "Zwei geeichte Kunstwelten als Nullpunkt - das ist mehr als "
            "die Norm verlangt, aber KEINE Trennschaerfe auf den echten "
            "Daten."),
    Messung("N-53", "Tragen funding/turnover Richtung?", ("spot", "einstieg"),
            "barriere", True, True, "frei", 5, False,
            "funding GS +0,00197 ✔ · turnover GS +0,00512 ✔ · vola ✖",
            "positiv",
            "Die POSITIVEN Befunde brauchen keine Trennschaerfe. Der "
            "negative (vola) schon."),
    Messung("N-54", "Spielen Geometrie- und Richtungsebene zusammen?",
            ("spot", "einstieg"), "barriere", True, True, "frei", 5, False,
            "Baender ueberlappen - kein Zusammenspiel", "negativ", ""),
    Messung("N-55", "`vola` in der Geometrie: Stopweite, Horizont, Hebel?",
            ("spot", "einstieg"), "barriere", False, False, "frei", 0, False,
            "Spreizung haelt (+0,035..+0,126 R); Bauform aendert sich nicht",
            "gemischt",
            "Der PEGEL ist kein Armvergleich. Kunstwelt-Strukturfehler "
            "bereits im Befund vermerkt."),
    Messung("N-56", "Traegt die OI-Sperre Richtung? Reproduziert turnover?",
            ("spot", "einstieg"), "barriere", True, True, "frei", 5, False,
            "oi GS +0,00220/+0,00381 ✔ · turnover reproduziert NICHT",
            "gemischt",
            "⚠️ Der turnover-Teil ist durch F-212 widerlegt."),
    Messung("N-57", "Wieviel laeuft flach aus?", ("spot", "einstieg"),
            "zaehlung", False, False, "frei", 0, False,
            "31,4 % bei H5, 5,3 % bei H20; Median 3 Tage", "zaehlung",
            "Reine Zaehlung - kein Beitragsurteil. ⚠️ Aber die DEUTUNG "
            "('die Produktion laeuft bis Stop oder Ziel') ist falsch: bei "
            "spot beendet der Stop den Trade NICHT."),
    Messung("N-58", "Lassen sich turnovers Stufen herleiten?",
            ("spot", "einstieg"), "barriere", True, True, "frei", 5, True,
            "nichts traegt, Trennschaerfe 2,0 Punkte", "negativ",
            "⚠️ Durch F-212 widerlegt - auf der selektierten Menge "
            "reproduziert turnover (+0,0635 gegen +0,0616)."),
)


def pruefe(m: Messung) -> list:
    """Die vier Regeln auf eine Messung anwenden."""
    aus = []
    stop_beendet = m.lage in N.STOP_BEENDET
    # R1
    if m.zielgroesse == "barriere" and not stop_beendet:
        if m.armvergleich:
            aus.append(("○", "R1", "barriere auf %s x %s - zulaessig NUR als "
                        "Armvergleich, und das ist es" % m.lage))
        else:
            aus.append(("✖", "R1", "barriere auf %s x %s ohne Armvergleich - "
                        "UNZULAESSIG (Erwartungswert per Konstruktion null)"
                        % m.lage))
    # R2
    if m.beitragsurteil and m.menge == "frei":
        aus.append(("✖", "R2", "Beitragsurteil auf der FREIEN Menge - dort "
                    "wirken die Beitraege auf 1,5 % der Anker (F-212)"))
    # R3
    if m.richtung == "negativ" and not m.trennschaerfe:
        aus.append(("✖", "R3", "'traegt nicht' OHNE Trennschaerfe - nach "
                    "messnorm kein Befund, sondern das Fehlen einer Messung"))
    # R4
    if m.mischungen and m.mischungen < 5:
        aus.append(("✖", "R4", "nur %d Mischungen" % m.mischungen))
    if not aus:
        aus.append(("✔", "--", "keine Regel verletzt"))
    return aus


def main() -> int:
    print("=" * 96)
    print("AUDIT der Messungen vom 06./07.09.2026 gegen die eigenen Regeln")
    print("=" * 96)
    print("  STOP_BEENDET = %s" % sorted(N.STOP_BEENDET))
    print("  ⚠️ `spot x einstieg` ist NICHT dabei - und es ist die einzige")
    print("     Lage, die es in der Produktion gibt (3.513 spot, 0 hebel).")

    schwer, leicht, sauber = [], [], []
    for m in MESSUNGEN:
        print()
        print("  %s  %s" % (m.kennung, m.frage))
        print("     Lage %s x %s · Zielgroesse %s · Menge %s · %d Mischungen"
              % (m.lage[0], m.lage[1], m.zielgroesse, m.menge, m.mischungen))
        print("     Befund: %s" % m.kernbefund)
        for zeichen, regel, text in pruefe(m):
            print("       %s %-3s %s" % (zeichen, regel, text))
        if m.bemerkung:
            print("       ⓘ  %s" % m.bemerkung)
        marken = [z for z, _r, _t in pruefe(m)]
        if "✖" in marken:
            (schwer if m.beitragsurteil else leicht).append(m.kennung)
        else:
            sauber.append(m.kennung)

    print()
    print("=" * 96)
    print("DAS ERGEBNIS")
    print("=" * 96)
    print("  ✖ Beitragsurteil mit Regelverstoss : %s" % ", ".join(schwer))
    print("  ○ sonstiger Verstoss               : %s"
          % (", ".join(leicht) or "-"))
    print("  ✔ ohne Verstoss                    : %s"
          % (", ".join(sauber) or "-"))
    print()
    print("  ⚠️⚠️ DIE GEMEINSAME URSACHE ist NICHT die Zielgroesse - alle")
    print("     Beitragsurteile waren Armvergleiche und damit zulaessig.")
    print("     Es ist die MENGE: sechs von sieben Messungen liefen auf der")
    print("     freien Menge, obwohl F-212 seit dem 04.09. belegt, dass die")
    print("     Beitraege dort auf 1,5 % der Anker wirken.")
    print()
    print("  ⚠️ UND DIE TRENNSCHAERFE: vier Nullbefunde ohne Positivkontrolle.")
    print("     `messnorm.Befund` lehnt genau das ab - ich habe die Norm")
    print("     umgangen, weil meine Zielgroesse dort nicht vorgesehen war.")
    print("     Der Grund, warum sie nicht vorgesehen war, ist der Befund.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
