# -*- coding: utf-8 -*-
"""D-1 — Reihen aus der PRODUKTION in die Messbasis uebernehmen (08.09.2026)

## Warum es das braucht

`pruefe_neuaufnahme.py` meldet acht gehaltene Krypto-Positionen ohne
Messreihe. Die Ursache ist keine Nachlaessigkeit, sondern die Quelle: die
Messbasis laedt **Binance-USDT** (`quelle='binance_mess'`), und Binance
fuehrt diese Symbole ueberwiegend nicht.

Die Produktion hat sie trotzdem - aus `bybit` und `gemessen` (letzteres
ist laut `database/db.py` ein *„echter Kursabruf"*, also echte Kerzen).

## ⚠️⚠️ WARUM NICHT EINFACH KOPIEREN

Die Messbasis ist heute **quellenrein**: 5.114.965 Zeilen, alle
`binance_mess`. Wer fremde Reihen stumm dazulegt, macht jede spaetere
Messung blind fuer den Unterschied.

> **Deshalb traegt jede uebernommene Zeile eine eigene Quelle:**
> `uebernommen_bybit`, `uebernommen_gemessen`, `uebernommen_binance`.
> Ein `SELECT DISTINCT quelle` zeigt es sofort.

## ⚠️ UND SIE VERALTEN STILL

Diese Symbole sind NICHT auf Binance - `lade_messreihen.py` kann sie nie
auffrischen. Sie enden heute am 19.08. bzw. 13.07. und bleiben dort
stehen, bis jemand sie erneut uebernimmt. **Das ist der Preis, und er
gehoert benannt**, nicht entdeckt.

## Was geprueft wird, BEVOR eine Zeile geschrieben wird

Dieselben Bedingungen wie in `lade_messreihen.py` - nicht gelockert:

    Tagesabstand   Median der Luecken genau 1
    Laenge         mindestens 400 Kerzen
    Plausibel      high >= low, alle Preise > 0
    Doppelte       je Tag genau EINE Zeile

⚠️ **Bei mehreren Quellen je Tag gewinnt die beste**: binance vor bybit
vor gemessen. Binance-Kerzen sind dieselbe Quelle wie die Messbasis
selbst; `gemessen` ist der Rueckfall.

## ⚠️ Die harte Sperre

Wie in `lade_messreihen.py`: diese Datei schreibt NIE in die
Produktionsdatenbank. Ein Tippfehler im Pfad wuerde sonst Messreihen in
den Live-Betrieb tragen.

    python uebernehme_messreihen.py              # Probelauf
    python uebernehme_messreihen.py --schreiben
"""
from __future__ import annotations

import argparse
import datetime as _d
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRODUKTION = "tradinginfotool.db"
QUELLE = "data/tradinginfotool.db"
ZIEL = "data/messdaten.db"
MIND_KERZEN = 400
# ⚠️ Rangfolge der Quellen je Tag. binance ist DIESELBE Quelle wie die
# Messbasis; `gemessen` ist der Rueckfall.
RANG = {"binance": 0, "binance_historie": 0, "bybit": 1, "gemessen": 2}
# Die zehn, die `pruefe_neuaufnahme` als aufnehmbar ausweist.
SYMBOLE = ("AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS",
           "MORPHO", "PLUME", "SUPRA")


def beste_je_tag(rows: list) -> list:
    """Je Kalendertag die Zeile der besten Quelle."""
    best: dict = {}
    for r in rows:
        tag = r[0][:10]
        if tag not in best or RANG.get(r[6], 9) < RANG.get(best[tag][6], 9):
            best[tag] = r
    return [best[t] for t in sorted(best)]


