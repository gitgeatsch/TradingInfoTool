# -*- coding: utf-8 -*-
"""Prueft den INHALT der nachgeladenen eingestellten Paare - nicht nur, ob Daten da sind.

**27.09.2026.** Nutzer: *"nicht nur die Daten abfragen, sondern auch pruefen, ob
das drinnen ist, was wir erwarten"* und *"pruefen und gegenpruefen"*. Voranalyse
`Basisinfos/Voranalyse_Nachladen_Eingestellte_27_09.md`, Abschnitt 4.

    P1  ARCHIV GEGEN BESTAND: dieselbe Ladefunktion auf heute gehandelte
        Symbole (--kontrolle-db) muss stundenkurse, fluss, premium und funding
        des Bestands EXAKT treffen
    P2  ZOMBIE: am Reihenende kein Lauf >= 72 h mit Volumen 0 und konstantem Kurs
    P3  Zeitformat, Jahresbereich, Stundenluecken je Symbol
    P4  VORGESCHICHTE: Uebergang alter Reihe -> Nachfolger im Bestand, Kurssprung
    P5  EINORDNUNG: kein Symbol der Art kein_krypto / umbenennung geladen
    P6  PLAUSIBILITAET: Kaeuferanteil <= Volumen, Premium-Groessenordnung, das
        Ende ist echt (Volumen vorhanden) - der Absturz vor der Einstellung

NUR LESEND (`mode=ro`), oeffnet tradinginfotool.db nicht.

    python pruefe_eingestellte.py --db data/eingestellt_historie.db --kontrolle-db <Pfad>
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
BESTAND = {"stundenkurse": os.path.join(HIER, "data", "stundenkurse.db"),
           "richtung": os.path.join(HIER, "data", "richtung_historie.db"),
           "funding": os.path.join(HIER, "data", "funding_historie.db")}


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(HIER, "data", "eingestellt_historie.db"))
    ap.add_argument("--kontrolle-db", default="")
    a = ap.parse_args()
    fehler = []
    c = ro(a.db)
    print("=" * 100)
    print("PRUEFUNG EINGESTELLTE - %s" % a.db)
    print("=" * 100)

    # ── P1 Archiv gegen Bestand
    if a.kontrolle_db:
        k = ro(a.kontrolle_db)
        sk, ri, fu = ro(BESTAND["stundenkurse"]), ro(BESTAND["richtung"]), ro(BESTAND["funding"])
        p1_ok = 0
        for sym, in k.execute("SELECT DISTINCT symbol FROM stundenkurse"):
            neu = {r[0]: r[1:] for r in k.execute(
                "SELECT stunde, open, high, low, close, volumen, quelle FROM stundenkurse "
                "WHERE symbol=?", (sym,))}
            alt = {r[0]: r[1:] for r in sk.execute(
                "SELECT stunde, open, high, low, close, volumen FROM stundenkurse WHERE symbol=? "
                "AND stunde BETWEEN ? AND ?", (sym, min(neu), max(neu)))}
            if not alt:
                print("  P1 %-5s nicht im Bestand - keine Kontrolle moeglich (zaehlt nicht)" % sym)
                continue
            gemeinsam = set(neu) & set(alt)
            abw = sum(1 for t in gemeinsam
                      if any(abs(x - y) > 1e-9 * max(1.0, abs(y)) for x, y in zip(neu[t][:5], alt[t])))
            nur_neu, nur_alt = len(set(neu) - set(alt)), len(set(alt) - set(neu))
            quellen = sorted({v[5] for v in neu.values()})
            fl_n = {r[0]: r[1:] for r in k.execute("SELECT stunde, volumen, kauf_volumen FROM fluss WHERE symbol=?", (sym,))}
            fl_a = {r[0]: r[1:] for r in ri.execute("SELECT stunde, volumen, kauf_volumen FROM fluss WHERE symbol=? "
                                                     "AND stunde BETWEEN ? AND ?", (sym, min(neu), max(neu)))}
            fl_abw = sum(1 for t in set(fl_n) & set(fl_a)
                         if any(abs(x - y) > 1e-9 * max(1.0, abs(y)) for x, y in zip(fl_n[t], fl_a[t])))
            pr_n = {r[0]: r[1] for r in k.execute("SELECT stunde, close FROM premium WHERE symbol=?", (sym,))}
            pr_a = {r[0]: r[1] for r in ri.execute("SELECT stunde, close FROM premium WHERE symbol=? "
                                                    "AND stunde BETWEEN ? AND ?", (sym, min(neu), max(neu)))}
            pr_abw = sum(1 for t in set(pr_n) & set(pr_a) if abs(pr_n[t] - pr_a[t]) > 1e-12)
            fu_n = {r[0]: r[1] for r in k.execute("SELECT datum, wert FROM funding WHERE symbol=?", (sym,))}
            fu_a = {r[0]: r[1] for r in fu.execute("SELECT datum, wert FROM funding WHERE symbol=?", (sym,))
                    if r[0] in fu_n}
            fu_abw = [(t, fu_n[t], fu_a[t]) for t in fu_a if abs(fu_n[t] - fu_a[t]) > 1e-10]
            ok = (abw == 0 and nur_neu == 0 and nur_alt == 0 and fl_abw == 0 and pr_abw == 0
                  and not fu_abw and len(gemeinsam) > 0 and len(fu_a) > 0)
            print("  P1 %-5s Kurs %d Stunden gemeinsam, %d abweichend, nur neu %d, nur Bestand %d, Quelle %s · "
                  "fluss %d abw. · premium %d abw. · funding %d Tage, %d abw.  %s"
                  % (sym, len(gemeinsam), abw, nur_neu, nur_alt, quellen, fl_abw, pr_abw,
                     len(fu_a), len(fu_abw), "✔" if ok else "✘"))
            for t, x, y in fu_abw[:3]:
                print("       funding %s: Archiv %.8f · Bestand %.8f" % (t, x, y))
            if not ok:
                fehler.append("P1 %s" % sym)
            else:
                p1_ok += 1
        if p1_ok < 3:
            fehler.append("P1 nur %d vergleichbare Kontrollsymbole (Soll 3)" % p1_ok)
    else:
        print("  P1 ⚠ ohne --kontrolle-db nicht gerechnet")
        fehler.append("P1 nicht gerechnet")

    # ── P5 Einordnung
    arten = dict(c.execute("SELECT art, COUNT(*) FROM symbole GROUP BY art").fetchall())
    geladen = {r[0] for r in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
    falsch = [r for r in c.execute("SELECT paar, symbol, art FROM symbole WHERE art IN "
                                   "('kein_krypto','umbenennung')") if r[1] in geladen
              and not c.execute("SELECT COUNT(*) FROM symbole WHERE symbol=? AND art IN "
                                "('eingestellt','vorgeschichte','ergaenzung')", (r[1],)).fetchone()[0]]
    print("  P5 Einordnung %s · geladen %d Symbole · falsch geladen %d  %s"
          % (arten, len(geladen), len(falsch), "✔" if not falsch else "✘"))
    if falsch:
        fehler.append("P5")

    # ── P2, P3, P6 je Symbol
    zombie, luecken, zeitfehler, kauf, ende_tot = [], [], 0, 0, []
    for sym in sorted(geladen):
        rows = c.execute("SELECT stunde, close, volumen FROM stundenkurse WHERE symbol=? ORDER BY stunde",
                         (sym,)).fetchall()
        st = [r[0] for r in rows]
        zeitfehler += sum(1 for x in st if not re.match(r"^(20(1[7-9]|2[0-6]))-\d\d-\d\d \d\d:00$", x))
        vol = np.array([r[2] or 0 for r in rows]); cl = np.array([r[1] for r in rows])
        k = len(rows)
        while k > 1 and vol[k - 1] == 0 and cl[k - 1] == cl[k - 2]:
            k -= 1
        if len(rows) - k >= 72:
            zombie.append((sym, len(rows) - k))
        h = np.array(st, "datetime64[h]") if st else np.array([], "datetime64[h]")
        if len(h) > 1:
            luecken.append((sym, int((h[-1] - h[0]).astype(int)) + 1 - len(h)))
        if len(vol) >= 720 and np.mean(vol[-720:] > 0) < 0.5:
            ende_tot.append(sym)
    # ── P7 Zombie MITTEN in der Reihe, P8 Spruenge (28.09., im Vergleich gefunden:
    # die Pruefung kannte beide Faelle nicht - LUNA und die eingefrorenen
    # Terminmarkt-Stunden nach dem Ende des Spot-Handels)
    innen, sprung_wechsel, sprung_luecke = [], [], []
    for sym in sorted(geladen):
        rows = c.execute("SELECT stunde, close, volumen, quelle FROM stundenkurse WHERE symbol=? "
                         "ORDER BY stunde", (sym,)).fetchall()
        lauf = 0
        for i in range(1, len(rows)):
            if (rows[i][2] or 0) == 0 and rows[i][1] == rows[i - 1][1]:
                lauf += 1
                if lauf == 72:
                    innen.append((sym, rows[i][0]))
            else:
                lauf = 0
            a0, b0 = rows[i - 1], rows[i]
            if a0[1] > 0 and b0[1] > 0:
                f = b0[1] / a0[1]
                dt = (np.datetime64(b0[0].replace(" ", "T")) - np.datetime64(a0[0].replace(" ", "T"))
                      ).astype("timedelta64[h]").astype(int)
                if dt == 1 and a0[3] != b0[3] and not (0.8 < f < 1.25):
                    sprung_wechsel.append((sym, b0[0], round(f, 3)))
                if dt > 1 and (f > 3 or f < 1 / 3):
                    sprung_luecke.append((sym, a0[0], b0[0], round(f, 3)))
    print("  P7 Zombie-Laeufe >= 72 h MITTEN in der Reihe: %d %s  %s" % (
        len(innen), innen[:4], "✔" if not innen else "✘"))
    if innen:
        fehler.append("P7")
    print("  P8 Quellenwechsel OHNE Luecke mit Kurssprung > 25 %%: %d %s  %s" % (
        len(sprung_wechsel), sprung_wechsel[:4], "✔" if not sprung_wechsel else "✘"))
    if sprung_wechsel:
        fehler.append("P8")
    print("     Info: Spruenge > Faktor 3 UEBER eine Luecke (Umstellung, Neustart - die Messung "
          "schliesst Fenster ueber Luecken aus): %d %s" % (len(sprung_luecke), sprung_luecke[:6]))
    kauf = c.execute("SELECT COUNT(*) FROM fluss WHERE kauf_volumen > volumen * (1 + 1e-9)").fetchone()[0]
    print("  P2 Zombie-Laeufe >= 72 h am Reihenende: %d %s  %s" % (
        len(zombie), zombie[:5], "✔" if not zombie else "✘ (--abschliessen nicht gelaufen?)"))
    if zombie:
        fehler.append("P2")
    print("  P3 Zeitformat-Fehler %d · Stundenluecken: %d Symbole mit Luecken, groesste %s  %s" % (
        zeitfehler, sum(1 for _s, x in luecken if x > 0),
        sorted(luecken, key=lambda x: -x[1])[:3], "✔" if zeitfehler == 0 else "✘"))
    if zeitfehler:
        fehler.append("P3")

    # ── P4 Vorgeschichte
    sk = ro(BESTAND["stundenkurse"])
    for paar, sym, nf in c.execute("SELECT paar, symbol, nachfolger FROM symbole WHERE art='vorgeschichte'"):
        alt = c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? ORDER BY stunde DESC LIMIT 1",
                        (sym,)).fetchone()
        neu = sk.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? ORDER BY stunde LIMIT 1",
                         (nf,)).fetchone()
        if not alt or not neu:
            print("  P4 %-10s -> %-6s nicht pruefbar (alt %s, neu %s)" % (paar, nf, alt, neu))
            continue
        # Ueberlappung: die alte Reihe darf den Bestand nicht ueberdecken
        ueber = c.execute("SELECT COUNT(*) FROM stundenkurse WHERE symbol=? AND stunde>=?",
                          (sym, neu[0])).fetchone()[0]
        verh = neu[1] / alt[1] if alt[1] else float("nan")
        # ⚠️ Liegt zwischen altem Ende und neuem Anfang eine LUECKE, ist der
        # Kurs dazwischen weitergelaufen (KLAY->KAIA: ein Monat, der Alt-Anstieg
        # Nov. 2024). Dann gegen den MEDIAN der Marktbewegung im selben Zeitraum
        # pruefen, nicht gegen 1 - ein Umtauschverhaeltnis ungleich 1 zeigt sich
        # als Abweichung vom Markt um ein Vielfaches.
        luecke_t = (np.datetime64(neu[0].replace(" ", "T")) - np.datetime64(alt[0].replace(" ", "T"))
                    ).astype("timedelta64[D]").astype(int)
        markt = 1.0
        if luecke_t > 7:
            fak = []
            for (x,) in sk.execute("SELECT DISTINCT symbol FROM stundenkurse").fetchall():
                a0 = sk.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde>=? ORDER BY stunde LIMIT 1",
                                (x, alt[0])).fetchone()
                b0 = sk.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde>=? ORDER BY stunde LIMIT 1",
                                (x, neu[0])).fetchone()
                if a0 and b0 and a0[0] > 0 and x not in ("BTC",):
                    fak.append(b0[0] / a0[0])
            markt = float(np.median(fak)) if fak else 1.0
        rel = verh / markt
        ok = 0.5 <= rel <= 2.0 if luecke_t > 7 else 0.8 <= verh <= 1.25
        print("  P4 %-10s -> %-6s alt endet %s (%.5g) · Bestand beginnt %s (%.5g) · Verhaeltnis %.3f · "
              "Luecke %d Tage%s · Ueberlappung %d Stunden  %s" % (
                  paar, nf, alt[0], alt[1], neu[0], neu[1], verh, luecke_t,
                  (" · Markt-Median %.2f, relativ %.2f" % (markt, rel)) if luecke_t > 7 else "",
                  ueber, "✔" if ok else "⚠ Kurssprung - Umtauschverhaeltnis pruefen"))
        if not ok:
            fehler.append("P4 %s" % paar)

    # ── P6 Plausibilitaet
    pm = [r[0] for r in c.execute("SELECT close FROM premium")]
    med = float(np.median(np.abs(pm))) if pm else float("nan")
    print("  P6 Kaeufer > Volumen: %d Stunden · Premium |Median| %.5f · Reihen, deren letzte 30 Tage "
          "zu > 50 %% ohne Volumen sind: %d %s  %s" % (
              kauf, med, len(ende_tot), ende_tot[:6], "✔" if kauf == 0 and med < 0.01 else "✘"))
    if kauf or not (med < 0.01):
        fehler.append("P6")
    print()
    print("ERGEBNIS: %s" % ("✔ Inhalt wie erwartet" if not fehler else "✘ " + ", ".join(fehler)))
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
