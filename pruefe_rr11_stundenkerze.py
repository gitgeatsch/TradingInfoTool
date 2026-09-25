# -*- coding: utf-8 -*-
"""R-R11 fuer die Stundenkerzen-Korrektur: halten 2.597 und 2.598?

**25.09.2026**, Nutzervorgabe: *"dann korrigieren und R-R11 pruefen und
gegenpruefen"*.

> **R-R11:** Ein registrierter Befund darf nur von einer Messung umgestossen
> werden, die ihn ZUERST reproduziert. Wer die Basis aendert und ein anderes
> Ergebnis bekommt, hat nichts widerlegt - er hat etwas anderes gemessen.

Die Korrektur der 116 offenen Stundenkerzen AENDERT DIE MESSBASIS. Also ist
nachzuweisen, dass die Befunde 2.597 und 2.598 darauf weiter gelten.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ DIE TOLERANZ IST HERGELEITET, NICHT GESETZT
═══════════════════════════════════════════════════════════════════════

Das ist die Lehre aus 2.597: eine gesetzte Toleranz ist ein Urteil im
Messwerkzeug. Hier laesst sie sich ausrechnen.

`ausgaenge()` sperrt die letzten `max(HORIZONTE)` = 24 Anker:

    gueltig[max(0, n - max(HORIZONTE)):] = False

Der letzte GUELTIGE Anker ist damit `n-25`. Welche Anker LESEN die letzte
Kerze `n-1`?

    Anker i liest die Kerzen i+1 .. i+H.
    Also liest Anker i die Kerze n-1  <=>  i + H >= n-1  <=>  i >= n-1-H

    H = 6   ->  i >= n-7   ->  alle diese Anker sind GESPERRT   -> 0 Anker
    H = 12  ->  i >= n-13  ->  alle diese Anker sind GESPERRT   -> 0 Anker
    H = 24  ->  i >= n-25  ->  genau EINER ist gueltig: n-25    -> 1 Anker

⭐⭐ **Daraus zwei Proben unterschiedlicher Scharfe:**

    H6 und H12    die Kennzahlen muessen BITGLEICH sein. Nicht "aehnlich" -
                  exakt gleich, denn kein einziger gueltiger Anker liest
                  die korrigierte Kerze. Jede Abweichung waere ein Fehler
                  in der Korrektur selbst.

    H24           je Symbol genau EIN Anker ist betroffen, also 116 von
                  3.237.922. Die groesstmoegliche Aenderung je Anker ist
                  der Sprung von STOP auf ZIEL, also `crv - (-1) = crv+1`.
                  Damit:

                      |dE[R]|  <=  116 / 3.237.922 * (crv+1)

                  Bei CRV 4,0 sind das 0,00018. Ueberschreitet die
                  gemessene Differenz diese Grenze, ist mehr passiert als
                  die Kerzenkorrektur.

⚠️ Der ATR aendert sich ebenfalls in der letzten Kerze, aber `atr_tag_relativ`
mittelt ueber 24 Stunden und wird nur fuer den Anker selbst gebraucht - die
betroffenen ATR-Werte liegen bei n-1 und damit im gesperrten Bereich.

    python pruefe_rr11_stundenkerze.py <vorher.txt> <nachher.txt>
"""
from __future__ import annotations

import io
import re
import sys

# ⚠️ Die Windows-Konsole ist cp1252 und bricht an den Zeichen,
# die dieses Projekt ueberall verwendet.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:                                  # noqa: BLE001
    pass

ANKER_JE_SYMBOL_H24 = 1
SYMBOLE = 116
ANKER_GESAMT = 3_237_922
ROT: list = []


def lies(pfad: str) -> dict:
    """-> {(art, k, crv, H): {kennzahl: wert}} aus einer Laufausgabe."""
    aus: dict = {}
    schl = None
    for z in io.open(pfad, encoding="utf-8"):
        m = re.match(r"(k ([\d.]+) x ATR|FIX (\d+) %[^·]*)\s*· "
                     r"CRV ([\d.]+) · H(\d+) · (\d+) Anker", z)
        if m:
            art = "ATR" if m.group(2) else "FIX"
            k = float(m.group(2) or m.group(3))
            schl = (art, k, float(m.group(4)), int(m.group(5)))
            aus[schl] = {"anker": int(m.group(6))}
            continue
        if schl is None:
            continue
        m = re.search(r"E\[R\]_alle ([+-][\d.]+) · Drift ohne Barriere "
                      r"([+-][\d.]+)", z)
        if m:
            aus[schl]["er_alle"] = float(m.group(1))
            aus[schl]["drift"] = float(m.group(2))
        m = re.search(r"Aufloesung ([\d.]+) %", z)
        if m:
            aus[schl]["aufloesung"] = float(m.group(1))
        m = re.match(r"\s+Stop in ATR\s+((?:[\d.]+\s+){5})", z)
        if m:
            aus[schl]["stop_atr"] = [float(x) for x in m.group(1).split()]
        m = re.match(r"\s+⭐ E\[R\] NETTO\s+((?:[+-][\d.]+\s+){5})", z)
        if m:
            aus[schl]["netto"] = [float(x) for x in m.group(1).split()]
        m = re.match(r"\s+q\s+((?:[\d.nan]+\s+){5})", z)
        if m:
            try:
                aus[schl]["q"] = [float(x) for x in m.group(1).split()]
            except ValueError:
                pass
    return aus


