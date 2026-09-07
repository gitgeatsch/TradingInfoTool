# -*- coding: utf-8 -*-
"""ÄNDERT EINE ERWEITERTE MESSBASIS DIE URTEILE? (07.09.2026)

## Warum es dieses Werkzeug gibt

Am 07.09. wurde festgestellt, dass **sieben Kryptoreihen in der Messbasis
fehlen** — `DASH`, `STX`, `DIA`, `MDT`, `T`, `BOND`, `C`. Sie waren bei
der Kollisionsbereinigung (F-198) herausgefallen, weil dieselben Kürzel
auch US-Aktien und ETF sind. F-198 führt das ausdrücklich als **offenen
Punkt**:

> *„falls unter den sieben bereinigten Symbolen echte Altcoin-Ticker
> waren (BOND, DASH, MDT, STX, T sind alle plausible Kryptonamen), fehlen
> sie jetzt möglicherweise in Kryptos eigener Messbasis. **Das ist ein
> offener Punkt, keine Annahme.**"*

Gemessen: **sie fehlen.** Alle sieben sind bei Binance als USDT-Spotpaare
mit langer Historie verfügbar (DASH 2.721 Kerzen, STX 2.510, DIA 2.195,
MDT 2.149, T 1.656, BOND 1.114).

## ⚠️⚠️ Die Frage, die dieses Werkzeug beantwortet

Die Messbasis waechst um **1,4 %**. Damit verschiebt sich **jeder**
Querschnittsrang und damit jeder gemessene Wert — auch die
Reproduktionsanker, die den Audit vom 07.09. getragen haben.

> **Ändert sich ein URTEIL, oder nur eine Nachkommastelle?**

Das ist nicht zu schätzen, sondern zu messen: dieselben Messungen VORHER
und NACHHER, und verglichen wird das **Urteil**, nicht die Zahl.

    python pruefe_messbasis_wechsel.py --vorher
    #   ... laden ...
    python pruefe_messbasis_wechsel.py --nachher

⚠️ Die Werte werden in `Basisinfos/messbasis_anker.json` abgelegt — sie
sind der Bezug, gegen den die naechste Aenderung geprueft wird.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import pruefe_auswahl                  # noqa: E402

DATEI = "Basisinfos/messbasis_anker.json"

# ⚠️ DIE ANKER SIND DIE, DIE HEUTE ETWAS TRAGEN - nicht eine beliebige
# Auswahl. Jeder von ihnen hat am 06./07.09. ein Urteil begruendet.
ANKER = (
    # (Kandidat, Horizont, Menge, was er begruendet)
    ("funding", 20, "frei", "F-212 · Kontrollanker des Audits"),
    ("funding", 20, "5%", "F-212 · Kontrollanker des Audits"),
    ("turnover", 20, "frei", "F-212 · die registrierte Tabelle"),
    ("schnitt", 20, "20%", "N-59 · der Kandidat"),
    ("schnitt", 5, "20%", "N-60 · derselbe bei H5"),
    ("zufall", 20, "frei", "darf NIE tragen"),
    ("zufall", 20, "5%", "darf NIE tragen"),
)


def miss():
    """Alle Anker messen und als Liste von dicts zurueckgeben."""
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    lage = N.Lage(instrument="spot", strategie="einstieg")
    aus = []
    print("  Messbasis: %d Krypto-Symbole" % len(reihen))
    for art, hz, menge, wofuer in ANKER:
        je = K.baue(reihen, art, zus.get(art), horizont=hz)
        rng = np.random.default_rng(20260907)
        try:
            b = pruefe_auswahl(art, je, mom, lage=lage, menge=menge, rng=rng,
                               horizont=hz, hypothese="Messbasis-Anker",
                               verwendung="Beitrag")
            z = {"art": art, "hz": hz, "menge": menge, "wofuer": wofuer,
                 "wirkung": round(b.wirkung, 5), "unten": round(b.unten, 5),
                 "oben": round(b.oben, 5), "traegt": bool(b.traegt),
                 "urteil": b.urteil.split(" - ")[0].split(" (")[0],
                 "symbole": len(reihen)}
        except Exception as exc:                             # noqa: BLE001
            z = {"art": art, "hz": hz, "menge": menge, "wofuer": wofuer,
                 "fehler": str(exc)[:70], "symbole": len(reihen)}
        aus.append(z)
        print("     %-9s H%-3d %-5s %s"
              % (art, hz, menge,
                 ("%+9.5f R  %s" % (z["wirkung"], z["urteil"]))
                 if "wirkung" in z else "-> " + z["fehler"]), flush=True)
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vorher", action="store_true")
    ap.add_argument("--nachher", action="store_true")
    a = ap.parse_args()
    if not (a.vorher or a.nachher):
        ap.error("--vorher oder --nachher angeben")

    print("=" * 92)
    print("MESSBASIS-ANKER — %s" % ("VORHER" if a.vorher else "NACHHER"))
    print("=" * 92)
    jetzt = miss()

    if a.vorher:
        os.makedirs(os.path.dirname(DATEI), exist_ok=True)
        io.open(DATEI, "w", encoding="utf-8").write(
            json.dumps(jetzt, indent=2, ensure_ascii=False))
        print()
        print("  ✔ %d Anker festgehalten in %s" % (len(jetzt), DATEI))
        print("  ⚠️ JETZT laden, dann mit --nachher vergleichen.")
        return 0

    if not os.path.exists(DATEI):
        print("  ⚠️ %s fehlt - erst --vorher laufen lassen." % DATEI)
        return 1
    vorher = json.loads(io.open(DATEI, encoding="utf-8").read())

    print()
    print("=" * 92)
    print("DER VERGLEICH — aendert sich ein URTEIL?")
    print("=" * 92)
    print("  %-9s %-4s %-5s %10s %10s %8s   %s"
          % ("Anker", "H", "Menge", "vorher", "nachher", "Diff", "Urteil"))
    urteilswechsel, groesste = [], 0.0
    for v, n in zip(vorher, jetzt):
        if "wirkung" not in v or "wirkung" not in n:
            print("  %-9s %-4d %-5s   nicht vergleichbar"
                  % (v["art"], v["hz"], v["menge"]))
            continue
        d = n["wirkung"] - v["wirkung"]
        groesste = max(groesste, abs(d))
        gleich = (v["traegt"] == n["traegt"]) and (v["urteil"] == n["urteil"])
        if not gleich:
            urteilswechsel.append((v, n))
        print("  %-9s %-4d %-5s %+10.5f %+10.5f %+8.5f   %s"
              % (v["art"], v["hz"], v["menge"], v["wirkung"], n["wirkung"],
                 d, "✔ unveraendert" if gleich
                 else "⚠️⚠️ %s -> %s" % (v["urteil"], n["urteil"])))
    print()
    print("  Symbole: %d -> %d" % (vorher[0]["symbole"], jetzt[0]["symbole"]))
    print("  groesste Verschiebung: %+.5f R" % groesste)
    print()
    if not urteilswechsel:
        print("  ✔✔ KEIN URTEIL AENDERT SICH.")
        print("     Die bisherigen Befunde bleiben gueltig - nur ihre")
        print("     Punktschaetzer verschieben sich minimal. Die NEUEN")
        print("     Werte sind ab jetzt der Bezug.")
    else:
        print("  ⚠️⚠️ %d URTEIL(E) AENDERN SICH:" % len(urteilswechsel))
        for v, n in urteilswechsel:
            print("     %-9s H%-3d %-5s   %s -> %s   (%s)"
                  % (v["art"], v["hz"], v["menge"], v["urteil"], n["urteil"],
                     v["wofuer"]))
        print()
        print("     ⚠️ Diese Befunde sind auf der NEUEN Basis neu zu fassen.")
        print("        Nach R-R11 gilt: was sich beim Basiswechsel dreht,")
        print("        war nie robust - der Wechsel hat es nur gezeigt.")
    io.open(DATEI, "w", encoding="utf-8").write(
        json.dumps(jetzt, indent=2, ensure_ascii=False))
    print()
    print("  ✔ %s auf den neuen Stand gesetzt." % DATEI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
