# -*- coding: utf-8 -*-
"""Wie scharf sind die Bewegungen - und was kostet das die Zielgroesse?

Nutzereinwand 24.09.2026:
    "bei Krypto sind Bewegungen oft schnell kurz hoeher - wie auch die
     Gegenbewegungen"

⚠️ Das ist ein Einwand gegen die ZIELGROESSE der Vorabfestlegung 10, nicht
gegen ihre Kandidaten. Sie nimmt bei offenen Trades den SCHLUSSKURS am Ende
der Haltedauer. Wenn der Nutzer recht hat, ist dieser Kurs ein schlechter
Zeuge - und zwar in BEIDE Richtungen:

    nach oben    der Trade stand zwischendurch bei +1,8 R und ist am Ende
                 bei 0 - gezaehlt wird 0, obwohl das Potential da war
    nach unten   die Gegenbewegung raeumt den Stop ab, BEVOR das Ziel kommt

Gemessen werden deshalb vier Groessen je Einstieg und Haltedauer:

    schluss_r    (close am Ende - Einstieg) / Stopabstand   ← Vorabfestlegung
    mfe_r        weitester Stand NACH OBEN im Fenster (max high)
    mae_r        weitester Stand NACH UNTEN im Fenster (min low)
    ausgang      ziel | stop | offen | MEHRDEUTIG

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ MEHRDEUTIG - die Aufloesungsgrenze, die BLEIBT
═══════════════════════════════════════════════════════════════════════

Beruehrt EINE Stunde sowohl das Ziel als auch den Stop, ist die Reihenfolge
auch auf Stundenbasis unbekannt. Auf TAGESbasis war das der Normalfall und
der Hauptfehler; die Frage ist, wie viel davon uebrig bleibt.

⚠️ Der Anteil MEHRDEUTIG ist die Zahl, die entscheidet, ob die Stundenbasis
ueberhaupt reicht. Er wird NICHT geschaetzt und NICHT weggerundet.

⚠️⚠️ UND: MFE ist NICHT handelbar. Man kann nicht am Hoch aussteigen, wenn
man es nicht vorher kennt - das ist genau die Falle "ein Maximum ist kein
Schaetzer" (Messstandard 08.09.). MFE steht hier als OBERGRENZE des
Erreichbaren, nie als Ergebnis.

    Stop     PRODUKTIONSGEOMETRIE, wie Befund 2.582 sie benutzt:
                 min(25 %, max(5 %, 0,75 x ATR14))
             ⚠️ Der erste Entwurf nahm 2,5 x ATR (rund 12 %) und bekam
             deshalb bei 48 h nur 2,7 % Stop statt der 29,5 % aus 2.582 -
             Faktor 11. Der Fehler lag im Stopabstand, nicht im Markt.
    Ziel     CRV 2,0 (config.yaml: crv_minimum)

    ⚠️⚠️ ZWEITE ACHSE - der Stop wird MITSKALIERT. Ein auf Tagesbewegung
    ausgelegter Stop ist fuer ein 6-h-Fenster zu weit; die Barriere wird
    dann nie beruehrt und die Mehrdeutigkeitsfrage gar nicht erst gestellt.
    Volatilitaet waechst mit der Wurzel der Zeit, also:

             skaliert:  stop_prod x sqrt(H / 24)

    Beide Varianten laufen nebeneinander. Welche besser ist, entscheidet
    die Messung - hier wird nur beides SICHTBAR gemacht.
    Richtung LONG - short ist eine eigene Frage (Nutzer 24.09.: "lass es")

⚠️ Liest NUR `data/stundenkurse.db` mit mode=ro. Ruehrt keine
Produktionsdatenbank an und schreibt nirgends hin.

    python messe_scharfe_bewegungen.py
    python messe_scharfe_bewegungen.py --symbole 20     # Probelauf
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUELLE = os.path.join("data", "stundenkurse.db")
HALTEDAUERN = (6, 12, 24, 48, 72)          # Stunden - Vorabfestlegung 10 § 3
SKALIERT = False                            # --skaliert: Stop mit sqrt(H/24)
CRV = 2.0                                   # config.yaml crv_minimum
ATR_FENSTER = 14
# Produktionsgeometrie - Befund 2.582, Feld `basis`
ATR_ANTEIL, STOP_MIN, STOP_MAX = 0.75, 0.05, 0.25
TAKT = 12                                   # jede 12. Stunde ein Einstieg


def _atr_je_stunde(stunde, hi, lo, cl):
    """Taeglicher ATR14, jeder Stunde zugeordnet - aus den Stundenkerzen.

    ⚠️ Der ATR des VORTAGS wird zugeordnet, nie der des laufenden Tages:
    sonst kennt der Einstieg seine eigene Zukunft.
    """
    tag = np.array([s[:10] for s in stunde])
    grenzen = np.flatnonzero(np.r_[True, tag[1:] != tag[:-1]])
    t_hi = np.maximum.reduceat(hi, grenzen)
    t_lo = np.minimum.reduceat(lo, grenzen)
    t_cl = cl[np.r_[grenzen[1:] - 1, len(cl) - 1]]
    if len(t_hi) < ATR_FENSTER + 2:
        return None
    vor = np.r_[t_cl[0], t_cl[:-1]]
    tr = np.maximum(t_hi - t_lo,
                    np.maximum(np.abs(t_hi - vor), np.abs(t_lo - vor)))
    atr = np.full(len(tr), np.nan)
    lauf = np.cumsum(tr)
    atr[ATR_FENSTER - 1:] = (
        (lauf[ATR_FENSTER - 1:] - np.r_[0, lauf[:-ATR_FENSTER]]) / ATR_FENSTER)
    # ⚠️ um einen Tag versetzt - der Einstieg sieht nur Abgeschlossenes
    atr_vortag = np.r_[np.nan, atr[:-1]]
    je_tag = np.repeat(np.arange(len(grenzen)), np.diff(np.r_[grenzen, len(hi)]))
    return atr_vortag[je_tag]


def _ein_symbol(hi, lo, cl, atr, ergebnis, skaliert):
    n = len(cl)
    for h in HALTEDAUERN:
        idx = np.arange(0, n - h, TAKT)
        idx = idx[np.isfinite(atr[idx]) & (atr[idx] > 0)]
        if not len(idx):
            continue
        e = cl[idx]
        # ⚠️ Produktionsgeometrie, relativ zum Kurs - wie 2.582
        rel = np.clip(ATR_ANTEIL * atr[idx] / e, STOP_MIN, STOP_MAX)
        if skaliert:
            rel = rel * np.sqrt(h / 24.0)
        s = rel * e
        ziel, stop = e + CRV * s, e - s

        erst_ziel = np.full(len(idx), h, np.int32)
        erst_stop = np.full(len(idx), h, np.int32)
        mfe = np.full(len(idx), -np.inf)
        mae = np.full(len(idx), np.inf)
        for t in range(1, h + 1):                 # ⚠️ ab t=1: der Einstieg
            f_hi, f_lo = hi[idx + t], lo[idx + t]  # selbst zaehlt nicht
            mfe = np.maximum(mfe, f_hi)
            mae = np.minimum(mae, f_lo)
            erst_ziel = np.where((erst_ziel == h) & (f_hi >= ziel), t, erst_ziel)
            erst_stop = np.where((erst_stop == h) & (f_lo <= stop), t, erst_stop)

        traf_z, traf_s = erst_ziel < h, erst_stop < h
        # ⚠️ MEHRDEUTIG: beide in DERSELBEN Stunde - Reihenfolge unbekannt
        unklar = traf_z & traf_s & (erst_ziel == erst_stop)
        ist_ziel = traf_z & ~unklar & (~traf_s | (erst_ziel < erst_stop))
        ist_stop = traf_s & ~unklar & (~traf_z | (erst_stop < erst_ziel))
        offen = ~traf_z & ~traf_s

        a = ergebnis.setdefault(h, {k: [] for k in
                                    ("schluss", "mfe", "mae", "ziel", "stop",
                                     "offen", "unklar", "spaet_z", "spaet_s")})
        a["schluss"].append((cl[idx + h] - e) / s)
        a["mfe"].append((mfe - e) / s)
        a["mae"].append((mae - e) / s)
        a["ziel"].append(ist_ziel)
        a["stop"].append(ist_stop)
        a["offen"].append(offen)
        a["unklar"].append(unklar)
        a["spaet_z"].append(erst_ziel[ist_ziel].astype(float))
        a["spaet_s"].append(erst_stop[ist_stop].astype(float))


def main() -> int:
    global SKALIERT
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    SKALIERT = "--skaliert" in sys.argv

    print("=" * 88)
    print("WIE SCHARF SIND DIE BEWEGUNGEN - Nutzereinwand 24.09.")
    print("=" * 88)
    c = sqlite3.connect("file:%s?mode=ro" % QUELLE, uri=True)
    syms = [r[0] for r in c.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    if grenze:
        syms = syms[:grenze]
    print("  %d Symbole · Stop %s · CRV %.1f · Takt %d h · LONG"
          % (len(syms),
             "min(25%%, max(5%%, 0,75 x ATR14))" + (" x sqrt(H/24)  ⚠️ SKALIERT"
                                                    if SKALIERT else "  (PRODUKTION)"),
             CRV, TAKT))

    erg = {}
    for i, sym in enumerate(syms, 1):
        rows = c.execute("SELECT stunde, high, low, close FROM stundenkurse "
                         "WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
        if len(rows) < 500:
            continue
        st = [r[0] for r in rows]
        hi = np.array([r[1] for r in rows], float)
        lo = np.array([r[2] for r in rows], float)
        cl = np.array([r[3] for r in rows], float)
        atr = _atr_je_stunde(st, hi, lo, cl)
        if atr is None:
            continue
        _ein_symbol(hi, lo, cl, atr, erg, SKALIERT)
        if i % 25 == 0:
            print("  ... %d/%d" % (i, len(syms)))
    c.close()

    print()
    print("─" * 88)
    print("1) DER AUSGANG - und wie viel die Stundenbasis NICHT aufloest")
    print("─" * 88)
    print("  %-5s %9s   %7s %7s %7s  %10s" %
          ("H", "n", "Ziel%", "Stop%", "offen%", "MEHRDEUT%"))
    for h in HALTEDAUERN:
        a = erg[h]
        z = np.concatenate(a["ziel"]); s = np.concatenate(a["stop"])
        o = np.concatenate(a["offen"]); u = np.concatenate(a["unklar"])
        n = len(z)
        print("  %-5s %9s   %6.1f%% %6.1f%% %6.1f%%  %9.2f%%"
              % ("%dh" % h, f"{n:,}".replace(",", "."),
                 100 * z.mean(), 100 * s.mean(), 100 * o.mean(), 100 * u.mean()))

    print()
    print("─" * 88)
    print("2) DER EINWAND - war zwischendurch mehr da, als am Ende uebrig ist?")
    print("─" * 88)
    print("  %-5s %8s %8s %8s   %9s %9s" %
          ("H", "Schluss", "MFE", "MAE", "MFE-Schl", "Anteil>1R"))
    for h in HALTEDAUERN:
        a = erg[h]
        sc = np.concatenate(a["schluss"])
        mf = np.concatenate(a["mfe"]); ma = np.concatenate(a["mae"])
        gut = np.isfinite(sc) & np.isfinite(mf) & np.isfinite(ma)
        sc, mf, ma = sc[gut], mf[gut], ma[gut]
        # ⚠️ Anteil, bei dem MFE ueber 1 R lag, der Schluss aber darunter -
        # genau der Fall "kurz hoeher, dann wieder weg"
        weg = ((mf > 1.0) & (sc < 1.0)).mean()
        print("  %-5s %+8.4f %+8.4f %+8.4f   %+9.4f %8.1f%%"
              % ("%dh" % h, np.median(sc), np.median(mf), np.median(ma),
                 np.median(mf) - np.median(sc), 100 * weg))
    print("  (Mediane in R · MFE ist eine OBERGRENZE, kein handelbares Ergebnis)")

    print()
    print("─" * 88)
    print("3) WIE SCHNELL - Median der Stunden bis zur Beruehrung")
    print("─" * 88)
    print("  %-5s %12s %12s" % ("H", "bis Ziel", "bis Stop"))
    for h in HALTEDAUERN:
        a = erg[h]
        z = np.concatenate(a["spaet_z"]) if a["spaet_z"] else np.array([])
        s = np.concatenate(a["spaet_s"]) if a["spaet_s"] else np.array([])
        print("  %-5s %11.1f h %11.1f h"
              % ("%dh" % h, np.median(z) if len(z) else float("nan"),
                 np.median(s) if len(s) else float("nan")))

    print()
    print("─" * 88)
    print("WAS DAS ENTSCHEIDET")
    print("─" * 88)
    u6 = np.concatenate(erg[6]["unklar"]).mean()
    u72 = np.concatenate(erg[72]["unklar"]).mean()
    print("  MEHRDEUTIG bei 6h %.2f%% · bei 72h %.2f%%" % (100 * u6, 100 * u72))
    print("  ⚠️ Unter 2%% traegt die Stundenbasis die Reihenfolge.")
    print("     Darueber ist die Zielgroesse `barriere` auch hier nicht sauber")
    print("     und der Ausgang muss ueber `schluss_r` bewertet werden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
