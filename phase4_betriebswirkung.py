# -*- coding: utf-8 -*-
"""PHASE 4 - DIE BETRIEBSWIRKUNG: stimmt die Simulation mit der Wirklichkeit?

Die Simulation (2.517, 21.09.) hat vorhergesagt:

    Durchlass sinkt von 532 auf 399 Signale (20,9 -> 15,6 Prozent, -25 %)
    beim HEBEL: 11 von 16 bekommen einen hoeheren Faktor, Median 1,00 -> 3,49

Seit dem 22.09. gegen 17:00 UTC laeuft der neue Nenner. Diese Datei
fragt: was ist SEITHER tatsaechlich passiert?

⚠️⚠️ DIE EHRLICHE VORBEMERKUNG: die Umschaltung liegt beim Stand der
Sicherung (23.09. 04:21) rund ELF STUNDEN zurueck. Was hier herauskommt,
ist ein ANFANG, keine Verteilung - und die Datei sagt das in jeder Zeile
mit, statt es in einer Fussnote zu verstecken.

## Womit es laeuft

    python phase4_betriebswirkung.py <pfad-zur-sicherung.db>

Die Sicherung liegt im Austauschordner unter
`DB_Backups/tradinginfotool_<datum>.db.gz` - entpacken, Pfad uebergeben.

⚠️ NUR LESEND, mode=ro. Die Produktionsdatei wird nicht angefasst.

## ⚠️⚠️ DIE KONTROLLE STEHT VOR DER DEUTUNG - und sie hat am 23.09.
## ANGESCHLAGEN

Der Anteil der Aktionen haengt am Modell, nicht am Nenner. Er hat sich im
selben Fenster UMGEDREHT (NACHKAUFEN 36 auf 52 Prozent). Damit ist der
Unterschied NICHT dem Nennerwechsel zuschreibbar - bei 7,9 Stunden ist er
der Tagesgang.

⚠️ Und die Kontrolle ist nicht vollkommen unbeteiligt: ein anderer Nenner
aendert, welche Assets ueberhaupt bewertet werden, und damit mittelbar
auch die Aktionen. Sie taugt als WARNUNG, nicht als Beweis.
"""
import collections
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠️ DER PFAD IST EIN ARGUMENT, KEINE KONSTANTE. Die erste Fassung trug
# den Scratchpad-Pfad EINER Sitzung im Quelltext - damit waere sie beim
# naechsten Export unbrauchbar gewesen, und genau dafuer ist sie gebaut.
if len(sys.argv) < 2:
    raise SystemExit(__doc__)
DB = sys.argv[1]
assert os.path.exists(DB), DB
c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)

# ⚠️ DIE GRENZE WIRD AUS DEN DATEN ABGELEITET, NICHT GESETZT: das erste
# Signal mit der neuen Schwelle markiert die Umschaltung. Ein von Hand
# gesetzter Zeitpunkt waere eine Annahme.
NEU = (0.06, 0.021547)
grenze = c.execute(
    "SELECT MIN(created_at) FROM signals "
    "WHERE potential_schwelle_r IN (?, ?)", NEU).fetchone()[0]

print("=" * 96)
print("PHASE 4 - DIE BETRIEBSWIRKUNG DES NENNERWECHSELS")
print("=" * 96)
print("  Umschaltung (erstes Signal mit neuer Schwelle): %s" % grenze)
letzte = c.execute("SELECT MAX(created_at) FROM signals").fetchone()[0]
print("  Letztes Signal der Sicherung:                   %s" % letzte)

from datetime import datetime as dt
_a = dt.fromisoformat(str(grenze).replace("Z", "+00:00"))
_b = dt.fromisoformat(str(letzte).replace("Z", "+00:00"))
stunden = (_b - _a).total_seconds() / 3600.0
print("  \u26a0\ufe0f\u26a0\ufe0f FENSTER SEIT DER UMSCHALTUNG: %.1f Stunden"
      % stunden)
print("     Alles unten ist ein ANFANG, keine Verteilung.")

