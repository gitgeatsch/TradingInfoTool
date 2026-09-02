# -*- coding: utf-8 -*-
"""Wieviel vom Takt ist WIEDERHOLUNG derselben Empfehlung? (02.09.2026)

## Der Auftrag

Nutzervorgabe: *„1,1 Signale pro Asset ist besser — es muss ggf. auf
Assetebene nachgeschärft werden, dass nicht 'gleiche oder ähnliche'
Empfehlungen redundant sind."*

F-172 hat den Takt gemessen (133,2 Mails/Tag) und gezeigt, wo er
**entsteht** — bei NACHKAUFEN und ERÖFFNEN. Dieses Werkzeug fragt eine
Stufe tiefer: **wieviel davon ist neue Information, und wieviel ist
dieselbe Empfehlung noch einmal?**

## Die Zerlegung

Je Asset wird die Folge der Empfehlungen in der Zeit gelesen:

    NEU          eine andere Aktion als beim letzten Mal
    WIEDERHOLUNG dieselbe Aktion wie beim letzten Mal
    AEHNLICH     eine Aktion derselben KLASSE (Einstieg/Ausstieg), aber
                 ein anderes Wort - z. B. EROEFFNEN nach KAUFEN

⚠️ **Die dritte Klasse ist die interessante.** Ein Leser, der gestern
„KAUFEN" bekam und heute „ERÖFFNEN" liest, bekommt zweimal dieselbe
Botschaft in verschiedenen Worten. Für den Trichter sind das zwei
verschiedene Aktionen; für den Nutzer ist es eine.

## Und die Auswirkungen werden getrennt

    Bestand      hat das Asset einen Bestand? (dann ist NACHKAUFEN/
                 REDUZIEREN moeglich und die Sperren greifen nicht)
    Assetklasse  Krypto gegen Aktien/ETF/Rohstoffe

    python rechne_redundanz_je_asset.py --db <backup>
"""
import argparse
import collections
import datetime as dt
import sqlite3
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EINSTIEG = {"KAUFEN", "NACHKAUFEN", "ERÖFFNEN", "EROEFFNEN"}
AUSSTIEG = {"REDUZIEREN", "VERKAUFEN", "SCHLIESSEN"}
MAIL = EINSTIEG | AUSSTIEG


def klasse(a):
    return "Einstieg" if a in EINSTIEG else ("Ausstieg" if a in AUSSTIEG
                                             else "Nichts")


