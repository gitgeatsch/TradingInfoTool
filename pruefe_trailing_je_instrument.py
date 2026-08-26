"""Trägt das Trailing für SPOT und HEBEL gleichermaßen? (26.08.2026, Frage B)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. Frage A hat gemessen (33.192 mechanische Anker, Block-Bootstrap):
das Trailing NUETZT im Baermarkt (+0,059 R, [+0,037; +0,080]) und SCHADET in
der Aufwaertsphase (-0,043 R, [-0,068; -0,018]). Beide Intervalle schliessen
die Null nicht ein.

Offen bleibt die zweite Trennung, und sie entscheidet ueber die Konsequenz:

    Traegt die Regel bei HEBEL und nicht bei SPOT?
    Dann lautet die Antwort nicht "abschalten", sondern "nur an den Hebel".

WARUM DAS EINE ANDERE FRAGE IST ALS A. Bei Frage A wurden mechanische
Einstiege auf Kursreihen gerechnet - dort gibt es kein Spot und kein Hebel,
nur Parameter. ⚠️ UND DIE VERWENDETEN PARAMETER SIND HEBEL-NAH: Stop 3,94 %,
Horizont 14 Tage. Der Spot-Stop liegt bei 6-12 %, der Horizont bei 120 Tagen.
Frage A hat also naeherungsweise den HEBEL-Fall gemessen.

DESHALB HIER: echte, aufgeloeste Signale, getrennt nach Instrument.

DIE RECHNUNG, wie am 04.08.:

    ohne Trailing  = outcome_realisiertes_crv        (was tatsaechlich geschah)
    mit Trailing   = max(realisiert, MFE - abstand)  falls MFE >= ausloese
                     sonst unveraendert

    Begruendung: der nachgezogene Stop sichert `MFE - abstand`. Lag das
    tatsaechliche Ergebnis darunter, haette er gegriffen; lag es darueber,
    aendert er nichts.

DIE KONTROLLE ist ein BLOCK-BOOTSTRAP auf den paarweisen Differenzen
(Methodik 2.55) - keine Permutation: beide Werte stammen vom SELBEN Signal,
es gibt keine Zuordnung zu zerstoeren.

⚠️ BLOECKE NACH ZEIT, nicht nach Symbol. Signale verschiedener Symbole am
selben Tag sind abhaengig - sie sehen denselben Markt. Sortiert wird nach
`created_at`, Bloecke sind zusammenhaengende Laeufe.

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    beide Intervalle ueber null
        -> die Regel traegt fuer beide; A's Phasenbefund bleibt die einzige
           Einschraenkung
    HEBEL ueber null, SPOT nicht
        -> ⚠️ die Regel gehoert NUR AN DEN HEBEL - dorthin, wo der Stop real
           hinterlegt wird und die Liquidation droht
    SPOT ueber null, HEBEL nicht
        -> die Erwartung waere umgekehrt; dann ist die Begruendung "der Stop
           liegt bei Spot nicht an der Boerse" zu ueberdenken
    keines von beiden trennbar
        -> auf dieser Basis nicht entscheidbar; als Zerlegung ablegen (2.51)

⚠️ DIE BASIS IST DUENN, und das ist vorab zu sagen: rund 100 aufgeloeste
Spot- und 127 Hebel-Signale. Bei Bloecken von 10 sind das etwa 10 bzw. 13
Bloecke - die Untergrenze fuer einen Bootstrap. Ein Intervall, das die Null
knapp verfehlt, ist hier KEIN Beleg, sondern ein Hinweis.

    python pruefe_trailing_je_instrument.py
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys

import numpy as np

EXPORT = (r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten"
          r"/notebook_diagnose.json")
AUFGELOEST = ("take_profit_erreicht", "stop_loss_erreicht",
              "abgelaufen_unentschieden")
AUSLOESE_R = 1.0
ABSTAND_R = 1.0
BLOCKLAENGE = 10
ZIEHUNGEN = 2000


def _paare(rows: list, ausloese: float, abstand: float) -> list:
    """(created_at, ohne, mit) je aufgeloestem Signal mit MFE."""
    aus = []
    for r in rows:
        if str(r.get("outcome_status")) not in AUFGELOEST:
            continue
        ohne = r.get("outcome_realisiertes_crv")
        mfe = r.get("outcome_max_realisiertes_crv")
        if ohne is None or mfe is None:
            continue
        ohne, mfe = float(ohne), float(mfe)
        # Der nachgezogene Stop sichert MFE - abstand. Lag das Ergebnis
        # darunter, haette er gegriffen.
        mit = max(ohne, mfe - abstand) if mfe >= ausloese else ohne
        aus.append((str(r.get("created_at") or ""), ohne, mit))
    aus.sort()
    return aus


def _bootstrap(diffs: list, blocklaenge: int, ziehungen: int,
               saat: int = 20260826) -> dict | None:
    """Vertrauensintervall der mittleren Differenz, Bloecke nach ZEIT."""
    if len(diffs) < 2 * blocklaenge:
        return None
    bloecke = [diffs[s:s + blocklaenge]
               for s in range(0, len(diffs), blocklaenge)]
    bloecke = [b for b in bloecke if b]
    if len(bloecke) < 8:
        return None
    rng = np.random.default_rng(saat)
    mittel = []
    for _z in range(ziehungen):
        gez: list = []
        while len(gez) < len(diffs):
            gez.extend(bloecke[int(rng.integers(0, len(bloecke)))])
        mittel.append(float(np.mean(gez[:len(diffs)])))
    mittel.sort()
    return {"punkt": float(np.mean(diffs)), "n": len(diffs),
            "bloecke": len(bloecke),
            "u": mittel[int(0.025 * len(mittel))],
            "o": mittel[int(0.975 * len(mittel))]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=EXPORT)
    ap.add_argument("--ausloese", type=float, default=AUSLOESE_R)
    ap.add_argument("--abstand", type=float, default=ABSTAND_R)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_trailing_instrument.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    d = json.load(io.open(a.export, encoding="utf-8"))
    print("=" * 78)
    print("TRAILING JE INSTRUMENT - echte, aufgeloeste Signale")
    print("=" * 78)
    print(f"Regel: Trailing ab {a.ausloese:.1f} R, Abstand {a.abstand:.1f} R")
    print(f"Bloecke von {a.blocklaenge} zusammenhaengenden Signalen (nach Zeit)")
    print()
    print(f"{'Instrument':11s}{'n':>6s}{'Bloecke':>9s}{'EW ohne':>10s}"
          f"{'EW mit':>10s}{'Delta':>9s}{'95%-Intervall':>21s}   Urteil")

    erg = {}
    for name, key in (("SPOT", "spot_signals"), ("HEBEL", "hebel_signals")):
        p = _paare(d.get(key, []), a.ausloese, a.abstand)
        if not p:
            print(f"{name:11s}   keine auswertbaren Faelle")
            continue
        ohne = [x[1] for x in p]
        mit = [x[2] for x in p]
        diffs = [m - o for o, m in zip(ohne, mit)]
        bs = _bootstrap(diffs, a.blocklaenge, ZIEHUNGEN)
        if not bs:
            print(f"{name:11s}{len(p):>6d}   zu wenige Bloecke fuer den Bootstrap")
            continue
        schliesst_null = bs["u"] <= 0 <= bs["o"]
        urteil = ("nicht von null zu trennen" if schliesst_null
                  else "NUETZT" if bs["u"] > 0 else "SCHADET")
        erg[name] = {**bs, "ew_ohne": st.fmean(ohne), "ew_mit": st.fmean(mit),
                     "urteil": urteil,
                     "n_beruehrt": sum(1 for o, m in zip(ohne, mit) if m != o)}
        print(f"{name:11s}{bs['n']:>6d}{bs['bloecke']:>9d}"
              f"{st.fmean(ohne):>+10.3f}{st.fmean(mit):>+10.3f}"
              f"{bs['punkt']:>+9.3f}"
              f"  [{bs['u']:+7.3f}, {bs['o']:+7.3f}]   {urteil}")

    print()
    for name, v in erg.items():
        print(f"  {name}: das Trailing beruehrt {v['n_beruehrt']} von {v['n']} "
              f"Signalen ({100 * v['n_beruehrt'] / v['n']:.0f} %)")

    print()
    print("=" * 78)
    print("LESART - vorab festgelegt")
    print("=" * 78)
    s_, h_ = erg.get("SPOT"), erg.get("HEBEL")
    if s_ and h_:
        if h_["urteil"] == "NUETZT" and s_["urteil"] != "NUETZT":
            print("  ⚠️ Die Regel gehoert NUR AN DEN HEBEL - dorthin, wo der")
            print("     Stop real hinterlegt wird und die Liquidation droht.")
        elif s_["urteil"] == "NUETZT" and h_["urteil"] != "NUETZT":
            print("  Umgekehrt zur Erwartung: sie traegt bei SPOT, nicht bei")
            print("  Hebel. Dann ist die Begruendung zu ueberdenken.")
        elif s_["urteil"] == h_["urteil"] == "NUETZT":
            print("  Die Regel traegt fuer beide; A's Phasenbefund bleibt die")
            print("  einzige Einschraenkung.")
        else:
            print("  Auf dieser Basis NICHT ENTSCHEIDBAR - als Zerlegung")
            print("  ablegen (2.51), nicht als Nullbefund.")
    print()
    print("⚠️ Die Basis ist duenn (rund 100 bzw. 127 Faelle). Ein Intervall,")
    print("   das die Null knapp verfehlt, ist hier ein Hinweis, kein Beleg.")

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"ausloese_r": a.ausloese, "abstand_r": a.abstand,
             "blocklaenge": a.blocklaenge, "ergebnis": erg},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
