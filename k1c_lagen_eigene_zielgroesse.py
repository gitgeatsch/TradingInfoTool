# -*- coding: utf-8 -*-
"""K-1c — Gilt der Beleg auch für die AKKUMULATION? (09.09.2026)

## Die Frage

Alle Beitraege sind auf `spot x einstieg` mit `bewegung_r` belegt. Die
Kette kennt aber mehrere Lagen, und **jede hat ihr eigenes Erfolgsmass**:

    spot x einstieg       bewegung_r     barrierenfrei, H20
    spot x akkumulation   VERBILLIGUNG   Perzentilrang, H90
    hebel x einstieg      barriere       Ziel vor Stop

⚠️⚠️ **Die Lage war bis zum 09.09. nur ein Etikett.** `pruefe_auswahl`
hatte `zielgroesse="bewegung_r"` fest verdrahtet und reichte die `lage`
nur an den Befund durch - eine Messung mit `lage=Lage("hebel",...)`
haette Spot-Bewegung gemessen und "Hebel" daraufgeschrieben. Seit dem
09.09. prueft `ZIELGROESSE_JE_LAGE` das und weist es ab.

## Die Zielgroesse der Akkumulation

`handelsauftrag.py` gibt der Akkumulation ausdruecklich die VERBILLIGUNG:

    V(t,H) = Mittel(Kurs[t+1 .. t+H]) / Kurs(t) - 1

Gewertet wird ihr **Perzentilrang INNERHALB der eigenen Reihe**. Damit ist
die Basisrate exakt 0,500 per Konstruktion - **der Drift kann nicht als
Signal durchgehen**. Das ist der ganze Trick dieser Groesse, und er ist
der Grund, warum sie nicht durch `bewegung_r` ersetzbar ist.

⚠️ Belegt am 28.08. auf 505 lueckenlosen Reihen ueber neun Jahre, sieben
Kontrollen bestanden. ⚠️⚠️ Und mit einer Einschraenkung, die bleibt: fuer
**BTC, ETH und SOL traegt der Befund NICHT** (Rang -0,025 bis -0,031,
p 0,72 bis 0,86) - und genau BTC und ETH stehen in
`asset_dca_settings`.

## Was hier gemessen wird

Dieselben Kandidaten wie sonst, aber gegen die VERBILLIGUNG statt gegen
`bewegung_r`, auf H90 statt H20, unter `Lage("spot", "akkumulation")`.

    Kandidaten   funding · turnover · oi_aenderung · schnitt · zufall
    Menge        `frei` - die Registrierungsbasis aller drei (2.227)
    Messmenge    messmenge.V1, eingefroren
    Kontrolle    `zufall` an derselben Stelle

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

Die Verbilligung ist eine **Reihen-INTERNE** Groesse (Perzentilrang in
der eigenen Reihe), die Beitraege sind **Querschnitts**raenge. Beides
misst verschiedene Achsen.

    Erwartung   sie tragen SCHWAECHER oder gar nicht - ein Querschnitts-
                rang sagt wenig darueber, ob DIESER Wert gerade guenstig
                gegen SEINE eigene Geschichte steht
    Gegenthese  sie tragen auch hier - dann waeren die Beitraege
                lagenuebergreifend, was ihren Wert deutlich erhoeht

⚠️ **Ein Nullbefund waere hier die Regel, kein Ausreisser** - und er
waere ein echtes Ergebnis: dann gilt die Bewertung fuer die
Akkumulation NICHT, und `NACHKAUFEN` (51,7 Mails am Tag) stuende ohne
Beleg da.

    python k1c_lagen_eigene_zielgroesse.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import zusatzquellen              # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

H_AKKU = 90
KANDIDATEN = ("funding", "turnover", "oi_aenderung", "schnitt", "zufall")


def verbilligung_je_tag(je_tag: dict, reihen: dict, H: int) -> dict:
    """Ersetzt `in_r` durch den PERZENTILRANG der Verbilligung.

    ⚠️⚠️ Der Rang wird INNERHALB DER EIGENEN REIHE gebildet, nicht im
    Querschnitt. Genau daher kommt die Basisrate 0,500 - im Querschnitt
    gerangt waere es eine andere Groesse, und der Drift kaeme durch die
    Hintertuer wieder herein.

    ⚠️ Die Kennzahl (der Kandidatenwert) bleibt unangetastet - nur die
    ZIELGROESSE wechselt.
    """
    # Je Symbol: V(t) fuer alle Tage, daraus der Perzentilrang.
    rang_je_sym: dict = {}
    for sym, reihe in reihen.items():
        tage = [x[0] for x in reihe]
        c = np.array([x[1] for x in reihe], float)
        if len(c) < H + 2:
            continue
        v = np.full(len(c), np.nan)
        for i in range(len(c) - H):
            if c[i] > 0:
                v[i] = float(np.mean(c[i + 1:i + 1 + H]) / c[i] - 1.0)
        gut = np.isfinite(v)
        if gut.sum() < 60:
            continue
        # Perzentilrang in der eigenen Reihe.
        r = np.full(len(c), np.nan)
        w = v[gut]
        ordnung = np.argsort(np.argsort(w))
        r[gut] = ordnung / max(len(w) - 1, 1)
        rang_je_sym[sym] = dict(zip(tage, r))

    neu = {}
    for tag, zeilen in je_tag.items():
        z = []
        for x in zeilen:
            rr = (rang_je_sym.get(x["sym"]) or {}).get(tag)
            if rr is None or not np.isfinite(rr):
                continue
            z.append({"sym": x["sym"], "kennzahl": x["kennzahl"],
                      "in_r": float(rr)})
        if len(z) >= 12:
            neu[tag] = z
    return neu


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="akkumulation")

    print("=" * 108)
    print("K-1c — gilt der Beleg auch fuer die AKKUMULATION?")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print("  %s" % messmenge.zeile())
    print("  Lage: %s · Zielgroesse: %s · H%d"
          % (lage, N.ZIELGROESSE_JE_LAGE[("spot", "akkumulation")], H_AKKU))
    print("  ⚠️ Perzentilrang der Verbilligung INNERHALB der eigenen Reihe -")
    print("     Basisrate exakt 0,500, der Drift kann nicht durchgehen.")
    print()
    print("  %-14s %9s %20s %9s %8s %7s  %s"
          % ("Kandidat", "Wirkung", "Band", "Bezug", "Tage", "Bloecke",
             "Urteil"))

    erg = {}
    for kand in KANDIDATEN:
        try:
            je0 = K.baue(reihen, kand, zus.get(kand), horizont=H_AKKU)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        je = verbilligung_je_tag(je0, reihen, H_AKKU)
        if not je:
            print("  %-14s -> leere Welt nach der Umrechnung" % kand)
            continue
        try:
            b = MA.pruefe_auswahl(
                kand, je, mom, lage=lage, menge="frei",
                rng=np.random.default_rng(20260909), horizont=H_AKKU,
                hypothese="K-1c Akkumulation", verwendung="Beitrag",
                zielgroesse="verbilligung")
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:70]))
            continue
        erg[kand] = b
        print("  %-14s %+9.4f [%+.4f..%+.4f] %+9.4f %8d %7d  %s"
              % (kand, b.wirkung, b.unten, b.oben, b.bezugswert,
                 b.n_tage, b.n_bloecke, kurz(b.urteil)), flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 108)
    print("GILT DIE BEWERTUNG FUER DIE AKKUMULATION?")
    print("=" * 108)
    zf = erg.get("zufall")
    if zf is not None:
        print("  Kontrolle `zufall`: %+.4f · %s"
              % (zf.wirkung, "⚠️ TRAEGT" if zf.traegt else "traegt nicht"))
    # ⚠️⚠️ NICHT `b.traegt` LESEN, SONDERN DAS URTEIL (korrigiert 09.09.).
    #
    # `traegt` prueft nur "Band ueber dem Bezugspunkt" - es weiss NICHTS
    # von der Blockzahl. Bei zu wenigen Bloecken deckt das Band nicht, und
    # `messnorm.urteil` sagt deshalb KEIN BEFUND. Die erste Fassung dieses
    # Skripts las `traegt` und meldete drei Traeger, waehrend ALLE FUENF
    # "KEIN BEFUND" lauteten. Genau dieselbe Verwechslung wie in
    # `messnorm.urteil` selbst (Fehler 4 vom 08.09.) - diesmal an der Norm
    # vorbei, weil das Skript die Eigenschaft direkt gelesen hat.
    kein_befund = [k for k, b in erg.items()
                   if b.urteil.upper().startswith("KEIN BEFUND")]
    traeger = [k for k, b in erg.items()
               if k != "zufall" and b.traegt
               and not b.urteil.upper().startswith("KEIN BEFUND")]
    if kein_befund:
        print("  ⚠️⚠️ KEIN BEFUND bei %d von %d Kandidaten: %s"
              % (len(kein_befund), len(erg), ", ".join(kein_befund)))
        knapp = min((b.n_bloecke for b in erg.values()), default=0)
        gross = max((b.n_bloecke for b in erg.values()), default=0)
        print("     Bloecke: %d bis %d - gefordert sind 20." % (knapp, gross))
        print("  ⚠️ DIE URSACHE IST STRUKTURELL: bei H%d betraegt die "
              "Blocklaenge 3 x %d = %d Tage." % (H_AKKU, H_AKKU, 3 * H_AKKU))
        print("     Fuer 20 Bloecke braeuchte es %d Handelstage - rund %d "
              "Jahre. Vorhanden sind rund 2.900."
              % (20 * 3 * H_AKKU, 20 * 3 * H_AKKU // 365 + 8))
        print("     ⚠️⚠️ Die Akkumulationslage ist mit dieser Blockregel "
              "NICHT messbar -")
        print("        und das gilt fuer die Kontrolle `zufall` genauso.")
        print()
    print()
    if kein_befund and len(kein_befund) == len(erg):
        print("  ⚠️⚠️⚠️ DIE MESSUNG ENTSCHEIDET NICHTS. Weder fuer noch "
              "gegen die Beitraege -")
        print("     die Anlage kann auf diesem Horizont nicht urteilen. "
              "Ein 'traegt' hier")
        print("     abzulesen waere derselbe Fehler wie Fehler 4 vom "
              "08.09.")
    elif traeger:
        print("  ✔ Tragen auch unter der Verbilligung: %s"
              % ", ".join(traeger))
        print("     Damit waeren die Beitraege LAGENUEBERGREIFEND - das "
              "erhoeht ihren Wert erheblich.")
    else:
        print("  ⚠️⚠️ KEIN Beitrag traegt unter der Verbilligung.")
        print("     Dann gilt die Bewertung fuer die AKKUMULATION nicht - "
              "und `NACHKAUFEN`")
        print("     (51,7 Mails am Tag) stuende ohne Beleg da.")
        print("  ⚠️ Das war die VORHERGESAGTE Erwartung: ein "
              "Querschnittsrang sagt wenig")
        print("     darueber, ob DIESER Wert gegen SEINE eigene Geschichte "
              "guenstig steht.")
    print()
    print("  ⚠️ Und die Einschraenkung von 2.157 bleibt: fuer BTC, ETH und "
          "SOL traegt")
    print("     das Akkumulationsmass selbst NICHT - und genau BTC und ETH "
          "stehen in `asset_dca_settings`.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
