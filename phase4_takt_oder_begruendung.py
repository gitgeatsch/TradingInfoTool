# -*- coding: utf-8 -*-
"""Loest die BEGRUENDUNG aus - oder die UHR? (Nutzerfrage 20.09.2026)

## Die Frage, und warum sie die wichtigste ist

> *„die Begruendung soll einen Trade starten nicht die Zeit bzw. Takt"*

Das ist **Regel 1** des uebergeordneten Ziels (*der Takt ist nie
Signalgeber*), und CLAUDE.md nennt *,Cooldown abgelaufen`* ausdruecklich
als Beispiel fuer einen **Fakt, der keine Begruendung ist** (Regel 4).

## ⚠️⚠️ Warum das messbar ist und nicht nur eine Haltung

Die Kette laeuft alle **15 Minuten** ueber dieselben Werte. Der Cooldown
sperrt ein Symbol nach einem Signal fuer eine feste Zeit
(`cooldown_stunden` 3,5 fuer Hebel, `spot_cooldown_stunden` 15 bzw. 8 fuer
gehaltene und Kernwerte). Daraus folgen zwei unterscheidbare Welten:

    DIE UHR LOEST AUS   die Bewertung liegt dauerhaft ueber der Schwelle,
                        und das naechste Signal kommt, sobald die Sperre
                        faellt. Dann KLEBEN die Abstaende zwischen zwei
                        Signalen desselben Symbols an der Cooldown-Laenge.
    DIE BEGRUENDUNG     die Lage aendert sich, und das naechste Signal
                        kommt irgendwann danach. Dann sind die Abstaende
                        unregelmaessig und im Mittel deutlich LAENGER.

⚠️ Gemessen wird der Abstand in EINHEITEN DES COOLDOWNS, nicht in Stunden
- sonst vergleicht man Hebel (3,5 h) mit Spot (15 h) und misst die
Konfiguration statt das Verhalten.

⚠️ EIN ABSTAND KNAPP UEBER 1,0 IST DER VERDACHTSFALL. Bei einem Takt von
15 Minuten kann ein von der Uhr getriebenes Signal fruehestens bei 1,0
und spaetestens bei rund 1,07 Cooldowns erscheinen (3,5 h plus eine
Viertelstunde). Der Anteil in diesem Band ist die Kennzahl.

## ⚠️ Was diese Messung NICHT kann

Sie sieht nur die Signale, die DURCHGEKOMMEN sind. Ob die Bewertung
zwischen zwei Signalen unter die Schwelle gefallen und wieder darueber
gestiegen ist, steht hier nicht - dafuer braeuchte es das Trichter-
protokoll je Lauf. Ein hoher Anteil am Cooldown ist deshalb ein
**starker Hinweis**, kein Beweis; ein niedriger Anteil ist dagegen ein
belastbarer Freispruch.

⚠️ NUR LESEND, gegen eine SICHERUNG. Nie gegen die Standard-DB - am
Notebook ist sie die Produktion.

    python phase4_takt_oder_begruendung.py --db <sicherung.db>
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Die laufenden Werte aus `config.yaml` - NICHT die Code-Vorgaben.
#
# ⚠️⚠️ HEBEL HAT EINEN COOLDOWN, SPOT HAT VIER. Mein erster Lauf
# setzte fuer Spot pauschal 15 h an und bekam ,89,2 % der Abstaende
# unter einem Cooldown` - das sah aus wie ein uebergangener Riegel
# und war meine eigene Annahme. Welche Stufe gilt, haengt am Signal
# (Rolle, Bestand, Re-Evaluierung) und steht nicht in `signals`.
#
# ➔ Deshalb: fuer HEBEL in Cooldowns rechnen (eindeutig), fuer SPOT
# in STUNDEN zeigen und ALLE vier Stufen danebenstellen. Eine
# geratene Stufe enthielte die Antwort schon.
COOLDOWN_STUNDEN = {"hebel": 3.5}
# ⚠️⚠️ `cooldown_stunden` 3,5 STEHT HIER MIT, obwohl es der HEBEL-Wert
# ist: der erste Lauf gab fuer Spot Median 3,75 h bei einem 10.-Perzentil
# von 3,51 - das klebt an 3,5 und an keiner der vier Spot-Stufen. F-214
# sagt dasselbe (,Cooldown 3,5 h, kein Bug`). Wer nur die Spot-Stufen
# danebenstellt, sieht genau das nicht.
SPOT_STUFEN = {"re-Evaluierung": 1.0, "⚠️ cooldown_stunden (Hebelwert)": 3.5,
               "Kern/gehalten": 8.0,
               "Spot regulaer": 15.0, "ausgemustert": 120.0}
TAKT_MINUTEN = 15.0
# Das Verdachtsband: von genau einem Cooldown bis einen Takt darueber.
BAND_OBEN = {k: 1.0 + (TAKT_MINUTEN / 60.0) / v
             for k, v in COOLDOWN_STUNDEN.items()}


def _pfad(flagge: str, vorgabe: str) -> str:
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def main() -> int:
    db = _pfad("--db", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "prod_1432.db"))
    if not os.path.exists(db):
        raise SystemExit(
            "Sicherung nicht gefunden: %s%s   mit --db <sicherung.db> setzen "
            "- NIE die Standard-DB" % (db, chr(10)))
    c = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    tage = int(_pfad("--tage", "30"))

    print("=" * 100)
    print("LOEST DIE BEGRUENDUNG AUS - ODER DIE UHR?")
    print("=" * 100)
    print("  Takt der Kette: alle %.0f Minuten · Fenster: %d Tage"
          % (TAKT_MINUTEN, tage))
    print("  Cooldown laut laufender config.yaml: %s"
          % ", ".join("%s %.1f h" % (k, v)
                      for k, v in COOLDOWN_STUNDEN.items()))
    print()

    for instrument, cd in COOLDOWN_STUNDEN.items():
        zeilen = list(c.execute(
            "SELECT symbol, created_at FROM signals "
            " WHERE instrument = ? AND created_at >= date('now', ?) "
            " ORDER BY symbol, created_at", (instrument, "-%d day" % tage)))
        je_symbol: dict = {}
        for sym, ts in zeilen:
            je_symbol.setdefault(sym, []).append(ts)
        abstaende = []
        for sym, liste in je_symbol.items():
            for a, b in zip(liste, liste[1:]):
                try:
                    st = (datetime.fromisoformat(b)
                          - datetime.fromisoformat(a)).total_seconds() / 3600.0
                except Exception:                            # noqa: BLE001
                    continue
                if st > 0:
                    abstaende.append((sym, st, st / cd))
        print("-" * 100)
        print("  %s - %d Signale, %d Symbole, %d Abstaende"
              % (instrument.upper(), len(zeilen), len(je_symbol),
                 len(abstaende)))
        if not abstaende:
            print("    (keine zwei Signale desselben Symbols im Fenster)")
            print()
            continue
        v = sorted(x[2] for x in abstaende)
        n = len(v)
        oben = BAND_OBEN[instrument]
        im_band = sum(1 for x in v if 1.0 <= x <= oben)
        drunter = sum(1 for x in v if x < 1.0)
        print("    Abstand in COOLDOWNS: Median %.2f · 10.%% %.2f · "
              "90.%% %.2f · Maximum %.2f"
              % (v[n // 2], v[max(0, n // 10)], v[min(n - 1, 9 * n // 10)],
                 v[-1]))
        print("    ⚠️ VERDACHTSBAND 1,00 bis %.2f Cooldowns (ein Takt breit):"
              % oben)
        print("       %d von %d = %.1f %% - so oft kam das Signal, sobald "
              "die Sperre fiel" % (im_band, n, 100.0 * im_band / n))
        print("    unter 1,00 Cooldown (Sperre uebergangen): %d = %.1f %%"
              % (drunter, 100.0 * drunter / n))
        print("    ➤ %s" % (
            "DIE UHR TAKTET - die Mehrheit der Abstaende klebt am Cooldown"
            if im_band > n / 2 else
            "DIE UHR TAKTET NICHT DIE MEHRHEIT - aber %.1f %% kleben"
            % (100.0 * im_band / n)))
        print()

    # ---- SPOT: in Stunden, gegen ALLE vier Stufen ----------------
    zeilen = list(c.execute(
        "SELECT symbol, created_at FROM signals "
        " WHERE instrument = 'spot' AND created_at >= date('now', ?) "
        " ORDER BY symbol, created_at", ("-%d day" % tage,)))
    je_symbol: dict = {}
    for sym, ts in zeilen:
        je_symbol.setdefault(sym, []).append(ts)
    stunden = []
    for sym, liste in je_symbol.items():
        for a, b in zip(liste, liste[1:]):
            try:
                st = (datetime.fromisoformat(b)
                      - datetime.fromisoformat(a)).total_seconds() / 3600.0
            except Exception:                            # noqa: BLE001
                continue
            if st > 0:
                stunden.append(st)
    print("-" * 100)
    print("  SPOT - %d Signale, %d Symbole, %d Abstaende"
          % (len(zeilen), len(je_symbol), len(stunden)))
    if not stunden:
        print("    (keine zwei Signale desselben Symbols im Fenster)")
        return 0
    stunden.sort()
    m = len(stunden)
    print("    Abstand in STUNDEN: Median %.2f · 10.%% %.2f · 90.%% %.2f · Maximum %.1f"
          % (stunden[m // 2], stunden[max(0, m // 10)],
             stunden[min(m - 1, 9 * m // 10)], stunden[-1]))
    print("    ⚠️ Welche Stufe gilt, steht nicht im Signal - deshalb ALLE vier:")
    for name, cd in sorted(SPOT_STUFEN.items(), key=lambda t: t[1]):
        # ⚠️ ZWEI Takte breit, nicht einer: die Kette laeuft alle 15 min,
        # und ein Lauf kann ausfallen oder laenger dauern. Ein Band von
        # genau einem Takt wuerde solche Faelle faelschlich freisprechen.
        oben = cd + 2 * TAKT_MINUTEN / 60.0
        im = sum(1 for x in stunden if cd <= x <= oben)
        print("      %-16s %6.1f h -> im Band %6.1f bis %6.1f h: %4d von %d = %.1f %%"
              % (name, cd, cd, oben, im, m, 100.0 * im / m))
    # ⚠️⚠️ DAS FAZIT WIRD GERECHNET, NICHT GESCHRIEBEN. Die erste Fassung
    # sagte fest ,klebt keine Stufe` - und stand damit falsch da, sobald
    # die 3,5-h-Stufe dazukam und 57,7 % einsammelte. Ein Werkzeug mit
    # festem Fazit prueft nichts, es behauptet.
    _beste = max(((n, cd, sum(1 for x in stunden
                               if cd <= x <= cd + 2 * TAKT_MINUTEN / 60.0))
                  for n, cd in SPOT_STUFEN.items()), key=lambda t: t[2])
    _name, _cd, _treffer = _beste
    _anteil = 100.0 * _treffer / m
    if _anteil >= 50.0:
        print("    ➤⚠️⚠️ DIE UHR TAKTET DIE SPOT-SEITE: %.1f %% der "
              "Abstaende kleben bei %.1f h (%s)." % (_anteil, _cd, _name))
        print("       Bei so vielen Signalen hat die SPERRE den Zeitpunkt "
              "bestimmt, nicht die Bewertung -")
        print("       das ist Regel 1 (,der Takt ist nie Signalgeber`) in "
              "der Praxis, nicht in der Absicht.")
    else:
        print("    ➤ Keine Stufe sammelt die Mehrheit (hoechste: %.1f %% "
              "bei %.1f h) - die Uhr taktet die Spot-Seite nicht."
              % (_anteil, _cd))
    print("       Median %.2f h sagt daneben, wie weit die Signale "
          "wirklich auseinanderliegen." % stunden[m // 2])
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
