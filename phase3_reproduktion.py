# -*- coding: utf-8 -*-
"""Phase 3, Schritt 1: die drei tragenden Beitraege REPRODUZIEREN (18.09.2026).

⚠️⚠️ WARUM ZUERST REPRODUZIERT WIRD (R-R11, Reproduktionspflicht):

    Ein registrierter Befund darf nur von einer Messung umgestossen werden,
    die ihn ZUERST reproduziert. Wer die Basis aendert und ein anderes
    Ergebnis bekommt, hat nichts widerlegt - er hat etwas anderes gemessen.

Die Reproduktion ist deshalb kein Formalismus, sondern der SELBSTTEST DES
MESSAUFBAUS fuer alles, was in Phase 3 danach kommt: Kette gegen Nullwelten,
Beitrag je Stufe, die vier ungemessenen Groessen. Findet dieser Aufbau die
drei bekannten Zahlen nicht wieder, ist jede weitere Zahl von ihm wertlos.

⚠️ ZWEI FENSTER, UND DER UNTERSCHIED IST WICHTIG (Entscheidung beim Bau,
18.09.):

    REPRODUKTION laeuft auf der ORIGINALBASIS der Registrierung (volles
    Fenster). Alles andere waere keine Reproduktion, sondern eine neue
    Messung mit demselben Namen.

    Daneben steht der HEUTIGE STAND ab 2023 - denn die Vorgabe
    ZEITFENSTER-AB-2023 gilt fuer neue Messungen (die 7-Jahres-Tabelle
    mittelt eine gute und eine schlechte Haelfte, +8,64 gegen +2,77).

Beide Zahlen nebeneinander sagen mehr als jede allein: die erste prueft den
Aufbau, die zweite den Beitrag von heute.

⚠️ NUR LESEND, am Desktop, gegen die Messbasis - kein LLM, kein Kontingent,
keine Beruehrung der Produktion (Nutzerentscheidung E1).
"""
from __future__ import annotations

import sys

import numpy as np

import messe_funding_niveau as F
import messe_kandidaten_als_regel as K
import messe_regel_wirksamkeit as RW
import messnorm
import messmenge
import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B

HORIZONT = 20

# Die registrierten Werte - die Zielmarken dieser Reproduktion.
# Quelle: bestand.KANDIDATEN (Stand 18.09.2026).
REGISTRIERT = {
    "funding": {"wert": 0.0246, "basis": "H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre",
                "band": None},
    "turnover": {"wert": 0.0616, "basis": "H20 · 2.636 Kalendertage",
                 "band": (0.0203, 0.1111)},
    "oi_aenderung": {"wert": 0.0145, "basis": "H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker",
                     "band": (0.0097, 0.0193)},
}


def _zusatz(art: str):
    """Die Zusatzquelle je Beitrag - dieselbe wie in der Kette."""
    if art == "funding":
        return F.lade_funding()
    if art == "turnover":
        return MB.reihe("data/onchain_historie.db", "splycur")
    if art in ("oi_aenderung", "long_bias", "top_bias", "taker_bias"):
        # ⚠️ 18.09.: hier stand `None` - und die Messung lief mit NULL Tagen
        # durch, ohne zu klagen. Genau die Sorte stiller Ausfall, gegen die
        # die Reproduktionspflicht gebaut ist: die Zahl fehlte, das Urteil
        # haette "nicht reproduzierbar" gelautet, und die Ursache waere
        # meine Ladung gewesen, nicht der Beitrag.
        return _TERMINMARKT().get(art)
    return None


_TM_ZWISCHENSPEICHER: dict = {}


def _TERMINMARKT() -> dict:
    """Die Terminmarktgroessen - einmal geladen, mehrfach gebraucht."""
    if not _TM_ZWISCHENSPEICHER:
        _TM_ZWISCHENSPEICHER.update(K.lade_terminmarkt())
    return _TM_ZWISCHENSPEICHER


def _ab(je_tag: dict, ab_datum: str | None) -> dict:
    if not ab_datum:
        return je_tag
    return {t: z for t, z in je_tag.items() if str(t)[:10] >= ab_datum}


def messe(je_tag: dict, name: str, rng) -> dict:
    """Die Wirkung als REGEL - dieselbe Funktion, mit der F-212 gerechnet wurde."""
    d, anteil, gesperrt, uebrig = RW.wirkung(je_tag)
    if not d:
        return {"tage": 0}
    werte = np.array(list(d.values()), float)
    return {"tage": len(d), "wirkung": float(np.mean(werte)),
            "median": float(np.median(werte)),
            "anteil_gesperrt": float(np.mean(anteil)) if anteil else float("nan")}


def main() -> int:
    ab = sys.argv[1] if len(sys.argv) > 1 else None
    print("=" * 100)
    print("PHASE 3 · SCHRITT 1 - REPRODUKTION DER DREI TRAGENDEN BEITRAEGE (R-R11)")
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  Zielgroesse bewegung_r · Horizont H%d · Frageart beitrag" % HORIZONT)
    print("  ⚠️ Stellvertretermenge (Nutzerentscheidung N3 b): die Bewertung gilt")
    print("     ausdruecklich NUR auf dieser Menge als validiert, NICHT auf der")
    print("     Live-Menge (Blocker A8, Befund 2.273).")
    print("  ⚠️ Reproduktion auf der ORIGINALBASIS; der heutige Stand steht daneben.")
    print("\n  Kursreihen laden ...")
    reihen = B.lade("krypto", "V1")
    print("  %d Reihen geladen" % len(reihen))

    rng = np.random.default_rng(messnorm.SAAT)
    print("\n  %-14s %12s %12s %12s %10s %10s"
          % ("Beitrag", "registriert", "reproduziert", "ab 2023", "Tage voll", "Tage 2023"))
    ergebnisse = {}
    for art in ("funding", "turnover", "oi_aenderung"):
        je_tag = K.baue(reihen, art, _zusatz(art), horizont=HORIZONT)
        voll = messe(je_tag, art, rng)
        neu = messe(_ab(je_tag, "2023-01-01"), art, rng)
        ergebnisse[art] = {"voll": voll, "ab2023": neu}
        print("  %-14s %+12.4f %+12.4f %+12.4f %10d %10d"
              % (art, REGISTRIERT[art]["wert"],
                 voll.get("wirkung", float("nan")),
                 neu.get("wirkung", float("nan")),
                 voll.get("tage", 0), neu.get("tage", 0)))

    print("\n  Bewertung der Reproduktion:")
    for art, e in ergebnisse.items():
        soll = REGISTRIERT[art]["wert"]
        ist = e["voll"].get("wirkung")
        band = REGISTRIERT[art]["band"]
        if ist is None:
            print("    %-14s KEINE DATEN" % art)
            continue
        if band:
            ok = band[0] <= ist <= band[1]
            wie = "im registrierten Band [%+.4f .. %+.4f]" % band
        else:
            ok = abs(ist - soll) <= max(0.1 * abs(soll), 0.005)
            wie = "innerhalb 10 %% von %+.4f" % soll
        print("    %-14s %s - %s (gemessen %+.4f)"
              % (art, "REPRODUZIERT" if ok else "⚠️ NICHT REPRODUZIERT", wie, ist))
    print("\n" + "=" * 100)
    print("⚠️ Diese Ausgabe ist die ROHE Wirkung. Ein Normurteil (Band, Nullpunkt,")
    print("   Trennschaerfe) folgt im naechsten Schritt - erst muss der Aufbau stehen.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
