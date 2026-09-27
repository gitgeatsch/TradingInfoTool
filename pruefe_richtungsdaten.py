# -*- coding: utf-8 -*-
"""Prueft den INHALT von richtung_historie.db - nicht nur, ob Daten da sind.

**27.09.2026.** Nutzervorgabe: *"nicht nur die Daten abfragen, sondern auch
pruefen, ob das drinnen ist, was wir erwarten."*

    P1  VOLLSTAENDIGKEIT  Stunden je Symbol und Monat gegen die Kalenderstunden;
                          Quelle (spot / um) je Symbol; Status aus _geladen
    P2  ZEIT              jede Stunde auf :00, keine Doppelten, Monatsgrenzen
                          lueckenlos - auch ueber den Wechsel Milli- zu
                          Mikrosekunden (Spot-Archiv ab 2025)
    P3  GEGEN STUNDENKURSE  gleiche Stunden vorhanden? und bei Quelle spot muss
                          `volumen` EXAKT dem Volumen in stundenkurse entsprechen
                          (beides Binance-Spot) - der haerteste Abgleich
    P4  PLAUSIBEL         0 <= kauf_volumen <= volumen; Kaeuferanteil im Mittel
                          nahe 0,5; Premium-Index betragsmaessig klein
                          (Median |close| unter 0,5 Prozent), Ausreisser gezaehlt
    P5  HERKUNFT          _herkunft vollstaendig (Kennzeichnung fuer die
                          Wiederverwendung)

NUR LESEND auf beiden Dateien.
    python pruefe_richtungsdaten.py [--db <Pfad>]
"""
from __future__ import annotations

