# -*- coding: utf-8 -*-
"""Schritt 1: die GRUNDLINIE der Hebelgeometrie (05.09.2026)

Teil der vereinbarten Reihenfolge zu N-38:

    0 Entscheidung   ✔ erledigt - der Ankerwechsel trifft den HEBEL, nicht
                       den Betrag; Spot bleibt unberuehrt (F-216)
    1 Referenzlauf   <- DIESE DATEI
    2 Zielzustand    alle vier Komponenten aus N-38 durchdefiniert
    3 Machbarkeit    je Komponente
    4 Wirkungslauf   Zielzustand gegen diese Grundlinie
    5 Bau            schrittweise, jeder Schritt gegen dieselbe Grundlinie

## Warum ein WERKZEUG und keine Einmalabfrage

Eine einzelne Messung sagt fuer die Dimensionierung nichts. Der Sinn ist
die Grundlinie, gegen die Schritt 4 und jeder Bauschritt in 5 verglichen
wird - mit DERSELBEN Rechnung, sonst vergleicht man zwei Definitionen.

## ⚠️ Zwei Fallen, beide heute erlebt

1 ALT UND NEU TRENNEN (Nutzerwarnung 05.09.). `signals` enthaelt beide
  Ketten: 3.524 mit `quelle_kette='rollen'`, 2.983 ohne. Die alte Kette
  mitzuzaehlen verfaelscht jede Verteilung. `hebel_signals` ist ebenfalls
  Altbestand (letztes Signal 10.08.).

2 DIE RICHTIGE STOP-DEFINITION. `entry_usd`/`stop_loss_usd` sind LEERE
  Altfelder; gefuellt sind die Bereiche `_von`/`_bis`. Und die Rechnung
  benutzt die MITTE beider Bereiche - nur damit ergibt sich der
  konfigurierte `verlustanteil` von 6 %. Mit den Unterkanten kaeme 4,2 %
  heraus (mein Fehler vom 05.09.).

## Die eingebaute Gegenpruefung

`verlustanteil = hebel x stop_rel` muss den Wert aus
`Basisinfos/config.yaml` treffen. Weicht er ab, stimmt die Stop-Definition
nicht - dann gilt keine Zahl darunter.

    python referenzlauf_hebelgeometrie.py [--db PFAD] [--seit 2026-08-29]
"""
from __future__ import annotations

import argparse
import sqlite3
import statistics as st
import sys

import numpy as np
import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIG = "Basisinfos/config.yaml"