def lade(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    aus = []
    for sym, ts, akt, strat, instr in c.execute(
            "SELECT symbol, created_at, action, strategie, "
            "COALESCE(richtung,'') FROM signals "
            "WHERE quelle_kette='rollen' AND action IS NOT NULL "
            "ORDER BY symbol, created_at"):
        try:
            z = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            continue
        aus.append({"sym": str(sym).upper(), "zeit": z,
                    "aktion": str(akt).upper().strip(),
                    "strategie": strat})
    # Bestand aus holdings
    # ⚠️ DIE SPALTE HEISST `quantity`, NICHT `menge` (Fehler vom 02.09.,
    # gefunden weil die Auswertung 0 Bestaende meldete - bei 56 Zeilen in
    # der Tabelle). Ein leises `except` haette das verschluckt; die Null
    # fiel nur auf, weil sie unglaubwuerdig war.
    #
    # ⚠️ UND GESTAKTES ZAEHLT MIT. Der Lauf meldet "vollstaendig gestakt,
    # nicht frei verkaeuflich" - das ist Bestand, auch wenn er nicht
    # verkaeuflich ist. Wer ihn ausliesse, zaehlte gehaltene Werte als
    # bestandsfrei und wuerde die Sperren falsch zuordnen.
    best = set()
    for s, q, st in c.execute(
            "SELECT symbol, COALESCE(quantity,0), COALESCE(staked_quantity,0) "
            "FROM holdings"):
        if float(q) > 0 or float(st) > 0:
            best.add(str(s).upper())
    c.close()
    return aus, best


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--fenster", type=float, default=24.0,
                   help="Stunden, innerhalb derer eine Wiederholung zaehlt")
    a = p.parse_args()

    sig, bestand = lade(a.db)
    mails = [s for s in sig if s["aktion"] in MAIL]
    tage = len({s["zeit"].date() for s in sig})
    print("=" * 92)
    print("REDUNDANZ JE ASSET — %d Mails ueber %d Tage" % (len(mails), tage))
    print("=" * 92)
    print("  Bestand laut `holdings`: %d Werte" % len(bestand))
    print()

    # ---- 1: die Zerlegung ----------------------------------------------
    je_sym = collections.defaultdict(list)
    for s in mails:
        je_sym[s["sym"]].append(s)
    neu = wied = aehn = 0
    abstaende = []
    je_sym_z = {}
    for sym, folge in je_sym.items():
        folge.sort(key=lambda x: x["zeit"])
        n = w = ae = 0
        letzte = None
        for s in folge:
            if letzte is None:
                n += 1
            else:
                std = (s["zeit"] - letzte["zeit"]).total_seconds() / 3600.0
                abstaende.append(std)
                if std > a.fenster:
                    n += 1
                elif s["aktion"] == letzte["aktion"]:
                    w += 1
                elif klasse(s["aktion"]) == klasse(letzte["aktion"]):
                    ae += 1
                else:
                    n += 1
            letzte = s
        neu += n; wied += w; aehn += ae
        je_sym_z[sym] = (n, w, ae, len(folge))
    g = neu + wied + aehn
    print("  Innerhalb von %.0f Stunden je Asset:" % a.fenster)
    print("    NEU (andere Botschaft)      %5d   %5.1f %%   (%.1f/Tag)"
          % (neu, 100*neu/g, neu/tage))
    print("    WIEDERHOLUNG (gleiches Wort)%5d   %5.1f %%   (%.1f/Tag)"
          % (wied, 100*wied/g, wied/tage))
    print("    AEHNLICH (gleiche Klasse)   %5d   %5.1f %%   (%.1f/Tag)"
          % (aehn, 100*aehn/g, aehn/tage))
    print()
    print("    -> zusammengefasst blieben  %5d Mails  (%.1f/Tag statt %.1f)"
          % (neu, neu/tage, len(mails)/tage))
    if abstaende:
        q = np.quantile(abstaende, [.1, .25, .5, .75])
        print()
        print("  Abstand zwischen zwei Mails DESSELBEN Assets:")
        print("    Q10 %.1f h · Q25 %.1f h · Median %.1f h · Q75 %.1f h"
              % tuple(q))

    # ---- 2: getrennt nach Bestand --------------------------------------
    print()
    print("=" * 92)
    print("GETRENNT NACH BESTAND")
    print("=" * 92)
    print("  %-14s %7s %7s %8s %8s %8s"
          % ("", "Assets", "Mails", "je Tag", "NEU %", "Wdh+aehnl %"))
    for name, menge in (("MIT Bestand", bestand),
                        ("OHNE Bestand", None)):
        syms = [s for s in je_sym_z
                if (s in bestand) == (menge is not None)]
        if not syms:
            continue
        n = sum(je_sym_z[s][0] for s in syms)
        w = sum(je_sym_z[s][1] + je_sym_z[s][2] for s in syms)
        m = sum(je_sym_z[s][3] for s in syms)
        print("  %-14s %7d %7d %8.1f %7.1f %% %8.1f %%"
              % (name, len(syms), m, m/tage, 100*n/max(n+w,1),
                 100*w/max(n+w,1)))

    # ---- 3: je Asset, die lautesten -------------------------------------
    print()
    print("=" * 92)
    print("DIE ZWANZIG LAUTESTEN — was davon ist Wiederholung?")
    print("=" * 92)
    print("  %-10s %6s %6s %6s %6s   %8s  %s"
          % ("Asset", "Mails", "NEU", "Wdh", "aehnl", "je Tag", "Bestand"))
    for sym, (n, w, ae, m) in sorted(je_sym_z.items(),
                                     key=lambda x: -x[1][3])[:20]:
        print("  %-10s %6d %6d %6d %6d   %8.1f  %s"
              % (sym, m, n, w, ae, m/tage,
                 "ja" if sym in bestand else "-"))

    # ---- 4: die Strategie - greift der Cooldown ueberhaupt? -------------
    print()
    print("=" * 92)
    print("WARUM DER COOLDOWN NICHT GREIFT")
    print("=" * 92)
    mit_strat = sum(1 for s in sig if s["strategie"])
    print("  Signale mit gesetzter `strategie`: %d von %d (%.1f %%)"
          % (mit_strat, len(sig), 100*mit_strat/len(sig)))
    print("  ⚠️ `wiederholung.gesperrt_bis` schluesselt auf")
    print("     (symbol, instrument, strategie). Steht die Strategie nicht,")
    print("     ist der Schluessel unvollstaendig - und zwei Zellen")
    print("     desselben Assets teilen sich denselben Cooldown oder gar")
    print("     keinen.")


if __name__ == "__main__":
    main()