import argparse
import calendar
import os
import sqlite3
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
PFLICHT_HERKUNFT = ("kennzeichen", "quelle", "zweck", "tabelle fluss", "einheit fluss",
                    "tabelle premium", "einheit premium", "zeit", "zuordnung", "lader")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(HIER, "data", "richtung_historie.db"))
    a = ap.parse_args()
    c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    s = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    fehler = []

    # P5 Herkunft
    hk = dict(c.execute("SELECT schluessel, wert FROM _herkunft"))
    fehlt = [k for k in PFLICHT_HERKUNFT if not hk.get(k)]
    print("P5 HERKUNFT: %s" % ("✔ vollstaendig (%d Eintraege)" % len(hk) if not fehlt
                               else "⛔ fehlt: %s" % ", ".join(fehlt)))
    if fehlt:
        fehler.append("P5")

    # P1 Vollstaendigkeit je Symbol und Monat
    print()
    print("P1 VOLLSTAENDIGKEIT (Stunden je Monat gegen Kalenderstunden)")
    stat = c.execute("SELECT reihe, status, COUNT(*) FROM _geladen GROUP BY reihe, status").fetchall()
    print("   _geladen: " + " · ".join("%s %s %d" % x for x in stat))
    for tab in ("fluss", "premium"):
        rows = c.execute("SELECT symbol, substr(stunde,1,7), COUNT(*) FROM %s "
                         "GROUP BY 1, 2" % tab).fetchall()
        unvoll = []
        for sym, mon, anz in rows:
            j, m = map(int, mon.split("-"))
            soll = calendar.monthrange(j, m)[1] * 24
            if anz != soll:
                unvoll.append((sym, mon, anz, soll))
        print("   %-8s %5d Symbol-Monate · unvollstaendig %d%s"
              % (tab, len(rows), len(unvoll), (" - z. B. " + ", ".join(
                  "%s %s %d/%d" % u for u in unvoll[:6])) if unvoll else ""))
    quellen = c.execute("SELECT quelle, COUNT(DISTINCT symbol) FROM fluss GROUP BY quelle").fetchall()
    print("   fluss nach Quelle: " + " · ".join("%s %d Symbole" % q for q in quellen))
    gemischt = c.execute("SELECT symbol, GROUP_CONCAT(DISTINCT quelle) FROM fluss GROUP BY symbol "
                         "HAVING COUNT(DISTINCT quelle) > 1").fetchall()
    if gemischt:
        print("   ⚠️ Symbole mit Quellwechsel: " + ", ".join("%s (%s)" % g for g in gemischt[:10]))

    # P2 Zeit
    print()
    for tab in ("fluss", "premium"):
        falsch = c.execute("SELECT COUNT(*) FROM %s WHERE substr(stunde,15,2) <> '00' "
                           "OR length(stunde) <> 16" % tab).fetchone()[0]
        doppelt = c.execute("SELECT COUNT(*) FROM (SELECT symbol, stunde FROM %s GROUP BY 1,2 "
                            "HAVING COUNT(*) > 1)" % tab).fetchone()[0]
        v, b = c.execute("SELECT MIN(stunde), MAX(stunde) FROM %s" % tab).fetchone()
        print("P2 ZEIT %-8s falsches Format %d · doppelt %d · %s bis %s  %s"
              % (tab, falsch, doppelt, v, b, "✔" if falsch == doppelt == 0 else "⛔"))
        if falsch or doppelt:
            fehler.append("P2 " + tab)

    # P3 gegen stundenkurse
    print()
    print("P3 GEGEN STUNDENKURSE")
    syms = [r[0] for r in c.execute("SELECT DISTINCT symbol FROM fluss")]
    abw_max, gleich, verglichen, ohne_sk, nur_hier = 0.0, 0, 0, 0, 0
    for sym in syms:
        f = {r[0]: (r[1], r[2]) for r in c.execute(
            "SELECT stunde, volumen, quelle FROM fluss WHERE symbol=?", (sym,))}
        v, b = min(f), max(f)
        sk = {r[0]: r[1] for r in s.execute(
            "SELECT stunde, volumen FROM stundenkurse WHERE symbol=? AND stunde BETWEEN ? AND ?",
            (sym, v, b))}
        nur_hier += len(set(f) - set(sk))
        ohne_sk += len(set(sk) - set(f))
        for st, (vol, q) in f.items():
            if q == "spot" and st in sk and sk[st] is not None:
                verglichen += 1
                d = abs(vol - sk[st]) / max(abs(sk[st]), 1e-12)
                abw_max = max(abw_max, d)
                gleich += int(d < 1e-9)
    print("   Stunden nur im Archiv %d · nur in stundenkurse %d" % (nur_hier, ohne_sk))
    print("   Spot-Volumen verglichen %d Stunden · exakt gleich %d · groesste relative Abweichung %.2e  %s"
          % (verglichen, gleich, abw_max, "✔" if verglichen and gleich == verglichen else "⚠️"))
    if verglichen and gleich != verglichen:
        fehler.append("P3")

    # P4 plausibel
    print()
    x = np.array(c.execute("SELECT volumen, kauf_volumen FROM fluss").fetchall(), float)
    unmoeglich = int(((x[:, 1] < 0) | (x[:, 1] > x[:, 0] * (1 + 1e-9))).sum())
    anteil = x[:, 1][x[:, 0] > 0] / x[:, 0][x[:, 0] > 0]
    print("P4 KAEUFERANTEIL  unmoeglich (kauf > volumen oder < 0): %d · Mittel %.3f · Median %.3f · "
          "P1 %.3f · P99 %.3f · Stunden ohne Umsatz %d  %s"
          % (unmoeglich, anteil.mean(), np.median(anteil), np.percentile(anteil, 1),
             np.percentile(anteil, 99), int((x[:, 0] <= 0).sum()),
             "✔" if unmoeglich == 0 and 0.4 < anteil.mean() < 0.6 else "⛔"))
    if unmoeglich or not 0.4 < anteil.mean() < 0.6:
        fehler.append("P4 fluss")
    p = np.array([r[0] for r in c.execute("SELECT close FROM premium")], float)
    med = float(np.median(np.abs(p)))
    print("P4 PREMIUM        Median |close| %.5f · P99 |close| %.5f · ueber 5 Prozent %d  %s"
          % (med, np.percentile(np.abs(p), 99), int((np.abs(p) > 0.05).sum()),
             "✔" if med < 0.005 else "⛔"))
    if med >= 0.005:
        fehler.append("P4 premium")
    # P6 btcdom (falls geladen)
    tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "btcdom" in tabs and c.execute("SELECT COUNT(*) FROM btcdom").fetchone()[0]:
        print()
        rows = c.execute("SELECT substr(stunde,1,7), COUNT(*) FROM btcdom GROUP BY 1").fetchall()
        unvoll = [(m_, n_) for m_, n_ in rows
                  if n_ != calendar.monthrange(*map(int, m_.split("-")))[1] * 24]
        x = np.array([r[0] for r in c.execute("SELECT close FROM btcdom ORDER BY stunde")], float)
        sprung = np.abs(np.diff(np.log(np.maximum(x, 1e-12))))
        falsch = c.execute("SELECT COUNT(*) FROM btcdom WHERE substr(stunde,15,2) <> '00'").fetchone()[0]
        ok6 = not unvoll and falsch == 0 and (x > 0).all() and sprung.max() < 0.10
        print("P6 BTCDOM  %d Monate · unvollstaendig %d%s · falsches Format %d · min %.1f max %.1f · "
              "groesster Stundensprung %.2f Prozent  %s"
              % (len(rows), len(unvoll), (" (" + ", ".join("%s %d" % u for u in unvoll[:4]) + ")")
                 if unvoll else "", falsch, x.min(), x.max(), 100 * sprung.max(),
                 "✔" if ok6 else "⛔"))
        for k in ("tabelle btcdom", "einheit btcdom"):
            if not hk.get(k):
                ok6 = False
                print("   ⛔ _herkunft fehlt: %s" % k)
        if not ok6:
            fehler.append("P6 btcdom")
    print()
    print("ERGEBNIS: %s" % ("✔ Inhalt wie erwartet" if not fehler else "⛔ " + ", ".join(fehler)))
    c.close(); s.close()
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
