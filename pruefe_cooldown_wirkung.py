# -*- coding: utf-8 -*-
"""Warum greift der Cooldown nicht? (02.09.2026)

## Der Widerspruch, der das ausgeloest hat

F-173 hat gemessen: zwischen zwei Mails DESSELBEN Assets liegen im Median
**3,7 Stunden** (Q10 3,4 · Q75 4,1). Die Vorgabe in
`wiederholung.VORGABE_STUNDEN` lautet aber:

    spot   15,0 Stunden
    hebel   3,5 Stunden

**Bei 15 Stunden Spot-Cooldown duerfte es alle 3,7 Stunden kein zweites
Signal geben.** Entweder greift der Cooldown nicht, oder er wird
umgangen, oder die Signale gehoeren verschiedenen Schluesseln.

## ⚠️ Meine erste Hypothese war falsch - und die Quelle sagt es

Ich hatte vermutet, der Schluessel sei unvollstaendig, weil `strategie`
nur in 33 % der Signale steht. **Die Abfrage in `gesperrt_bis` kennt die
Strategie aber gar nicht:**

    SELECT created_at FROM signals WHERE symbol = ?
      AND quelle_kette = 'rollen' AND <hebel-bedingung>
    ORDER BY created_at DESC LIMIT 1

Geschluesselt wird auf **(symbol, instrument)**. Die Strategie geht nur in
`stunden(...)` ein, also in die **Dauer**. Damit faellt meine Erklaerung -
und die echte Ursache ist noch offen.

## Was dieses Werkzeug prueft

  1  welche Dauer gilt tatsaechlich? (config gegen Vorgabe)
  2  wie viele Signalpaare liegen NAEHER beieinander als erlaubt?
  3  und wenn ja: gehoeren sie zu verschiedenen Schluesseln (spot/hebel),
     oder ist es dieselbe Zelle?
  4  Gegenprobe: `gesperrt_bis` gegen den echten Bestand laufen lassen -
     haette die Funktion an diesen Zeitpunkten gesperrt?

⚠️ Punkt 4 ist der eigentliche Nachweis. Die ersten drei rechnen ueber
die Daten; erst der vierte fragt die FUNKTION, die im Betrieb entscheidet.

    python pruefe_cooldown_wirkung.py --db <backup>
"""
import argparse
import collections
import datetime as dt
import sqlite3
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    a = p.parse_args()

    from agent import wiederholung as WH

    # ---- 1: welche Dauer gilt? -----------------------------------------
    print("=" * 92)
    print("1) WELCHE DAUER GILT?")
    print("=" * 92)
    print("  Vorgabe im Modul: %s" % WH.VORGABE_STUNDEN)
    try:
        import config as CFG
        cfg = CFG.load_config() if hasattr(CFG, "load_config") else {}
    except Exception:                                        # noqa: BLE001
        cfg = {}
    for instr in ("spot", "hebel"):
        for strat in (None, "einstieg", "akkumulation"):
            h = WH.stunden(instr, cfg, "krypto", strategie=strat)
            print("    %-6s / %-13s -> %5.1f h" % (instr, strat or "(ohne)", h))

    # ---- 2: die echten Abstaende je Schluessel --------------------------
    c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    sig = []
    for sym, ts, akt, heb in c.execute(
            "SELECT symbol, created_at, action, hebel FROM signals "
            "WHERE quelle_kette='rollen' ORDER BY symbol, created_at"):
        try:
            z = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            continue
        if z.tzinfo is None:
            z = z.replace(tzinfo=dt.timezone.utc)
        sig.append({"sym": str(sym).upper(), "zeit": z,
                    "aktion": str(akt or "").upper(),
                    "instr": "hebel" if heb is not None else "spot"})
    print()
    print("=" * 92)
    print("2) LIEGEN SIGNALE NAEHER BEIEINANDER ALS ERLAUBT?")
    print("=" * 92)
    print("  %d Signale, davon spot %d / hebel %d"
          % (len(sig), sum(1 for s in sig if s["instr"] == "spot"),
             sum(1 for s in sig if s["instr"] == "hebel")))
    je = collections.defaultdict(list)
    for s in sig:
        je[(s["sym"], s["instr"])].append(s)
    verletzt = collections.Counter()
    abstaende = collections.defaultdict(list)
    for (sym, instr), folge in je.items():
        folge.sort(key=lambda x: x["zeit"])
        grenze = WH.stunden(instr, cfg, "krypto")
        for x, y in zip(folge, folge[1:]):
            std = (y["zeit"] - x["zeit"]).total_seconds() / 3600.0
            abstaende[instr].append(std)
            if std < grenze - 0.01:
                verletzt[instr] += 1
    for instr in sorted(abstaende):
        n = len(abstaende[instr])
        g = WH.stunden(instr, cfg, "krypto")
        med = np.median(abstaende[instr])
        print()
        print("  %s (Cooldown %.1f h): %d Paare, Median-Abstand %.1f h"
              % (instr, g, n, med))
        print("    NAEHER als erlaubt: %d von %d  = %.1f %%"
              % (verletzt[instr], n, 100 * verletzt[instr] / max(n, 1)))

    # ---- 3: Gegenprobe - haette `gesperrt_bis` gesperrt? ---------------
    #
    # ⚠️⚠️ MEINE ERSTE FASSUNG WAR KAPUTT, und sie meldete 100 %.
    #
    # `gesperrt_bis` liest das JUENGSTE Signal des Symbols aus der Tabelle -
    # in einer fertigen Historie ist das oft eines, das NACH dem gerade
    # betrachteten Zeitpunkt liegt. Die Funktion sah die Zukunft. Aufgefallen
    # ist es an den Beispielen: "Signal 16.08., gesperrt bis 22.08." - ein
    # Sperrende NACH dem Signal kann nicht die Ursache seiner Sperre sein.
    #
    # Richtig ist der Nachbau des Betriebs: eine leere Kopie, in die
    # chronologisch eingefuegt wird, und VOR jedem Einfuegen wird gefragt.
    print()
    print("=" * 92)
    print("3) GEGENPROBE — die FUNKTION, chronologisch nachgestellt")
    print("=" * 92)
    import tempfile, os
    tmp = os.path.join(tempfile.gettempdir(), "cooldown_nachbau.db")
    if os.path.exists(tmp):
        os.remove(tmp)
    quelle = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    ziel = sqlite3.connect(tmp)
    quelle.backup(ziel)          # ⚠️ nur ueber backup(), nie als Dateikopie
    quelle.close()
    ziel.execute("DELETE FROM signals")
    ziel.commit()
    spalten = [r[1] for r in ziel.execute("PRAGMA table_info(signals)")]
    q2 = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    zeilen = list(q2.execute(
        "SELECT %s FROM signals WHERE quelle_kette='rollen' "
        "ORDER BY created_at" % ", ".join(spalten)))
    q2.close()
    idx = {n: k for k, n in enumerate(spalten)}
    gesperrt = frei = 0
    beispiele = []
    for z in zeilen:
        sym = str(z[idx["symbol"]]).upper()
        ts = str(z[idx["created_at"]])
        instr = "hebel" if z[idx["hebel"]] is not None else "spot"
        strat = z[idx["strategie"]] if "strategie" in idx else None
        bis = WH.gesperrt_bis(ziel, sym, instr, config=cfg, gruppe="krypto",
                              jetzt=ts, strategie=strat)
        if bis:
            gesperrt += 1
            if len(beispiele) < 5:
                beispiele.append((sym, instr, ts[:16], bis[:16]))
        else:
            frei += 1
        ziel.execute("INSERT INTO signals (%s) VALUES (%s)"
                     % (", ".join(spalten), ", ".join("?" * len(spalten))), z)
    ziel.commit()
    ziel.close()
    os.remove(tmp)
    n = gesperrt + frei
    print("  %d Signale chronologisch nachgestellt:" % n)
    print("    die Funktion HAETTE GESPERRT:      %5d  (%.1f %%)"
          % (gesperrt, 100 * gesperrt / max(n, 1)))
    print("    die Funktion haette durchgelassen: %5d  (%.1f %%)"
          % (frei, 100 * frei / max(n, 1)))
    for b in beispiele:
        print("      z.B. %-8s %-5s Signal %s, gesperrt bis %s" % b)
    c.close()

    print()
    print("  LESART: sperrt die Funktion fast immer, aber die Signale sind")
    print("  trotzdem da, dann wird sie im Lauf NICHT GEFRAGT oder ihr")
    print("  Ergebnis nicht befolgt. Sperrt sie selten, liegt es an der")
    print("  Dauer oder am Schluessel.")


if __name__ == "__main__":
    main()
