# -*- coding: utf-8 -*-
"""Die DEPOT-Simulation - wie weit weichen die Ergebnisse ab?

**27.09.2026**, Nutzerauftrag: *"Optimal waere auch noch eine saubere
Simulation an Echtdaten, wie weit die Ergebnisse abweichen."*

Vorabfestlegung: `Basisinfos/Vorabfestlegung_31_Depotsimulation_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WAS BISHER FEHLT
═══════════════════════════════════════════════════════════════════════

Gemessen sind der Ertrag JE TRADE (+1,2568 gegen +1,2864) und die
Ueberlappung der Auswahl (68,7 / 55,4 Prozent). Was ein DEPOT daraus
macht - mit KAPAZITAETSGRENZE, ueber die Zeit, mit Verlustserien und
Rueckgaengen - ist offen.

⭐ Beantwortet zugleich den offenen Punkt aus 2.633: die Signalmenge
schwankt zwischen 3,2 und 11,7 je Tag, und es gibt heute KEINEN Deckel.

═══════════════════════════════════════════════════════════════════════
 DER ABLAUF
═══════════════════════════════════════════════════════════════════════

Chronologisch ueber alle Stunden. Wer die Schwelle unterschreitet, kommt
auf die Kandidatenliste; bei Ueberhang gewinnen die BESTEN. Ein Symbol
nie zweimal gleichzeitig. Haltedauer H24.

⚠️ KEINE ZUKUNFT: die Kandidatenwahl kennt nur `W` zum Zeitpunkt der
Eroeffnung, nie das Ergebnis.

⚠️ NUR LESEN.  python simuliere_depot.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import (                          # noqa: E402
    trailing_mit_ausloeser, EMA_L, VORLAUF)
from messe_skalenangleich import atr_aus_schluessen             # noqa: E402

HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
SCHWELLE = -1.2881          # 2.632
FAKTOR = 2.0832             # 2.637
HEBEL = 3.0                 # konstant (2.633); reiner Massstab
ANTEIL_D = 16.0 / 44.0      # so viele Symbole haben kein OHLC
ZIEHUNGEN_MISCH = 12
SAAT = 20260927


def simuliere(zeit, sym_id, W, P, kapazitaet):
    """Chronologische Depotsimulation.

    Gibt (Ergebnisliste je Trade, Eroeffnungszeit, Symbol) zurueck.

    ⚠️ Die Kandidatenwahl kennt NUR `W`. Dass `P` im selben Feld liegt,
    ist Buchhaltung - es wird erst NACH der Wahl gelesen."""
    o = np.argsort(zeit, kind="stable")
    zeit, sym_id, W, P = zeit[o], sym_id[o], W[o], P[o]
    frei_ab = {}                       # Symbol -> Stunde, ab der es frei ist
    belegt = []                        # Endzeiten der offenen Positionen
    erg, wann, wer = [], [], []
    i, n = 0, len(zeit)
    while i < n:
        t = zeit[i]
        j = i
        while j < n and zeit[j] == t:
            j += 1
        # Plaetze freigeben
        belegt = [e for e in belegt if e > t]
        platz = kapazitaet - len(belegt)
        if platz > 0:
            kand = [k for k in range(i, j)
                    if W[k] <= SCHWELLE and frei_ab.get(int(sym_id[k]), -1) <= t]
            if kand:
                kand.sort(key=lambda k: W[k])
                for k in kand[:platz]:
                    erg.append(P[k]); wann.append(t); wer.append(int(sym_id[k]))
                    frei_ab[int(sym_id[k])] = t + HZ
                    belegt.append(t + HZ)
        i = j
    return np.array(erg), np.array(wann), np.array(wer)


def einsatz_je_platz(kapazitaet: int) -> float:
    """Das Konto wird gleichmaessig auf die Plaetze verteilt.

    ⚠️ IM PROBELAUF GEFUNDEN: mit `einsatz=1.0` (das ganze Konto je
    Position!) meldete die Simulation Rueckgaenge von -99 Prozent. Das
    ist kein Marktbefund, sondern eine unsinnige Positionsgroesse - bei
    Hebel 3 reicht ein Kursverlust von 33 Prozent fuer den Totalverlust.
    Der Einsatz ist ein MASSSTAB und muss zur Platzzahl passen."""
    return 1.0 / max(1, min(kapazitaet, 20))


def kennzahlen(r, hebel=HEBEL, einsatz=0.1):
    """Geometrisches Wachstum, Verlustserie, groesster Rueckgang."""
    if not len(r):
        return dict(n=0)
    g = np.log(np.maximum(1.0 + einsatz * hebel * r, 1e-9))
    kum = np.cumsum(g)
    spitze = np.maximum.accumulate(kum)
    rueck = float((np.exp(kum - spitze) - 1.0).min())
    serie = best = 0
    for x in r:
        if x <= 0:
            serie += 1; best = max(best, serie)
        else:
            serie = 0
    return dict(n=len(r), q=float((r > 0).mean()),
                je_trade=100 * float(r.mean()),
                wachstum=float(kum[-1]),
                endwert=float(np.exp(kum[-1])),
                serie=best, rueckgang=100 * rueck)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    kap_liste = (2, 3, 5, 10, 999)

    print("=" * 108)
    print("DEPOT-SIMULATION - wie weit weichen die Ergebnisse ab?")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  Schwelle %.4f (2.632) · Hebel konstant %.1fx (2.633) · "
          "Skalenfaktor %.4f (2.637)" % (SCHWELLE, HEBEL, FAKTOR))
    print("  H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    Z, SI, WA, WD, P = [], [], [], [], []
    namen = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        aA = atr_tag_relativ(h, l, cc)
        aD = atr_aus_schluessen(cc)
        e = ema(cc, EMA_L)
        _r, p, _g = trailing_mit_ausloeser(h, l, cc, aA, STOP, AUSL, ABST, HZ)
        gu = (np.isfinite(aA) & (aA > 0) & np.isfinite(aD) & (aD > 0)
              & np.isfinite(e) & np.isfinite(p))
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        idx = len(namen); namen.append(sym)
        Z.append(gi[s2]); SI.append(np.full(len(s2), idx, np.int64))
        WA.append((cc[s2] - e[s2]) / np.maximum(aA[s2] * cc[s2], 1e-12))
        WD.append(((cc[s2] - e[s2]) / np.maximum(aD[s2] * cc[s2], 1e-12))
                  / FAKTOR)
        P.append(p[s2])
    Z = np.concatenate(Z); SI = np.concatenate(SI)
    WA = np.concatenate(WA); WD = np.concatenate(WD); P = np.concatenate(P)
    print("  %d Anker · %d Symbole · %d Tage"
          % (len(Z), len(namen), len(np.unique(Z // 24))), flush=True)
    print()

    # ══ 1. DIE DREI VARIANTEN, je Kapazitaet ═════════════════════════
    rng = np.random.default_rng(SAAT)
    print("=" * 108)
    print("TEIL 1 - DIE VARIANTEN, je Kapazitaet")
    print("  Variante 3 ist der REALE Betrieb: %.0f %% der Symbole ohne "
          "OHLC (16 von 44)" % (100 * ANTEIL_D))
    print()
    print("  %-22s %6s %8s %8s %11s %11s %9s %11s"
          % ("Variante", "Kap.", "Trades", "q", "je Trade %", "Wachstum",
             "Serie", "Rueckgang"))
    erg_je_kap = {}
    for kap in kap_liste:
        # Variante 1: alles A
        r1, _w, _s = simuliere(Z, SI, WA, P, kap)
        k1 = kennzahlen(r1, einsatz=einsatz_je_platz(kap))
        # Variante 2: alles D korrigiert
        r2, _w, _s = simuliere(Z, SI, WD, P, kap)
        k2 = kennzahlen(r2, einsatz=einsatz_je_platz(kap))
        # Variante 3: gemischt, mehrere Ziehungen
        m3 = []
        for _ in range(ZIEHUNGEN_MISCH):
            dsym = set(rng.choice(len(namen),
                                  size=int(round(ANTEIL_D * len(namen))),
                                  replace=False).tolist())
            istD = np.isin(SI, list(dsym))
            Wm = np.where(istD, WD, WA)
            r3, _w, _s = simuliere(Z, SI, Wm, P, kap)
            m3.append(kennzahlen(r3, einsatz=einsatz_je_platz(kap)))
        # Variante 4: Zufall gleicher Groesse
        Wz = rng.permutation(WA)
        r4, _w, _s = simuliere(Z, SI, Wz, P, kap)
        k4 = kennzahlen(r4, einsatz=einsatz_je_platz(kap))
        erg_je_kap[kap] = (k1, k2, m3, k4)
        print("  --- Kapazitaet %s, Einsatz je Position %.3f des Kontos"
              % ("frei" if kap > 100 else str(kap),
                 einsatz_je_platz(kap)))
        for nm, k in (("1  alles OHLC", k1), ("2  alles ohne OHLC", k2)):
            print("  %-22s %6s %8d %7.1f%% %+11.4f %+11.4f %9d %+10.2f%%"
                  % (nm, "frei" if kap > 100 else kap, k["n"], 100 * k["q"],
                     k["je_trade"], k["wachstum"], k["serie"],
                     k["rueckgang"]))
        mw = lambda f: float(np.mean([x[f] for x in m3]))          # noqa: E731
        sd = lambda f: float(np.std([x[f] for x in m3]))           # noqa: E731
        print("  %-22s %6s %8d %7.1f%% %+11.4f %+11.4f %9d %+10.2f%%"
              % ("3  gemischt (real)", "frei" if kap > 100 else kap,
                 int(mw("n")), 100 * mw("q"), mw("je_trade"), mw("wachstum"),
                 int(mw("serie")), mw("rueckgang")))
        print("  %-22s %6s %8s %7s %11s %11s"
              % ("   Streuung ueber %d" % ZIEHUNGEN_MISCH, "", "",
                 "", "%.4f" % sd("je_trade"), "%.4f" % sd("wachstum")))
        print("  %-22s %6s %8d %7.1f%% %+11.4f %+11.4f %9d %+10.2f%%"
              % ("4  Zufall (Kontrolle)", "frei" if kap > 100 else kap,
                 k4["n"], 100 * k4["q"], k4["je_trade"], k4["wachstum"],
                 k4["serie"], k4["rueckgang"]))
        print()

    # ══ 2. DIE PRUEFUNGEN ════════════════════════════════════════════
    print("=" * 108)
    print("TEIL 2 - DIE PRUEFUNGEN")
    print()
    k1f = erg_je_kap[999][0]
    print("  SELBSTPROBE (Falle 3): bei freier Kapazitaet muss der mittlere")
    print("     Trade-Ertrag gegen den bekannten Wert +1,2568 laufen.")
    print("     gemessen: %+.4f  ->  %s"
          % (k1f["je_trade"],
             "✔ stimmt" if abs(k1f["je_trade"] - 1.2568) < 0.15
             else "⛔ die Buchfuehrung weicht ab"))
    print()
    k4f = erg_je_kap[999][3]
    print("  ZUFALLSKONTROLLE (Falle 4): sie muss deutlich schlechter sein.")
    print("     A %+.4f gegen Zufall %+.4f  ->  %s"
          % (k1f["je_trade"], k4f["je_trade"],
             "✔ klar getrennt" if k1f["je_trade"] > k4f["je_trade"] + 0.3
             else "⛔ zu nah - gemessen wird die Kapazitaetsregel"))
    print()
    print("  ⭐ DER ABSTAND, um den es geht (Variante 1 gegen 3):")
    print("  %-10s %14s %14s %12s %12s"
          % ("Kapazitaet", "A je Trade", "gemischt", "Abstand", "relativ"))
    for kap in kap_liste:
        k1, _k2, m3, _k4 = erg_je_kap[kap]
        mg = float(np.mean([x["je_trade"] for x in m3]))
        d = mg - k1["je_trade"]
        print("  %-10s %+14.4f %+14.4f %+12.4f %11.1f %%"
              % ("frei" if kap > 100 else kap, k1["je_trade"], mg, d,
                 100 * d / max(abs(k1["je_trade"]), 1e-9)))

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet "
          "(Regel 2).")
    print("     ⚠️ Fuer ein DEPOTergebnis ist das eine echte "
          "Einschraenkung.")
    print("  ⚠️ Welche Symbole ohne OHLC laufen, ist GELOST und ueber %d"
          % ZIEHUNGEN_MISCH)
    print("     Ziehungen gemittelt - die echten 16 haben keine "
          "Stundendaten.")
    print("  ⚠️ Der Einsatz je Position ist ein MASSSTAB: er trifft alle")
    print("     Varianten gleich und faellt im Vergleich heraus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
