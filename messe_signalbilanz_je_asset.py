"""SIGNALBILANZ JE ASSET (nicht verwechseln mit messe_signalbilanz.py, Kapitel 125/126) - stehend bei jeder Aenderung der REGEL0 (Nutzer 01.10.2026).

*"Hier musst du mir die Auswirkungen konkret mitteilen - aktuell wissen wir nicht, ob ueberhaupt und wie viele 'echte Signale je Asset'
ankommen werden, z.B. BTC, ETH, LINK - dies muessen wir ohnehin je Anpassung der REGEL0 durchfuehren."* - und: *"bitte fuer alle Assets,
welche in der Watchlist, Portfolio bzw. Bestand sind."*

Zeigt je Asset der WATCHLIST (Krypto), des BESTANDS und der HEBEL-LISTE die Zahl der Signale je Jahr VORHER (REGEL0) und NACHHER
(REGELn), dazu Summe, Median je Asset und die Assets, die mehr als die Haelfte verlieren. Assets ohne Signal werden mit Grund genannt
(keine Stundendaten in der Messmenge).

Listenquelle: der NB-Teilexport (``nb_betriebsdaten_T440.txt`` im Austauschordner bzw. ``--nb <datei>``) - das ist der Betriebsstand.
Fehlt er, die Desktop-Kopie (``Basisinfos/config.yaml``, ``data/tradinginfotool.db`` nur lesend) mit Vermerk.

    python messe_signalbilanz_je_asset.py --vorher <einstiege.csv> --nachher <einstiege.csv>
    python messe_signalbilanz_je_asset.py --liq data/_vergleich/l_liq_bestand.csv --x 2000000      (L1: Filter Liquiditaet >= X)

Einstiegsdateien: ``symbol;stunde;...`` (Stunde = Stunden seit 2020-01-01), wie ``kern48jb_einstiege_<m>.csv`` oder ``l_liq_<m>.csv``.
Nur lesen, keine Netzabfrage.
"""
from __future__ import annotations

import csv
import os
import re
import sqlite3
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
B0 = datetime(2020, 1, 1)


def _drive():
    for b in ("G", "K", "H", "E", "F"):
        for o in ("My Drive", "Meine Ablage"):
            if os.path.isdir("%s:/%s" % (b, o)):
                return "%s:/%s" % (b, o)
    return None


def listen(nb=None):
    """-> (quelle, {'Watchlist': [...], 'Bestand': [...], 'Hebel': [...]})"""
    if nb is None and _drive():
        k = os.path.join(_drive(), "Claude_Austauschordner", "Notebook_Analysedaten", "nb_betriebsdaten_T440.txt")
        nb = k if os.path.exists(k) else None
    aus = {}
    if nb:
        txt = open(nb, encoding="utf-8").read()
        for key, muster in (("Hebel", r"HEBEL-LISTE[^:]*:\s*\d+\s*-\s*(.*)"), ("Watchlist", r"WATCHLIST krypto[^:]*:\s*\d+\s*-\s*(.*)"),
                            ("Bestand", r"BESTAND \(holdings[^:]*:\s*\d+\s*-\s*(.*)")):
            m = re.search(muster, txt)
            if m:
                aus[key] = [s.strip() for s in m.group(1).split(",") if s.strip()]
        stand = re.search(r"- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - Geraet (\S+)", txt)
        quelle = "NB-Teilexport %s (%s)" % (stand.group(1) if stand else "?", os.path.basename(nb))
        if len(aus) == 3:
            return quelle, aus
        quelle += " - unvollstaendig, Rest aus der Desktop-Kopie"
    else:
        quelle = "⚠️ Desktop-Kopie (kein NB-Teilexport gefunden)"
    if "Watchlist" not in aus:
        import yaml
        cfg = yaml.safe_load(open(os.path.join(HIER, "Basisinfos", "config.yaml"), encoding="utf-8")) or {}
        aus["Watchlist"] = sorted(str(e.get("symbol")) for e in cfg.get("watchlist") or [] if (e.get("assetklasse") or "krypto") == "krypto")
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(HIER, "data", "tradinginfotool.db").replace("\\", "/"), uri=True)
    if "Bestand" not in aus:
        aus["Bestand"] = [r[0] for r in c.execute("SELECT symbol FROM holdings WHERE COALESCE(quantity, 0) > 0 ORDER BY symbol")]
    if "Hebel" not in aus:
        aus["Hebel"] = [r[0] for r in c.execute("SELECT symbol FROM asset_hebel_settings WHERE hebel_pruefung_erlaubt ORDER BY symbol")]
    c.close()
    return quelle, aus


