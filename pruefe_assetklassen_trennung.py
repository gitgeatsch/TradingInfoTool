# -*- coding: utf-8 -*-
"""ÄNDERT DER ASSETKLASSEN-FILTER ETWAS? — der Beweis (07.09.2026)

## Der Anlass

`lade_reihen_aus_db` gruppierte nach `(symbol, currency)` und las die
Spalte `assetklasse` **nicht** — obwohl F-198 sie am 03.09. eigens
eingeführt hat, samt Primary Key `(symbol, assetklasse, currency, date)`.

> **Heute folgenlos**, weil F-198 die sieben kollidierten Symbole (`C`,
> `DASH`, `STX`, `T`, `BOND`, `DIA`, `MDT`) bereinigt hat. Gemessen am
> 07.09.: **null** Symbol/Währung-Paare mit mehreren Assetklassen.
>
> ⚠️ **Aber sobald die fehlenden Kryptoreihen nachgeladen werden**, hätte
> `DASH` Aktien- UND Kryptokerzen unter derselben Währung. Sie fielen in
> DIESELBE Liste — zwei Instrumente ineinander verwoben.

## Was dieses Werkzeug beweist

Der Filter ist eingebaut. **Die Frage ist, ob er HEUTE etwas ändert.**
Ändert er etwas, hätte er einen bestehenden Zustand verschoben — und dann
wäre jeder Befund neu zu prüfen. Ändert er nichts, ist er reine Vorsorge.

    Für JEDE Assetklasse:  `_reihen_roh` mit und ohne Filter
    Verglichen wird:       Symbolmenge, Reihenlängen, JEDER Kurswert

⚠️ Nicht „ungefähr gleich" — **bitgleich**. Alles andere wäre eine
Verhaltensänderung, die begründet gehört.

    python pruefe_assetklassen_trennung.py
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backtest_llm1_historisch import lade_reihen_aus_db      # noqa: E402
# ⚠️ DIE ECHTE FUNKTION, keine Kopie (stehende Vorgabe). Nur die ALTE
# Fassung muss nachgebildet werden - ihren Code gibt es nicht mehr.
from simuliere_bremse import _reihen_roh, klassen_aus_db     # noqa: E402

DB = "data/messdaten.db"
KLASSEN = ("krypto", "aktien", "themen_etf", "rohstoffe")


def alt_reihen_roh(db, klasse, klassen):
    """Die Fassung VOR dem 07.09. — ohne Filter in der Abfrage.

    ⚠️ Das IST eine Kopie, und sie muss es sein: den alten Code gibt es
    nicht mehr. Sie ist auf vier Zeilen beschraenkt und steht hier, damit
    der Vergleich ueberhaupt moeglich ist. Die NEUE Seite ruft die echte
    Funktion.
    """
    kl = klassen
    aus = {}
    for sym, kerzen in lade_reihen_aus_db(db).items():
        if sym.startswith("_") or kl.get(sym) != klasse or len(kerzen) < 400:
            continue
        aus[sym] = [(k.date, k.close, k.high, k.low) for k in kerzen]
    return aus


def neu_reihen_roh(db, klasse, klassen):
    """⚠️ DIE ECHTE `_reihen_roh` — keine Nachbildung.

    Sie gibt Arrays zurueck; fuer den Vergleich werden Schluss, Hoch und
    Tief in dieselbe Form gebracht wie die Altfassung.
    """
    roh = _reihen_roh(db, klasse, klassen)
    aus = {}
    for sym, (c, h, l, v, a, off, d) in roh.items():
        aus[sym] = [(d[i], float(c[i]), float(h[i]), float(l[i]))
                    for i in range(len(c))]
    return aus


def main() -> int:
    print("=" * 92)
    print("ÄNDERT DER ASSETKLASSEN-FILTER ETWAS? — bitgleich oder nicht")
    print("=" * 92)
    kl = klassen_aus_db(DB)
    if kl is None:
        print("  ⚠️ %s hat keine Tabelle `messreihen`." % DB)
        return 1
    print("  %s · %d Symbole in `messreihen`" % (DB, len(kl)))
    print()
    print("  %-12s %8s %8s %10s   %s"
          % ("Klasse", "alt", "neu", "Kurswerte", "Urteil"))
    alles_gleich = True
    for klasse in KLASSEN:
        a = alt_reihen_roh(DB, klasse, kl)
        n = neu_reihen_roh(DB, klasse, kl)
        gleiche_menge = set(a) == set(n)
        werte = 0
        abweich = []
        for sym in sorted(set(a) & set(n)):
            werte += len(a[sym])
            if a[sym] != n[sym]:
                abweich.append(sym)
        ok = gleiche_menge and not abweich
        alles_gleich &= ok
        print("  %-12s %8d %8d %10d   %s"
              % (klasse, len(a), len(n), werte,
                 "✔ BITGLEICH" if ok else
                 "⚠️⚠️ ABWEICHUNG: %s%s"
                 % ("Symbolmenge " if not gleiche_menge else "",
                    ", ".join(abweich[:4]))))
        if not gleiche_menge:
            nur_a = sorted(set(a) - set(n))
            nur_n = sorted(set(n) - set(a))
            if nur_a:
                print("       nur ALT: %s" % ", ".join(nur_a[:8]))
            if nur_n:
                print("       nur NEU: %s" % ", ".join(nur_n[:8]))

    print()
    print("=" * 92)
    if alles_gleich:
        print("  ✔✔ DER FILTER AENDERT HEUTE NICHTS - in keiner Klasse, in")
        print("     keinem Kurswert. Er ist reine Vorsorge: erst wenn ein")
        print("     Symbol in ZWEI Klassen Kerzen hat, greift er.")
        print()
        print("  ⚠️ Damit ist KEIN bestehender Befund betroffen. Wer das")
        print("     Gegenteil behauptet, muss diese Pruefung widerlegen.")
    else:
        print("  ⚠️⚠️ DER FILTER AENDERT ETWAS. Dann hat er einen")
        print("     bestehenden Zustand verschoben - und JEDER Befund auf")
        print("     dieser Basis gehoert neu geprueft, bevor weitergebaut")
        print("     wird.")
    return 0 if alles_gleich else 1


if __name__ == "__main__":
    sys.exit(main())