# ---- 1) Signale je Schwelle -----------------------------------------
print("\n  1) WIE VIELE SIGNALE, JE SCHWELLE")
print("  " + "-" * 92)
print("     %-12s %-10s %8s %8s" % ("Schwelle", "Art", "Signale", "davon Hebel"))
for w, n, h in c.execute(
        "SELECT potential_schwelle_r, COUNT(*), "
        "SUM(CASE WHEN hebel > 1.0 THEN 1 ELSE 0 END) FROM signals "
        "WHERE potential_schwelle_r IS NOT NULL "
        "AND created_at >= '2026-09-18' GROUP BY 1 ORDER BY 2 DESC"):
    art = "NEU" if w in NEU else "alt"
    print("     %-12s %-10s %8d %8s" % (w, art, n, h or 0))

# ---- 2) Rate je Stunde, vorher gegen nachher ------------------------
print("\n  2) DIE RATE - Signale je Stunde")
print("  " + "-" * 92)
vor_a, vor_b = "2026-09-18", grenze
n_vor = c.execute("SELECT COUNT(*) FROM signals WHERE created_at >= ? "
                  "AND created_at < ?", (vor_a, vor_b)).fetchone()[0]
n_nach = c.execute("SELECT COUNT(*) FROM signals WHERE created_at >= ?",
                   (grenze,)).fetchone()[0]
_v = dt.fromisoformat(vor_a + "T00:00:00+00:00")
std_vor = (_a - _v).total_seconds() / 3600.0
print("     vorher  %4d Signale in %5.1f h = %.2f je Stunde"
      % (n_vor, std_vor, n_vor / max(1e-9, std_vor)))
print("     nachher %4d Signale in %5.1f h = %.2f je Stunde"
      % (n_nach, stunden, n_nach / max(1e-9, stunden)))
print("     \u26d4 %d Signale sind KEINE Rate. Die Zahl steht hier, damit "
      "sie spaeter" % n_nach)
print("        verglichen werden kann - nicht, damit heute etwas daraus "
      "folgt.")

# ---- 3) Der Hebel ----------------------------------------------------
print("\n  3) DER HEBEL - vorher gegen nachher")
print("  " + "-" * 92)
for label, wo, par in (("vorher ", "created_at >= '2026-09-12' AND "
                        "created_at < ?", (grenze,)),
                       ("nachher", "created_at >= ?", (grenze,))):
    z = c.execute("SELECT hebel, potential_r FROM signals WHERE hebel > 1.0 "
                  "AND " + wo, par).fetchall()
    if not z:
        print("     %s keine Hebelsignale" % label)
        continue
    h = sorted(x[0] for x in z)
    p = [x[1] for x in z if x[1] is not None]
    print("     %s %2d Signale | Hebel %.2f bis %.2f (Median %.2f) | "
          "potential %.4f bis %.4f"
          % (label, len(z), h[0], h[-1], h[len(h) // 2],
             min(p) if p else 0, max(p) if p else 0))

# ---- 4) Die Zuschreibungskontrolle ----------------------------------
#
# ⚠️⚠️ VOR JEDER DEUTUNG: aendert sich etwas, das mit dem Nenner NICHTS
# zu tun hat? Der Anteil der Aktionen ist so ein Arm - er haengt am
# Modell, nicht an der Bewertung. Bewegt er sich gleich stark, misst
# diese Datei den Tagesgang und nicht die Umschaltung.
print("\n  4) KONTROLLE - bewegt sich auch, was NICHT am Nenner haengt?")
print("  " + "-" * 92)
for label, wo, par in (("vorher ", "created_at >= '2026-09-18' AND "
                        "created_at < ?", (grenze,)),
                       ("nachher", "created_at >= ?", (grenze,))):
    g = collections.Counter(
        r[0] for r in c.execute(
            "SELECT action FROM signals WHERE " + wo, par))
    ges = sum(g.values()) or 1
    print("     %s %s" % (label, "  ".join(
        "%s %d (%.0f%%)" % (k, v, 100.0 * v / ges)
        for k, v in g.most_common(4))))

c.close()
print("\n" + "=" * 96)
print("  \u26a0\ufe0f WAS NICHT FOLGT: aus %.1f Stunden folgt keine "
      "Betriebsrate, kein" % stunden)
print("     typischer Hebel und kein Vergleich mit der Simulation (2.517).")
print("     Die Datei ist der ANFANG der Messung, nicht ihr Ergebnis.")
print("=" * 96)
