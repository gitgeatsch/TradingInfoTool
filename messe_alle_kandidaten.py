# -*- coding: utf-8 -*-
"""DER GESAMTSTAND — alle Kandidaten, EIN Standard, EINE Basis (08.09.2026)

## Warum es das gibt

Nutzervorgabe 08.09., woertlich: *„beachte dass wir schon mehrfach
Beiträge unterschiedlich als gefallen und wieder aufgenommen haben. bitte
den Messtandard sauber umsetzen für alle."*

Er hat recht. `turnover` ist an einem Tag gefallen und wieder
aufgenommen worden; `schnitt` dreimal. Die Ursache war nie der Kandidat,
sondern dass jede Messung eine andere Anlage benutzte: andere Menge,
anderer Horizont, andere Zielgroesse, andere Basis.

> **Diese Datei misst ALLE Kandidaten in EINEM Lauf, auf EINER Basis,
> nach EINEM Kriterium.** Was hier steht, ist der Stand - alles andere
> ist Geschichte.

## ⚠️⚠️ DIE VORABFESTLEGUNG — sie stand bisher nirgends klar

`messnorm_auswahl` bindet die Frageart an die Menge:

    frei             -> frageart "markt"    (P6: breiter als das Portfolio)
    5/10/20/50 %     -> frageart "beitrag"  (F-212: dort wirken sie)

> **Fuer ein BEITRAGSURTEIL zaehlt `frei` deshalb NICHT.** Ein Kandidat,
> der nur auf der freien Menge traegt, hat eine MARKT-Aussage gemacht -
> keine Beitragsaussage.

⚠️ Das aendert die Lage fuer `turnover`: er traegt auf `frei` (+0,0639),
auf den selektierten Mengen aber nicht trennbar. Nach dieser Festlegung
ist das **kein tragender Beitrag**, und das ist keine neue Messung,
sondern eine saubere Anwendung der bestehenden Regel.

## Das Kriterium, vorab und fuer alle gleich

⚠️⚠️ **DIE ERSTE FASSUNG WAR UNERFUELLBAR** (Nutzerhinweis 08.09.: *„es
macht auch keinen Sinn, nicht realistische bzw. erreichbare Regeln
aufzustellen"*). Sie verlangte "TRAEGT auf ALLEN zulaessigen Mengen" -
nach den Zahlen vom 08.09. haette das KEIN Kandidat bestanden. Ein
Kriterium, das jeden ausschliesst, ist keins.

**Der Denkfehler:** die Norm kennt VIER Urteile, und zwei davon sind
ausdruecklich Aussagen ueber die MESSUNG, nicht ueber die Welt:

    TRAEGT              Aussage ueber die Welt
    TRAEGT NICHT BIS X  Aussage ueber die Welt
    NICHT TRENNBAR      ueber die MESSUNG - zu unpraezise
    KEIN BEFUND         ueber die MESSUNG - "wird nicht als Nullbefund
                        ausgegeben" (messnorm.Befund.urteil)

Ich habe die letzten beiden als Gegenstimme gezaehlt. Bei 5 % gibt es
wenige Anker, breite Baender und fast immer "kein Befund" - **das ist ein
Mangel der MENGE, nicht des Kandidaten.**

### Das korrigierte Kriterium

    Aussagen = Mengen mit Urteil TRAEGT oder TRAEGT NICHT BIS X
               ("nicht trennbar" und "kein Befund" sind ENTHALTUNGEN)

    TRAEGT              mindestens eine Aussage, und ALLE lauten TRAEGT
    WIDERSPRUCH         die Aussagen widersprechen sich -> nicht robust
    TRAEGT NICHT        alle Aussagen lauten "traegt nicht bis X"
    NICHT ENTSCHEIDBAR  keine Menge liefert ueberhaupt eine Aussage

⚠️ Streng bleibt es trotzdem: ein Kandidat, dessen AUSSAGEN sich
widersprechen, ist kein Beitrag. Genau daran ist `schnitt` dreimal
gescheitert - jedesmal unbemerkt, weil nur EINE Menge gemessen wurde.

## Die Kontrolle

`zufall` laeuft mit und muss "TRAEGT NICHT" oder "NICHT MESSBAR"
ergeben. Alles andere macht den Lauf wertlos.

    python messe_alle_kandidaten.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

HORIZONT = 20
# ⚠️ `frei` ist die MARKT-Menge und zaehlt NICHT fuer das Beitragsurteil.
SELEKTIERT = ("5%", "10%", "20%", "50%")
# Alle Kandidaten, die `messe_kandidaten_als_regel.baue` erzeugen kann.
KANDIDATEN = ("funding", "turnover", "oi_aenderung", "oi_je_umsatz",
              "long_bias", "top_bias", "taker_bias", "vola", "schnitt",
              "schnitt50", "amihud", "rsi", "momentum", "momentum_kurz",
              "funding_extrem", "zufall")


def zusatzquellen() -> dict:
    z = {"funding": F.lade_funding(),
         "funding_extrem": F.lade_funding(),
         "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    try:
        tm = K.lade_terminmarkt()
        z["oi_aenderung"] = tm["oi_aenderung"]
        z["oi_je_umsatz"] = tm["oi_wert"]
        z["long_bias"] = tm["long_bias"]
        z["top_bias"] = tm["top_bias"]
        z["taker_bias"] = tm["taker_bias"]
    except Exception as exc:                                 # noqa: BLE001
        print("  ⚠️ Terminmarkt nicht ladbar: %s" % str(exc)[:60])
    return z


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()
    print("=" * 104)
    print("DER GESAMTSTAND — alle Kandidaten, ein Standard")
    print("=" * 104)
    print("  Basis: %d Krypto-Reihen · H%d · Zielgroesse bewegung_r"
          % (len(reihen), HORIZONT))
    print("  ⚠️ `frei` zaehlt NICHT - sie ist die MARKT-Menge (P6/F-212).")
    print()
    print("  %-15s %-6s %10s %22s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Band", "Urteil"))

    erg, zul = {}, {}
    for a in KANDIDATEN:
        try:
            je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-15s -> %s" % (a, str(exc)[:60]))
            continue
        if not je:
            print("  %-15s -> leere Welt" % a)
            continue
        alle = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        # ⚠️ NUR die selektierten - `frei` faellt hier heraus.
        mengen = [m for m in alle if m in SELEKTIERT]
        zul[a] = mengen
        if not mengen:
            print("  %-15s %-6s   ⚠️ keine zulaessige SELEKTIERTE Menge "
                  "(zulaessig waere nur: %s)"
                  % (a, "-", ", ".join(alle) or "keine"))
            erg[a] = []
            continue
        for m in mengen:
            rng = np.random.default_rng(20260908)
            try:
                b = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                      rng=rng, horizont=HORIZONT,
                                      hypothese="Gesamtstand 08.09.",
                                      verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("  %-15s %-6s -> %s" % (a, m, str(exc)[:44]))
                continue
            erg.setdefault(a, []).append((m, b))
            print("  %-15s %-6s %+10.4f [%+.4f .. %+.4f]  %s"
                  % (a, m, b.wirkung, b.unten, b.oben,
                     b.urteil.split(" (")[0].split(" - ")[0][:30]),
                  flush=True)
        print()

    # ---- Das Gesamturteil, nach dem vorab gesetzten Kriterium ----------
    print("=" * 104)
    print("DAS GESAMTURTEIL — Kriterium stand VOR dem Lauf fest")
    print("=" * 104)
    print("  %-15s %-22s %8s   %s"
          % ("Kandidat", "zulaessige Mengen", "traegt", "URTEIL"))
    urteile = {}
    for a in KANDIDATEN:
        if a not in erg:
            continue
        paare = erg[a]
        # ⚠️ NUR MENGEN, DIE EINE AUSSAGE LIEFERN. "nicht trennbar" und
        # "kein Befund" sind laut `messnorm` Aussagen ueber die MESSUNG -
        # sie zaehlen als Enthaltung, nicht als Gegenstimme.
        aussagen = []
        for m, b in paare:
            u = b.urteil.upper()
            if b.traegt:
                aussagen.append((m, True))
            elif u.startswith("TRAEGT NICHT BIS"):
                aussagen.append((m, False))
        ja = [m for m, w in aussagen if w]
        nein = [m for m, w in aussagen if not w]
        if not aussagen:
            urteile[a] = "NICHT ENTSCHEIDBAR"
        elif ja and nein:
            urteile[a] = ("WIDERSPRUCH (traegt auf %s, nicht auf %s)"
                          % (", ".join(ja), ", ".join(nein)))
        elif ja:
            urteile[a] = "TRAEGT"
        else:
            urteile[a] = "TRAEGT NICHT"
        print("  %-15s %-22s %8s   %s"
              % (a, ", ".join(zul.get(a) or []) or "—",
                 "%d Aussagen" % len(aussagen), urteile[a]))

    print()
    z = urteile.get("zufall", "?")
    if z.startswith(("TRAEGT NICHT", "NICHT ENTSCHEIDBAR")):
        print("  ✔ Kontrolle `zufall`: %s - der Lauf ist gueltig." % z)
    else:
        print("  ⚠️⚠️ Kontrolle `zufall`: %s - DER LAUF IST WERTLOS." % z)
        return 1
    traeger = [a for a, u in urteile.items()
               if u == "TRAEGT" and a != "zufall"]
    print()
    print("  TRAGENDE BEITRAEGE nach diesem Standard: %s"
          % (", ".join(traeger) if traeger else "⚠️ KEINER"))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