def _melde(name: str, ok: bool, text: str) -> None:
    print("  %-46s %s" % (name, "OK" if ok else "⛔ FEHL"))
    print("      %s" % text)
    if not ok:
        ROT.append(name)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    vor, nach = lies(sys.argv[1]), lies(sys.argv[2])
    print("=" * 100)
    print("R-R11: halten 2.597 und 2.598 nach der Kerzenkorrektur?")
    print("=" * 100)
    print("  vorher  %s  (%d Zellen)" % (sys.argv[1], len(vor)))
    print("  nachher %s  (%d Zellen)" % (sys.argv[2], len(nach)))
    print()

    gemeinsam = sorted(set(vor) & set(nach))
    if not gemeinsam:
        _melde("Zellen vergleichbar", False, "keine gemeinsamen Zellen")
        return 1
    _melde("Zellen vergleichbar", len(gemeinsam) == len(vor) == len(nach),
           "%d gemeinsam, %d vorher, %d nachher"
           % (len(gemeinsam), len(vor), len(nach)))

    # ── PROBE 1: H6 und H12 muessen BITGLEICH sein ────────────────────
    kurz = [s for s in gemeinsam if s[3] < 24]
    abw = []
    for s in kurz:
        for feld in ("er_alle", "drift", "aufloesung", "anker"):
            a, b = vor[s].get(feld), nach[s].get(feld)
            if a is not None and b is not None and a != b:
                abw.append("%s/%s: %s -> %s" % (s, feld, a, b))
        for feld in ("netto", "q", "stop_atr"):
            a, b = vor[s].get(feld), nach[s].get(feld)
            if a and b and a != b:
                abw.append("%s/%s" % (s, feld))
    _melde("H6 und H12 BITGLEICH (kein gueltiger Anker liest die Kerze)",
           not abw,
           "%d Zellen geprueft, %d Abweichungen%s"
           % (len(kurz), len(abw),
              " -> " + "; ".join(abw[:3]) if abw else ""))

    # ── PROBE 2: H24 innerhalb der HERGELEITETEN Grenze ───────────────
    lang = [s for s in gemeinsam if s[3] == 24]
    # ⚠️ Nach Ausschoepfung sortiert, nicht nach Differenz - und die Liste
    # wird IMMER gefuellt, auch wenn alle Differenzen null sind. Die erste
    # Fassung liess `schlimmste` dann auf None stehen und meldete "keine
    # H24-Zelle", obwohl 20 davon vorlagen. Eine Pruefung, die bei
    # PERFEKTEM Ergebnis meldet, sie habe nichts gefunden, ist wertlos:
    # man kann den Erfolg nicht vom Ausfall unterscheiden.
    kandidaten = []
    for s in lang:
        grenze = SYMBOLE * ANKER_JE_SYMBOL_H24 / ANKER_GESAMT * (s[2] + 1.0)
        a, b = vor[s].get("er_alle"), nach[s].get("er_alle")
        if a is None or b is None:
            continue
        kandidaten.append((abs(b - a) / grenze, abs(b - a), s, grenze))
    if not kandidaten:
        _melde("H24 innerhalb der hergeleiteten Grenze", False,
               "%d H24-Zellen, aber keine mit `E[R]_alle` in BEIDEN "
               "Laeufen - der Vergleich konnte nicht gerechnet werden"
               % len(lang))
        d = s = grenze = None
    else:
        ausschoepfung, d, s, grenze = max(kandidaten)
    if s is not None:
        _melde("H24 innerhalb der hergeleiteten Grenze", d <= grenze,
               "%d Zellen · groesste Differenz %.6f in %s · "
               "Grenze %.6f (= %d/%d x (CRV+1)) · ausgeschoepft %.1f %%"
               % (len(lang), d, s, grenze, SYMBOLE, ANKER_GESAMT,
                  100.0 * ausschoepfung))

    # ── PROBE 3: die BEFUNDAUSSAGEN selbst, nicht nur die Zahlen ──────
    #
    # ⚠️ Zahlen koennen halten und der BEFUND trotzdem kippen - wenn er an
    # einem Vorzeichen oder einer Reihenfolge haengt. 2.597 sagt: (a) der
    # Stop ist bei k <= 1,0 lageneutral, (b) NETTO ist Fuenftel 4 das beste.
    kipp = []
    for s in gemeinsam:
        n = nach[s]
        if s[0] == "ATR" and s[1] <= 1.0 and n.get("stop_atr"):
            sp = max(n["stop_atr"]) - min(n["stop_atr"])
            if sp >= 0.02:
                kipp.append("%s: Stopspanne %.4f >= 0,02" % (s, sp))
        if n.get("netto") and s[0] == "ATR" and abs(s[1] - 1.0) < 1e-9:
            if n["netto"][4] <= max(n["netto"][:4]):
                kipp.append("%s: Fuenftel 4 nicht mehr das beste" % (s,))
    _melde("die AUSSAGEN von 2.597 halten (nicht nur die Zahlen)",
           not kipp,
           "geprueft: Stopneutralitaet bei k<=1,0 und NETTO-Rang von "
           "Fuenftel 4 · %d Verletzungen%s"
           % (len(kipp), " -> " + "; ".join(kipp[:3]) if kipp else ""))

    print()
    print("=" * 100)
    if ROT:
        print("⛔ %d FEHLGESCHLAGEN: %s" % (len(ROT), ", ".join(ROT)))
        print("   ⚠ R-R11 NICHT erfuellt - die Korrektur hat mehr")
        print("      veraendert als die 116 Kerzen. Vor jeder weiteren")
        print("      Messung klaeren.")
        return 1
    print("✔✔ R-R11 ERFUELLT - 2.597 und 2.598 gelten auf der")
    print("   korrigierten Messbasis weiter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