def lies(p, x=None):
    """-> Counter[(symbol, jahr)]; bei x: nur Zeilen mit liq_usd >= x."""
    z = Counter()
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if x is not None:
                try:
                    if not float(r["liq_usd"]) >= x:
                        continue
                except ValueError:
                    continue
            z[(r["symbol"], (B0 + timedelta(hours=int(r["stunde"]))).year)] += 1
    return z


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    arg = sys.argv
    if "--liq" in arg:
        p = arg[arg.index("--liq") + 1]; x = float(arg[arg.index("--x") + 1])
        v, n_ = lies(p), lies(p, x)
        was = "Filter Liquiditaet >= %.1f Mio USD (%s)" % (x / 1e6, os.path.basename(p))
    else:
        v = lies(arg[arg.index("--vorher") + 1]); n_ = lies(arg[arg.index("--nachher") + 1])
        was = "%s -> %s" % (os.path.basename(arg[arg.index("--vorher") + 1]), os.path.basename(arg[arg.index("--nachher") + 1]))
    quelle, L = listen(arg[arg.index("--nb") + 1] if "--nb" in arg else None)
    # Zuordnung Bitpanda -> Binance (Basisinfos/symbol_zuordnung.csv): die Einstiegsdateien tragen das BINANCE-Kuerzel (z. B. 1000CAT, CC)
    zu = {}
    with open(os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv"), encoding="utf-8") as f_:
        for r_ in csv.DictReader(f_, delimiter=";"):
            zu[r_["bitpanda"]] = r_["binance"]
    v = Counter({(next((b for b, bn in zu.items() if bn == s), s), j): k for (s, j), k in v.items()})
    n_ = Counter({(next((b for b, bn in zu.items() if bn == s), s), j): k for (s, j), k in n_.items()})
    jahre = sorted({j for _, j in v} | {j for _, j in n_})
    gemessen = {s for s, _ in v} | {s for s, _ in n_}       # vorher ODER nachher - neue Assets haben vorher null
    alle = sorted(set(L["Watchlist"]) | set(L["Bestand"]) | set(L["Hebel"]))
    print("=" * 110)
    print("SIGNALBILANZ JE ASSET · %s · Jahre %s" % (was, ", ".join(map(str, jahre))))
    print("Listen: %s · Watchlist %d · Bestand %d · Hebel-Liste %d · zusammen %d" % (
        quelle, len(L["Watchlist"]), len(L["Bestand"]), len(L["Hebel"]), len(alle)))
    print("=" * 110)
    print("  %-9s %-5s | %s | gesamt" % ("Asset", "W B H", " | ".join("%d vorher->nachher" % j for j in jahre)))
    ohne, verl = [], []
    for s in alle:
        fl = " ".join("x" if s in L[k] else "." for k in ("Watchlist", "Bestand", "Hebel"))
        if s not in gemessen:
            ohne.append((s, fl))
            continue
        a_ = sum(v[(s, j)] for j in jahre); b_ = sum(n_[(s, j)] for j in jahre)
        if b_ < 0.5 * a_:
            verl.append(s)
        print("  %-9s %-5s | %s | %4d -> %4d%s" % (s, fl, " | ".join("%4d -> %4d     " % (v[(s, j)], n_[(s, j)]) for j in jahre),
                                                   a_, b_, "  ⚠️ mehr als die Haelfte weg" if b_ < 0.5 * a_ else ""))
    gm = [s for s in alle if s in gemessen]
    if gm:
        tv = [sum(v[(s, j)] for j in jahre) for s in gm]; tn = [sum(n_[(s, j)] for j in jahre) for s in gm]
        print("  SUMME (%d gemessene Assets dieser Listen): %d -> %d (%.0f %%) · Median je Asset %.0f -> %.0f" % (
            len(gm), sum(tv), sum(tn), 100.0 * sum(tn) / max(sum(tv), 1), statistics.median(tv), statistics.median(tn)))
    print("  mehr als die Haelfte verloren (%d): %s" % (len(verl), ", ".join(verl) or "keine"))
    print("  OHNE Signal in der Messmenge (%d, keine Stundenkurse oder kein Krypto): %s" % (
        len(ohne), ", ".join("%s [%s]" % (s, f) for s, f in ohne)))
    print("  Legende W B H = Watchlist / Bestand / Hebel-Liste")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