def pruefe_reihe(rr: list) -> tuple[bool, str]:
    """Haelt die Reihe die Aufnahmebedingungen? (dieselben wie der Lader)"""
    if len(rr) < MIND_KERZEN:
        return False, "zu kurz (%d)" % len(rr)
    dt = [_d.date.fromisoformat(x[0][:10]) for x in rr]
    if len(set(dt)) != len(dt):
        return False, "doppelte Daten"
    ab = sorted((dt[i + 1] - dt[i]).days for i in range(len(dt) - 1))
    med = ab[len(ab) // 2]
    if med != 1:
        return False, "Median-Tagesabstand %d statt 1" % med
    for tag, hoch, tief, schluss, offen, vol, q in rr:
        if not (hoch >= tief and schluss > 0 and hoch > 0 and tief > 0):
            return False, "unplausible Preise am %s" % tag[:10]
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", default=ZIEL)
    ap.add_argument("--schreiben", action="store_true",
                    help="ohne dies wird nur geprueft, nichts geschrieben")
    ap.add_argument("--nur", default="", help="Symbole, kommagetrennt")
    a = ap.parse_args()

    # ⚠️ HARTE SPERRE - dieselbe wie in `lade_messreihen.py`.
    if PRODUKTION in a.ziel.replace("\\", "/"):
        raise SystemExit("'%s' ist die Produktionsdatenbank. Messreihen "
                         "gehoeren in eine eigene Datei." % a.ziel)

    syms = ([x.strip().upper() for x in a.nur.split(",") if x.strip()]
            if a.nur else list(SYMBOLE))
    print("=" * 96)
    print("UEBERNAHME AUS DER PRODUKTION - %d Symbole -> %s" % (len(syms), a.ziel))
    print("  %s" % ("schreibend" if a.schreiben
                    else "PROBELAUF, es wird nichts geschrieben"))
    print("=" * 96)

    p = sqlite3.connect("file:%s?mode=ro" % QUELLE, uri=True)
    z = sqlite3.connect(a.ziel) if a.schreiben else \
        sqlite3.connect("file:%s?mode=ro" % a.ziel, uri=True)
    jetzt = _d.datetime.now(_d.timezone.utc).isoformat()
    ok = zeilen = 0
    abgelehnt = []
    print("  %-10s %8s %12s %12s   %s"
          % ("Symbol", "Zeilen", "von", "bis", "Quellen / Urteil"))
    for s in syms:
        # ⚠️ Steht das Symbol schon in `messreihen`? Dann NICHT anfassen -
        # eine Klassenumstellung waere ein stiller Eingriff (F-198).
        vorhanden = z.execute(
            "SELECT assetklasse FROM messreihen WHERE symbol=?", (s,)).fetchone()
        if vorhanden:
            abgelehnt.append((s, "steht bereits als %s" % vorhanden[0]))
            print("  %-10s %8s   ⚠️ steht bereits als %s"
                  % (s, "-", vorhanden[0]))
            continue
        rows = p.execute(
            "SELECT date, high, low, close, open, volume, quelle "
            "FROM price_history_ohlc WHERE UPPER(symbol)=? AND currency='USD' "
            "ORDER BY date", (s,)).fetchall()
        if not rows:
            abgelehnt.append((s, "keine USD-Zeile in der Produktion"))
            print("  %-10s %8s   ⚠️ keine USD-Zeile" % (s, "-"))
            continue
        rr = beste_je_tag(rows)
        gut, grund = pruefe_reihe(rr)
        quellen = {}
        for r in rr:
            quellen[r[6]] = quellen.get(r[6], 0) + 1
        qtext = ", ".join("%s %d" % (k, v) for k, v in sorted(quellen.items()))
        if not gut:
            abgelehnt.append((s, grund))
            print("  %-10s %8d %12s %12s   ⚠️ %s"
                  % (s, len(rr), rr[0][0][:10], rr[-1][0][:10], grund))
            continue
        print("  %-10s %8d %12s %12s   %s"
              % (s, len(rr), rr[0][0][:10], rr[-1][0][:10], qtext))
        ok += 1
        zeilen += len(rr)
        if a.schreiben:
            for tag, hoch, tief, schluss, offen, vol, q in rr:
                z.execute(
                    "INSERT OR REPLACE INTO price_history_ohlc "
                    "(symbol, assetklasse, currency, date, open, high, low, "
                    " close, volume, fetched_at, quelle) "
                    "VALUES (?,'krypto','USD',?,?,?,?,?,?,?,?)",
                    (s, tag[:10], offen, hoch, tief, schluss, vol or 0.0,
                     jetzt, "uebernommen_%s" % q))
            z.execute("INSERT OR REPLACE INTO messreihen VALUES (?, 'krypto')",
                      (s,))
            # ⚠️ NICHT 'handelnd'. Diese Reihen kann `lade_messreihen` NIE
            # auffrischen - sie sind nicht auf Binance. Ein eigener Status
            # macht sichtbar, dass sie einen anderen Weg brauchen.
            z.execute("INSERT OR REPLACE INTO messreihen_status "
                      "VALUES (?, 'uebernommen')", (s,))
    if a.schreiben:
        z.commit()
    p.close()
    z.close()

    print()
    print("  %d von %d Reihen aufnehmbar, %d Zeilen" % (ok, len(syms), zeilen))
    if abgelehnt:
        print("  %d abgelehnt:" % len(abgelehnt))
        for s, g in abgelehnt:
            print("     %-10s %s" % (s, g))
    print()
    if a.schreiben:
        print("  ✔ geschrieben nach %s" % a.ziel)
        print("  ⚠️ Status `uebernommen` - diese Reihen sind NICHT auf")
        print("     Binance und veralten, bis sie erneut uebernommen werden.")
        print("  ⚠️ JETZT die Anker gegenpruefen: die Messbasis hat sich")
        print("     geaendert (`pruefe_messbasis_wechsel.py --nachher`).")
    else:
        print("  PROBELAUF - nichts geschrieben. Mit --schreiben wiederholen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
