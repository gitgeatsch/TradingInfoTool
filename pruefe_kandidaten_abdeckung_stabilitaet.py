# -*- coding: utf-8 -*-
"""N-43: TRAEGT er UND DECKT er? - beide Kriterien gemeinsam (05.09.2026)

## Warum beide, und warum jetzt

Nutzerentscheidung 05.09.: **erst die Bewertung, dann der Hebelumbau.**
O4 ist damit der Blocker, nicht mehr die Richtung.

Aus **F-217** und **F-218** kommen zwei Kriterien, die bisher nie zusammen
erhoben wurden:

    TRAEGT er   haelt die Fuenftel-Ordnung ueber die ZEIT?
                turnover ist genau hier gefallen (+0,020 gegen Zufall -0,007)

    DECKT er    fuer wie viele Symbole liegt er ueberhaupt vor?
                turnover deckt 42 von 302 - und aus der ungleichen Abdeckung
                entstand die Scheinkalibrierung, die F-215 zu Fall brachte

⚠️ Ein Kandidat, der nur eines von beiden erfuellt, wird NICHT registriert.
Genau das ist mit funding (traegt schwach, deckt 302) und turnover (traegt
nicht, deckt 42) passiert.

## Die Kandidaten

Aus **N-17b**, dort bereits als tragend gemessen - aber nie auf Stabilitaet
und nie auf Abdeckung geprueft:

    vola             aus Kursdaten    keine Zusatzquelle
    rsi              aus Kursdaten    keine Zusatzquelle
    momentum_kurz    aus Kursdaten    keine Zusatzquelle
    funding_extrem   aus Funding      302 Symbole

Zum Vergleich laufen die beiden REGISTRIERTEN mit, damit die Zahlen
einzuordnen sind - und `zufall` als Kontrolle.

## Die Messung

Unveraendert die aus **F-217** (`pruefe_stufen_stabilitaet.py`), importiert
statt nachgebaut: Spearman ueber alle Blockpaare, gegen einen UNTEREN
Nullpunkt (Fuenftel je Tag gemischt) und eine SPANNENREIHE als oberen.

    python pruefe_kandidaten_abdeckung_stabilitaet.py [--bloecke 6]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ IMPORTIERT, NICHT NACHGEBAUT - dieselbe Rechnung wie in F-217.
from pruefe_stufen_stabilitaet import (                     # noqa: E402
    stufen_je_block, bewerte, MIND_JE_FUENFTEL)

SAAT = 20260905

KANDIDATEN = ("vola", "rsi", "momentum_kurz", "funding_extrem")
REGISTRIERT = ("funding", "turnover")

# Welche Zusatzquelle braucht welche Art? Wer hier fehlt, kommt aus den
# reinen Kursdaten und braucht keine.
BRAUCHT_FUNDING = ("funding", "funding_extrem")
BRAUCHT_TURNOVER = ("turnover",)
BRAUCHT_TERMIN = ("oi_aenderung", "long_bias", "top_bias", "oi_je_umsatz")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bloecke", type=int, default=6)
    p.add_argument("--laengs", action="store_true",
                   help="Fuenftel je SYMBOL aus der eigenen Vergangenheit "
                        "statt je Tag quer - die Regel-3-reine Form. Die "
                        "Stabilitaetspruefung lief bisher NUR quer; fuer "
                        "einen Bau auf der Laengs-Form fehlte sie (N-43c).")
    p.add_argument("--arten", default=None,
                   help="Kommaliste; Vorgabe sind die vier aus N-17b. "
                        "`zufall` wird immer ergaenzt - es ist der Nullpunkt.")
    a = p.parse_args()

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    if a.arten:
        arten = [x.strip() for x in a.arten.split(",") if x.strip()]
    else:
        arten = list(KANDIDATEN) + list(REGISTRIERT)
    if "zufall" not in arten:
        arten.append("zufall")

    # ⚠️ Quellen NUR laden, wo sie gebraucht werden - `lade_funding()` und
    # die Onchain-Reihe kosten Zeit und werden sonst umsonst geholt.
    quellen = {}
    if any(x in BRAUCHT_FUNDING for x in arten):
        print("  lade funding ...", flush=True)
        fu = F.lade_funding()
        for x in BRAUCHT_FUNDING:
            quellen[x] = fu
    if any(x in BRAUCHT_TURNOVER for x in arten):
        print("  lade turnover ...", flush=True)
        quellen["turnover"] = MB.reihe("data/onchain_historie.db", "splycur")
    f5 = {}
    for art in arten:
        print("  baue %s%s ..." % (art, " (laengs)" if a.laengs else ""),
              flush=True)
        gebaut = K.baue(reihen, art, quellen.get(art), horizont=20)
        if a.laengs:
            # ⚠️ IMPORTIERT, NICHT NACHGEBAUT - dieselben Funktionen wie in
            # N-43c, damit quer und laengs wirklich vergleichbar sind.
            from pruefe_vola_zeitpunkt_oder_asset import (
                laengs_fuenftel, _als_reihen)
            f5[art] = laengs_fuenftel(_als_reihen(gebaut, tage_je_sym),
                                      tage_je_sym)
        else:
            f5[art] = _fuenftel_je_tag(gebaut)

    alle = sorted({t for d in f5.values() for t in d})
    gr = len(alle) // a.bloecke
    bloecke = [set(alle[i * gr:(i + 1) * gr]) for i in range(a.bloecke)]

    # ---- KRITERIUM 2: Abdeckung -------------------------------------
    print()
    print("=" * 92)
    print("KRITERIUM 2 — ABDECKUNG")
    print("=" * 92)
    print("  %-16s %9s %11s %9s" % ("Kandidat", "Symbole", "Sym-Tage", "Anteil"))
    sym_ges = len(reihen)
    abdeckung = {}
    for art in arten:
        syms = {s for d in f5[art].values() for s in d}
        paare = sum(len(d) for d in f5[art].values())
        abdeckung[art] = len(syms)
        print("  %-16s %9d %11d %8.1f %%"
              % (art, len(syms), paare, 100.0 * len(syms) / max(sym_ges, 1)))
    print()
    print("  (%d Reihen insgesamt · turnover deckte 42 und fiel deshalb auf)"
          % sym_ges)

    # ---- KRITERIUM 1: Stabilitaet -----------------------------------
    # ⚠️ DER NULLPUNKT IST DIE KUNSTGROESSE `zufall`, NICHT DIE EIGENE
    # MISCHUNG (05.09., eigener Fehler in der ersten Fassung).
    #
    # Die erste Urteilsregel verglich jede Groesse nur mit ihrer eigenen
    # Mischung und schrieb bei `momentum_kurz` "haelt" - bei +0,080 gegen
    # -0,153. Der belastbare Massstab ist die Kunstgroesse `zufall`: ihr
    # ECHT-Wert zeigt, wie "kein Signal" bei DIESER Blockzahl aussieht,
    # und ihre Streuung gibt das Rauschband. Es wird deshalb zuerst
    # gerechnet und danach als Schwelle benutzt.
    rng = np.random.default_rng(SAAT)
    arten = ["zufall"] + [a for a in arten if a != "zufall"]
    rauschen = None
    for art in arten:
        print()
        print("=" * 92)
        print("%s — haelt die Ordnung? (deckt %d Symbole)"
              % (art.upper(), abdeckung[art]))
        print("=" * 92)

        echt = bewerte("ECHT", stufen_je_block(zeilen, tage_je_sym,
                                               f5[art], bloecke))

        misch = {}
        for tag, d in f5[art].items():
            syms = list(d)
            werte = list(d.values())
            rng.shuffle(werte)
            misch[tag] = dict(zip(syms, werte))
        zufall = bewerte("ZUFALL", stufen_je_block(zeilen, tage_je_sym,
                                                   misch, bloecke))

        # Spannenreihe - erkennt die Messung eine Ordnung DIESER Groesse?
        gepflanzt = {}
        for spanne in (1.0, 2.0, 4.0):
            h = spanne / 100.0 / 4.0
            wahr = {f: 1.0 / 3.0 + (2 - f) * h for f in range(5)}
            r2 = np.random.default_rng(SAAT + 1)
            kunst = []
            for z in zeilen:
                tage = tage_je_sym.get(z["sym"])
                if not tage or z["i"] >= len(tage):
                    continue
                f = (f5[art].get(tage[z["i"]]) or {}).get(z["sym"])
                if f is None:
                    continue
                kunst.append({"sym": z["sym"], "i": z["i"],
                              "ZIEL 2,0": (2.0 if r2.random() < wahr[f] else -1.0)})
            gepflanzt[spanne] = bewerte(
                "GEPFLANZT %4.1f Pkt" % spanne,
                stufen_je_block(kunst, tage_je_sym, f5[art], bloecke))

        print()
        if echt is None or zufall is None:
            print("  -> nicht einordenbar")
            continue
        # Bei welcher gepflanzten Spanne liegt der echte Wert?
        erreicht = None
        for spanne in sorted(gepflanzt):
            w = gepflanzt[spanne]
            if w is not None and echt < w:
                erreicht = spanne
                break
        if art == "zufall":
            rauschen = max(abs(echt), abs(zufall)) + 0.10
            print("  -> NULLPUNKT gesetzt: alles unter %+.3f ist Rauschen"
                  % rauschen)
            continue
        # ⚠️ BEIDE KONTROLLEN MUESSEN GREIFEN (05.09., zweiter eigener
        # Fehler an dieser Regel).
        #
        # Bei `amihud` in der LAENGS-Form lag die EIGENE Mischung bei
        # +0,620 gegen einen echten Wert von +0,713 - die Kontrolle
        # reproduzierte den Befund fast vollstaendig. Die Regel verglich
        # aber nur gegen den globalen Nullpunkt (+0,267) und schrieb
        # "haelt". Der Grund ist strukturell: Laengs-Fuenftel tragen eine
        # MARKTWEITE Gemeinsamkeit (in einer ruhigen Phase sind viele
        # Symbole gleichzeitig in ihrem eigenen niedrigen Fuenftel), und
        # eine Mischung INNERHALB des Tages laesst die unberuehrt.
        #
        # Wo die eigene Mischung den echten Wert fast erreicht, ist nicht
        # der Befund stark, sondern die Kontrolle untauglich - und dann
        # gilt gar nichts.
        grenze = rauschen if rauschen is not None else zufall + 0.10
        if echt - zufall < 0.15:
            print("  -> ⚠️ KONTROLLE UNTAUGLICH: die eigene Mischung liefert"
                  " %+.3f gegen %+.3f." % (zufall, echt))
            print("     Der Nullpunkt zerstoert die Struktur nicht - es gilt"
                  " kein Befund.")
        elif echt <= grenze:
            print("  -> ⚠️ NICHT trennbar (%+.3f gegen den Nullpunkt %+.3f)"
                  % (echt, grenze))
        elif erreicht is None:
            print("  -> ✔✔ haelt STARK (ueber 4 Punkten gepflanzter Spanne)")
        else:
            print("  -> ✔ haelt, entspricht rund %.1f Punkten stabiler Spanne"
                  % erreicht)

    print()
    print("=" * 92)
    print("⚠️ Ein Kandidat wird nur registriert, wenn BEIDE Kriterien halten.")
    print("   funding traegt schwach und deckt 302 · turnover traegt nicht und deckt 42")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