def _config_verlustanteil(instrument: str = "spot") -> float | None:
    try:
        cfg = yaml.safe_load(open(CONFIG, encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return None
    for wurzel in (("risiko", "rollen_kette"), ("rollen_kette",)):
        d = cfg
        for k in wurzel:
            d = (d or {}).get(k) or {}
        v = (d.get("verlustanteil") or {}).get(instrument)
        if v is not None:
            return float(v)
    return None


def _mitte(von, bis):
    """Die Mitte eines Bereichs - `bis` darf fehlen."""
    if von is None:
        return None
    return (float(von) + float(bis)) / 2.0 if bis else float(von)


def lade(db: str, seit: str) -> list[dict]:
    """Nur die NEUE Kette, nur mit vollstaendiger Geometrie."""
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    aus = []
    for sym, ts, heb, ev, eb, sv, sb, pos, act in c.execute(
            "SELECT symbol, created_at, hebel, entry_usd_von, entry_usd_bis, "
            "stop_loss_usd_von, stop_loss_usd_bis, position_size_eur, action "
            "FROM signals WHERE quelle_kette='rollen' AND created_at>=? "
            "ORDER BY created_at", (seit,)):
        e = _mitte(ev, eb)
        s = _mitte(sv, sb)
        if not e or not s or e <= 0:
            continue
        stop_rel = (e - s) / e
        if not 0 < stop_rel < 0.6:
            continue
        aus.append({"sym": sym, "zeit": ts, "hebel": heb,
                    "stop_rel": stop_rel, "einsatz": pos, "action": act})
    c.close()
    return aus


def _verteilung(name: str, werte: list, einheit: str = "") -> None:
    if not werte:
        print("  %-24s keine Werte" % name)
        return
    a = np.array(werte, float)
    print("  %-24s n=%4d · Median %7.2f%s · P10 %6.2f · P90 %6.2f · max %7.2f"
          % (name, a.size, np.median(a), einheit,
             np.percentile(a, 10), np.percentile(a, 90), a.max()))


def bericht(zeilen: list[dict], titel: str) -> dict:
    print()
    print("=" * 92)
    print("GRUNDLINIE — %s" % titel)
    print("=" * 92)
    if not zeilen:
        print("  keine Zeilen")
        return {}
    print("  %d Signale der NEUEN Kette · %s .. %s"
          % (len(zeilen), zeilen[0]["zeit"][:16], zeilen[-1]["zeit"][:16]))
    print()

    # ---- die eingebaute Gegenpruefung -------------------------------
    va_cfg = _config_verlustanteil()
    va_ist = [z["hebel"] * z["stop_rel"] for z in zeilen
              if z["hebel"] and z["hebel"] > 1.0]
    print("  GEGENPRUEFUNG — reproduziert die Rechnung den config-Wert?")
    if va_cfg is None:
        print("    config nicht lesbar - Befund ungeprueft")
    elif va_ist:
        gem = st.median(va_ist)
        ab = abs(gem - va_cfg)
        print("    config verlustanteil %.3f · gemessen %.3f · Abweichung %.4f  %s"
              % (va_cfg, gem, ab,
                 "OK" if ab < 0.005 else "⚠️⚠️ WEICHT AB - Stop-Definition pruefen"))
    print()

    print("  DIE VIER GROESSEN")
    _verteilung("Einsatz (EUR)", [z["einsatz"] for z in zeilen if z["einsatz"]])
    _verteilung("Stopabstand (%)", [100 * z["stop_rel"] for z in zeilen], " %")
    _verteilung("Hebel", [z["hebel"] for z in zeilen if z["hebel"]])
    _verteilung("Risiko (EUR)",
                [z["hebel"] * z["stop_rel"] * z["einsatz"] for z in zeilen
                 if z["hebel"] and z["einsatz"]])
    print()

    heb = [z["hebel"] for z in zeilen if z["hebel"]]
    print("  HEBELVERTEILUNG — wieviel waere nach der neuen Regel ueberhaupt Hebel?")
    for lo, hi, lab in ((0, 1.0001, "genau 1,0  (Spot)"),
                        (1.0001, 2.0, "1,0 - 2,0  (nach neuer Regel KEIN Hebel)"),
                        (2.0, 5.0, "2,0 - 5,0  (Hebel)"),
                        (5.0, 10.0, "5,0 - 10,0 (Hebel)"),
                        (10.0, 1e9, "ueber 10   (Deckel)")):
        n = sum(1 for h in heb if lo <= h < hi)
        print("    %-42s %5d  (%4.1f %%)" % (lab, n, 100 * n / max(len(heb), 1)))
    print()

    print("  DURCHLASSMENGE")
    tage = len({z["zeit"][:10] for z in zeilen})
    print("    %d Signale ueber %d Tage  ->  %.1f je Tag" % (len(zeilen), tage, len(zeilen) / max(tage, 1)))
    from collections import Counter
    for a, n in Counter(z["action"] for z in zeilen).most_common(6):
        print("    %-16s %5d" % (a, n))
    return {"n": len(zeilen), "hebel": heb}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=None)
    p.add_argument("--seit", default="2026-08-29",
                   help="Vorgabe: nach der Config-Aenderung vom 28.08.")
    a = p.parse_args()
    db = a.db
    if not db:
        import glob
        kand = sorted(glob.glob(
            "C:/Users/Geatsch/AppData/Local/Temp/claude/*/*/scratchpad/nb_*.db"))
        db = kand[-1] if kand else "data/tradinginfotool.db"
    print("Datenbank: %s" % db)
    bericht(lade(db, a.seit), "heutiger Stand, seit %s" % a.seit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
